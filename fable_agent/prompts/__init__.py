"""System prompts for Fable agents.

Prompts live as markdown files in this package so they can be exported,
edited, and reused by external agents (via the MCP server's prompt
endpoints or by reading the files directly).
"""

from __future__ import annotations

from importlib import resources

AGENT_ROLES = ("orchestrator", "coder", "verifier", "architect")


def load_prompt(role: str) -> str:
    """Load the system prompt for an agent role (e.g. 'coder')."""
    if role not in AGENT_ROLES:
        raise KeyError(f"Unknown agent role {role!r}. Available: {AGENT_ROLES}")
    return (resources.files(__package__) / f"{role}.md").read_text(encoding="utf-8")
