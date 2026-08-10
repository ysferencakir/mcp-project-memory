from datetime import datetime, timezone
from typing import cast

from mcp_obsidian.config import ProjectMemoryConfig
from mcp_obsidian.obsidian import Obsidian, ObsidianApiError
from mcp_obsidian.project_memory import CheckpointData, ProjectMemory


class InMemoryObsidian:
    def __init__(self):
        self.files: dict[str, str] = {}

    def get_file_contents(self, filepath: str) -> str:
        try:
            return self.files[filepath]
        except KeyError as exc:
            raise ObsidianApiError(404, 40400, "missing") from exc

    def put_content(self, filepath: str, content: str) -> None:
        self.files[filepath] = content

    def append_content(self, filepath: str, content: str) -> None:
        self.files[filepath] = self.files.get(filepath, "") + content


def test_agent_can_recover_context_after_init_and_checkpoint():
    storage = InMemoryObsidian()
    service = ProjectMemory(cast(Obsidian, storage), ProjectMemoryConfig())

    initialized = service.init_project(
        "mcp-project-memory",
        "Persistent context shared by coding agents.",
    )
    assert len(initialized.created) == 7
    assert "[[STATE.md|STATE]]" in storage.files["PROJECT.md"]
    assert "[[PROGRESS.md|PROGRESS]]" in storage.files["PROJECT.md"]

    checkpoint = service.checkpoint(
        CheckpointData(
            agent_id="claude-code",
            summary="Safe project memory primitives are working.",
            completed=["Initialized the vault.", "Added continuity tools."],
            verification=["All unit tests passed."],
            next_steps=["Continue from Codex using project_get_context."],
            session_id="handoff-to-codex",
        ),
        now=datetime(2026, 8, 10, 15, 0, tzinfo=timezone.utc),
    )

    assert checkpoint.session_path in storage.files
    assert "Safe project memory primitives" in storage.files["STATE.md"]
    assert "Continue from Codex" in storage.files["HANDOFF.md"]
    assert checkpoint.session_path in storage.files["PROGRESS.md"]

    recovered = service.get_context()
    recovered_by_name = {document.name: document for document in recovered.documents}
    assert recovered_by_name["state"].status == "loaded"
    assert "Safe project memory primitives" in (
        recovered_by_name["state"].content or ""
    )
    assert "Continue from Codex" in (recovered_by_name["handoff"].content or "")
    assert recovered.omitted == []

    state_before_second_init = storage.files["STATE.md"]
    second_init = service.init_project("mcp-project-memory")
    assert len(second_init.already_exists) == 7
    assert storage.files["STATE.md"] == state_before_second_init
