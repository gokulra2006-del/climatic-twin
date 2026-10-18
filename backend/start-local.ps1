# Starts the ClimateTwin API for local development.
# It keeps plotting-library cache files inside the project because some Windows
# profiles prevent Matplotlib from writing to its default cache directory.

$ErrorActionPreference = 'Stop'
$backendRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sitePackages = Join-Path $backendRoot 'venv\Lib\site-packages'
$codexRuntime = Join-Path $env:LOCALAPPDATA 'codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$venvRuntime = Join-Path $backendRoot 'venv\Scripts\python.exe'

if (Test-Path $codexRuntime) {
    $pythonRuntime = $codexRuntime
} elseif (Test-Path $venvRuntime) {
    $pythonRuntime = $venvRuntime
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonRuntime = (Get-Command python).Source
} else {
    throw 'Python was not found. Install Python 3.11+ or restore backend\\venv.'
}

$pythonPaths = @($backendRoot)
if (Test-Path $sitePackages) {
    $pythonPaths += $sitePackages
}
$env:PYTHONPATH = $pythonPaths -join [IO.Path]::PathSeparator

$env:MPLCONFIGDIR = Join-Path $backendRoot '.matplotlib'
New-Item -ItemType Directory -Force -Path $env:MPLCONFIGDIR | Out-Null

Set-Location $backendRoot
Write-Host 'Starting ClimateTwin API at http://127.0.0.1:8000 ...'
& $pythonRuntime -m uvicorn app.main:app --host 127.0.0.1 --port 8000
