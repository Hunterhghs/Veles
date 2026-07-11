"""Provider factory: turn a FableConfig into a concrete LLMProvider."""

from __future__ import annotations

from fable_agent.config import FableConfig
from fable_agent.llm.base import LLMProvider


def create_provider(config: FableConfig) -> LLMProvider:
    if not config.api_key:
        raise ValueError(
            "No API key configured. Set FABLE_API_KEY, ANTHROPIC_API_KEY, or "
            "OPENAI_API_KEY, or pass api_key explicitly."
        )

    if config.provider == "anthropic":
        from fable_agent.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            api_key=config.api_key,
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )

    if config.provider in ("openai", "openai-compatible"):
        from fable_agent.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=config.api_key,
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            base_url=config.base_url,
        )

    raise ValueError(
        f"Unknown provider {config.provider!r}. "
        "Expected 'anthropic', 'openai', or 'openai-compatible'."
    )
