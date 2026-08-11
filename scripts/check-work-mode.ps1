#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$ConfigPath = (Join-Path $env:USERPROFILE ".codex\config.toml")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$imageName = "mcp-project-memory:local"
$failureCount = 0

function Write-CheckOk {
    param([string]$Message)
    Write-Host "[OK]   $Message" -ForegroundColor Green
}

function Write-CheckFail {
    param([string]$Message)
    $script:failureCount += 1
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Write-CheckWarn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function ConvertTo-PythonEncodedCommand {
    param([string]$Source)

    $encodedSource = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Source))
    return "import base64; exec(base64.b64decode('$encodedSource'))"
}

function Get-DockerCommandPath {
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\docker.exe"),
        "C:\Program Files\Docker\Docker\resources\bin\docker.exe",
        "C:\ProgramData\DockerDesktop\version-bin\docker.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

function Test-ConfigSetting {
    param(
        [string]$Block,
        [string]$Pattern,
        [string]$SuccessMessage,
        [string]$FailureMessage
    )

    if ($Block -match $Pattern) {
        Write-CheckOk $SuccessMessage
    }
    else {
        Write-CheckFail $FailureMessage
    }
}

Write-Host "mcp-project-memory readiness check"
Write-Host "No API key or vault content will be printed."
Write-Host ""

$configBlock = $null
if (-not (Test-Path -LiteralPath $ConfigPath)) {
    Write-CheckFail "Codex config was not found: $ConfigPath"
}
else {
    $configText = [IO.File]::ReadAllText($ConfigPath)
    $configPattern = "(?ms)^\[mcp_servers\.project_memory\]\r?\n.*?(?=^\[[^\r\n]+\]\s*$|\z)"
    $configMatch = [Text.RegularExpressions.Regex]::Match($configText, $configPattern)
    if (-not $configMatch.Success) {
        Write-CheckFail "Codex config does not contain [mcp_servers.project_memory]."
    }
    else {
        $configBlock = $configMatch.Value
        Write-CheckOk "Codex project_memory block exists."
        Test-ConfigSetting $configBlock '(?m)^enabled\s*=\s*true\s*$' `
            "project_memory is enabled." `
            "project_memory is not enabled. Run INSTALL.cmd."
        Test-ConfigSetting $configBlock '(?m)^required\s*=\s*false\s*$' `
            "Work safety setting required=false is active." `
            "required=false is missing. Run INSTALL.cmd before using Work."
        Test-ConfigSetting $configBlock '(?im)^command\s*=\s*"[^"]*docker(?:\.exe)?"\s*$' `
            "Codex starts project_memory through Docker." `
            "project_memory command is not Docker. Run INSTALL.cmd."
        Test-ConfigSetting $configBlock 'mcp-project-memory:local' `
            "Codex configuration uses the local project-memory image." `
            "Codex configuration does not reference mcp-project-memory:local."
    }
}

$apiKey = [Environment]::GetEnvironmentVariable("OBSIDIAN_API_KEY", "User")
$projectRoot = [Environment]::GetEnvironmentVariable("PROJECT_MEMORY_ROOT", "User")
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-CheckFail "OBSIDIAN_API_KEY is not configured for this Windows user."
}
elseif ($apiKey.StartsWith("Bearer ", [StringComparison]::OrdinalIgnoreCase)) {
    Write-CheckFail "OBSIDIAN_API_KEY must not include the Bearer prefix."
}
else {
    Write-CheckOk "Obsidian API key is configured (value hidden)."
}

if ($null -eq $projectRoot) {
    Write-CheckFail "PROJECT_MEMORY_ROOT is not configured for this Windows user."
}
else {
    Write-CheckOk "Project memory root is configured (empty means vault root)."
}

$dockerCommand = Get-DockerCommandPath
$dockerReady = $false
$imageReady = $false
if ($null -eq $dockerCommand) {
    Write-CheckFail "Docker CLI was not found. Install and start Docker Desktop."
}
else {
    Write-CheckOk "Docker CLI found."
    try {
        $dockerVersion = & $dockerCommand version --format "{{.Server.Version}}" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-CheckFail "Docker Engine is not ready. Start Docker Desktop."
        }
        else {
            $dockerReady = $true
            Write-CheckOk "Docker Engine is ready."
        }
    }
    catch {
        Write-CheckFail "Docker Engine could not be started or queried. Start Docker Desktop."
    }
}

if ($dockerReady) {
    try {
        $imageOutput = & $dockerCommand image inspect --format "{{.Id}}" $imageName 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-CheckFail "Docker image '$imageName' was not found. Run INSTALL.cmd."
        }
        else {
            $imageReady = $true
            Write-CheckOk "Docker image '$imageName' exists."
        }
    }
    catch {
        Write-CheckFail "Docker image '$imageName' could not be inspected. Run INSTALL.cmd."
    }
}
else {
    Write-CheckWarn "Image and live container checks were skipped because Docker is unavailable."
}

