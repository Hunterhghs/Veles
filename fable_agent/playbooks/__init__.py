"""Domain playbooks: task-type guidance for business deliverables.

Playbooks encode how Fable approaches common client and company work —
dashboards, datasets, reports, websites, research, and business writing.
The orchestrator consults them via its `playbook` tool, external agents
fetch them over MCP (``fable_playbook_<name>`` prompts), and humans read
them with ``fable playbooks <name>``.
"""

from __future__ import annotations

from importlib import resources

PLAYBOOKS = ("dashboard", "dataset", "report", "website", "research", "writing")


def load_playbook(name: str) -> str:
    """Load a domain playbook by name (e.g. 'dashboard')."""
    if name not in PLAYBOOKS:
        raise KeyError(f"Unknown playbook {name!r}. Available: {PLAYBOOKS}")
    return (resources.files(__package__) / f"{name}.md").read_text(encoding="utf-8")
