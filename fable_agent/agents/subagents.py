"""Specialized sub-agents: Coder, Verifier, Architect, and Reporter.

Each is the same core Agent loop with a role-specific system prompt and
an appropriately restricted toolset:

- Coder: full read/write/execute access.
- Verifier: read + execute (can run tests, cannot edit files).
- Architect: read-only exploration.
- Reporter: full read/write/execute access (writes documents, runs
  chart/PDF generation commands).
"""

from __future__ import annotations

from fable_agent.agents.base import Agent, EventHook
from fable_agent.config import FableConfig
from fable_agent.llm.base import LLMProvider
from fable_agent.prompts import load_prompt
from fable_agent.tools import (
    ApplyDiffTool,
    GlobTool,
    GrepTool,
    ListDirTool,
    ReadFileTool,
    RunCommandTool,
    ToolRegistry,
    WriteFileTool,
)


def _registry(tools) -> ToolRegistry:
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)
    return registry


class CoderAgent(Agent):
    name = "coder"

    def __init__(self, provider: LLMProvider, config: FableConfig, on_event: EventHook | None = None):
        ws = config.workspace
        super().__init__(
            provider=provider,
            system_prompt=load_prompt("coder"),
            tools=_registry(
                [
                    ReadFileTool(ws),
                    WriteFileTool(ws),
                    ApplyDiffTool(ws),
                    ListDirTool(ws),
                    GrepTool(ws),
                    GlobTool(ws),
                    RunCommandTool(ws, timeout=config.command_timeout),
                ]
            ),
            max_iterations=config.max_iterations,
            on_event=on_event,
        )


class VerifierAgent(Agent):
    name = "verifier"

    def __init__(self, provider: LLMProvider, config: FableConfig, on_event: EventHook | None = None):
        ws = config.workspace
        super().__init__(
            provider=provider,
            system_prompt=load_prompt("verifier"),
            tools=_registry(
                [
                    ReadFileTool(ws),
                    ListDirTool(ws),
                    GrepTool(ws),
                    GlobTool(ws),
                    RunCommandTool(ws, timeout=config.command_timeout),
                ]
            ),
            max_iterations=config.max_iterations,
            on_event=on_event,
        )


class ArchitectAgent(Agent):
    name = "architect"

    def __init__(self, provider: LLMProvider, config: FableConfig, on_event: EventHook | None = None):
        ws = config.workspace
        super().__init__(
            provider=provider,
            system_prompt=load_prompt("architect"),
            tools=_registry(
                [
                    ReadFileTool(ws),
                    ListDirTool(ws),
                    GrepTool(ws),
                    GlobTool(ws),
                ]
            ),
            max_iterations=config.max_iterations,
            on_event=on_event,
        )


class ReporterAgent(Agent):
    name = "reporter"

    def __init__(self, provider: LLMProvider, config: FableConfig, on_event: EventHook | None = None):
        ws = config.workspace
        super().__init__(
            provider=provider,
            system_prompt=load_prompt("reporter"),
            tools=_registry(
                [
                    ReadFileTool(ws),
                    WriteFileTool(ws),
                    ApplyDiffTool(ws),
                    ListDirTool(ws),
                    GrepTool(ws),
                    GlobTool(ws),
                    RunCommandTool(ws, timeout=config.command_timeout),
                ]
            ),
            max_iterations=config.max_iterations,
            on_event=on_event,
        )


SUBAGENT_TYPES = {
    "coder": CoderAgent,
    "verifier": VerifierAgent,
    "architect": ArchitectAgent,
    "reporter": ReporterAgent,
}


def create_subagent(
    role: str,
    provider: LLMProvider,
    config: FableConfig,
    on_event: EventHook | None = None,
) -> Agent:
    cls = SUBAGENT_TYPES.get(role)
    if cls is None:
        raise ValueError(f"Unknown sub-agent role {role!r}. Available: {sorted(SUBAGENT_TYPES)}")
    return cls(provider, config, on_event)
