param(
  [Parameter(Mandatory=$false)]
  [string]$OutDir = "_snapshots"
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $repoRoot
Set-Location $repoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$destDir = Join-Path $repoRoot $OutDir
New-Item -ItemType Directory -Force -Path $destDir | Out-Null

$zipPath = Join-Path $destDir "working_snapshot_$stamp.zip"

# Exclude large/secret-ish local artifacts
$exclude = @(
  '.git', '.venv', '__pycache__', 'logs',
  'call_logs.db', 'agents.db', 'users.db', '*.db',
  '*.log', '*.err', '*debug_audio_*.wav',
  'cloudflared_config.yml', 'google-credentials.json'
)

# Build file list (simple approach: copy everything then compress)
$tmp = Join-Path $destDir "_tmp_snapshot_$stamp"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

Write-Host "Creating snapshot in: $zipPath"

# Robocopy is fast and supports excludes
$robocopyExcludeDirs = @('.git', '.venv', '__pycache__', 'logs')
$robocopyExcludeFiles = @('*.db','*.log','*.err','cloudflared_config.yml','google-credentials.json','debug_audio_*.wav')

$null = robocopy $repoRoot $tmp /E /XD $robocopyExcludeDirs /XF $robocopyExcludeFiles

Compress-Archive -Path (Join-Path $tmp '*') -DestinationPath $zipPath -Force
Remove-Item -Recurse -Force $tmp

Write-Host "Snapshot created: $zipPath"
