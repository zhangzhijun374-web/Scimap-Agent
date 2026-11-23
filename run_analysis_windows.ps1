$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    [System.Windows.Forms.MessageBox]::Show(
        "SciMap-Agent has not been installed yet. Run install_windows.ps1 first.",
        "SciMap-Agent", "OK", "Warning"
    ) | Out-Null
    throw "Virtual environment not found. Run .\install_windows.ps1 first."
}

$open = New-Object System.Windows.Forms.OpenFileDialog
$open.Title = "Select bibliography export files"
$open.Filter = "Bibliography files (*.csv;*.txt;*.ciw;*.wos;*.ris;*.xlsx)|*.csv;*.txt;*.ciw;*.wos;*.ris;*.xlsx|All files (*.*)|*.*"
$open.Multiselect = $true
$open.CheckFileExists = $true

if ($open.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
    Write-Host "No files selected."
    exit 0
}

$folder = New-Object System.Windows.Forms.FolderBrowserDialog
$folder.Description = "Choose where SciMap-Agent should save the figures and report"
$folder.ShowNewFolderButton = $true
$DefaultOutput = Join-Path $ProjectRoot "outputs\analysis"
New-Item -ItemType Directory -Path $DefaultOutput -Force | Out-Null
$folder.SelectedPath = $DefaultOutput

if ($folder.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
    Write-Host "No output folder selected."
    exit 0
}

$InputFolder = Join-Path ([System.IO.Path]::GetTempPath()) ("SciMap-Agent-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $InputFolder -Force | Out-Null

try {
    foreach ($file in $open.FileNames) {
        $destination = Join-Path $InputFolder ([System.IO.Path]::GetFileName($file))
        if (Test-Path $destination) {
            $base = [System.IO.Path]::GetFileNameWithoutExtension($file)
            $ext = [System.IO.Path]::GetExtension($file)
            $destination = Join-Path $InputFolder ($base + "_" + [guid]::NewGuid().ToString("N").Substring(0, 6) + $ext)
        }
        Copy-Item -LiteralPath $file -Destination $destination
    }

    New-Item -ItemType Directory -Path $folder.SelectedPath -Force | Out-Null
    Push-Location $ProjectRoot
    try {
        Write-Host "Running SciMap-Agent on $($open.FileNames.Count) file(s)..."
        & $Python -m scimap_agent.cli analyze `
            --input $InputFolder `
            --output $folder.SelectedPath `
            --min-occurrences auto `
            --dpi 600
        if ($LASTEXITCODE -ne 0) {
            throw "Analysis failed. Check the console output above."
        }
    }
    finally {
        Pop-Location
    }

    $Figures = Join-Path $folder.SelectedPath "figures"
    $Report = Join-Path $folder.SelectedPath 'reports\analysis_report.md'
    if (-not (Test-Path $Figures)) {
        $Figures = $folder.SelectedPath
        $Report = Join-Path $folder.SelectedPath 'comparison\comparison_report_zh.md'
    }
    if (Test-Path $Figures) { Start-Process explorer.exe $Figures }
    [System.Windows.Forms.MessageBox]::Show(
        "Analysis completed.`n`nResults: $Figures`nReport: $Report",
        "SciMap-Agent", "OK", "Information"
    ) | Out-Null
}
finally {
    if (Test-Path $InputFolder) {
        Remove-Item -LiteralPath $InputFolder -Recurse -Force
    }
}
