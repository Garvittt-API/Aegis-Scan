$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { $python = 'python' }
Write-Host '=================================' -ForegroundColor Cyan
Write-Host 'AEGISSCAN LOCAL DEMO' -ForegroundColor Cyan
Write-Host '=================================' -ForegroundColor Cyan
Start-Process -WorkingDirectory $root -FilePath $python -ArgumentList 'demo\security-lab\server.py'
Start-Process -WorkingDirectory (Join-Path $root 'backend') -FilePath $python -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000'
Start-Process -WorkingDirectory (Join-Path $root 'frontend') -FilePath 'npm.cmd' -ArgumentList 'run','dev','--','--host','127.0.0.1'
Write-Host 'Dashboard:  http://127.0.0.1:5173'
Write-Host 'Demo Lab:  http://127.0.0.1:8010'
Write-Host 'API Docs:  http://127.0.0.1:8000/api/docs'
Write-Host 'Mode:      LOCAL / AUTHORIZED'
