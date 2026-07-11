"""Terminal execution tool with timeout and output capping."""

from __future__ import annotations

import subprocess
from typing import Any

from fable_agent.tools.base import ToolResult, WorkspaceTool

MAX_OUTPUT_CHARS = 30_000


class RunCommandTool(WorkspaceTool):
    name = "run_command"
    description = (
        "Run a shell command in the workspace directory and return its "
        "combined stdout/stderr and exit code. Use for builds, tests, git, "
        "package managers, etc. Commands time out after the configured limit."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command to execute."},
            "cwd": {"type": "string", "description": "Working directory relative to workspace root (optional)."},
        },
        "required": ["command"],
    }

    def __init__(self, workspace, timeout: int = 120) -> None:
        super().__init__(workspace)
        self.timeout = timeout

    def execute(self, command: str, cwd: str | None = None) -> ToolResult:
        workdir = self.resolve_path(cwd) if cwd else self.workspace
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                output=f"Command timed out after {self.timeout}s: {command}",
                success=False,
            )

        output = (proc.stdout or "") + (proc.stderr or "")
        if len(output) > MAX_OUTPUT_CHARS:
            half = MAX_OUTPUT_CHARS // 2
            output = output[:half] + "\n... [output truncated] ...\n" + output[-half:]

        result = f"exit code: {proc.returncode}\n{output.strip() or '(no output)'}"
        return ToolResult(output=result, success=proc.returncode == 0)
