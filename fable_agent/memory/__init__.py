from fable_agent.memory.store import MemoryEntry, MemoryStore
from fable_agent.memory.json_store import JsonMemoryStore
from fable_agent.memory.sqlite_store import SqliteMemoryStore


def create_memory(backend: str, path) -> MemoryStore:
    """Create a memory store: 'sqlite' (default) or 'json'."""
    if backend == "sqlite":
        return SqliteMemoryStore(path)
    if backend == "json":
        return JsonMemoryStore(path)
    raise ValueError(f"Unknown memory backend {backend!r}. Expected 'sqlite' or 'json'.")


__all__ = [
    "MemoryEntry",
    "MemoryStore",
    "JsonMemoryStore",
    "SqliteMemoryStore",
    "create_memory",
]
