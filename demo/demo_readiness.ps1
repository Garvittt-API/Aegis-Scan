$ErrorActionPreference = 'SilentlyContinue'
$base = 'http://127.0.0.1:8000/api'
$ready = $true
function Check($label, $condition, $detail) {
  if ($condition) { Write-Host "[OK] $label" -ForegroundColor Green }
  else { Write-Host "[!] $label - $detail" -ForegroundColor Yellow; $script:ready = $false }
}
function Get-Json($url) { try { return Invoke-RestMethod $url } catch { return $null } }

$backend = Get-Json 'http://127.0.0.1:8000/health'
$frontend = Test-NetConnection 127.0.0.1 -Port 5173 -InformationLevel Quiet
$lab = Get-Json 'http://127.0.0.1:8010/api/health'
$assessments = Get-Json "$base/assessments?limit=100"
$demo = $assessments.items | Where-Object { $_.name -eq 'AegisScan Local Demo Assessment' } | Select-Object -First 1
$scanners = Get-Json "$base/scanners/status"
$jobs = if ($demo) { Get-Json "$base/assessments/$($demo.id)/scan-jobs" } else { $null }
$completed = if ($jobs) { @($jobs.items | Where-Object { $_.status -eq 'completed' -and $_.result_location }).Count -gt 0 } else { $false }
$surface = if ($demo) { Get-Json "$base/assessments/$($demo.id)/attack-surface" } else { $null }

Write-Host 'DEMO READINESS' -ForegroundColor Cyan
Check 'Backend' ($null -ne $backend -and $backend.status -eq 'healthy') 'start the backend'
Check 'Frontend' $frontend 'start the frontend'
Check 'Demo Lab' ($null -ne $lab -and $lab.scope -eq 'local-demo') 'start the lab on port 8010'
Check 'Database' ($null -ne $assessments) 'start the backend once to initialize SQLite'
Check 'Target' ($null -ne $demo) 'run demo/prepare_demo.ps1'
Check 'Assessment' ($null -ne $demo) 'run demo/prepare_demo.ps1'
Check 'Discovery' ($null -ne $surface -and $surface.total -gt 0) 'run discovery from Attack Surface'
Check 'Scanner execution' $completed 'generate a plan and run the custom check'
Check 'Evidence' $completed 'open the completed job raw artifacts'
Check 'Scanner availability API' ($null -ne $scanners -and @($scanners).Count -eq 5) 'check backend scanner status'
if (-not $ready) { exit 1 }