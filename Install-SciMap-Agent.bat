@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1"
echo.
echo If installation completed, double-click Start-SciMap-Agent.bat to analyze your bibliography exports.
pause
