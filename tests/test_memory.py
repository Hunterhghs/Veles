"""Tests for the memory store backends."""

import pytest

from fable_agent.memory import JsonMemoryStore, SqliteMemoryStore, create_memory
from fable_agent.memory.store import MemoryEntry


@pytest.fixture(params=["json", "sqlite"])
def store(request, tmp_path):
    return create_memory(request.param, tmp_path / "memory")


def test_remember_and_recent(store):
    store.remember("Project uses FastAPI for the web layer", category="project-fact")
    store.remember("Decided to use SQLite over Postgres", category="decision")

    recent = store.recent(limit=5)
    assert len(recent) == 2
    assert recent[0].content.startswith("Decided")  # newest first


def test_search(store):
    store.remember("The API server runs on port 8080", tags=["api", "config"])
    store.remember("Tests live in the tests/ directory")

    hits = store.search("port 8080")
    assert len(hits) >= 1
    assert "8080" in hits[0].content


def test_category_filter(store):
    store.remember("a task summary", category="task")
    store.remember("a plain note", category="note")

    tasks = store.recent(category="task")
    assert len(tasks) == 1
    assert tasks[0].category == "task"


def test_delete(store):
    entry_id = store.remember("temporary fact")
    assert store.delete(entry_id) is True
    assert store.delete(entry_id) is False
    assert store.recent() == []


def test_entry_roundtrip():
    entry = MemoryEntry(content="hello", category="note", tags=["t1"])
    clone = MemoryEntry.from_dict(entry.to_dict())
    assert clone.id == entry.id
    assert clone.content == entry.content
    assert clone.tags == entry.tags


def test_unknown_backend(tmp_path):
    with pytest.raises(ValueError):
        create_memory("redis", tmp_path / "m")
