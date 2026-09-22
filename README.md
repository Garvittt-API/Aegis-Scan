# AegisScan — Automated Application Security Assessment & Verification Platform

**Built for Smart India Hackathon 2026**
Problem Statement: SIH26163 - Security Assessment of the World Monitor application

## Overview

AegisScan is a local-first, multi-engine security assessment platform that discovers an application's attack surface, executes multi-vector security testing (DAST, SAST, SCA, Custom Checks), normalizes and correlates findings, verifies them with evidence, evaluates risk, and provides remediation guidance.

### Main Pipeline Architecture

```
TARGET → DISCOVER → SCAN → NORMALIZE → CORRELATE → VERIFY → RISK → REMEDIATE → REPORT
```

---

## Key Features (Completed Through Phase 4)

- **Target Management (Phase 2)**: Comprehensive target registry supporting web applications, local microservices, repositories, and source code trees with strict authorization tracking.
- **Multi-Step Assessment Wizard (Phase 2)**: 5-step configuration wizard covering target selection, scope definition, scanner module toggles, and safe scan parameters.
- **World Monitor Preset (Phase 2)**: Instant SIH preset loader pre-configured for safe local assessment of the World Monitor application.
- **Attack Surface Discovery (Phase 3)**: Same-origin spidering engine discovering URLs, endpoints, APIs, forms, parameters, JavaScript assets, and technologies.
- **URL Normalization & Deduplication (Phase 3)**: Deterministic asset fingerprinting and multi-source provenance tracking (`discovered_by = ["crawler", "openapi"]`).
- **Scan Orchestrator & Planner (Phase 3)**: Structured scan job generator queuing scan jobs with state machine validation.
- **Real Scanner Adapters (Phase 4)**: Local OWASP ZAP, Nuclei, Semgrep, Dependency-Check, and native custom-check execution with availability detection, timeouts, raw artifact storage, and failure isolation (**zero fake scan results**).
- **Pipeline Visualizer**: Live visual status tracking across all 9 lifecycle phases.

