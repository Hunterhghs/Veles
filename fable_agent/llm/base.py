"""Provider-agnostic LLM interface.

Every provider (Anthropic, OpenAI, or any OpenAI-compatible endpoint)
normalizes to these types, so agents never depend on a specific vendor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ToolCall:
    """A tool invocation requested by the model."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Message:
    """One turn in a conversation, normalized across providers."""

    role: Role
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    # For role="tool": the id of the tool call this message answers
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class ToolSpec:
    """JSON-schema description of a tool, passed to the model."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for the arguments object


@dataclass
class LLMResponse:
    """Normalized model output."""

    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)

    @property
    def wants_tools(self) -> bool:
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """Abstract chat-completion provider with tool-calling support."""

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        """Send a conversation to the model and return its response."""
        raise NotImplementedError
