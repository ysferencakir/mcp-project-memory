from datetime import datetime, timezone
from typing import Sequence, cast
from unittest.mock import MagicMock, patch

import pytest

from mcp_obsidian.config import ProjectMemoryConfig
from mcp_obsidian.obsidian import ObsidianApiError
from mcp_obsidian.project_memory import (
    CheckpointConflictError,
    CheckpointData,
    CreateFileResult,
    ProjectMemory,
    ProjectPathError,
    validate_relative_path,
)


def _service(root=""):
    client = MagicMock()
    return ProjectMemory(client, ProjectMemoryConfig(root=root)), client


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/STATE.md",
        "STATE.md/",
        "../STATE.md",
        "notes/../STATE.md",
        "notes//STATE.md",
        "./STATE.md",
        "notes\\STATE.md",
        "%2e%2e/STATE.md",
        " STATE.md",
        "STATE.md ",
        "STATE.md\x00",
    ],
)
def test_validate_relative_path_rejects_unsafe_or_ambiguous_paths(path):
    with pytest.raises(ProjectPathError):
        validate_relative_path(path)


def test_validate_relative_path_allows_unicode_and_nested_paths():
    assert validate_relative_path("oturumlar/gelişme.md") == "oturumlar/gelişme.md"


def test_validate_relative_path_rejects_non_string_input():
    with pytest.raises(ProjectPathError, match="path must be a string"):
        validate_relative_path(cast(str, 1))


def test_resolve_path_defaults_to_vault_root():
    service, _ = _service()
    assert service.resolve_path("STATE.md") == "STATE.md"


def test_resolve_path_supports_configured_subdirectory():
    service, _ = _service("memory/project")
    assert service.resolve_path("sessions/one.md") == "memory/project/sessions/one.md"


def test_resolve_path_requires_markdown_extension():
    service, _ = _service()
    with pytest.raises(ProjectPathError, match=".md extension"):
        service.resolve_path("STATE.txt")


def test_resolve_path_validates_configured_root():
    service, _ = _service("../other-project")
    with pytest.raises(ProjectPathError):
        service.resolve_path("STATE.md")


def test_resolve_document_path_rejects_unknown_document():
    service, _ = _service()
    with pytest.raises(ValueError, match="unknown project document"):
        service.resolve_document_path("missing")


def test_create_file_safe_does_not_write_when_file_exists():
    service, client = _service()
    client.get_file_contents.return_value = "existing"

    result = service.create_file_safe("STATE.md", "new")

    assert result.status == "already_exists"
    assert result.path == "STATE.md"
    client.put_content.assert_not_called()


def test_create_file_safe_creates_only_after_404():
    service, client = _service("memory")
    client.get_file_contents.side_effect = ObsidianApiError(404, 40400, "missing")

    result = service.create_file_safe("STATE.md", "# State\n")

    assert result.status == "created"
    assert result.path == "memory/STATE.md"
    client.put_content.assert_called_once_with("memory/STATE.md", "# State\n")


def test_create_file_safe_propagates_non_404_api_error():
    service, client = _service()
    error = ObsidianApiError(401, 40149, "bad key")
    client.get_file_contents.side_effect = error

    with pytest.raises(ObsidianApiError) as excinfo:
        service.create_file_safe("STATE.md", "new")

    assert excinfo.value is error
    client.put_content.assert_not_called()


def test_create_file_safe_propagates_transport_error():
    service, client = _service()
    error = Exception("Request failed: offline")
    client.get_file_contents.side_effect = error

    with pytest.raises(Exception, match="offline"):
        service.create_file_safe("STATE.md", "new")

    client.put_content.assert_not_called()


def test_create_file_safe_rejects_non_string_content():
    service, client = _service()

    with pytest.raises(ValueError, match="content must be a string"):
        service.create_file_safe("STATE.md", cast(str, None))

    client.get_file_contents.assert_not_called()


def test_init_project_creates_templates_without_overwriting_existing_files():
    service, _ = _service()
    results = [
        CreateFileResult("created", "PROJECT.md"),
        CreateFileResult("already_exists", "STATE.md"),
        CreateFileResult("created", "ROADMAP.md"),
        CreateFileResult("created", "DECISIONS.md"),
        CreateFileResult("created", "TODO.md"),
        CreateFileResult("created", "HANDOFF.md"),
        CreateFileResult("created", "PROGRESS.md"),
    ]

    with patch.object(service, "create_file_safe", side_effect=results) as create:
        result = service.init_project("Memory Project", "Persistent context")

    assert result.already_exists == ["STATE.md"]
    assert "PROJECT.md" in result.created
    assert "PROGRESS.md" in result.created
    assert result.skipped == []
    project_call = create.call_args_list[0]
    assert project_call.args[0] == "PROJECT.md"
    assert "Memory Project" in project_call.args[1]
    assert "Persistent context" in project_call.args[1]
    assert "[[STATE.md|STATE]]" in project_call.args[1]
    assert "[[ROADMAP.md|ROADMAP]]" in project_call.args[1]
    assert "[[TODO.md|TODO]]" in project_call.args[1]


