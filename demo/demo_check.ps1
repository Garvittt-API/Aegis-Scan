$ErrorActionPreference = 'SilentlyContinue'
function Check-Port($name, $port) {
  $ok = Test-NetConnection 127.0.0.1 -Port $port -InformationLevel Quiet
  if ($ok) { Write-Host "[OK] $name (127.0.0.1:$port)" -ForegroundColor Green }
  else { Write-Host "[!] $name is not running (127.0.0.1:$port)" -ForegroundColor Yellow }
}
Check-Port 'Backend' 8000
Check-Port 'Frontend' 5173
Check-Port 'Demo Lab' 8010
foreach ($tool in @('zap','nuclei','semgrep','dependency-check')) {
  if (Get-Command $tool) { Write-Host "[OK] $tool" -ForegroundColor Green }
  else { Write-Host "[!] $tool not installed; its job will be UNAVAILABLE" -ForegroundColor Yellow }
}
$venv = Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'
if (Test-Path $venv) { Write-Host '[OK] Project Python environment' -ForegroundColor Green }
else { Write-Host '[!] .venv missing; run the project setup first' -ForegroundColor Yellow }
