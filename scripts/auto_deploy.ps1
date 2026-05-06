param(
    [string]$GitHubRepo = "",
    [ValidateSet("private", "public", "internal")]
    [string]$GitHubVisibility = "private",
    [string]$VercelProjectName = "agentmesh",
    [string]$VercelToken = $env:VERCEL_TOKEN,
    [switch]$SkipImmediateDeploy
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found on PATH."
    }
}

function Run-Git {
    param([string[]]$ArgsList)
    & git @ArgsList
    if ($LASTEXITCODE -ne 0) {
        throw "git $($ArgsList -join ' ') failed."
    }
}

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Require-Command git
Require-Command npm
Require-Command vercel

Write-Host "1/7 Installing frontend dependencies" -ForegroundColor Cyan
npm --prefix frontend ci

Write-Host "2/7 Building frontend" -ForegroundColor Cyan
npm --prefix frontend run build

Write-Host "3/7 Running backend tests when Python is available" -ForegroundColor Cyan
if (Test-Path ".\.venv\Scripts\python.exe") {
    .\.venv\Scripts\python.exe -m pytest
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py -m pytest
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python -m pytest
} else {
    Write-Warning "Python was not found. Skipping backend tests."
}

Write-Host "4/7 Preparing git repository" -ForegroundColor Cyan
if (-not (Test-Path ".git")) {
    Run-Git @("init")
}
Run-Git @("branch", "-M", "main")
Run-Git @("add", ".")

& git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    Run-Git @("commit", "-m", "Automated AgentMesh deployment setup")
} else {
    Write-Host "No new git changes to commit."
}

$HasOrigin = $false
& git remote get-url origin *> $null
if ($LASTEXITCODE -eq 0) {
    $HasOrigin = $true
}

if (-not $HasOrigin) {
    if ($GitHubRepo) {
        Run-Git @("remote", "add", "origin", $GitHubRepo)
    } else {
        Require-Command gh
        $visibilityFlag = "--$GitHubVisibility"
        gh repo create $VercelProjectName $visibilityFlag --source . --remote origin
        if ($LASTEXITCODE -ne 0) {
            throw "GitHub repository creation failed. Run 'gh auth login' or pass -GitHubRepo."
        }
    }
}

Write-Host "5/7 Pushing main branch to GitHub" -ForegroundColor Cyan
Run-Git @("push", "-u", "origin", "main")

Write-Host "6/7 Linking Vercel and installing GitHub secrets" -ForegroundColor Cyan
if ($VercelToken) {
    vercel link --yes --project $VercelProjectName --token=$VercelToken
    if ($LASTEXITCODE -ne 0) {
        throw "Vercel link failed."
    }

    $ProjectSettings = Get-Content ".vercel\project.json" -Raw | ConvertFrom-Json

    if (Get-Command gh -ErrorAction SilentlyContinue) {
        $VercelToken | gh secret set VERCEL_TOKEN
        $ProjectSettings.orgId | gh secret set VERCEL_ORG_ID
        $ProjectSettings.projectId | gh secret set VERCEL_PROJECT_ID
    } else {
        Write-Warning "GitHub CLI is not available, so workflow secrets were not installed."
    }

    if (-not $SkipImmediateDeploy) {
        Write-Host "7/7 Deploying production build to Vercel" -ForegroundColor Green
        vercel pull --yes --environment=production --token=$VercelToken
        vercel build --prod --token=$VercelToken
        vercel deploy --prebuilt --prod --token=$VercelToken
    } else {
        Write-Host "7/7 Immediate deploy skipped. GitHub Actions will deploy on push." -ForegroundColor Yellow
    }
} else {
    Write-Warning "VERCEL_TOKEN was not provided. GitHub push is complete, but Vercel linking/deploy needs 'vercel login' or a token."
    if (-not $SkipImmediateDeploy) {
        vercel deploy --prod --yes
    }
}

Write-Host "Automated deployment process finished." -ForegroundColor Green
