@echo off
setlocal
title mcp-project-memory - Install or Repair

echo mcp-project-memory install/repair is starting...
echo Keep Docker Desktop and Obsidian open.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup-work-mode.ps1"
set "exitCode=%ERRORLEVEL%"

echo.
if "%exitCode%"=="0" (
  echo SUCCESS: Installation and live checks completed.
) else (
  echo FAILED: Installation was not completed. Existing Codex config was not replaced before live checks passed.
)
echo.
pause
exit /b %exitCode%
