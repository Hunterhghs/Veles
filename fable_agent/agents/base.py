"""The core agent loop: model <-> tools until the task is done."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from fable_agent.llm.base import LLMProvider, Message
from fable_agent.tools.base import ToolRegistry

# Called with (agent_name, event_type, detail) for progress reporting.
EventHook = Callable[[str, str, str], None]


@dataclass
class AgentResult:
    """Final outcome of an agent run."""

    output: str
    iterations: int
    transcript: list[Message] = field(default_factory=list)
    success: bool = True


class Agent:
    """A single agent: a system prompt, a toolset, and a run loop.

    The loop sends the conversation to the model; if the model requests
    tool calls, they are executed and results appended, and the loop
    continues. It ends when the model responds without tool calls or the
    iteration budget is exhausted.
    """

    name = "agent"

    def __init__(
        self,
        provider: LLMProvider,
        system_prompt: str,
        tools: ToolRegistry,
        max_iterations: int = 40,
        on_event: EventHook | None = None,
    ) -> None:
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools
        self.max_iterations = max_iterations
        self.on_event = on_event or (lambda *_: None)

    def run(self, task: str, context: str | None = None) -> AgentResult:
        messages: list[Message] = []
        if context:
            messages.append(Message(role="user", content=f"<context>\n{context}\n</context>\n\n{task}"))
        else:
            messages.append(Message(role="user", content=task))

        self.on_event(self.name, "start", task)

        for iteration in range(1, self.max_iterations + 1):
            response = self.provider.chat(
                messages=messages,
                tools=self.tools.specs() or None,
                system=self.system_prompt,
            )

            messages.append(
                Message(role="assistant", content=response.content, tool_calls=response.tool_calls)
            )

            if not response.wants_tools:
                self.on_event(self.name, "finish", response.content[:200])
                return AgentResult(output=response.content, iterations=iteration, transcript=messages)

            for call in response.tool_calls:
                self.on_event(self.name, "tool", f"{call.name}({_summarize(call.arguments)})")
                result = self.tools.execute(call.name, call.arguments)
                messages.append(
                    Message(role="tool", content=result.render(), tool_call_id=call.id, name=call.name)
                )

        self.on_event(self.name, "budget_exhausted", str(self.max_iterations))
        return AgentResult(
            output=(
                f"Stopped after reaching the iteration limit ({self.max_iterations}). "
                "Partial progress may have been made; see transcript."
            ),
            iterations=self.max_iterations,
            transcript=messages,
            success=False,
        )


def _summarize(arguments: dict, max_len: int = 120) -> str:
    parts = []
    for key, value in arguments.items():
        text = str(value).replace("\n", "\\n")
        if len(text) > 40:
            text = text[:40] + "..."
        parts.append(f"{key}={text}")
    joined = ", ".join(parts)
    return joined[:max_len]
