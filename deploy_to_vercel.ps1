$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
npm --prefix frontend ci

Write-Host "Building frontend..." -ForegroundColor Cyan
npm --prefix frontend run build

Write-Host "Deploying AgentMesh to Vercel production..." -ForegroundColor Green
vercel deploy --prod --yes
