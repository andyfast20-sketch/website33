param(
  [Parameter(Mandatory=$false)]
  [string]$Tag = "answerly-working-pre-postgres",

  [Parameter(Mandatory=$false)]
  [switch]$IncludeUntracked
)

$ErrorActionPreference = 'Stop'

function Assert-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Required command not found: $name"
  }
}

Assert-Command git

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $repoRoot
Set-Location $repoRoot

Write-Host "Repo: $repoRoot"

# Stash any local changes to avoid losing work
try {
  $status = git status --porcelain
  if ($status) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    if ($IncludeUntracked) {
      git stash push -u -m "auto-stash-before-rollback-$stamp" | Out-Null
    } else {
      git stash push -m "auto-stash-before-rollback-$stamp" | Out-Null
    }
    Write-Host "Stashed local changes." 
  }
} catch {
  Write-Host "Warning: could not stash changes: $($_.Exception.Message)"
}

Write-Host "Fetching latest tags..."
try {
  git fetch --all --tags | Out-Null
} catch {
  Write-Host "Warning: fetch failed (offline?): $($_.Exception.Message)"
}

Write-Host "Checking out tag: $Tag"
# Ensure the tag exists locally
$tagList = git tag --list $Tag
if (-not $tagList) {
  throw "Tag '$Tag' not found. Run: git tag --list"
}

git checkout -f $Tag

Write-Host "Restarting server..."
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  throw "Python venv not found at $python. Create it, or update this script to point to your python.exe."
}

& $python start_server_clean.py
