# AegisScan SIH Demo Package

## Start

Run `start_demo.bat`, then open `http://127.0.0.1:5173`. Use `demo/demo_check.ps1` to inspect service and scanner availability.

## Reset

Run `powershell -ExecutionPolicy Bypass -File demo/reset_demo.ps1`, then restart the services.

## Honest demo scope

Current working flow: authorized target setup, local discovery, scanner planning, real local scanner execution, availability states, raw logs, and raw result storage. Finding normalization, correlation, verification, risk scoring, and report generation are clearly marked as planned because they are not implemented in the current codebase.

Screenshots belong in `demo/screenshots/`; diagrams and speaking notes are in this directory.

Capture the seven real screens after the services are running:

```powershell
node demo/capture_screenshots.mjs
```

Check readiness with:

```powershell
powershell -ExecutionPolicy Bypass -File demo/demo_readiness.ps1
```
