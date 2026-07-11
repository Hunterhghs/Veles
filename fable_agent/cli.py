"""Fable CLI.

Usage:
    fable run "Add a /health endpoint to the API"   # run the full agent
    fable mcp --workspace .                          # start the MCP server
    fable prompts [role]                             # print system prompts
    fable memory recent|search <query>               # inspect memory
    fable tools                                      # list the tool suite
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fable_agent import __version__
from fable_agent.config import FableConfig
from fable_agent.memory import create_memory
from fable_agent.prompts import AGENT_ROLES, load_prompt
from fable_agent.tools import default_registry


def _print_event(agent: str, event: str, detail: str) -> None:
    if event == "start":
        print(f"[{agent}] starting: {detail[:120]}")
    elif event == "tool":
        print(f"[{agent}] tool: {detail}")
    elif event == "finish":
        print(f"[{agent}] done.")
    elif event == "budget_exhausted":
        print(f"[{agent}] stopped: iteration limit ({detail}) reached.")


def cmd_run(args: argparse.Namespace) -> int:
    from fable_agent.agents.orchestrator import Orchestrator

    config = FableConfig.load(
        workspace=args.workspace,
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
    )
    print(f"fable v{__version__} | provider={config.provider} model={config.model}")
    print(f"workspace: {config.workspace}\n")

    orchestrator = Orchestrator(config=config, on_event=_print_event)
    result = orchestrator.run_task(args.task)

    print("\n" + "=" * 72)
    print(result.output)
    return 0 if result.success else 1


def cmd_mcp(args: argparse.Namespace) -> int:
    from fable_agent.mcp_server.server import build_server

    config = FableConfig.load(workspace=args.workspace)
    server = build_server(config)
    server.run(transport="stdio")
    return 0


def cmd_prompts(args: argparse.Namespace) -> int:
    roles = [args.role] if args.role else list(AGENT_ROLES)
    for role in roles:
        print(f"{'=' * 24} {role} {'=' * 24}")
        print(load_prompt(role))
        print()
    return 0


def cmd_tools(args: argparse.Namespace) -> int:
    registry = default_registry(Path(args.workspace).resolve())
    for spec in registry.specs():
        params = ", ".join(spec.parameters.get("properties", {}))
        print(f"{spec.name}({params})")
        print(f"    {spec.description}\n")
    return 0


def cmd_memory(args: argparse.Namespace) -> int:
    config = FableConfig.load(workspace=args.workspace)
    memory = create_memory(config.memory_backend, config.memory_path)

    if args.action == "recent":
        entries = memory.recent(limit=args.limit)
    else:  # search
        if not args.query:
            print("memory search requires a query", file=sys.stderr)
            return 2
        entries = memory.search(" ".join(args.query), limit=args.limit)

    if not entries:
        print("(no memories)")
        return 0
    for e in entries:
        print(f"[{e.category}] {e.content}  (id={e.id})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fable", description="Fable AI coding agent framework.")
    parser.add_argument("--version", action="version", version=f"fable-agent {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run the orchestrator on a task.")
    p_run.add_argument("task", help="The task to perform.")
    p_run.add_argument("--workspace", default=".", help="Project directory to work in.")
    p_run.add_argument(
        "--provider",
        default=None,
        help="anthropic | openai | deepseek | ollama | lmstudio | openai-compatible "
        "(ollama/lmstudio/openai-compatible need no API key)",
    )
    p_run.add_argument("--model", default=None, help="Model name, e.g. claude-sonnet-4-5, gpt-4o, or qwen2.5-coder.")
    p_run.add_argument("--base-url", default=None, help="Base URL for OpenAI-compatible endpoints.")
    p_run.set_defaults(func=cmd_run)

    p_mcp = sub.add_parser("mcp", help="Start the MCP server (stdio).")
    p_mcp.add_argument("--workspace", default=".", help="Workspace to sandbox tools to.")
    p_mcp.set_defaults(func=cmd_mcp)

    p_prompts = sub.add_parser("prompts", help="Print exported system prompts.")
    p_prompts.add_argument("role", nargs="?", choices=AGENT_ROLES, help="A specific role (optional).")
    p_prompts.set_defaults(func=cmd_prompts)

    p_tools = sub.add_parser("tools", help="List the tool suite and schemas.")
    p_tools.add_argument("--workspace", default=".")
    p_tools.set_defaults(func=cmd_tools)

    p_mem = sub.add_parser("memory", help="Inspect long-term memory.")
    p_mem.add_argument("action", choices=["recent", "search"])
    p_mem.add_argument("query", nargs="*", help="Search keywords (for 'search').")
    p_mem.add_argument("--workspace", default=".")
    p_mem.add_argument("--limit", type=int, default=10)
    p_mem.set_defaults(func=cmd_memory)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
