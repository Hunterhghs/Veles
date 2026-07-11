"""Tests for prompt loading and configuration."""

import pytest

from fable_agent.config import FableConfig
from fable_agent.prompts import AGENT_ROLES, load_prompt


def test_all_prompts_load():
    for role in AGENT_ROLES:
        text = load_prompt(role)
        assert len(text) > 100
        assert role.capitalize()[:5].lower() in text.lower()


def test_unknown_prompt_role():
    with pytest.raises(KeyError):
        load_prompt("wizard")


def test_config_defaults(tmp_path):
    cfg = FableConfig(workspace=tmp_path, api_key="k")
    assert cfg.provider == "anthropic"
    assert cfg.memory_path == tmp_path / ".fable" / "memory"


def test_config_from_toml(tmp_path):
    (tmp_path / "fable.toml").write_text(
        '[fable]\nprovider = "openai-compatible"\nmodel = "my-model"\nbase_url = "http://localhost:11434/v1"\n'
    )
    cfg = FableConfig.load(workspace=tmp_path, api_key="k")
    assert cfg.provider == "openai-compatible"
    assert cfg.model == "my-model"
    assert cfg.base_url == "http://localhost:11434/v1"


def test_config_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("FABLE_MODEL", "env-model")
    monkeypatch.setenv("FABLE_API_KEY", "env-key")
    cfg = FableConfig.load(workspace=tmp_path)
    assert cfg.model == "env-model"
    assert cfg.api_key == "env-key"
