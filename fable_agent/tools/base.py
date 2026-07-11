"""Tool abstraction shared by agents and the MCP server."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fable_agent.llm.base import ToolSpec


@dataclass
class ToolResult:
    """Outcome of a tool execution, rendered back to the model as text."""

    output: str
    success: bool = True

    def render(self) -> str:
        prefix = "" if self.success else "ERROR: "
        return f"{prefix}{self.output}"


class Tool(ABC):
    """A capability the agent can invoke (and the MCP server can expose)."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for arguments

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        raise NotImplementedError

    def spec(self) -> ToolSpec:
        return ToolSpec(name=self.name, description=self.description, parameters=self.parameters)


class WorkspaceTool(Tool, ABC):
    """A tool whose file access is confined to a workspace directory."""

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()

    def resolve_path(self, path: str) -> Path:
        """Resolve a path relative to the workspace and refuse escapes."""
        p = (self.workspace / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
        if not p.is_relative_to(self.workspace):
            raise PermissionError(f"Path {path!r} is outside the workspace {self.workspace}")
        return p


class ToolRegistry:
    """Named collection of tools; dispatches calls and lists specs."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def specs(self) -> list[ToolSpec]:
        return [t.spec() for t in self._tools.values()]

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(output=f"Unknown tool: {name}", success=False)
        try:
            return tool.execute(**arguments)
        except TypeError as e:
            return ToolResult(output=f"Invalid arguments for {name}: {e}", success=False)
        except PermissionError as e:
            return ToolResult(output=str(e), success=False)
        except Exception as e:  # tools must never crash the agent loop
            return ToolResult(output=f"{type(e).__name__}: {e}", success=False)
