$ErrorActionPreference = 'Stop'
$base = 'http://127.0.0.1:8000/api'
$targetName = 'AegisScan Security Demo Lab'
$targetUrl = 'http://127.0.0.1:8010'
$targets = Invoke-RestMethod "$base/targets?limit=100"
$target = $targets.items | Where-Object { $_.name -eq $targetName } | Select-Object -First 1
if (-not $target) {
  $target = Invoke-RestMethod "$base/targets" -Method Post -ContentType 'application/json' -Body (@{
    name = $targetName
    target_type = 'web'
    base_url = $targetUrl
    environment = 'local'
    authorization_status = 'authorized'
    description = 'Local-only intentionally insecure AegisScan demonstration target.'
  } | ConvertTo-Json)
}
$assessment = Invoke-RestMethod "$base/assessments" -Method Post -ContentType 'application/json' -Body (@{
  name = 'AegisScan Local Demo Assessment'
  target_id = $target.id
  target_url = $targetUrl
  environment = 'local'
  authorization_confirmed = $true
  modules = @{ dast = $false; nuclei = $false; sast = $false; sca = $false; custom_checks = $true }
  scan_settings = @{ timeout = 15; crawl_depth = 1; rate_limit = 'low'; active_testing = $false; passive_checks = $true; follow_redirects = $true }
} | ConvertTo-Json -Depth 5)
Write-Host "[OK] Target: $($target.id) / $targetName" -ForegroundColor Green
Write-Host "[OK] Assessment: $($assessment.id) / $($assessment.name)" -ForegroundColor Green
Write-Host "Open /assessments/$($assessment.id)/scan-jobs, generate a plan, and run the queued custom check." 
