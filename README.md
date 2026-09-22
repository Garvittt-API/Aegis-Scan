# 🛡️ AegisScan

<div align="center">

## Automated Application Security Assessment & Verification Platform

**Discover → Scan → Normalize → Correlate → Verify → Risk → Remediate → Report**

Built for **Smart India Hackathon 2026**

**Problem Statement:** SIH26163 — Security Assessment of the World Monitor application

**Team:** Cloud Alchemists

<br/>

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-Build-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Security](https://img.shields.io/badge/Application-Security-8B5CF6?style=for-the-badge)](#)

</div>

---

## 📌 Overview

**AegisScan** is a **local-first, multi-engine application security assessment platform** designed to bring different security testing workflows into a single structured pipeline.

Instead of manually operating multiple security tools and analyzing their outputs separately, AegisScan provides a centralized workflow for:

- 🎯 Target management
- 🗺️ Attack-surface discovery
- 🔍 Multi-engine security scanning
- 🧩 Finding normalization
- 🔗 Finding correlation
- 🛡️ Evidence-based verification
- 📊 Risk evaluation
- 🔧 Remediation guidance
- 📑 Security reporting
- 📈 Security analytics
- 🔄 CI/CD policy evaluation

The platform is designed around **traceability and evidence**.

> AegisScan does not treat scanner output as unquestionable truth. Security results are preserved as evidence, normalized into a common model, correlated, verified where possible, and then used for risk and remediation analysis.

---

# 🧠 Core Pipeline

```text
                         ┌──────────────┐
                         │    TARGET    │
                         └──────┬───────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │    DISCOVER     │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │      SCAN       │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │    EVIDENCE     │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   NORMALIZE     │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   CORRELATE     │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     VERIFY      │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │      RISK       │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   REMEDIATE     │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     REPORT      │
                       └─────────────────┘
````

---

# ✨ Why AegisScan?

Modern applications often require several different security tools.

One tool may analyze web traffic.

Another may inspect source code.

Another may analyze dependencies.

Another may perform template-based vulnerability detection.

The result is often:

```text
Tool A → Output A
Tool B → Output B
Tool C → Output C
Tool D → Output D
             ↓
       Manual Analysis
```

AegisScan brings those workflows together:

```text
Multiple Security Engines
          ↓
    AegisScan Pipeline
          ↓
   Unified Evidence
          ↓
 Normalized Findings
          ↓
 Verification + Risk
          ↓
 Remediation + Reports
```

---

# 🚀 Key Features

## 🎯 Target Management

AegisScan provides a target registry for authorized assessment targets.

Supported target concepts include:

* Web applications
* Local microservices
* Repositories
* Source-code trees
* Local/controlled environments

Targets maintain authorization information to help keep assessments within an explicitly permitted scope.

---

## 🧙 Assessment Wizard

A multi-step assessment wizard simplifies configuration.

The wizard covers:

1. Target selection
2. Scope definition
3. Scanner selection
4. Scan configuration
5. Validation

This provides a structured way to prepare an assessment before execution.

---

## 🌍 World Monitor Preset

AegisScan includes a dedicated **World Monitor assessment preset** for the SIH26163 problem statement.

The preset provides a predefined assessment configuration intended for safe, controlled testing.

---

# 🗺️ Attack Surface Discovery

Before security testing begins, AegisScan can discover the application's attack surface.

The discovery engine can identify:

* URLs
* Endpoints
* APIs
* Forms
* Parameters
* JavaScript assets
* Technologies

### Discovery Flow

```text
Target
  │
  ▼
Crawler
  │
  ├── URLs
  ├── Endpoints
  ├── APIs
  ├── Forms
  ├── Parameters
  └── JavaScript Assets
          │
          ▼
   Attack Surface
      Inventory
```

AegisScan also performs deterministic URL normalization and deduplication.

Multiple discovery sources can be preserved through provenance information such as:

```json
{
  "discovered_by": [
    "crawler",
    "openapi"
  ]
}
```

---

# ⚙️ Scan Orchestration

AegisScan provides a central scan planner and orchestrator.

```text
Assessment
    ↓
Discovery
    ↓
Scan Planning
    ↓
Job Creation
    ↓
Scanner Execution
    ↓
Raw Evidence
```

Each scanner runs as an independent job.

This provides **failure isolation**, meaning an unavailable or failed scanner does not automatically prevent other configured assessment jobs from running.

---

# 🔍 Security Engines

AegisScan integrates multiple security assessment engines.

| Tool                      | Purpose                              | Type   |
| ------------------------- | ------------------------------------ | ------ |
| 🕷️ OWASP ZAP             | Web application security testing     | DAST   |
| 🎯 Nuclei                 | Template-based security checks       | DAST   |
| 🔬 Semgrep                | Source-code security analysis        | SAST   |
| 📦 OWASP Dependency-Check | Dependency vulnerability analysis    | SCA    |
| 🧪 Custom Checks          | Application-specific security checks | Custom |

External scanners are optional.

Their availability is detected at runtime.

If a scanner is unavailable, AegisScan records it as **unavailable** instead of pretending that the scanner found nothing.

---

# 📦 Raw Evidence

Every scanner execution can preserve its raw execution artifacts.

Example:

```text
reports/
└── assessments/
    └── <assessment_id>/
        └── scans/
            └── <scan_job_id>/
                ├── metadata.json
                ├── stdout.log
                ├── stderr.log
                └── result.json
```

This creates a traceable relationship between:

```text
Finding
   ↓
Normalized Result
   ↓
Scanner
   ↓
Raw Evidence
   ↓
Assessment
   ↓
Target
```

Raw evidence remains separate from presentation-level reports.

---

# 🧩 Finding Normalization

Different scanners produce different output formats.

AegisScan converts those outputs into a unified finding representation.

```text
Scanner Output
      ↓
    Parser
      ↓
Normalized Finding
      ↓
Fingerprint
      ↓
Deduplication
      ↓
Correlation
      ↓
Verification
```

A finding can contain information such as:

* Finding ID
* Title
* Description
* Severity
* Confidence
* Category
* Scanner
* Source
* CWE
* CVSS
* Endpoint
* HTTP method
* Parameter
* Evidence
* Verification status
* Reproducibility
* Impact
* Remediation
* References
* Fingerprint
* Lifecycle status
* First/last seen timestamps

---

# 🔗 Correlation & Deduplication

Multiple scanners may detect the same underlying issue.

AegisScan uses deterministic fingerprints and correlation logic to reduce duplicate findings.

```text
ZAP ───────┐
           │
Nuclei ────┤
           ├──→ Correlation → Unified Finding
Semgrep ───┤
           │
Custom ────┘
```

This helps prevent the same security issue from appearing as multiple unrelated findings.

---

# 🛡️ Evidence-Based Verification

A scanner alert is not automatically treated as a verified vulnerability.

AegisScan separates scanner detection from verification.

```text
Scanner Alert
      ↓
Evidence
      ↓
Verification
      ↓
Confidence
```

Supported verification states include:

```text
UNVERIFIED
LIKELY
VERIFIED
FALSE_POSITIVE
NOT_REPRODUCIBLE
```

Where supported, AegisScan can perform safe, non-destructive reverification.

---

# 📊 Risk Intelligence

AegisScan keeps security concepts such as **severity**, **confidence**, and **priority** separate.

```text
Severity
   +
Confidence
   +
Available Evidence
   +
Exposure Information
   ↓
Risk Analysis
   ↓
Priority
```

The system aims to provide explainable risk information instead of hiding security decisions behind an unexplained score.

Existing CVSS information is preserved when reliable information is available.

---

# 🔧 Remediation Intelligence

Finding a vulnerability is only part of the security workflow.

AegisScan connects findings with deterministic remediation guidance.

Remediation information can include:

* Recommended action
* Technical steps
* Code guidance
* Configuration guidance
* Dependency guidance
* Verification steps
* Priority
* Estimated effort
* References

### Remediation Lifecycle

```text
NOT_STARTED
     ↓
IN_PROGRESS
     ↓
READY_FOR_VALIDATION
     ↓
VALIDATED
```

A finding is not considered fixed simply because a status button was clicked.

Validation is tied to reassessment evidence where supported.

---

# 📑 Security Reporting

AegisScan can generate reports from persisted assessment data.

Reports can contain:

* Assessment metadata
* Scope
* Executive summary
* Finding summaries
* Severity information
* Verification information
* Risk information
* Remediation information
* Scanner status
* Evidence references
* Methodology
* Limitations

### Supported Formats

```text
HTML
JSON
PDF*
```

> PDF generation requires an available WeasyPrint or ReportLab renderer.

If PDF generation is unavailable, AegisScan records the failure rather than pretending a PDF was generated.

---

# 📈 Security Analytics

AegisScan provides analytics based on actual stored assessment data.

Available analytics include:

### Overview

Aggregate information about:

* Findings
* Verification
* Remediation
* Scan execution

### Assessment History

Chronological assessment information and trends where sufficient historical data exists.

### Finding Analytics

* Severity
* Categories
* Verification
* Remediation

### Scanner Analytics

* Scanner execution
* Scanner availability
* Attack-surface information
* Coverage where measurable

### Finding Recurrence

Fingerprint-based comparison can identify:

```text
NEW
RECURRING
RESOLVED
REOPENED
```

Analytics do **not** generate synthetic history, predictions, or arbitrary security scores.

Unavailable data remains unavailable.

---

# 🔄 CI/CD Security Integration

AegisScan provides a CI-oriented CLI.

Example:

```powershell
cd backend

python -m app ci `
    --target http://127.0.0.1:8010 `
    --policy ../security-policy.example.yaml `
    --format json,sarif,html `
    --output ../artifacts
```

The CI layer can evaluate policies based on:

* Severity thresholds
* Verification requirements
* Required scanners
* Scanner failures
* Maximum findings
* New findings
* Reopened findings
* Baseline comparison

---

## 🚦 Deterministic Exit Codes

AegisScan distinguishes between different CI outcomes.

| Exit Code | Meaning                          |
| --------: | -------------------------------- |
|       `0` | Configured policy passed         |
|       `1` | Policy failed                    |
|       `2` | Configuration / invocation error |
|       `3` | Runtime / assessment failure     |

A policy result is not the same thing as a claim that the target is completely secure.

For example:

```text
Scanner unavailable
       ≠
Scanner returned zero findings
```

and:

```text
0 findings
       ≠
Guaranteed security
```

This distinction is preserved throughout the CI workflow.

---

# 📄 JSON & SARIF

CI results can be exported in machine-readable formats.

```text
artifacts/
└── security/
    ├── aegisscan-results.json
    └── aegisscan-results.sarif
```

### JSON

Useful for:

* CI automation
* Integrations
* Custom dashboards
* Programmatic processing

### SARIF

Useful for security tooling and CI systems that consume standardized static-analysis results.

---

# 🔐 Security & Responsible Use

AegisScan is designed for **authorized security assessment**.

Only assess:

* Applications you own
* Applications you have explicit permission to test
* Local laboratory environments
* Controlled demonstration targets

Do not use the platform for unauthorized testing of third-party systems.

### Important Principles

> **Evidence over assumptions.**

> **Scanner failure is not a clean result.**

> **Zero findings is not proof of security.**

> **Verification should be evidence-backed.**

> **Do not fabricate security results.**

---

# 🏗️ Architecture

```text
┌──────────────────────────────────────────────────────────┐
│                    AegisScan Dashboard                   │
│                    React + Vite + UI                     │
└───────────────────────────┬──────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│                     FastAPI Backend                      │
├──────────────────────────────────────────────────────────┤
│ Target Management                                        │
│ Assessment Management                                    │
│ Discovery                                                │
│ Scan Planning                                            │
│ Finding Management                                       │
│ Verification                                             │
│ Risk Intelligence                                       │
│ Remediation                                              │
│ Reporting                                                │
│ Analytics                                                │
│ CI/CD                                                    │
└───────────────────────────┬──────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│                  Assessment Orchestrator                  │
└───────────────────────────┬──────────────────────────────┘
                            │
        ┌───────────────────┼────────────────────┐
        │                   │                    │
        ▼                   ▼                    ▼
   OWASP ZAP             Nuclei              Semgrep
      DAST              Templates              SAST
        │                   │                    │
        └───────────────────┼────────────────────┘
                            │
                            ▼
                    Dependency-Check
                            │
                            ▼
                      Custom Checks
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│                     Evidence Layer                       │
├──────────────────────────────────────────────────────────┤
│ Raw Results → Normalize → Fingerprint → Correlate        │
└───────────────────────────┬──────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│                Security Intelligence                     │
├──────────────────────────────────────────────────────────┤
│ Verification → Confidence → Risk → Priority              │
└───────────────────────────┬──────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│                  Remediation & Reporting                 │
├──────────────────────────────────────────────────────────┤
│ Remediation → Reports → Analytics → CI/CD                │
└──────────────────────────────────────────────────────────┘
```

---

# 🧰 Technology Stack

## Frontend

* React
* Vite
* Tailwind CSS
* Recharts

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy

## Database

* SQLite

## Security Tooling

* OWASP ZAP
* Nuclei
* Semgrep
* OWASP Dependency-Check
* Custom Python security checks

## Reporting

* HTML
* JSON
* SARIF
* PDF where a supported renderer is installed

## Testing

* Pytest
* Frontend build validation
* Python compilation validation

---

# 📂 Project Structure

```text
Aegis-Scan/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── scanners/
│   │   ├── checks/
│   │   ├── reports/
│   │   ├── cli.py
│   │   └── ...
│   │
│   └── tests/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── ...
│
├── demo/
│   └── ...
│
├── artifacts/
│   └── ...
│
├── security-policy.example.yaml
├── README.md
└── ...
```

---

# ⚡ Quick Start

## Prerequisites

Install:

* Python 3.x
* Node.js
* npm

Optional security engines:

* OWASP ZAP
* Nuclei
* Semgrep
* OWASP Dependency-Check

External security tools are optional. AegisScan detects their availability at runtime.

---

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Aegis-Scan.git
cd Aegis-Scan
```

---

## 2. Backend Setup

```bash
cd backend

python -m venv venv
```

### Windows

```powershell
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 3. Backend Documentation

Once the backend is running:

**Swagger**

```text
http://127.0.0.1:8000/api/docs
```

**ReDoc**

```text
http://127.0.0.1:8000/api/redoc
```

---

## 4. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server will display the dashboard URL.

Typically:

```text
http://127.0.0.1:5173
```

---

# 🧪 Testing

### Backend Tests

```bash
cd backend
python -m pytest -q
```

### Python Compilation

```bash
python -m compileall -q app tests
```

### Frontend Build

```bash
cd ../frontend
npm run build
```

---

# 🧪 Local Assessment Demo

AegisScan includes a controlled local assessment workflow.

The recommended demonstration flow is:

```text
Start Local Target
       ↓
Open AegisScan
       ↓
Select Target
       ↓
Run Discovery
       ↓
Generate Scan Plan
       ↓
Execute Scan Jobs
       ↓
Inspect Raw Evidence
       ↓
Review Findings
       ↓
Verify
       ↓
Analyze Risk
       ↓
Review Remediation
       ↓
Generate Report
```

Example controlled target:

```text
http://127.0.0.1:8010
```

Only use targets that you are authorized to assess.

---

# 📡 API Overview

## Target Management

```text
POST   /api/targets
GET    /api/targets
GET    /api/targets/{id}
PUT    /api/targets/{id}
DELETE /api/targets/{id}
```

## Assessment Management

```text
GET    /api/assessments/presets/world-monitor
POST   /api/assessments/validate
POST   /api/assessments
GET    /api/assessments
GET    /api/assessments/{id}
POST   /api/assessments/{id}/validate
PATCH  /api/assessments/{id}
DELETE /api/assessments/{id}
GET    /api/assessments/{id}/summary
```

## Discovery

```text
GET    /api/assessments/{id}/attack-surface
POST   /api/assessments/{id}/attack-surface
POST   /api/assessments/{id}/discovery
GET    /api/assessments/{id}/discovery
GET    /api/assessments/{id}/discovery/{run_id}
POST   /api/assessments/{id}/discovery/{run_id}/cancel
```

## Scan Jobs

```text
POST   /api/assessments/{id}/scan-jobs/plan
GET    /api/assessments/{id}/scan-jobs
GET    /api/assessments/{id}/scan-jobs/{job_id}
POST   /api/assessments/{id}/scan-jobs/{job_id}/cancel
POST   /api/assessments/{id}/scan-jobs/{job_id}/execute
POST   /api/assessments/{id}/scan-jobs/execute-all
GET    /api/scanners/status
GET    /api/assessments/{id}/scan-jobs/{job_id}/raw
```

## Findings

```text
GET    /api/findings
GET    /api/findings/{id}
POST   /api/findings/{id}/reverify
```

## Remediation

```text
GET    /api/findings/{id}/remediation
```

## Reports

```text
POST   /api/reports
GET    /api/reports/{id}/html
GET    /api/reports/{id}/pdf
GET    /api/reports/assessments/{id}/report
```

## Analytics

```text
/api/analytics/overview
/api/analytics/assessments
/api/analytics/trends
/api/analytics/severity
/api/analytics/categories
/api/analytics/verification
/api/analytics/remediation
/api/analytics/scanners
/api/analytics/attack-surface
/api/analytics/coverage
/api/analytics/recurrence
/api/analytics/comparison/{previous_id}/{current_id}
```

---

# 🔄 Development Roadmap

```text
┌─────────────────────────────────────────┐
│ Phase 1 — Architecture Foundation      │ ✓
├─────────────────────────────────────────┤
│ Phase 2 — Targets & Assessment Wizard   │ ✓
├─────────────────────────────────────────┤
│ Phase 3 — Discovery & Scan Orchestrator │ ✓
├─────────────────────────────────────────┤
│ Phase 4 — Real Scanner Integration      │ ✓
├─────────────────────────────────────────┤
│ Phase 5 — Finding Normalization         │ ✓
├─────────────────────────────────────────┤
│ Phase 6 — Verification & Risk           │ ✓
├─────────────────────────────────────────┤
│ Phase 7 — Remediation Intelligence      │ ✓
├─────────────────────────────────────────┤
│ Phase 8 — Evidence-Based Reporting      │ ✓
├─────────────────────────────────────────┤
│ Phase 9 — Security Analytics             │ ✓
├─────────────────────────────────────────┤
│ Phase 10 — CI/CD Integration             │ ✓
├─────────────────────────────────────────┤
│ Phase 11 — Continuous Assessment         │ ○
└─────────────────────────────────────────┘
```

### Current Status

| Phase | Component                           | Status |
| ----- | ----------------------------------- | :----: |
| 1     | Architecture Foundation             |    ✅   |
| 2     | Target Management & Wizard          |    ✅   |
| 3     | Discovery & Orchestration           |    ✅   |
| 4     | Real Scanner Integrations           |    ✅   |
| 5     | Finding Normalization & Correlation |    ✅   |
| 6     | Verification & Risk Engine          |    ✅   |
| 7     | Remediation Intelligence            |    ✅   |
| 8     | Evidence-Based Reporting            |    ✅   |
| 9     | Security Analytics                  |    ✅   |
| 10    | CI/CD Integration                   |    ✅   |
| 11    | Continuous Assessment               |   🚧   |

---

# 🏆 Smart India Hackathon 2026

AegisScan was developed for:

> **SIH26163 — Security Assessment of the World Monitor application**

The project focuses on creating a structured security assessment workflow that can bring together multiple security testing engines and transform their outputs into evidence-backed security intelligence.

### Team

**Cloud Alchemists**

---

# 🤝 Contributing

Contributions and improvements are welcome.

Before submitting changes:

```bash
cd backend
python -m pytest -q
python -m compileall -q app tests

cd ../frontend
npm run build
```

Please keep contributions:

* Modular
* Tested
* Traceable
* Security-conscious
* Free from hard-coded secrets
* Within authorized testing boundaries

---

# 🔒 Security Policy

Please do not use AegisScan to perform unauthorized security assessments.

If you discover a security issue in AegisScan itself, report it responsibly rather than publicly exposing sensitive details.

Do not commit:

```text
.env
API keys
Passwords
Access tokens
Private certificates
Production credentials
Private assessment reports
Local databases
```

---

# 📜 License

> **License information should be added before public distribution.**

Choose the license that matches how you want others to use, modify, and distribute the project.

---

<div align="center">

# 🛡️ AegisScan

### Turn fragmented security testing into structured security intelligence.

**Discover → Scan → Normalize → Correlate → Verify → Risk → Remediate → Report**

<br/>

**Built by Cloud Alchemists · Smart India Hackathon 2026**

</div>
```

### One correction I intentionally made

Your current README says:

> `Key Features (Completed Through Phase 4)`

but then later documents **Phases 5–10 as completed**. It also ends with:

> `Phase 10: SIH Live Demonstration Mode`

even though your actual Phase 10 work is **CI/CD Security Integration**.

So the new README fixes that inconsistency and reflects the implementation you've actually described: **Phase 1–10 completed, Phase 11 next**.

Also, your original Markdown has malformed escaped links such as `[[http://localhost...` and broken PowerShell formatting. The replacement fixes those too.
