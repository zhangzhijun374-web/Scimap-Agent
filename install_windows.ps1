$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "[SciMap-Agent] Creating Python 3.11 virtual environment..."
py -3.11 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 was not found. Install Python 3.11 and retry." }

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
Write-Host "[SciMap-Agent] Installing dependencies..."
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }
& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
& $Python -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "SciMap-Agent installation failed." }

Write-Host "[SciMap-Agent] Installation complete."
Write-Host "Double-click Start-SciMap-Agent.bat to select bibliography files and generate figures."
Write-Host "Command-line alternative: .\.venv\Scripts\scimap.exe analyze --input data\raw --output outputs\analysis --min-occurrences auto"
