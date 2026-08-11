@echo off
setlocal
title mcp-project-memory - Emergency Disable

echo Only the project_memory MCP entry will be disabled.
echo Other MCP servers, the Docker image, and Obsidian data will be preserved.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\disable-project-memory.ps1"
set "exitCode=%ERRORLEVEL%"

echo.
if "%exitCode%"=="0" (
  echo SUCCESS: project_memory is disabled. Fully quit and reopen ChatGPT.
) else (
  echo FAILED: project_memory could not be disabled. Review the messages above.
)
echo.
pause
exit /b %exitCode%
