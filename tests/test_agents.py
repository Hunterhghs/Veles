"""Tests for the agent loop and orchestrator, using a scripted fake LLM."""

import pytest

from fable_agent.agents.base import Agent
from fable_agent.agents.orchestrator import Orchestrator
from fable_agent.config import FableConfig
from fable_agent.llm.base import LLMProvider, LLMResponse, ToolCall
from fable_agent.memory import JsonMemoryStore
from fable_agent.tools import default_registry


class ScriptedProvider(LLMProvider):
    """Returns a fixed sequence of responses; records what it was sent."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages, tools=None, system=None):
        self.calls.append({"messages": list(messages), "tools": tools, "system": system})
        return self.responses.pop(0)


@pytest.fixture
def config(tmp_path):
    return FableConfig(workspace=tmp_path, api_key="test-key", memory_backend="json")


def test_agent_returns_direct_answer(config):
    provider = ScriptedProvider([LLMResponse(content="All done.")])
    agent = Agent(provider, "system prompt", default_registry(config.workspace))

    result = agent.run("do something")
    assert result.success
    assert result.output == "All done."
    assert result.iterations == 1


def test_agent_executes_tool_calls(config, tmp_path):
    (tmp_path / "hello.txt").write_text("hi there\n")
    provider = ScriptedProvider(
        [
            LLMResponse(
                content="",
                tool_calls=[ToolCall(id="1", name="read_file", arguments={"path": "hello.txt"})],
            ),
            LLMResponse(content="The file says hi."),
        ]
    )
    agent = Agent(provider, "system", default_registry(config.workspace))

    result = agent.run("read hello.txt")
    assert result.success
    assert result.output == "The file says hi."
    # The tool result was fed back to the model on the second call
    tool_msgs = [m for m in provider.calls[1]["messages"] if m.role == "tool"]
    assert len(tool_msgs) == 1
    assert "hi there" in tool_msgs[0].content


def test_agent_stops_at_iteration_limit(config):
    looping = LLMResponse(
        content="",
        tool_calls=[ToolCall(id="1", name="list_dir", arguments={})],
    )
    provider = ScriptedProvider([looping] * 3)
    agent = Agent(provider, "system", default_registry(config.workspace), max_iterations=3)

    result = agent.run("loop forever")
    assert not result.success
    assert "iteration limit" in result.output


def test_orchestrator_delegates_to_subagent(config):
    # Orchestrator delegates to the coder, coder answers, orchestrator summarizes.
    provider = ScriptedProvider(
        [
            LLMResponse(
                content="",
                tool_calls=[
                    ToolCall(
                        id="d1",
                        name="delegate",
                        arguments={"agent": "coder", "objective": "write hello.py"},
                    )
                ],
            ),
            LLMResponse(content="Created hello.py as requested."),  # coder's turn
            LLMResponse(content="Task complete: hello.py created."),  # orchestrator summary
        ]
    )
    memory = JsonMemoryStore(config.memory_path)
    orchestrator = Orchestrator(config=config, provider=provider, memory=memory)

    result = orchestrator.run_task("create hello.py")
    assert result.success
    assert "complete" in result.output.lower()
    # Coder received the objective, not the raw user task
    coder_call = provider.calls[1]
    assert "write hello.py" in coder_call["messages"][0].content
    # Outcome persisted to memory
    assert any("create hello.py" in e.content for e in memory.recent(limit=5))


def test_orchestrator_memory_injected_as_context(config):
    memory = JsonMemoryStore(config.memory_path)
    memory.remember("Project uses tabs, not spaces", category="project-fact")

    provider = ScriptedProvider([LLMResponse(content="ok")])
    orchestrator = Orchestrator(config=config, provider=provider, memory=memory)
    orchestrator.run_task("anything")

    first_message = provider.calls[0]["messages"][0].content
    assert "tabs, not spaces" in first_message
