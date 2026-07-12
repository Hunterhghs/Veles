"""Veles — a general-purpose AI coding agent framework powered by Fable-5.

Use it for anything: business analytics, video game development, scientific
research, creative coding, infrastructure automation, and beyond.

Provides an orchestrator that plans tasks and delegates to specialized
sub-agents (Coder, Verifier, Architect, Reporter), a tooling suite (filesystem,
terminal, search), a persistent memory store, pluggable domain playbooks,
and an MCP server so any external AI agent can use Veles's tools and prompts.

Default configuration: DeepSeek API + H Heuristics business-analyst playbooks.
Swap the provider, model, and playbooks to target any domain.
"""

__version__ = "0.1.0"

from fable_agent.config import FableConfig
from fable_agent.agents.orchestrator import Orchestrator

__all__ = ["FableConfig", "Orchestrator", "__version__"]
