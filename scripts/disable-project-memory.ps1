#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$ConfigPath = (Join-Path $env:USERPROFILE ".codex\config.toml")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Set-BooleanSetting {
    param(
        [string]$Block,
        [string]$Name,
        [bool]$Value
    )

    $literal = if ($Value) { "true" } else { "false" }
    $pattern = "(?m)^$([Text.RegularExpressions.Regex]::Escape($Name))\s*=.*$"
    if ([Text.RegularExpressions.Regex]::IsMatch($Block, $pattern)) {
        return [Text.RegularExpressions.Regex]::Replace(
            $Block,
            $pattern,
            "$Name = $literal"
        )
    }

    return $Block.TrimEnd() + [Environment]::NewLine + "$Name = $literal" + [Environment]::NewLine
}

try {
    if (-not (Test-Path -LiteralPath $ConfigPath)) {
        throw "Codex config was not found: $ConfigPath"
    }

    $existing = [IO.File]::ReadAllText($ConfigPath)
    $pattern = "(?ms)^\[mcp_servers\.project_memory\]\r?\n.*?(?=^\[[^\r\n]+\]\s*$|\z)"
    $match = [Text.RegularExpressions.Regex]::Match($existing, $pattern)
    if (-not $match.Success) {
        throw "The [mcp_servers.project_memory] block was not found in: $ConfigPath"
    }

    $updatedBlock = Set-BooleanSetting -Block $match.Value -Name "enabled" -Value $false
    $updatedBlock = Set-BooleanSetting -Block $updatedBlock -Name "required" -Value $false
    $updated = $existing.Remove($match.Index, $match.Length).Insert($match.Index, $updatedBlock)

    if ($updated -eq $existing) {
        Write-Host "project_memory is already disabled and non-required." -ForegroundColor Green
        Write-Host "Other MCP servers were preserved. Fully quit and reopen ChatGPT."
        exit 0
    }

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmssfff"
    $backupPath = "$ConfigPath.backup-$timestamp"
    Copy-Item -LiteralPath $ConfigPath -Destination $backupPath

    $utf8WithoutBom = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($ConfigPath, $updated, $utf8WithoutBom)

    Write-Host "project_memory disabled safely." -ForegroundColor Green
    Write-Host "Backup: $backupPath"
    Write-Host "Only project_memory was disabled; other MCP servers were preserved."
    Write-Host "Fully quit and reopen ChatGPT. Run INSTALL.cmd to enable it again."
    exit 0
}
catch {
    Write-Host "DISABLE FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
