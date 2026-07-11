"""Search tools: regex content search (grep) and filename globbing."""

from __future__ import annotations

import fnmatch
import re
from typing import Any

from fable_agent.tools.base import ToolResult, WorkspaceTool

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".fable", "dist", "build", ".egg-info"}
MAX_RESULTS = 200
MAX_FILE_BYTES = 2_000_000


def _iter_files(root, glob: str | None = None):
    for path in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS or part.endswith(".egg-info") for part in path.parts):
            continue
        if not path.is_file():
            continue
        if glob and not fnmatch.fnmatch(path.name, glob):
            continue
        yield path


class GrepTool(WorkspaceTool):
    name = "grep"
    description = (
        "Search file contents in the workspace with a regular expression. "
        "Returns matching lines as path:line:content."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regular expression to search for."},
            "glob": {"type": "string", "description": "Optional filename filter, e.g. '*.py'."},
            "case_insensitive": {"type": "boolean", "description": "Case-insensitive search. Default false."},
        },
        "required": ["pattern"],
    }

    def execute(self, pattern: str, glob: str | None = None, case_insensitive: bool = False) -> ToolResult:
        try:
            regex = re.compile(pattern, re.IGNORECASE if case_insensitive else 0)
        except re.error as e:
            return ToolResult(output=f"Invalid regex: {e}", success=False)

        results: list[str] = []
        for path in _iter_files(self.workspace, glob):
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = path.relative_to(self.workspace)
            for lineno, line in enumerate(text.splitlines(), start=1):
                if regex.search(line):
                    results.append(f"{rel}:{lineno}:{line.strip()}")
                    if len(results) >= MAX_RESULTS:
                        results.append("... [result limit reached]")
                        return ToolResult(output="\n".join(results))
        return ToolResult(output="\n".join(results) or "No matches found.")


class GlobTool(WorkspaceTool):
    name = "glob"
    description = "Find files in the workspace whose names match a glob pattern, e.g. '*.py' or 'test_*'."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern matched against filenames."},
        },
        "required": ["pattern"],
    }

    def execute(self, pattern: str) -> ToolResult:
        matches = [
            str(p.relative_to(self.workspace))
            for p in _iter_files(self.workspace, pattern)
        ][:MAX_RESULTS]
        return ToolResult(output="\n".join(matches) or "No files matched.")
