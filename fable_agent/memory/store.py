"""Memory store interface.

Fable's memory keeps long-term context across sessions: task summaries,
decisions, and project facts. Agents write entries as they work and read
relevant entries back at the start of a new session, so a fresh process
can pick up where a previous one left off.
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class MemoryEntry:
    """One remembered fact, decision, or task summary."""

    content: str
    category: str = "note"  # e.g. "note", "decision", "task", "project-fact"
    tags: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MemoryEntry":
        return cls(
            content=d["content"],
            category=d.get("category", "note"),
            tags=list(d.get("tags", [])),
            id=d.get("id", uuid.uuid4().hex[:12]),
            created_at=d.get("created_at", time.time()),
        )


class MemoryStore(ABC):
    """Persistent store for MemoryEntry records."""

    @abstractmethod
    def add(self, entry: MemoryEntry) -> str:
        """Persist an entry; returns its id."""

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Keyword search over entry content and tags, newest first."""

    @abstractmethod
    def recent(self, limit: int = 10, category: str | None = None) -> list[MemoryEntry]:
        """Most recent entries, optionally filtered by category."""

    @abstractmethod
    def delete(self, entry_id: str) -> bool:
        """Remove an entry by id; returns True if it existed."""

    def remember(self, content: str, category: str = "note", tags: list[str] | None = None) -> str:
        """Convenience: create and persist an entry in one call."""
        return self.add(MemoryEntry(content=content, category=category, tags=tags or []))
