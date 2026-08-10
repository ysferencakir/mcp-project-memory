import json
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_uses_locked_non_root_runtime():
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "python:3.11.15-slim-bookworm" in dockerfile
    assert "sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3" in dockerfile
    assert "ghcr.io/astral-sh/uv:0.11.32" in dockerfile
    assert "sha256:df4cae8f3a96d175e2e5f992e597550000edbe78fdc2594d5cd8de1a217f504c" in dockerfile
    assert "uv sync --locked --no-dev --no-editable" in dockerfile
    assert 'ENTRYPOINT ["mcp-obsidian"]' in dockerfile
    assert "USER mcp" in dockerfile
    assert "OBSIDIAN_API_KEY" not in dockerfile


def test_dockerignore_excludes_local_secrets_and_platform_state():
    ignored = set(
        (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    )

    assert {".env", ".venv", ".git", "test-vault"} <= ignored


def test_codex_docker_config_preserves_stdio_and_secret_forwarding():
    path = (
        REPO_ROOT
        / "docs"
        / "config-examples"
        / "codex-docker-config.toml.example"
    )
    config = tomllib.loads(path.read_text(encoding="utf-8"))
    server = config["mcp_servers"]["project_memory"]

    assert server["command"] == "docker"
    assert server["env_vars"] == ["OBSIDIAN_API_KEY", "PROJECT_MEMORY_ROOT"]
    assert "-i" in server["args"]
    assert "-t" not in server["args"]
    assert server["args"][-1] == "mcp-project-memory:local"
    assert "--network" not in server["args"]
    assert "OBSIDIAN_HOST=host.docker.internal" in server["args"]
    assert "PROJECT_MEMORY_ROOT" in server["args"]


def test_claude_docker_config_is_valid_json_and_uses_same_image():
    path = (
        REPO_ROOT
        / "docs"
        / "config-examples"
        / "claude-docker-mcp.json.example"
    )
    config = json.loads(path.read_text(encoding="utf-8"))
    server = config["mcpServers"]["project-memory"]

    assert server["type"] == "stdio"
    assert server["command"] == "docker"
    assert "-i" in server["args"]
    assert "-t" not in server["args"]
    assert server["args"][-1] == "mcp-project-memory:local"
    assert "--network" not in server["args"]
    assert "OBSIDIAN_HOST=host.docker.internal" in server["args"]
    assert server["env"]["OBSIDIAN_API_KEY"] == "${OBSIDIAN_API_KEY}"
    assert server["env"]["PROJECT_MEMORY_ROOT"] == "${PROJECT_MEMORY_ROOT}"
