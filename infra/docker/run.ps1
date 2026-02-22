<# PowerShell wrapper for run.sh
   Usage: .\run.ps1 up
   Tries to run run.sh inside WSL if available, otherwise prints guidance.
#>
param(
  [Parameter(ValueFromRemainingArguments=$true)]
  $Args
)

function Run-InWSL {
  if (Get-Command wsl -ErrorAction SilentlyContinue) {
    $joined = $Args -join ' '
    wsl bash -lc "./infra/docker/run.sh $joined"
    return $true
  }
  return $false
}

if (-not (Test-Path ./infra/docker/run.sh)) {
  Write-Error "infra/docker/run.sh not found. Run from repo root."
  exit 1
}

if (Run-InWSL) {
  exit 0
}

Write-Host "WSL not available. Please run the following in Git Bash or WSL:" -ForegroundColor Yellow
Write-Host "  cd infra/docker" -ForegroundColor Cyan
Write-Host "  bash run.sh $($Args -join ' ')" -ForegroundColor Cyan
