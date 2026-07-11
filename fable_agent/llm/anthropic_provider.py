"""Anthropic Messages API provider (no SDK dependency, just httpx)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from fable_agent.llm.base import LLMProvider, LLMResponse, Message, ToolCall, ToolSpec

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5",
        max_tokens: int = 8192,
        temperature: float = 0.2,
        base_url: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.url = base_url or API_URL
        self.client = httpx.Client(timeout=timeout)

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [self._to_anthropic(m) for m in messages],
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters,
                }
                for t in tools
            ]

        resp = self.client.post(
            self.url,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": API_VERSION,
                "content-type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in data.get("content", []):
            if block["type"] == "text":
                text_parts.append(block["text"])
            elif block["type"] == "tool_use":
                tool_calls.append(
                    ToolCall(id=block["id"], name=block["name"], arguments=block["input"])
                )

        return LLMResponse(
            content="".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=data.get("stop_reason", "stop"),
            usage=data.get("usage", {}),
        )

    @staticmethod
    def _to_anthropic(msg: Message) -> dict[str, Any]:
        """Convert a normalized Message to Anthropic's content-block format."""
        if msg.role == "tool":
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content,
                    }
                ],
            }
        if msg.role == "assistant" and msg.tool_calls:
            content: list[dict[str, Any]] = []
            if msg.content:
                content.append({"type": "text", "text": msg.content})
            for tc in msg.tool_calls:
                content.append(
                    {"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.arguments}
                )
            return {"role": "assistant", "content": content}
        return {"role": msg.role, "content": msg.content}
