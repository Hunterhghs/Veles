"""Tests for domain playbooks and their wiring."""

import pytest

from fable_agent.config import FableConfig
from fable_agent.playbooks import PLAYBOOKS, load_playbook


def test_all_playbooks_load():
    assert set(PLAYBOOKS) == {"dashboard", "dataset", "report", "website", "research", "writing"}
    for topic in PLAYBOOKS:
        text = load_playbook(topic)
        assert len(text) > 300
        assert text.startswith("# Playbook:")


def test_unknown_playbook():
    with pytest.raises(KeyError):
        load_playbook("astrology")


def test_orchestrator_has_playbook_tool(tmp_path):
    from fable_agent.agents.orchestrator import Orchestrator
    from fable_agent.memory import JsonMemoryStore

    class NullProvider:
        def chat(self, *a, **k):
            raise AssertionError("not called")

    config = FableConfig(workspace=tmp_path, api_key="k", memory_backend="json")
    orch = Orchestrator(
        config=config, provider=NullProvider(), memory=JsonMemoryStore(config.memory_path)
    )
    result = orch.tools.execute("playbook", {"topic": "dashboard"})
    assert result.success
    assert "KPI" in result.output

    spec = next(s for s in orch.tools.specs() if s.name == "playbook")
    assert set(spec.parameters["properties"]["topic"]["enum"]) == set(PLAYBOOKS)


def test_mcp_exports_playbooks(tmp_path):
    import asyncio

    from fable_agent.mcp_server import build_server

    server = build_server(FableConfig(workspace=tmp_path, api_key="k"))

    tools = asyncio.run(server.list_tools())
    assert "get_playbook" in {t.name for t in tools}

    prompts = asyncio.run(server.list_prompts())
    prompt_names = {p.name for p in prompts}
    for topic in PLAYBOOKS:
        assert f"fable_playbook_{topic}" in prompt_names
