"""Fable Agent: an open-source, extensible AI coding agent framework.

Provides an orchestrator that plans tasks and delegates to specialized
sub-agents (Coder, Verifier, Architect), a tooling suite (filesystem,
terminal, search), a persistent memory store, and an MCP server so any
external AI agent can use Fable's tools and prompts.
"""

__version__ = "0.1.0"

from fable_agent.config import FableConfig
from fable_agent.agents.orchestrator import Orchestrator

__all__ = ["FableConfig", "Orchestrator", "__version__"]
