import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest


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
    assert server["enabled"] is True
    assert server["required"] is False


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


def test_work_mode_setup_script_is_non_blocking_and_secret_safe():
    script = (REPO_ROOT / "scripts" / "setup-work-mode.ps1").read_text(
        encoding="utf-8"
    )

    assert "Read-Host \"Obsidian Local REST API key\" -AsSecureString" in script
    assert 'Read-Host "Vault-relative project memory folder' in script
    assert '$PSBoundParameters.ContainsKey("ProjectMemoryRoot")' in script
    assert 'StartsWith("Bearer "' in script
    assert 'PROJECT_MEMORY_ROOT must be vault-relative' in script
    assert 'Join-Path $env:USERPROFILE ".codex"' in script
    assert 'Programs\\DockerDesktop\\resources\\bin\\docker.exe' in script
    assert 'C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe' in script
    assert "config.toml.backup-" not in script
    assert 'Copy-Item -LiteralPath $Path -Destination $backupPath' in script
    assert 'required = false' in script
    assert '@("build", "--pull", "-t", $ImageName, $repoRoot)' in script
    assert 'Set-CodexConfiguration -Path $configPath -DockerCommandPath $dockerCommand' in script
    assert 'command = "$escapedDockerCommand"' in script
    assert 'INSTALL FAILED: $($_.Exception.Message)' in script
    assert "This failed run did not write a new Codex configuration." in script

    # The permanent environment and non-blocking Codex config are written only
    # after both the real MCP handshake and the required Obsidian probe.
    assert "await session.initialize()" in script
    assert "await session.list_tools()" in script
    assert 'validate_relative_path(os.environ["PROJECT_MEMORY_ROOT"]' in script
    assert "assert len(tools.tools) == 19" in script
    assert "ConvertTo-PythonEncodedCommand -Source $handshakeProbe" in script
    assert "exec(base64.b64decode('$encodedSource'))" in script
    handshake_invocation = script[
        script.index("$handshakeOutput =") : script.index("$handshakeLine =")
    ]
    assert "$handshakeCommand" in handshake_invocation
    assert "$handshakeProbe" not in handshake_invocation
    assert "assert (4, 1, 7) <= plugin_version_tuple < (6, 0, 0)" in script
    assert "assert plugin_version ==" not in script
    assert script.index('[Environment]::SetEnvironmentVariable("OBSIDIAN_API_KEY"') > (
        script.index('Write-Host "Obsidian connection OK:')
    )
    assert script.index("Set-CodexConfiguration -Path $configPath") > script.index(
        "await session.list_tools()"
    )


def test_double_click_entrypoints_call_only_their_scoped_scripts():
    expected_scripts = {
        "INSTALL.cmd": "setup-work-mode.ps1",
        "CHECK.cmd": "check-work-mode.ps1",
        "DISABLE.cmd": "disable-project-memory.ps1",
    }

    for filename, script_name in expected_scripts.items():
        content = (REPO_ROOT / filename).read_text(encoding="utf-8")

        assert "powershell.exe -NoProfile -ExecutionPolicy Bypass -File" in content
        assert f'%~dp0scripts\\{script_name}' in content
        assert "pause" in content
        assert "exit /b %exitCode%" in content
        assert "OBSIDIAN_API_KEY=" not in content
        assert "Bearer " not in content