---

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create & activate virtual environment (optional)
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend API & Documentation:
- Swagger Docs: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- ReDoc: [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

Frontend Dashboard: [http://localhost:5173](http://localhost:5173)

---

## API Summary

### Target Management
- `POST   /api/targets` — Register a target
- `GET    /api/targets` — List targets with filtering & search
- `GET    /api/targets/{id}` — Get target details & history
- `PUT    /api/targets/{id}` — Update target configuration
- `DELETE /api/targets/{id}` — Delete target

### Assessment Management & Validation
- `GET    /api/assessments/presets/world-monitor` — Fetch World Monitor preset
- `POST   /api/assessments/validate` — Validate assessment configuration
- `POST   /api/assessments` — Create assessment
- `GET    /api/assessments` — List assessments
- `GET    /api/assessments/{id}` — Get assessment details
- `POST   /api/assessments/{id}/validate` — Validate existing assessment
- `PATCH  /api/assessments/{id}` — Update assessment
- `DELETE /api/assessments/{id}` — Delete assessment
- `GET    /api/assessments/{id}/summary` — Assessment finding metrics

### Attack Surface & Discovery (Phase 3)
- `GET    /api/assessments/{id}/attack-surface` — List attack surface inventory with metrics
- `POST   /api/assessments/{id}/attack-surface` — Manually add an attack surface item
- `POST   /api/assessments/{id}/discovery` — Launch background discovery run
- `GET    /api/assessments/{id}/discovery` — List discovery runs
- `GET    /api/assessments/{id}/discovery/{run_id}` — Get discovery run status
- `POST   /api/assessments/{id}/discovery/{run_id}/cancel` — Cancel discovery run

### Scan Orchestrator & Scan Jobs (Phase 4)
- `POST   /api/assessments/{id}/scan-jobs/plan` — Generate scan plan & queue jobs
- `GET    /api/assessments/{id}/scan-jobs` — List queued scan jobs
- `GET    /api/assessments/{id}/scan-jobs/{job_id}` — Get scan job details
- `POST   /api/assessments/{id}/scan-jobs/{job_id}/cancel` — Cancel scan job
- `POST   /api/assessments/{id}/scan-jobs/{job_id}/execute` — Execute one real scanner job
- `POST   /api/assessments/{id}/scan-jobs/execute-all` — Execute all queued jobs with failure isolation
- `GET    /api/scanners/status` — Check installed scanner engines
- `GET    /api/assessments/{id}/scan-jobs/{job_id}/raw` — Inspect stored raw execution artifacts

### Scanner Setup and Raw Results

External tools are optional. Configure executable paths with `ZAP_PATH`, `NUCLEI_PATH`,
`SEMGREP_PATH`, and `DEPENDENCY_CHECK_PATH`, or place the tools on `PATH`. Missing tools
are reported as `unavailable` and do not stop other scanner jobs.

Each execution stores `metadata.json`, `stdout.log`, `stderr.log`, and `result.json` under
`reports/assessments/{assessment_id}/scans/{scan_job_id}/`. These are raw scanner outputs
reserved for the Phase 5 normalization pipeline. Only run assessments against explicitly
authorized local or controlled targets; aggressive testing and credential attacks are not enabled by default.

### Findings, Remediation, and Reports (Phases 5-8)

- `GET /api/findings` and `GET /api/findings/{id}` — Evidence-backed normalized findings.
- `POST /api/findings/{id}/reverify` — Safe, non-destructive verification where supported.
- `GET /api/findings/{id}/remediation` — Deterministic remediation guidance tied to the finding.
- `POST /api/reports` — Generate an HTML, JSON, or PDF report from persisted assessment data.
- `GET /api/reports/{id}/html` and `GET /api/reports/{id}/pdf` — Retrieve generated reports.
- `GET /api/reports/assessments/{id}/report` — Retrieve the latest report for an assessment.

Reports contain real finding, verification, risk, remediation, scanner-status, and evidence-reference data.
Raw logs are not dumped into reports, and presentation output redacts bearer tokens, cookies, API keys,
and passwords without modifying original evidence. PDF generation requires an installed WeasyPrint or
ReportLab renderer; otherwise the API records an honest failed report status.

### Analytics (Phase 9)

Analytics are calculated from stored assessments, findings, scan jobs, discovery records,
attack-surface items, and remediations. The API is under `/api/analytics`:

- `/overview` — current aggregate findings, verification, remediation, and execution metrics.
- `/assessments` and `/trends` — chronological history; trends require multiple assessments.
- `/severity`, `/categories`, `/verification`, `/remediation` — evidence-backed distributions.
- `/scanners`, `/attack-surface`, `/coverage` — execution and discovery coverage where known.
- `/recurrence` and `/comparison/{previous_id}/{current_id}` — fingerprint-based comparison.

Unavailable scanner or discovery data is reported as unavailable, not as zero coverage or a clean result.
The analytics layer does not create security scores, synthetic history, predictions, or subjective posture claims.

### CI/CD Integration (Phase 10)

Run a local or CI assessment against an explicitly authorized target:

```powershell
cd backend
python -m app ci --target http://127.0.0.1:8010 `
	--policy ../security-policy.example.yaml `
	--format json,sarif,html `
	--output ../artifacts
```

Exit codes are deterministic: `0` means the configured policy passed (WARN/UNKNOWN do not
claim a pass of security checks), `1` means policy failure, `2` means configuration error,
and `3` means runtime failure. The command reuses the existing assessment orchestrator,
normalization, analytics comparison, and report generation. It writes JSON and SARIF artifacts
and can copy HTML/PDF reports when requested. Scanner failure or unavailability is retained in
coverage and is never interpreted as zero vulnerabilities.

The policy template is [security-policy.example.yaml](security-policy.example.yaml). A GitHub
Actions template is [.github/workflows/aegisscan.yml](.github/workflows/aegisscan.yml); it requires
the repository/environment variable `AEGISSCAN_TARGET_URL` and an authorized test application.
No public target or secret is configured by default.

---

## Development Roadmap

- [x] **Phase 1**: Architecture Foundation, DB Models, Base UI
- [x] **Phase 2**: Target Management, Assessment Wizard, Scan Configuration & Validation
- [x] **Phase 3**: Attack Surface Discovery & Scan Orchestrator Foundation
- [x] **Phase 4**: Real Scanner Integrations (OWASP ZAP, Nuclei, Semgrep, Dependency-Check)
- [x] **Phase 5**: Finding Normalization & Correlation Engine
- [x] **Phase 6**: Active Verification & Explainable Risk Engine
- [x] **Phase 7**: Deterministic Remediation Guidance
- [x] **Phase 8**: Evidence-Backed Reporting (HTML, optional PDF)
- [ ] **Phase 10**: SIH Live Demonstration Mode
