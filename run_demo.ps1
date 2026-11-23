$ErrorActionPreference = "Stop"
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Virtual environment not found. Run .\install_windows.ps1 first."
}
.\.venv\Scripts\python.exe -m scimap_agent.cli analyze --input data\sample\synthetic_wos.txt --output outputs\demo --min-occurrences 2 --dpi 150
