"""Tests for the tooling suite (filesystem, search, terminal)."""

import pytest

from fable_agent.tools import default_registry
from fable_agent.tools.filesystem import ApplyDiffTool, ReadFileTool, WriteFileTool
from fable_agent.tools.search import GlobTool, GrepTool
from fable_agent.tools.terminal import RunCommandTool


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def main():\n    print('hello')\n")
    (tmp_path / "README.md").write_text("# Demo project\n")
    return tmp_path


def test_read_file(workspace):
    result = ReadFileTool(workspace).execute(path="src/app.py")
    assert result.success
    assert "def main():" in result.output
    assert result.output.startswith("     1|")


def test_read_missing_file(workspace):
    result = ReadFileTool(workspace).execute(path="nope.py")
    assert not result.success


def test_write_and_read_roundtrip(workspace):
    write = WriteFileTool(workspace).execute(path="new/deep/file.txt", content="content here")
    assert write.success
    assert (workspace / "new" / "deep" / "file.txt").read_text() == "content here"


def test_edit_file_unique_replacement(workspace):
    result = ApplyDiffTool(workspace).execute(
        path="src/app.py", old_string="print('hello')", new_string="print('world')"
    )
    assert result.success
    assert "-    print('hello')" in result.output
    assert "+    print('world')" in result.output
    assert "world" in (workspace / "src" / "app.py").read_text()


def test_edit_file_rejects_ambiguous(workspace):
    (workspace / "dup.txt").write_text("x\nx\n")
    result = ApplyDiffTool(workspace).execute(path="dup.txt", old_string="x", new_string="y")
    assert not result.success
    assert "2 times" in result.output


def test_path_escape_blocked(workspace):
    registry = default_registry(workspace)
    result = registry.execute("read_file", {"path": "../../etc/passwd"})
    assert not result.success
    assert "outside the workspace" in result.output


def test_grep(workspace):
    result = GrepTool(workspace).execute(pattern=r"def \w+", glob="*.py")
    assert result.success
    assert "src/app.py:1:def main():" in result.output


def test_glob(workspace):
    result = GlobTool(workspace).execute(pattern="*.md")
    assert "README.md" in result.output


def test_run_command(workspace):
    result = RunCommandTool(workspace).execute(command="echo test-output")
    assert result.success
    assert "exit code: 0" in result.output
    assert "test-output" in result.output


def test_run_command_failure(workspace):
    result = RunCommandTool(workspace).execute(command="exit 3")
    assert not result.success
    assert "exit code: 3" in result.output


def test_registry_dispatch_and_unknown_tool(workspace):
    registry = default_registry(workspace)
    assert registry.execute("list_dir", {}).success
    unknown = registry.execute("nonexistent", {})
    assert not unknown.success


def test_registry_survives_bad_arguments(workspace):
    registry = default_registry(workspace)
    result = registry.execute("read_file", {"wrong_arg": True})
    assert not result.success
