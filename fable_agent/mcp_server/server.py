"""MCP server: exposes Fable's tools, memory, and system prompts.

Any MCP-capable client (Claude Code, Roo Code, Cursor, custom scripts,
Reasonix adapters, ...) can connect to this server over stdio and use:

Tools:
- read_file, write_file, edit_file, list_dir, grep, glob, run_command
  (the full Fable tooling suite, sandboxed to the chosen workspace)
- memory_remember / memory_recall (shared long-term memory)
- run_agent (drive the full orchestrator + sub-agent pipeline on a task,
  when an API key is configured)

Prompts:
- fable_orchestrator / fable_coder / fable_verifier / fable_architect
  (the system prompts, so external agents can adopt Fable's roles)

Run: ``fable mcp --workspace /path/to/project`` or
``python -m fable_agent.mcp_server``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fable_agent.config import FableConfig
from fable_agent.memory import create_memory
from fable_agent.prompts import AGENT_ROLES, load_prompt
from fable_agent.tools import default_registry


def build_server(config: FableConfig):
    """Construct the FastMCP server with all Fable capabilities attached."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as e:
        raise ImportError(
            "The 'mcp' package is required for the MCP server. "
            "Install it with: pip install 'fable-agent[mcp]' or pip install mcp"
        ) from e

    server = FastMCP(
        "fable-agent",
        instructions=(
            "Fable coding agent tools. File and search tools are sandboxed to "
            f"the workspace at {config.workspace}. Use memory_remember and "
            "memory_recall to persist context across sessions. Use run_agent "
            "to delegate a whole task to Fable's orchestrator."
        ),
    )

    registry = default_registry(config.workspace, config.command_timeout)
    memory = create_memory(config.memory_backend, config.memory_path)

    def call(tool_name: str, **kwargs) -> str:
        return registry.execute(tool_name, kwargs).render()

    # --- Tooling suite -----------------------------------------------------

    @server.tool(name="read_file")
    def read_file(path: str, offset: int = 1, limit: int | None = None) -> str:
        """Read a text file from the workspace, with 1-based line numbers."""
        return call("read_file", path=path, offset=offset, limit=limit)

    @server.tool(name="write_file")
    def write_file(path: str, content: str) -> str:
        """Create or overwrite a file in the workspace with the given content."""
        return call("write_file", path=path, content=content)

    @server.tool(name="edit_file")
    def edit_file(path: str, old_string: str, new_string: str) -> str:
        """Edit a file by exact, unique string replacement. Returns a unified diff."""
        return call("edit_file", path=path, old_string=old_string, new_string=new_string)

    @server.tool(name="list_dir")
    def list_dir(path: str = ".") -> str:
        """List files and directories at a path in the workspace."""
        return call("list_dir", path=path)

    @server.tool(name="grep")
    def grep(pattern: str, glob: str | None = None, case_insensitive: bool = False) -> str:
        """Regex-search file contents in the workspace; returns path:line:content."""
        return call("grep", pattern=pattern, glob=glob, case_insensitive=case_insensitive)

    @server.tool(name="glob")
    def glob_files(pattern: str) -> str:
        """Find files in the workspace whose names match a glob pattern."""
        return call("glob", pattern=pattern)

    @server.tool(name="run_command")
    def run_command(command: str, cwd: str | None = None) -> str:
        """Run a shell command in the workspace; returns exit code and output."""
        return call("run_command", command=command, cwd=cwd)

    # --- Memory ------------------------------------------------------------

    @server.tool(name="memory_remember")
    def memory_remember(content: str, category: str = "note", tags: list[str] | None = None) -> str:
        """Save a fact, decision, or task summary to Fable's long-term memory."""
        entry_id = memory.remember(content, category=category, tags=tags or [])
        return f"Remembered (id={entry_id})."

    @server.tool(name="memory_recall")
    def memory_recall(query: str, limit: int = 5) -> str:
        """Search Fable's long-term memory for context from previous sessions."""
        entries = memory.search(query, limit=limit)
        if not entries:
            return "No matching memories."
        return "\n".join(f"- [{e.category}] {e.content} (id={e.id})" for e in entries)

    # --- Full agent pipeline as a single tool --------------------------------

    @server.tool(name="run_agent")
    def run_agent(task: str) -> str:
        """Run Fable's full orchestrator (plan -> code -> verify) on a task.

        Requires an LLM API key in the server's environment
        (FABLE_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY).
        """
        from fable_agent.agents.orchestrator import Orchestrator

        orchestrator = Orchestrator(config=config, memory=memory)
        result = orchestrator.run_task(task)
        return result.output

    # --- System prompts, exported for external agents -----------------------

    for role in AGENT_ROLES:
        _register_prompt(server, role)

    return server


def _register_prompt(server, role: str) -> None:
    @server.prompt(name=f"fable_{role}", description=f"Fable's {role} system prompt.")
    def prompt_fn() -> str:
        return load_prompt(role)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Fable MCP server (stdio transport).")
    parser.add_argument("--workspace", default=".", help="Workspace directory to sandbox tools to.")
    args = parser.parse_args(argv)

    config = FableConfig.load(workspace=Path(args.workspace))
    server = build_server(config)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