def test_work_mode_check_is_read_only_secret_safe_and_exercises_live_stack():
    script = (REPO_ROOT / "scripts" / "check-work-mode.ps1").read_text(
        encoding="utf-8"
    )

    assert "SetEnvironmentVariable(" not in script
    assert "WriteAllText(" not in script
    assert "Copy-Item" not in script
    assert "Remove-Item" not in script
    assert 'GetEnvironmentVariable("OBSIDIAN_API_KEY", "User")' in script
    assert "No API key or vault content will be printed." in script
    assert "await session.initialize()" in script
    assert "await session.list_tools()" in script
    assert "assert len(tools.tools) == 19" in script
    assert "^1\\.29\\.0\\|mcp-project-memory\\|[^|]+\\|19$" in script
    assert "ConvertTo-PythonEncodedCommand -Source $handshakeProbe" in script
    handshake_invocation = script[
        script.index("$handshakeOutput =") : script.index("$handshakeLine =")
    ]
    assert "$handshakeCommand" in handshake_invocation
    assert "$handshakeProbe" not in handshake_invocation
    assert "2>&1" not in handshake_invocation
    assert (
        'Write-CheckFail "MCP container could not be started for its handshake. '
        'Run INSTALL.cmd."' in script
    )
    assert "client.list_files_in_vault()" in script
    assert "assert (4, 1, 7) <= plugin_version_tuple < (6, 0, 0)" in script
    assert "assert plugin_version ==" not in script
    assert "^OBSIDIAN_OK\\|(?<version>\\d+\\.\\d+\\.\\d+)$" in script
    assert '(?m)^required\\s*=\\s*false\\s*$' in script
    assert '"run",' in script
    assert '"--rm",' in script


def test_emergency_disable_is_scoped_backed_up_and_reversible():
    script = (REPO_ROOT / "scripts" / "disable-project-memory.ps1").read_text(
        encoding="utf-8"
    )

    assert "mcp_servers\\.project_memory" in script
    assert "Copy-Item -LiteralPath $ConfigPath -Destination $backupPath" in script
    assert 'Set-BooleanSetting -Block $match.Value -Name "enabled" -Value $false' in script
    assert 'Set-BooleanSetting -Block $updatedBlock -Name "required" -Value $false' in script
    assert "Text.UTF8Encoding($false)" in script
    assert "Run INSTALL.cmd to enable it again." in script
    assert "Remove-Item" not in script
    assert "SetEnvironmentVariable(" not in script
    assert "docker image rm" not in script.lower()


@pytest.mark.skipif(shutil.which("powershell.exe") is None, reason="Windows-only helper")
def test_emergency_disable_preserves_other_config_and_is_idempotent(tmp_path):
    config_path = tmp_path / "config.toml"
    original = """\
[features]
web_search = true

[mcp_servers.other]
command = "other-server"
enabled = true

[mcp_servers.project_memory]
command = "docker"
enabled = true
required = true

[profiles.demo]
model = "example"
"""
    config_path.write_text(original, encoding="utf-8")
    script_path = REPO_ROOT / "scripts" / "disable-project-memory.ps1"
    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-ConfigPath",
        str(config_path),
    ]

    first = subprocess.run(command, capture_output=True, text=True, check=False)
    assert first.returncode == 0, first.stdout + first.stderr

    updated_bytes = config_path.read_bytes()
    assert not updated_bytes.startswith(b"\xef\xbb\xbf")
    updated = tomllib.loads(updated_bytes.decode("utf-8"))
    assert updated["features"]["web_search"] is True
    assert updated["mcp_servers"]["other"]["command"] == "other-server"
    assert updated["mcp_servers"]["other"]["enabled"] is True
    assert updated["mcp_servers"]["project_memory"]["enabled"] is False
    assert updated["mcp_servers"]["project_memory"]["required"] is False
    assert updated["profiles"]["demo"]["model"] == "example"
    assert len(list(tmp_path.glob("config.toml.backup-*"))) == 1

    after_first_run = config_path.read_bytes()
    second = subprocess.run(command, capture_output=True, text=True, check=False)
    assert second.returncode == 0, second.stdout + second.stderr
    assert config_path.read_bytes() == after_first_run
    assert len(list(tmp_path.glob("config.toml.backup-*"))) == 1


def test_mcp_sdk_uses_current_maintained_v1_release():
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "mcp==1.29.0" in project["project"]["dependencies"]


def test_all_codex_examples_keep_work_usable_when_memory_is_offline():
    for filename in (
        "codex-config.toml.example",
        "codex-docker-config.toml.example",
    ):
        path = REPO_ROOT / "docs" / "config-examples" / filename
        config = tomllib.loads(path.read_text(encoding="utf-8"))
        server = config["mcp_servers"]["project_memory"]

        assert server["enabled"] is True
        assert server["required"] is False
