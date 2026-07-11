"""SQLite memory backend with FTS5 full-text search (default)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fable_agent.memory.store import MemoryEntry, MemoryStore


class SqliteMemoryStore(MemoryStore):
    def __init__(self, path: str | Path) -> None:
        base = Path(path)
        self.file = base if base.suffix == ".sqlite3" else base.with_suffix(".sqlite3")
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.file)
        self.conn.row_factory = sqlite3.Row
        self._fts = self._init_schema()

    def _init_schema(self) -> bool:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'note',
                tags TEXT NOT NULL DEFAULT '[]',
                created_at REAL NOT NULL
            )
            """
        )
        try:
            self.conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
                USING fts5(content, tags, content='memories', content_rowid='rowid')
                """
            )
            self.conn.executescript(
                """
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, content, tags)
                    VALUES (new.rowid, new.content, new.tags);
                END;
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content, tags)
                    VALUES ('delete', old.rowid, old.content, old.tags);
                END;
                """
            )
            fts_available = True
        except sqlite3.OperationalError:
            # FTS5 not compiled into this SQLite; fall back to LIKE search
            fts_available = False
        self.conn.commit()
        return fts_available

    def add(self, entry: MemoryEntry) -> str:
        self.conn.execute(
            "INSERT INTO memories (id, content, category, tags, created_at) VALUES (?, ?, ?, ?, ?)",
            (entry.id, entry.content, entry.category, json.dumps(entry.tags), entry.created_at),
        )
        self.conn.commit()
        return entry.id

    def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        if self._fts:
            try:
                rows = self.conn.execute(
                    """
                    SELECT m.* FROM memories m
                    JOIN memories_fts f ON m.rowid = f.rowid
                    WHERE memories_fts MATCH ?
                    ORDER BY rank LIMIT ?
                    """,
                    (" OR ".join(query.split()), limit),
                ).fetchall()
                return [self._row_to_entry(r) for r in rows]
            except sqlite3.OperationalError:
                pass  # malformed FTS query; fall through to LIKE

        like = f"%{query}%"
        rows = self.conn.execute(
            """
            SELECT * FROM memories
            WHERE content LIKE ? OR tags LIKE ?
            ORDER BY created_at DESC LIMIT ?
            """,
            (like, like, limit),
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def recent(self, limit: int = 10, category: str | None = None) -> list[MemoryEntry]:
        if category:
            rows = self.conn.execute(
                "SELECT * FROM memories WHERE category = ? ORDER BY created_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def delete(self, entry_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM memories WHERE id = ?", (entry_id,))
        self.conn.commit()
        return cur.rowcount > 0

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            id=row["id"],
            content=row["content"],
            category=row["category"],
            tags=json.loads(row["tags"]),
            created_at=row["created_at"],
        )
