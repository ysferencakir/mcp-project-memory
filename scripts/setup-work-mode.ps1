#requires -Version 5.1

[CmdletBinding()]
param(
    [AllowEmptyString()]
    [string]$ProjectMemoryRoot,

    [switch]$ResetApiKey,

    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$configDirectory = Join-Path $env:USERPROFILE ".codex"
$configPath = Join-Path $configDirectory "config.toml"
$imageName = "mcp-project-memory:local"

function Assert-ProjectMemoryRoot {
    param([string]$Value)

    if ($Value -ne $Value.Trim()) {
        throw "PROJECT_MEMORY_ROOT cannot contain outer whitespace."
    }
    if ($Value.Contains("\")) {
        throw "PROJECT_MEMORY_ROOT must use '/' separators, not '\'."
    }
    if ($Value -match "^[A-Za-z]:") {
        throw "PROJECT_MEMORY_ROOT must be vault-relative, not a Windows drive path."
    }
    if ($Value -match "^/|/$|//|(^|/)\.\.?(/|$)") {
        throw "PROJECT_MEMORY_ROOT must be a safe vault-relative path."
    }
    if ($Value -match "%[0-9A-Fa-f]{2}") {
        throw "PROJECT_MEMORY_ROOT cannot contain percent-encoded path parts."
    }
    foreach ($character in $Value.ToCharArray()) {
        if ([int]$character -lt 32) {
            throw "PROJECT_MEMORY_ROOT cannot contain control characters."
        }
    }
}

function ConvertFrom-SecureStringPlainText {
    param([System.Security.SecureString]$SecureValue)

    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
}

function Invoke-NativeCommand {
    param(
        [string]$Command,
        [string[]]$Arguments,
        [string]$FailureMessage
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (exit code $LASTEXITCODE)."
    }
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

    throw "Docker CLI was not found. Install and start Docker Desktop, then rerun this script."
}

function Publish-EnvironmentChange {
    try {
        if (-not ("ProjectMemoryEnvironment" -as [type])) {
            Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class ProjectMemoryEnvironment {
    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern IntPtr SendMessageTimeout(
        IntPtr hWnd,
        uint Msg,
        UIntPtr wParam,
        string lParam,
        uint fuFlags,
        uint uTimeout,
        out UIntPtr lpdwResult
    );
}
"@
        }

        $result = [UIntPtr]::Zero
        [void][ProjectMemoryEnvironment]::SendMessageTimeout(
            [IntPtr]0xffff,
            0x001A,
            [UIntPtr]::Zero,
            "Environment",
            0x0002,
            5000,
            [ref]$result
        )
    }
    catch {
        Write-Warning "Windows environment change broadcast failed. Sign out and back in if ChatGPT cannot see the variables."
    }
}

function Set-CodexConfiguration {
    param([string]$Path)

    $block = @'
[mcp_servers.project_memory]
command = "docker"
args = [
  "run",
  "--rm",
  "-i",
  "-e",
  "OBSIDIAN_API_KEY",
  "-e",
  "OBSIDIAN_HOST=host.docker.internal",
  "-e",
  "OBSIDIAN_PORT=27124",
  "-e",
  "OBSIDIAN_PROTOCOL=https",
  "-e",
  "PROJECT_MEMORY_ROOT",
  "mcp-project-memory:local",
]
env_vars = ["OBSIDIAN_API_KEY", "PROJECT_MEMORY_ROOT"]
startup_timeout_sec = 30
tool_timeout_sec = 60
enabled = true
required = false
'@

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path) | Out-Null
    $existing = if (Test-Path -LiteralPath $Path) {
        [IO.File]::ReadAllText($Path)
    }
    else {
        ""
    }

    $pattern = "(?ms)^\[mcp_servers\.project_memory\]\r?\n.*?(?=^\[[^\r\n]+\]\s*$|\z)"
    if ([Text.RegularExpressions.Regex]::IsMatch($existing, $pattern)) {
        $updated = [Text.RegularExpressions.Regex]::Replace(
            $existing,
            $pattern,
            $block.TrimEnd() + [Environment]::NewLine
        )
    }
    else {
        $separator = if ([string]::IsNullOrWhiteSpace($existing)) {
            ""
        }
        else {
            [Environment]::NewLine + [Environment]::NewLine
        }
        $updated = $existing.TrimEnd() + $separator + $block.TrimEnd() + [Environment]::NewLine
    }

    if ($updated -eq $existing) {
        Write-Host "Codex config already up to date: $Path"
        return
    }

    if (Test-Path -LiteralPath $Path) {
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $backupPath = "$Path.backup-$timestamp"
        Copy-Item -LiteralPath $Path -Destination $backupPath
        Write-Host "Codex config backup: $backupPath"
    }

    $utf8WithoutBom = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($Path, $updated, $utf8WithoutBom)
    Write-Host "Codex config updated: $Path"
}

if (-not $PSBoundParameters.ContainsKey("ProjectMemoryRoot")) {
    $ProjectMemoryRoot = Read-Host "Vault-relative project memory folder (press Enter for vault root)"
}
Assert-ProjectMemoryRoot -Value $ProjectMemoryRoot

$dockerCommand = Get-DockerCommandPath
Invoke-NativeCommand `
    -Command $dockerCommand `
    -Arguments @("version", "--format", "{{.Server.Version}}") `
    -FailureMessage "Docker Desktop is not ready"

$apiKey = [Environment]::GetEnvironmentVariable("OBSIDIAN_API_KEY", "User")
if ($ResetApiKey -or [string]::IsNullOrWhiteSpace($apiKey)) {
    $secureApiKey = Read-Host "Obsidian Local REST API key" -AsSecureString
    if ($secureApiKey.Length -eq 0) {
        throw "OBSIDIAN_API_KEY cannot be empty."
    }
    $apiKey = ConvertFrom-SecureStringPlainText -SecureValue $secureApiKey
}
if ($apiKey.StartsWith("Bearer ", [StringComparison]::OrdinalIgnoreCase)) {
    throw "Enter only the API key; do not include the 'Bearer ' prefix."
}

$env:OBSIDIAN_API_KEY = $apiKey
$env:PROJECT_MEMORY_ROOT = $ProjectMemoryRoot

if (-not $SkipBuild) {
    Write-Host "Building $ImageName ..."
    Invoke-NativeCommand `
        -Command $dockerCommand `
        -Arguments @("build", "--pull", "-t", $ImageName, $repoRoot) `
        -FailureMessage "Docker image build failed"
}

