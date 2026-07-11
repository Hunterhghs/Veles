from fable_agent.tools.base import Tool, ToolRegistry, ToolResult
from fable_agent.tools.filesystem import (
    ApplyDiffTool,
    ListDirTool,
    ReadFileTool,
    WriteFileTool,
)
from fable_agent.tools.search import GlobTool, GrepTool
from fable_agent.tools.terminal import RunCommandTool


def default_registry(workspace, command_timeout: int = 120) -> ToolRegistry:
    """The standard Fable toolset, sandboxed to a workspace directory."""
    registry = ToolRegistry()
    for tool in (
        ReadFileTool(workspace),
        WriteFileTool(workspace),
        ApplyDiffTool(workspace),
        ListDirTool(workspace),
        GrepTool(workspace),
        GlobTool(workspace),
        RunCommandTool(workspace, timeout=command_timeout),
    ):
        registry.register(tool)
    return registry


__all__ = [
    "Tool",
    "ToolRegistry",
    "ToolResult",
    "ReadFileTool",
    "WriteFileTool",
    "ApplyDiffTool",
    "ListDirTool",
    "GrepTool",
    "GlobTool",
    "RunCommandTool",
    "default_registry",
]