$previousApiKey = $env:OBSIDIAN_API_KEY
$previousProjectRoot = $env:PROJECT_MEMORY_ROOT
try {
    if ($imageReady -and $null -ne $projectRoot) {
        $env:PROJECT_MEMORY_ROOT = $projectRoot
        $handshakeProbe = @'
import os
from importlib.metadata import version

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp_obsidian.project_memory import validate_relative_path


async def main():
    validate_relative_path(os.environ["PROJECT_MEMORY_ROOT"], allow_empty=True)
    server = StdioServerParameters(
        command="mcp-obsidian",
        env={**os.environ, "OBSIDIAN_API_KEY": "handshake-only"},
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            assert initialized.serverInfo.name == "mcp-project-memory"
            assert initialized.instructions
            assert "project_get_context" in initialized.instructions[:512]
            assert len(tools.tools) == 19
            print("|".join((version("mcp"), initialized.serverInfo.name, initialized.serverInfo.version, str(len(tools.tools)))))


anyio.run(main)
'@
        $handshakeCommand = ConvertTo-PythonEncodedCommand -Source $handshakeProbe

        try {
            $handshakeOutput = & $dockerCommand @(
                "run",
                "--rm",
                "--entrypoint",
                "python",
                "-e",
                "OBSIDIAN_API_KEY=handshake-only",
                "-e",
                "PROJECT_MEMORY_ROOT",
                $imageName,
                "-c",
                $handshakeCommand
            )
            $handshakeLine = [string]($handshakeOutput | Select-Object -Last 1)
            if ($LASTEXITCODE -ne 0 -or $handshakeLine -notmatch "^1\.29\.0\|mcp-project-memory\|[^|]+\|19$") {
                Write-CheckFail "MCP container initialize/tools-list probe failed. Run INSTALL.cmd."
            }
            else {
                Write-CheckOk "MCP handshake succeeded with SDK 1.29.0 and 19 tools."
            }
        }
        catch {
            Write-CheckFail "MCP container could not be started for its handshake. Run INSTALL.cmd."
        }
    }
    elseif ($imageReady) {
        Write-CheckWarn "MCP handshake was skipped because PROJECT_MEMORY_ROOT is missing."
    }

    if ($imageReady -and -not [string]::IsNullOrWhiteSpace($apiKey)) {
        $env:OBSIDIAN_API_KEY = $apiKey
        $obsidianProbe = @(
            "import os",
            "import re",
            "import requests",
            "import urllib3",
            "from mcp_obsidian.obsidian import Obsidian",
            "urllib3.disable_warnings()",
            "status = requests.get('https://host.docker.internal:27124/', verify=False, timeout=(3, 6)).json()",
            "plugin_version = status.get('versions', {}).get('self')",
            "version_match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)', plugin_version or '')",
            "assert version_match, f'Expected Local REST API >=4.1.7 and <6.0.0, found {plugin_version}'",
            "plugin_version_tuple = tuple(map(int, version_match.groups()))",
            "assert (4, 1, 7) <= plugin_version_tuple < (6, 0, 0), f'Expected Local REST API >=4.1.7 and <6.0.0, found {plugin_version}'",
            "client = Obsidian(api_key=os.environ['OBSIDIAN_API_KEY'], host='host.docker.internal', port=27124, protocol='https')",
            "client.list_files_in_vault()",
            "print('OBSIDIAN_OK|' + plugin_version)"
        ) -join "; "

        try {
            $obsidianOutput = & $dockerCommand @(
                "run",
                "--rm",
                "--entrypoint",
                "python",
                "-e",
                "OBSIDIAN_API_KEY",
                $imageName,
                "-c",
                $obsidianProbe
            ) 2>&1
            $obsidianLine = [string]($obsidianOutput | Select-Object -Last 1)
            if ($LASTEXITCODE -ne 0 -or $obsidianLine -notmatch "^OBSIDIAN_OK\|(?<version>\d+\.\d+\.\d+)$") {
                Write-CheckFail "Compatible Obsidian Local REST API authentication failed (requires >=4.1.7 and <6.0.0). Keep Obsidian open and verify its plugin/API key."
            }
            else {
                Write-CheckOk "Obsidian Local REST API $($Matches['version']) is reachable and authenticated."
            }
        }
        catch {
            Write-CheckFail "Obsidian connection probe could not start. Keep Docker Desktop and Obsidian open."
        }
    }
    elseif ($imageReady) {
        Write-CheckWarn "Obsidian authentication check was skipped because the API key is missing."
    }
}
finally {
    $env:OBSIDIAN_API_KEY = $previousApiKey
    $env:PROJECT_MEMORY_ROOT = $previousProjectRoot
    $apiKey = $null
}

Write-Host ""
if ($failureCount -gt 0) {
    Write-Host "CHECK FAILED: $failureCount required check(s) failed." -ForegroundColor Red
    Write-Host "Fix the messages above or run INSTALL.cmd, then run CHECK.cmd again."
    exit 1
}

Write-Host "ALL CHECKS PASSED: project_memory is ready for a new Work chat." -ForegroundColor Green
Write-Host "If ChatGPT was open during setup, fully quit it (including the tray) and reopen it."
exit 0
