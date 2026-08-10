import json
from unittest.mock import patch

import pytest

from mcp_obsidian import project_tools
from mcp_obsidian.project_memory import (
    CheckpointResult,
    CreateFileResult,
    InitProjectResult,
    ProjectContextResult,
)


def _text(result):
    assert len(result) == 1
    return result[0].text


def test_create_project_file_safe_schema_requires_path_and_content():
    tool = project_tools.CreateProjectFileSafeToolHandler().get_tool_description()

    assert tool.name == "project_create_file_safe"
    assert set(tool.inputSchema["required"]) == {"relative_path", "content"}


def test_create_project_file_safe_handler_validates_arguments():
    handler = project_tools.CreateProjectFileSafeToolHandler()

    with pytest.raises(RuntimeError, match="relative_path and content"):
        handler.run_tool({"relative_path": "STATE.md"})


def test_create_project_file_safe_handler_requires_api_key(monkeypatch):
    monkeypatch.delenv("OBSIDIAN_API_KEY", raising=False)
    handler = project_tools.CreateProjectFileSafeToolHandler()

    with pytest.raises(RuntimeError, match="OBSIDIAN_API_KEY"):
        handler.run_tool({"relative_path": "STATE.md", "content": "# State\n"})


def test_create_project_file_safe_handler_returns_structured_result(monkeypatch):
    monkeypatch.setenv("OBSIDIAN_API_KEY", "test-key")
    monkeypatch.setenv("OBSIDIAN_HOST", "localhost")
    handler = project_tools.CreateProjectFileSafeToolHandler()

    with patch("mcp_obsidian.project_tools.obsidian.Obsidian") as client_cls, patch(
        "mcp_obsidian.project_tools.ProjectMemory"
    ) as service_cls:
        service_cls.return_value.create_file_safe.return_value = CreateFileResult(
            status="created", path="STATE.md"
        )
        result = handler.run_tool(
            {"relative_path": "STATE.md", "content": "# State\n"}
        )

    client_cls.assert_called_once_with(api_key="test-key", host="localhost")
    service_cls.return_value.create_file_safe.assert_called_once_with(
        "STATE.md", "# State\n"
    )
    assert json.loads(_text(result)) == {"status": "created", "path": "STATE.md"}


def test_init_project_handler_validates_and_returns_result():
    handler = project_tools.InitProjectToolHandler()
    with pytest.raises(RuntimeError, match="project_name"):
        handler.run_tool({})

    service = patch("mcp_obsidian.project_tools._build_service")
    with service as build:
        build.return_value.init_project.return_value = InitProjectResult(
            created=["PROJECT.md"],
            already_exists=["STATE.md"],
            skipped=[],
        )
        result = handler.run_tool(
            {"project_name": "Memory", "description": "Persistent context"}
        )

    build.return_value.init_project.assert_called_once_with(
        "Memory", "Persistent context"
    )
    assert json.loads(_text(result)) == {
        "created": ["PROJECT.md"],
        "already_exists": ["STATE.md"],
        "skipped": [],
    }


def test_get_project_context_handler_passes_options_and_returns_json():
    handler = project_tools.GetProjectContextToolHandler()
    with patch("mcp_obsidian.project_tools._build_service") as build:
        context = ProjectContextResult([], ["progress"], 1000, 0)
        build.return_value.get_context.return_value = context
        result = handler.run_tool({"include": ["state"], "max_chars": 1000})

    build.return_value.get_context.assert_called_once_with(
        include=["state"], max_chars=1000
    )
    assert json.loads(_text(result)) == {
        "documents": [],
        "omitted": ["progress"],
        "max_chars": 1000,
        "used_chars": 0,
    }


def test_checkpoint_handler_validates_required_arguments():
    handler = project_tools.CheckpointProjectToolHandler()
    with pytest.raises(RuntimeError, match="summary, next_steps"):
        handler.run_tool({"agent_id": "codex"})


def test_checkpoint_handler_builds_data_and_returns_result():
    handler = project_tools.CheckpointProjectToolHandler()
    with patch("mcp_obsidian.project_tools._build_service") as build:
        build.return_value.checkpoint.return_value = CheckpointResult(
            session_id="s1",
            timestamp="2026-08-10T12:30:00Z",
            session_path="sessions/s1.md",
            updated_paths=["STATE.md", "HANDOFF.md", "PROGRESS.md"],
        )
        result = handler.run_tool(
            {
                "agent_id": "codex",
                "summary": "done",
                "next_steps": ["continue"],
                "completed": ["tests"],
                "session_id": "s1",
            }
        )

    data = build.return_value.checkpoint.call_args.args[0]
    assert data.agent_id == "codex"
    assert data.completed == ["tests"]
    assert data.pending_approvals == ()
    assert json.loads(_text(result)) == {
        "session_id": "s1",
        "timestamp": "2026-08-10T12:30:00Z",
        "session_path": "sessions/s1.md",
        "updated_paths": ["STATE.md", "HANDOFF.md", "PROGRESS.md"],
    }
