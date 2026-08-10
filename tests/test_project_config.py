import json

import pytest

from mcp_obsidian.config import ProjectMemoryConfig


def test_project_memory_config_defaults_to_vault_root(monkeypatch):
    monkeypatch.delenv("PROJECT_MEMORY_ROOT", raising=False)
    monkeypatch.delenv("PROJECT_MEMORY_DOCUMENTS", raising=False)

    config = ProjectMemoryConfig.from_env()

    assert config.root == ""
    assert config.documents["state"] == "STATE.md"
    assert config.documents["progress"] == "PROGRESS.md"


def test_project_memory_config_supports_optional_root_and_document_overrides(monkeypatch):
    monkeypatch.setenv("PROJECT_MEMORY_ROOT", "memory")
    monkeypatch.setenv(
        "PROJECT_MEMORY_DOCUMENTS",
        json.dumps({"state": "status/CURRENT.md", "custom": "CUSTOM.md"}),
    )

    config = ProjectMemoryConfig.from_env()

    assert config.root == "memory"
    assert config.documents["state"] == "status/CURRENT.md"
    assert config.documents["custom"] == "CUSTOM.md"
    assert config.documents["handoff"] == "HANDOFF.md"


def test_project_memory_config_rejects_invalid_json(monkeypatch):
    monkeypatch.setenv("PROJECT_MEMORY_DOCUMENTS", "not-json")

    with pytest.raises(ValueError, match="valid JSON object"):
        ProjectMemoryConfig.from_env()


@pytest.mark.parametrize(
    "value",
    [json.dumps(["STATE.md"]), json.dumps({"state": 1})],
)
def test_project_memory_config_rejects_non_string_mapping(monkeypatch, value):
    monkeypatch.setenv("PROJECT_MEMORY_DOCUMENTS", value)

    with pytest.raises(ValueError, match="map string names to string paths"):
        ProjectMemoryConfig.from_env()
