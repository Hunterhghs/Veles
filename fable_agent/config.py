"""Configuration for the Fable agent framework.

Config resolution order (later overrides earlier):
1. Built-in defaults
2. ``fable.toml`` in the workspace root (if present)
3. Environment variables (``FABLE_*``, plus provider API keys)
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FableConfig:
    """Runtime configuration for agents, providers, and storage."""

    # LLM provider: "anthropic", "openai", or "openai-compatible"
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-5"
    api_key: str | None = None
    # Base URL for OpenAI-compatible endpoints (Reasonix, Ollama, OpenRouter, ...)
    base_url: str | None = None
    max_tokens: int = 8192
    temperature: float = 0.2

    # Agent behavior
    max_iterations: int = 40          # max tool-use rounds per agent run
    max_delegations: int = 12         # max sub-agent delegations per orchestrator run
    command_timeout: int = 120        # seconds for terminal commands

    # Workspace the agent is allowed to operate on
    workspace: Path = field(default_factory=Path.cwd)

    # Memory
    memory_backend: str = "sqlite"    # "sqlite" or "json"
    memory_path: Path | None = None   # defaults to <workspace>/.fable/memory

    def __post_init__(self) -> None:
        self.workspace = Path(self.workspace).resolve()
        if self.memory_path is None:
            self.memory_path = self.workspace / ".fable" / "memory"
        self.memory_path = Path(self.memory_path)

    @classmethod
    def load(cls, workspace: str | Path | None = None, **overrides: Any) -> "FableConfig":
        """Load config from fable.toml + environment, with keyword overrides."""
        ws = Path(workspace).resolve() if workspace else Path.cwd()
        data: dict[str, Any] = {}

        toml_path = ws / "fable.toml"
        if toml_path.exists():
            with open(toml_path, "rb") as f:
                raw = tomllib.load(f)
            data.update(raw.get("fable", raw))

        env_map = {
            "provider": "FABLE_PROVIDER",
            "model": "FABLE_MODEL",
            "base_url": "FABLE_BASE_URL",
            "max_tokens": "FABLE_MAX_TOKENS",
            "temperature": "FABLE_TEMPERATURE",
            "memory_backend": "FABLE_MEMORY_BACKEND",
        }
        for key, env in env_map.items():
            if os.environ.get(env):
                data[key] = os.environ[env]

        data["workspace"] = ws
        data.update({k: v for k, v in overrides.items() if v is not None})

        cfg = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        cfg.max_tokens = int(cfg.max_tokens)
        cfg.temperature = float(cfg.temperature)
        if cfg.api_key is None:
            cfg.api_key = resolve_api_key(cfg.provider)
        return cfg


def resolve_api_key(provider: str) -> str | None:
    """Find an API key for the given provider from the environment."""
    candidates = {
        "anthropic": ["FABLE_API_KEY", "ANTHROPIC_API_KEY"],
        "openai": ["FABLE_API_KEY", "OPENAI_API_KEY"],
        "openai-compatible": ["FABLE_API_KEY", "OPENAI_API_KEY"],
    }
    for env in candidates.get(provider, ["FABLE_API_KEY"]):
        if os.environ.get(env):
            return os.environ[env]
    return None
