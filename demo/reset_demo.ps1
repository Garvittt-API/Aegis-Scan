$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$backendDb = Join-Path $root 'backend\aegisscan.db'
$reports = Join-Path $root 'backend\reports'
if (Test-Path $backendDb) { Remove-Item $backendDb -Force }
if (Test-Path $reports) { Remove-Item $reports -Recurse -Force }
Write-Host '[OK] Demo database and raw scan artifacts reset.' -ForegroundColor Green
Write-Host 'Start the backend once to recreate the local schema.'