def test_init_project_index_uses_configured_root_and_document_paths():
    client = MagicMock()
    service = ProjectMemory(
        client,
        ProjectMemoryConfig(
            root="workspace",
            documents={
                "project": "OVERVIEW.md",
                "state": "status/CURRENT.md",
                "roadmap": "plans/NEXT.md",
            },
        ),
    )

    def create(relative_path, _content):
        return CreateFileResult("created", service.resolve_path(relative_path))

    with patch.object(service, "create_file_safe", side_effect=create) as create_file:
        result = service.init_project("Configured Project")

    project_content = create_file.call_args_list[0].args[1]
    assert "[[workspace/status/CURRENT.md|STATE]]" in project_content
    assert "[[workspace/plans/NEXT.md|ROADMAP]]" in project_content
    assert "TODO" not in project_content
    assert result.created == [
        "workspace/OVERVIEW.md",
        "workspace/status/CURRENT.md",
        "workspace/plans/NEXT.md",
    ]


def test_init_project_reports_templates_missing_from_custom_mapping():
    client = MagicMock()
    service = ProjectMemory(
        client,
        ProjectMemoryConfig(documents={"project": "ABOUT.md"}),
    )

    with patch.object(
        service,
        "create_file_safe",
        return_value=CreateFileResult("created", "ABOUT.md"),
    ):
        result = service.init_project("Project")

    assert result.created == ["ABOUT.md"]
    assert set(result.skipped) == {
        "state",
        "roadmap",
        "decisions",
        "todo",
        "handoff",
        "progress",
    }


@pytest.mark.parametrize(
    ("name", "description", "message"),
    [
        ("", "", "project_name"),
        ("Project", cast(str, None), "description"),
    ],
)
def test_init_project_validates_inputs(name, description, message):
    service, _ = _service()
    with pytest.raises(ValueError, match=message):
        service.init_project(name, description)


def test_get_context_uses_continuity_priority_and_reports_missing_documents():
    service, client = _service()

    def get_content(path):
        if path == "HANDOFF.md":
            raise ObsidianApiError(404, 40400, "missing")
        return f"content:{path}"

    client.get_file_contents.side_effect = get_content
    result = service.get_context(max_chars=10_000)

    assert [document.name for document in result.documents] == [
        "project",
        "state",
        "handoff",
        "roadmap",
        "todo",
        "decisions",
        "progress",
    ]
    handoff = result.documents[2]
    assert handoff.status == "missing"
    assert handoff.content is None
    assert result.omitted == []


def test_get_context_honors_include_order_and_removes_duplicates():
    service, client = _service()
    client.get_file_contents.side_effect = ["handoff", "state"]

    result = service.get_context(include=["handoff", "state", "handoff"])

    assert [document.name for document in result.documents] == ["handoff", "state"]
    assert client.get_file_contents.call_count == 2


def test_get_context_truncates_at_budget_and_reports_omitted_documents():
    client = MagicMock()
    client.get_file_contents.return_value = "123456789"
    service = ProjectMemory(
        client,
        ProjectMemoryConfig(documents={"project": "PROJECT.md", "state": "STATE.md"}),
    )

    result = service.get_context(max_chars=5)

    assert result.used_chars == 5
    assert result.documents[0].content == "12345"
    assert result.documents[0].truncated is True
    assert result.omitted == ["state"]
    client.get_file_contents.assert_called_once_with("PROJECT.md")


@pytest.mark.parametrize("max_chars", [0, -1, 200_001, True, "100"])
def test_get_context_validates_budget(max_chars):
    service, _ = _service()
    with pytest.raises(ValueError, match="between 1 and 200000"):
        service.get_context(max_chars=cast(int, max_chars))


def test_get_context_rejects_unknown_or_non_string_document_names():
    service, _ = _service()
    with pytest.raises(ValueError, match="unknown project documents"):
        service.get_context(include=["missing"])
    with pytest.raises(ValueError, match="only document names"):
        service.get_context(include=cast(Sequence[str], [1]))


