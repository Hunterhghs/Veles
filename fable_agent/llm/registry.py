"""Provider factory: turn a FableConfig into a concrete LLMProvider."""

from __future__ import annotations

from fable_agent.config import FableConfig
from fable_agent.llm.base import LLMProvider

# Providers that can run without an API key (local / self-hosted endpoints).
KEYLESS_PROVIDERS = {"ollama", "lmstudio", "openai-compatible"}

# Presets for popular local runtimes: (default base_url, default model).
LOCAL_PRESETS = {
    "ollama": ("http://localhost:11434/v1", "qwen2.5-coder"),
    "lmstudio": ("http://localhost:1234/v1", "local-model"),
}


def create_provider(config: FableConfig) -> LLMProvider:
    provider = config.provider

    if provider == "anthropic":
        from fable_agent.llm.anthropic_provider import AnthropicProvider

        _require_key(config, "ANTHROPIC_API_KEY")
        return AnthropicProvider(
            api_key=config.api_key,
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )

    if provider == "openai":
        from fable_agent.llm.openai_provider import OpenAIProvider

        _require_key(config, "OPENAI_API_KEY")
        return OpenAIProvider(
            api_key=config.api_key,
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            base_url=config.base_url,
        )

    if provider in KEYLESS_PROVIDERS:
        from fable_agent.llm.openai_provider import OpenAIProvider

        base_url = config.base_url
        model = config.model
        if provider in LOCAL_PRESETS:
            preset_url, preset_model = LOCAL_PRESETS[provider]
            base_url = base_url or preset_url
            # Don't inherit the cloud default model for a local runtime.
            if model == FableConfig.model:
                model = preset_model
        if provider == "openai-compatible" and not base_url:
            raise ValueError(
                "provider 'openai-compatible' requires a base_url "
                "(e.g. --base-url http://localhost:11434/v1 or FABLE_BASE_URL)."
            )

        return OpenAIProvider(
            api_key=config.api_key,  # optional: omitted from headers when unset
            model=model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            base_url=base_url,
        )

    raise ValueError(
        f"Unknown provider {provider!r}. Expected 'anthropic', 'openai', "
        "'ollama', 'lmstudio', or 'openai-compatible'."
    )


def _require_key(config: FableConfig, env_hint: str) -> None:
    if not config.api_key:
        raise ValueError(
            f"Provider {config.provider!r} requires an API key. Set FABLE_API_KEY "
            f"or {env_hint} — or run without a key using a local provider, e.g. "
            "--provider ollama (see README: 'Running without an API key')."
        )
