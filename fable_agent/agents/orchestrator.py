"""The Orchestrator: plans tasks and delegates to sub-agents.

The orchestrator is itself an Agent whose only tools are `delegate`
(spawn a sub-agent on an objective) and `remember`/`recall` (long-term
memory). It never edits files directly — all real work flows through
the Coder, Verifier, and Architect sub-agents.
"""

from __future__ import annotations

from typing import Any

from fable_agent.agents.base import Agent, AgentResult, EventHook
from fable_agent.agents.subagents import SUBAGENT_TYPES, create_subagent
from fable_agent.config import FableConfig
from fable_agent.llm import create_provider
from fable_agent.llm.base import LLMProvider
from fable_agent.memory import MemoryStore, create_memory
from fable_agent.prompts import load_prompt
from fable_agent.tools.base import Tool, ToolRegistry, ToolResult


class DelegateTool(Tool):
    """Lets the orchestrator hand an objective to a sub-agent."""

    name = "delegate"
    description = (
        "Delegate a self-contained objective to a specialized sub-agent and "
        "get its final report back. Sub-agents do not share your conversation "
        "history, so include all necessary context in the objective."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "agent": {
                "type": "string",
                "enum": sorted(SUBAGENT_TYPES),
                "description": "Which sub-agent to use: architect (plan), coder (implement), verifier (check).",
            },
            "objective": {
                "type": "string",
                "description": "The complete, self-contained objective for the sub-agent.",
            },
        },
        "required": ["agent", "objective"],
    }

    def __init__(
        self,
        provider: LLMProvider,
        config: FableConfig,
        on_event: EventHook | None = None,
        max_delegations: int = 12,
    ) -> None:
        self.provider = provider
        self.config = config
        self.on_event = on_event
        self.max_delegations = max_delegations
        self.delegations = 0

    def execute(self, agent: str, objective: str) -> ToolResult:
        if self.delegations >= self.max_delegations:
            return ToolResult(
                output=(
                    f"Delegation budget exhausted ({self.max_delegations}). "
                    "Summarize progress and finish."
                ),
                success=False,
            )
        self.delegations += 1
        sub = create_subagent(agent, self.provider, self.config, self.on_event)
        result = sub.run(objective)
        status = "completed" if result.success else "stopped early"
        return ToolResult(
            output=f"[{agent} {status} after {result.iterations} iteration(s)]\n\n{result.output}",
            success=result.success,
        )


class RememberTool(Tool):
    name = "remember"
    description = (
        "Save an important fact, decision, or task summary to long-term memory "
        "so future sessions can recall it."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "What to remember."},
            "category": {
                "type": "string",
                "description": "One of: note, decision, task, project-fact. Default: note.",
            },
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags."},
        },
        "required": ["content"],
    }

    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def execute(self, content: str, category: str = "note", tags: list[str] | None = None) -> ToolResult:
        entry_id = self.memory.remember(content, category=category, tags=tags or [])
        return ToolResult(output=f"Remembered (id={entry_id}).")


class RecallTool(Tool):
    name = "recall"
    description = "Search long-term memory for facts and decisions from previous sessions."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Keywords to search for."},
            "limit": {"type": "integer", "description": "Max results (default 5)."},
        },
        "required": ["query"],
    }

    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def execute(self, query: str, limit: int = 5) -> ToolResult:
        entries = self.memory.search(query, limit=limit)
        if not entries:
            return ToolResult(output="No matching memories.")
        lines = [f"- [{e.category}] {e.content} (id={e.id})" for e in entries]
        return ToolResult(output="\n".join(lines))


class Orchestrator(Agent):
    """Top-level agent: plan, delegate, verify, summarize."""

    name = "orchestrator"

    def __init__(
        self,
        config: FableConfig | None = None,
        provider: LLMProvider | None = None,
        memory: MemoryStore | None = None,
        on_event: EventHook | None = None,
    ) -> None:
        self.config = config or FableConfig.load()
        provider = provider or create_provider(self.config)
        self.memory = memory or create_memory(self.config.memory_backend, self.config.memory_path)

        tools = ToolRegistry()
        tools.register(
            DelegateTool(provider, self.config, on_event, max_delegations=self.config.max_delegations)
        )
        tools.register(RememberTool(self.memory))
        tools.register(RecallTool(self.memory))

        super().__init__(
            provider=provider,
            system_prompt=load_prompt("orchestrator"),
            tools=tools,
            max_iterations=self.config.max_iterations,
            on_event=on_event,
        )

    def run_task(self, task: str) -> AgentResult:
        """Run a task with recent memory injected as context."""
        recent = self.memory.recent(limit=5)
        context = None
        if recent:
            context = "Relevant long-term memory from previous sessions:\n" + "\n".join(
                f"- [{e.category}] {e.content}" for e in recent
            )
        result = self.run(task, context=context)
        if result.success:
            summary = result.output[:500]
            self.memory.remember(f"Task: {task[:200]} — Outcome: {summary}", category="task")
        return result
