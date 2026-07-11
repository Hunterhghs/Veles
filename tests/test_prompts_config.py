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


class TestKeylessProviders:
    """Fable must run without an API key against local endpoints."""

    def test_ollama_needs_no_key(self, tmp_path):
        from fable_agent.llm import create_provider
        from fable_agent.llm.openai_provider import OpenAIProvider

        cfg = FableConfig(workspace=tmp_path, provider="ollama", api_key=None)
        provider = create_provider(cfg)
        assert isinstance(provider, OpenAIProvider)
        assert provider.base_url == "http://localhost:11434/v1"
        assert provider.model == "qwen2.5-coder"  # local default, not the cloud model
        assert provider.api_key is None

    def test_lmstudio_needs_no_key(self, tmp_path):
        from fable_agent.llm import create_provider

        cfg = FableConfig(workspace=tmp_path, provider="lmstudio", api_key=None)
        provider = create_provider(cfg)
        assert provider.base_url == "http://localhost:1234/v1"

    def test_local_preset_respects_explicit_model_and_url(self, tmp_path):
        from fable_agent.llm import create_provider

        cfg = FableConfig(
            workspace=tmp_path,
            provider="ollama",
            model="llama3.3",
            base_url="http://otherhost:11434/v1",
            api_key=None,
        )
        provider = create_provider(cfg)
        assert provider.model == "llama3.3"
        assert provider.base_url == "http://otherhost:11434/v1"

    def test_openai_compatible_without_key(self, tmp_path):
        from fable_agent.llm import create_provider

        cfg = FableConfig(
            workspace=tmp_path,
            provider="openai-compatible",
            base_url="http://localhost:8000/v1",
            model="my-model",
            api_key=None,
        )
        provider = create_provider(cfg)
        assert provider.api_key is None

    def test_openai_compatible_requires_base_url(self, tmp_path):
        from fable_agent.llm import create_provider

        cfg = FableConfig(workspace=tmp_path, provider="openai-compatible", api_key=None)
        with pytest.raises(ValueError, match="base_url"):
            create_provider(cfg)

    def test_cloud_providers_still_require_key(self, tmp_path, monkeypatch):
        from fable_agent.llm import create_provider

        for env in ("FABLE_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            monkeypatch.delenv(env, raising=False)
        for provider_name in ("anthropic", "openai"):
            cfg = FableConfig(workspace=tmp_path, provider=provider_name, api_key=None)
            with pytest.raises(ValueError, match="API key"):
                create_provider(cfg)

    def test_deepseek_preset(self, tmp_path):
        from fable_agent.llm import create_provider

        cfg = FableConfig(workspace=tmp_path, provider="deepseek", api_key="ds-key")
        provider = create_provider(cfg)
        assert provider.base_url == "https://api.deepseek.com/v1"
        assert provider.model == "deepseek-chat"
        assert provider.api_key == "ds-key"

        explicit = FableConfig(
            workspace=tmp_path, provider="deepseek", model="deepseek-reasoner", api_key="ds-key"
        )
        assert create_provider(explicit).model == "deepseek-reasoner"

    def test_deepseek_key_from_env(self, tmp_path, monkeypatch):
        for env in ("FABLE_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            monkeypatch.delenv(env, raising=False)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "env-ds-key")
        cfg = FableConfig.load(workspace=tmp_path, provider="deepseek")
        assert cfg.api_key == "env-ds-key"

    def test_deepseek_requires_key(self, tmp_path, monkeypatch):
        from fable_agent.llm import create_provider

        for env in ("FABLE_API_KEY", "DEEPSEEK_API_KEY"):
            monkeypatch.delenv(env, raising=False)
        cfg = FableConfig(workspace=tmp_path, provider="deepseek", api_key=None)
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            create_provider(cfg)

    def test_no_auth_header_when_keyless(self):
        from fable_agent.llm.openai_provider import OpenAIProvider

        captured = {}

        class FakeClient:
            def post(self, url, headers=None, json=None):
                captured["headers"] = headers
                raise RuntimeError("stop before network")

        provider = OpenAIProvider(api_key=None, base_url="http://localhost:11434/v1")
        provider.client = FakeClient()
        with pytest.raises(RuntimeError):
            provider.chat([])
        assert "Authorization" not in captured["headers"]
