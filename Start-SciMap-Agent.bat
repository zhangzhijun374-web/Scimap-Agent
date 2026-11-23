@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_analysis_windows.ps1"
if errorlevel 1 (
  echo.
  echo SciMap-Agent encountered an error. Review the messages above.
  pause
)
