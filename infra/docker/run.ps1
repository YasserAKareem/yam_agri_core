<# PowerShell wrapper for run.sh
   Usage: .\run.ps1 up
   Tries to run run.sh inside WSL if available, otherwise prints guidance.
#>
param(
  [Parameter(ValueFromRemainingArguments=$true)]
  $Args
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Run-InWSL {
  if (Get-Command wsl -ErrorAction SilentlyContinue) {
    $joined = ($Args | ForEach-Object {
      # Wrap args containing spaces/quotes for bash
      if ($_ -match '[\\s"'']') { "'" + ($_ -replace "'", "'\\''") + "'" } else { $_ }
    }) -join ' '
    $wslDir = (wsl wslpath -a "$ScriptDir").Trim()
    wsl bash -lc "cd '$wslDir' && bash ./run.sh $joined"
    return $true
  }
  return $false
}

if (-not (Test-Path (Join-Path $ScriptDir 'run.sh'))) {
  Write-Error "run.sh not found next to run.ps1. Expected: $ScriptDir\\run.sh"
  exit 1
}

if (Run-InWSL) {
  exit 0
}

Write-Host "WSL not available. Please run the following in Git Bash or WSL:" -ForegroundColor Yellow
Write-Host "  cd infra/docker" -ForegroundColor Cyan
Write-Host "  bash run.sh $($Args -join ' ')" -ForegroundColor Cyan
