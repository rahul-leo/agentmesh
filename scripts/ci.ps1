$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Write-Host "Running backend tests..." -ForegroundColor Cyan
if (Test-Path ".\.venv\Scripts\python.exe") {
    .\.venv\Scripts\python.exe -m pytest
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py -m pytest
} else {
    python -m pytest
}

Write-Host "Building frontend..." -ForegroundColor Cyan
npm --prefix frontend install
npm --prefix frontend run build

Write-Host "CI checks passed." -ForegroundColor Green