def _checkpoint_data(**overrides):
    values = {
        "agent_id": "codex",
        "summary": "Implemented project continuity.",
        "next_steps": ["Run the live Obsidian smoke test."],
        "completed": ["Added checkpoint support."],
        "blockers": [],
        "decisions": ["Use one project per vault."],
        "pending_approvals": ["Approve main computer installation."],
        "verification": ["Tests passed."],
        "files_changed": ["project_memory.py"],
        "session_id": "session-1",
    }
    values.update(overrides)
    return CheckpointData(**values)


def test_checkpoint_creates_append_only_session_then_updates_current_documents():
    service, client = _service()
    now = datetime(2026, 8, 10, 12, 30, tzinfo=timezone.utc)

    with patch.object(
        service,
        "create_file_safe",
        return_value=CreateFileResult(
            "created", "sessions/session-1.md"
        ),
    ) as create:
        result = service.checkpoint(_checkpoint_data(), now=now)

    assert result.session_id == "session-1"
    assert result.timestamp == "2026-08-10T12:30:00Z"
    assert result.updated_paths == [
        "STATE.md",
        "HANDOFF.md",
        "DECISIONS.md",
        "PROGRESS.md",
    ]
    session_content = create.call_args.args[1]
    assert "# Session session-1" in session_content
    assert "Approve main computer installation" in session_content
    assert client.put_content.call_count == 2
    state_content = client.put_content.call_args_list[0].args[1]
    assert "Implemented project continuity" in state_content
    assert "Run the live Obsidian smoke test" in state_content
    assert client.append_content.call_count == 2
    decisions_call = client.append_content.call_args_list[0]
    assert decisions_call.args[0] == "DECISIONS.md"
    assert "Use one project per vault" in decisions_call.args[1]
    assert "Approve main computer installation" not in decisions_call.args[1]
    progress_content = client.append_content.call_args_list[1].args[1]
    assert "2026-08-10T12:30:00Z" in progress_content
    assert "[[sessions/session-1.md]]" in progress_content


def test_checkpoint_without_explicit_id_keeps_timestamped_session_path():
    service, _ = _service()
    now = datetime(2026, 8, 10, 12, 30, tzinfo=timezone.utc)

    with (
        patch("mcp_obsidian.project_memory.uuid4") as uuid4,
        patch.object(
            service,
            "create_file_safe",
            return_value=CreateFileResult(
                "created", "sessions/2026-08-10T12-30-00Z-abcdef123456.md"
            ),
        ) as create,
    ):
        uuid4.return_value.hex = "abcdef1234567890"
        result = service.checkpoint(
            _checkpoint_data(session_id=None, decisions=[]), now=now
        )

    assert result.session_id == "abcdef123456"
    assert create.call_args.args[0] == (
        "sessions/2026-08-10T12-30-00Z-abcdef123456.md"
    )


def test_explicit_session_id_conflicts_even_at_a_different_timestamp():
    service, client = _service()
    first_time = datetime(2026, 8, 10, 12, 30, tzinfo=timezone.utc)
    second_time = datetime(2026, 8, 10, 12, 31, tzinfo=timezone.utc)

    with patch.object(
        service,
        "create_file_safe",
        side_effect=[
            CreateFileResult("created", "sessions/session-1.md"),
            CreateFileResult("already_exists", "sessions/session-1.md"),
        ],
    ) as create:
        service.checkpoint(_checkpoint_data(), now=first_time)
        client.reset_mock()

        with pytest.raises(CheckpointConflictError, match="already exists"):
            service.checkpoint(_checkpoint_data(), now=second_time)

    assert [call.args[0] for call in create.call_args_list] == [
        "sessions/session-1.md",
        "sessions/session-1.md",
    ]
    client.put_content.assert_not_called()
    client.append_content.assert_not_called()


def test_checkpoint_conflict_never_updates_current_documents():
    service, client = _service()
    with patch.object(
        service,
        "create_file_safe",
        return_value=CreateFileResult(
            "already_exists", "sessions/existing-session.md"
        ),
    ):
        with pytest.raises(CheckpointConflictError, match="already exists"):
            service.checkpoint(_checkpoint_data())

    client.put_content.assert_not_called()
    client.append_content.assert_not_called()


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"agent_id": ""}, "agent_id"),
        ({"summary": ""}, "summary"),
        ({"next_steps": []}, "next_steps"),
        ({"completed": cast(Sequence[str], "bad")}, "completed"),
        ({"completed": [""]}, "completed"),
        ({"session_id": "bad/session"}, "session_id"),
    ],
)
def test_checkpoint_validates_inputs_before_writing(overrides, message):
    service, client = _service()
    with pytest.raises(ValueError, match=message):
        service.checkpoint(_checkpoint_data(**overrides))

    client.put_content.assert_not_called()
    client.append_content.assert_not_called()