Invoke-NativeCommand `
    -Command $dockerCommand `
    -Arguments @("image", "inspect", "--format", "{{.Id}}", $imageName) `
    -FailureMessage "Docker image '$ImageName' was not found"

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
        env={
            **os.environ,
            "OBSIDIAN_API_KEY": "handshake-only",
        },
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            assert initialized.serverInfo.name == "mcp-project-memory"
            assert initialized.instructions
            assert "project_get_context" in initialized.instructions[:512]
            assert len(tools.tools) == 19
            print(
                "|".join(
                    (
                        version("mcp"),
                        initialized.serverInfo.name,
                        initialized.serverInfo.version,
                        str(len(tools.tools)),
                    )
                )
            )


anyio.run(main)
'@

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
    $handshakeProbe
)
if ($LASTEXITCODE -ne 0) {
    throw "Container initialization probe failed (exit code $LASTEXITCODE)."
}
$handshakeLine = [string]($handshakeOutput | Select-Object -Last 1)
if ($handshakeLine -notmatch "^1\.29\.0\|mcp-project-memory\|[^|]+\|19$") {
    throw "Unexpected container initialization result: $handshakeLine"
}
Write-Host "Container initialization OK: $handshakeLine"

$obsidianProbe = @(
    "import os",
    "import requests",
    "import urllib3",
    "from mcp_obsidian.obsidian import Obsidian",
    "urllib3.disable_warnings()",
    "status = requests.get('https://host.docker.internal:27124/', verify=False, timeout=(3, 6)).json()",
    "plugin_version = status.get('versions', {}).get('self')",
    "assert plugin_version == '4.1.7', f'Expected Local REST API 4.1.7, found {plugin_version}'",
    "client = Obsidian(api_key=os.environ['OBSIDIAN_API_KEY'], host='host.docker.internal', port=27124, protocol='https')",
    "client.list_files_in_vault()",
    "print('OBSIDIAN_OK|' + plugin_version)"
) -join "; "

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
)
if ($LASTEXITCODE -ne 0 -or $obsidianOutput -notcontains "OBSIDIAN_OK|4.1.7") {
    throw "Container could not validate Obsidian Local REST API 4.1.7. Keep Obsidian and the compatible plugin open, verify the API key, then rerun this script."
}
Write-Host "Obsidian connection OK: Local REST API 4.1.7."

[Environment]::SetEnvironmentVariable("OBSIDIAN_API_KEY", $apiKey, "User")
[Environment]::SetEnvironmentVariable(
    "PROJECT_MEMORY_ROOT",
    $ProjectMemoryRoot,
    "User"
)
Publish-EnvironmentChange

Set-CodexConfiguration -Path $configPath

$apiKey = $null
$env:OBSIDIAN_API_KEY = $null

Write-Host ""
Write-Host "Setup complete."
Write-Host "1. Fully quit the ChatGPT desktop app, including the system tray."
Write-Host "2. Open it again and create a new Work chat."
Write-Host "3. Run /mcp and verify project_memory with 19 tools."
Write-Host "4. Normal test: 'Bu projede su anda neredeyiz? Herhangi bir degisiklik yapma.'"
Write-Host "If project_memory later fails, Work chats will still open because required=false."
