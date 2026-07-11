"""JSON-file memory backend: human-readable, easy to inspect and edit."""

from __future__ import annotations

import json
from pathlib import Path

from fable_agent.memory.store import MemoryEntry, MemoryStore


class JsonMemoryStore(MemoryStore):
    def __init__(self, path: str | Path) -> None:
        base = Path(path)
        self.file = base if base.suffix == ".json" else base.with_suffix(".json")
        self.file.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[MemoryEntry]:
        if not self.file.exists():
            return []
        data = json.loads(self.file.read_text(encoding="utf-8") or "[]")
        return [MemoryEntry.from_dict(d) for d in data]

    def _save(self, entries: list[MemoryEntry]) -> None:
        self.file.write_text(
            json.dumps([e.to_dict() for e in entries], indent=2), encoding="utf-8"
        )

    def add(self, entry: MemoryEntry) -> str:
        entries = self._load()
        entries.append(entry)
        self._save(entries)
        return entry.id

    def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        terms = [t for t in query.lower().split() if t]
        scored = []
        for e in self._load():
            haystack = (e.content + " " + " ".join(e.tags)).lower()
            score = sum(1 for t in terms if t in haystack)
            if score:
                scored.append((score, e.created_at, e))
        scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
        return [e for _, _, e in scored[:limit]]

    def recent(self, limit: int = 10, category: str | None = None) -> list[MemoryEntry]:
        entries = self._load()
        if category:
            entries = [e for e in entries if e.category == category]
        entries.sort(key=lambda e: e.created_at, reverse=True)
        return entries[:limit]

    def delete(self, entry_id: str) -> bool:
        entries = self._load()
        remaining = [e for e in entries if e.id != entry_id]
        if len(remaining) == len(entries):
            return False
        self._save(remaining)
        return True
