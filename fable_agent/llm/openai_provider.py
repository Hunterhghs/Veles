"""OpenAI Chat Completions provider.

Also works with any OpenAI-compatible endpoint (Reasonix, OpenRouter,
Ollama, LM Studio, vLLM, Together, Groq, ...) by passing ``base_url``.
For local/self-hosted endpoints that need no authentication, pass
``api_key=None`` and the Authorization header is omitted entirely.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from fable_agent.llm.base import LLMProvider, LLMResponse, Message, ToolCall, ToolSpec

DEFAULT_BASE_URL = "https://api.openai.com/v1"


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        api_key: str | None,
        model: str = "gpt-4o",
        max_tokens: int = 8192,
        temperature: float = 0.2,
        base_url: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.client = httpx.Client(timeout=timeout)

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        oai_messages: list[dict[str, Any]] = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        oai_messages.extend(self._to_openai(m) for m in messages)

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": oai_messages,
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        resp = self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        message = choice["message"]
        tool_calls: list[ToolCall] = []
        for tc in message.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {"_raw": tc["function"]["arguments"]}
            tool_calls.append(ToolCall(id=tc["id"], name=tc["function"]["name"], arguments=args))

        return LLMResponse(
            content=message.get("content") or "",
            tool_calls=tool_calls,
            stop_reason=choice.get("finish_reason", "stop"),
            usage=data.get("usage", {}),
            reasoning=message.get("reasoning_content") or None,
        )

    @staticmethod
    def _to_openai(msg: Message) -> dict[str, Any]:
        if msg.role == "tool":
            return {
                "role": "tool",
                "tool_call_id": msg.tool_call_id,
                "content": msg.content,
            }
        out: dict[str, Any] = {"role": msg.role, "content": msg.content}
        # Round-trip reasoning (DeepSeek et al.) so thinking context is not
        # lost on tool-call turns. Compliant endpoints ignore unknown fields.
        if msg.role == "assistant" and msg.reasoning:
            out["reasoning_content"] = msg.reasoning
        if msg.role == "assistant" and msg.tool_calls:
            out["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                }
                for tc in msg.tool_calls
            ]
            if not msg.content:
                out["content"] = None
        return out
