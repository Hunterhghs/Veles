"""Filesystem tools: read, write, diff-based edit, and directory listing."""

from __future__ import annotations

import difflib
from typing import Any

from fable_agent.tools.base import ToolResult, WorkspaceTool

MAX_READ_CHARS = 100_000


class ReadFileTool(WorkspaceTool):
    name = "read_file"
    description = (
        "Read a text file from the workspace. Returns content with 1-based "
        "line numbers. Supports optional offset/limit for large files."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path, relative to the workspace root."},
            "offset": {"type": "integer", "description": "1-based line to start from (optional)."},
            "limit": {"type": "integer", "description": "Max number of lines to return (optional)."},
        },
        "required": ["path"],
    }

    def execute(self, path: str, offset: int = 1, limit: int | None = None) -> ToolResult:
        p = self.resolve_path(path)
        if not p.exists():
            return ToolResult(output=f"File not found: {path}", success=False)
        if p.is_dir():
            return ToolResult(output=f"{path} is a directory; use list_dir.", success=False)

        text = p.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        start = max(offset - 1, 0)
        end = start + limit if limit else len(lines)
        selected = lines[start:end]

        numbered = "\n".join(f"{i + start + 1:6}|{line}" for i, line in enumerate(selected))
        if len(numbered) > MAX_READ_CHARS:
            numbered = numbered[:MAX_READ_CHARS] + "\n... [truncated]"
        return ToolResult(output=numbered or "(empty file)")


class WriteFileTool(WorkspaceTool):
    name = "write_file"
    description = "Create or overwrite a file in the workspace with the given content."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path, relative to the workspace root."},
            "content": {"type": "string", "description": "Full file content to write."},
        },
        "required": ["path", "content"],
    }

    def execute(self, path: str, content: str) -> ToolResult:
        p = self.resolve_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        existed = p.exists()
        p.write_text(content, encoding="utf-8")
        verb = "Updated" if existed else "Created"
        return ToolResult(output=f"{verb} {path} ({len(content)} chars).")


class ApplyDiffTool(WorkspaceTool):
    name = "edit_file"
    description = (
        "Edit a file by exact string replacement. `old_string` must appear "
        "exactly once in the file (include surrounding context to make it "
        "unique). Returns a unified diff of the change."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path, relative to the workspace root."},
            "old_string": {"type": "string", "description": "Exact text to replace (must be unique)."},
            "new_string": {"type": "string", "description": "Replacement text."},
        },
        "required": ["path", "old_string", "new_string"],
    }

    def execute(self, path: str, old_string: str, new_string: str) -> ToolResult:
        p = self.resolve_path(path)
        if not p.exists():
            return ToolResult(output=f"File not found: {path}", success=False)

        original = p.read_text(encoding="utf-8")
        count = original.count(old_string)
        if count == 0:
            return ToolResult(output=f"old_string not found in {path}.", success=False)
        if count > 1:
            return ToolResult(
                output=f"old_string appears {count} times in {path}; add context to make it unique.",
                success=False,
            )

        updated = original.replace(old_string, new_string, 1)
        p.write_text(updated, encoding="utf-8")

        diff = "".join(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                updated.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
        )
        return ToolResult(output=f"Edited {path}:\n{diff}")


class ListDirTool(WorkspaceTool):
    name = "list_dir"
    description = "List files and directories at a path in the workspace."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path relative to workspace root. Defaults to '.'"},
        },
        "required": [],
    }

    IGNORED = {".git", "__pycache__", "node_modules", ".venv", ".fable"}

    def execute(self, path: str = ".") -> ToolResult:
        p = self.resolve_path(path)
        if not p.is_dir():
            return ToolResult(output=f"Not a directory: {path}", success=False)

        entries = []
        for child in sorted(p.iterdir(), key=lambda c: (not c.is_dir(), c.name.lower())):
            if child.name in self.IGNORED:
                continue
            suffix = "/" if child.is_dir() else ""
            entries.append(f"{child.name}{suffix}")
        return ToolResult(output="\n".join(entries) or "(empty directory)")
