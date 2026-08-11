@echo off
setlocal
title mcp-project-memory - Check

echo mcp-project-memory diagnostics are starting...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\check-work-mode.ps1"
set "exitCode=%ERRORLEVEL%"

echo.
if "%exitCode%"=="0" (
  echo SUCCESS: project_memory is ready for a new Work chat.
) else (
  echo FAILED: One or more checks need attention. Review the messages above.
)
echo.
pause
exit /b %exitCode%
