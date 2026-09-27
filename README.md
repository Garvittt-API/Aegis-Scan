# 🛡️ AegisScan

<div align="center">

### Automated Application Security Assessment & Verification Platform

**Discover • Scan • Evidence • Normalize • Correlate • Verify • Risk • Remediate • Report**

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Production%20Hardened-009688?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18%20Vite-61DAFB?style=flat-square&logo=react)
![Security](https://img.shields.io/badge/Security-SSRF%20Protected-green?style=flat-square)
![Tests](https://img.shields.io/badge/Pytest-67%20Passed-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-Apache%202.0-orange?style=flat-square)

</div>

---

## 🚀 Overview

**AegisScan** is a multi-engine application security assessment and verification platform that consolidates DAST, SAST, SCA, attack-surface discovery, and custom security heuristics into one unified, evidence-driven workflow.

Instead of drowning in fragmented, unverified scanner outputs, AegisScan captures raw tool evidence, normalizes findings into a unified model, correlates duplicates across engines, performs active proof verification, scores contextual business risk, and delivers developer-ready remediation guidance.

```text
TARGET ➔ DISCOVER ➔ SCAN ➔ EVIDENCE ➔ NORMALIZE ➔ CORRELATE ➔ VERIFY ➔ RISK ➔ REMEDIATE ➔ REPORT
```

---

## ✨ Core Capabilities

- 🎯 **Target & Scope Management**: Strict authorization boundary tracking and SSRF prevention.
- 🗺️ **Attack Surface Discovery**: Safe spidering, endpoint cataloging, form parsing, and technology detection.
- 🔍 **Multi-Engine Orchestration**: Coordinated scanning with OWASP ZAP (DAST), Nuclei (Templates), Semgrep (SAST), Dependency-Check (SCA), and Custom heuristics.
- 🧩 **Zero-Fabrication Normalization**: Unified data model directly backed by raw stdout/stderr/JSON evidence. No simulated or artificial vulnerabilities.
- 🛡️ **Evidence-Based Verification**: Distinguishes reproducible exploits (`VERIFIED`) from theoretical alerts (`UNVERIFIED` / `FALSE_POSITIVE`).
- 📊 **Risk Scoring**: Real-world contextual scoring incorporating exploitability, asset exposure, and environmental impact.
- 🔧 **Remediation Engine**: Step-by-step code guidance, configuration fixes, and verification procedures.
- 📑 **Comprehensive Reporting**: Production-ready HTML, SARIF 2.1.0, and JSON executive reports.
- 🔄 **Deterministic CI/CD Integration**: CLI tool with strict exit codes and GitHub Code Scanning SARIF exports.
- 🔒 **Production Hardened**: JWT Authentication, IP Rate Limiting, Security Headers (CSP, HSTS, X-Frame-Options), and Non-Root Dockerization.

---

## 🔍 Integrated Security Engines

| Engine | Type | Detection Purpose |
| :--- | :--- | :--- |
| **OWASP ZAP** | DAST | Dynamic web vulnerability scanning and crawling |
| **Nuclei** | DAST / Templates | Fast, template-based CVE and misconfiguration detection |
| **Semgrep** | SAST | Static code analysis and security rule violations |
| **OWASP Dependency-Check** | SCA | Vulnerable open-source components and CVE mapping |
| **Custom Heuristics** | Hybrid | Security header auditing, cookie attributes, CORS policies |

---

## 🧠 System Architecture

```text
                                  INTERNET / CLIENTS
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │  HTTPS / TLS │
                                   │ (Nginx / ALB)│
                                   └──────┬───────┘
                                          │
                                          ▼
                        ┌───────────────────────────────────┐
                        │   Frontend (React 18 / Vite / CSS)│
                        └─────────────────┬─────────────────┘
                                          │
                                          ▼
                        ┌───────────────────────────────────┐
                        │   FastAPI Backend API & Gateway   │
                        │   - JWT Auth & Rate Limiting      │
                        │   - Security Headers & Middleware │
                        │   - Target & SSRF Validation      │
                        └─────────────────┬─────────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
          ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
          │  PostgreSQL  │        │ Concurrency  │        │ Raw Evidence │
          │   Database   │        │  Semaphore   │        │ Storage Dir  │
          └──────────────┘        └──────┬───────┘        └──────────────┘
                                         │
                                         ▼
                             ┌───────────────────────┐
                             │   Scan Orchestrator   │
                             └───────────┬───────────┘
                                         │
          ┌──────────────────────────────┼──────────────────────────────┐
          ▼                              ▼                              ▼
    ┌───────────┐                  ┌───────────┐                  ┌───────────┐
    │ OWASP ZAP │                  │  Nuclei   │                  │  Semgrep  │
    │  (DAST)   │                  │ (Templates│                  │  (SAST)   │
    └─────┬─────┘                  └─────┬─────┘                  └─────┬─────┘
          │                              │                              │
          └──────────────────────────────┼──────────────────────────────┘
                                         ▼
                             ┌───────────────────────┐
                             │ Raw Evidence Storage  │
                             └───────────┬───────────┘
                                         ▼
                             ┌───────────────────────┐
                             │ Normalized Findings   │
                             └───────────┬───────────┘
                                         ▼
                             ┌───────────────────────┐
                             │ Risk & Remediation    │
                             └───────────┬───────────┘
                                         ▼
                             ┌───────────────────────┐
                             │ Reports (HTML/SARIF)  │
                             └───────────────────────┘
```

---

## 🛠️ Technology Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons, Recharts, Axios.
- **Backend API**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn, Jose JWT.
- **Database**: PostgreSQL 16 (Production) / SQLite (Local Development).
- **Security & Networking**: Nginx TLS Reverse Proxy, HTTP Security Headers, IP Token Bucket Rate Limiting.
- **Testing & CI**: Pytest, Pytest-Asyncio, Playwright, GitHub Actions.

---

## ⚡ Quick Start

### 1. Docker Compose (Production Setup)
```bash
# Clone the repository
git clone https://github.com/Garvittt-API/Aegis-Scan.git
cd Aegis-Scan

# Copy environment template
cp .env.example .env

# Start multi-container stack
docker-compose up -d --build
```
Access the application at `http://localhost:8000` (API Docs: `http://localhost:8000/api/docs`).

---

### 2. Local Development Setup

#### Backend:
```bash
# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Start backend server
cd backend
python -m app.main
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🔄 CI/CD Security Policy Scanning

AegisScan can be integrated directly into your build pipeline:

```bash
python -m app ci \
  --target ./src \
  --policy security-policy.example.yaml \
  --format json,sarif,html \
  --output artifacts
```

### Deterministic Exit Codes:
- `0`: Policy Passed (or warnings only).
- `1`: Policy Failed (thresholds breached).
- `2`: Configuration Error (missing target or malformed policy).
- `3`: Runtime / System Failure.

---

## 🧪 Testing

Run backend tests:
```bash
pytest backend/tests -v
```

Build and validate frontend:
```bash
npm --prefix frontend run build
```

---

## 📖 Documentation Index

| Guide | Description |
| :--- | :--- |
| 📐 [Architecture Guide](docs/architecture.md) | High-level system design, concurrency model, and data flow |
| 🚀 [Deployment Guide](docs/deployment.md) | Docker, PostgreSQL, Nginx reverse proxy, and TLS setup |
| 💻 [Development Guide](docs/development.md) | Local environment setup, test runner, and code conventions |
| 🔐 [Security & Threat Model](docs/security.md) | SSRF prevention, input validation, and responsible disclosure |
| 📡 [REST API Reference](docs/api.md) | Authentication, Target, Assessment, and Report endpoint specs |
| 🤖 [CI/CD Integration](docs/ci-cd.md) | CLI security gatekeeper, SARIF generation, and exit codes |
| 🩺 [Troubleshooting Guide](docs/troubleshooting.md) | Resolving common operational and configuration errors |

---

## 🔐 Responsible Use & Security Policy

AegisScan is designed exclusively for **authorized security assessments** against applications and infrastructure you own or have explicit written permission to test. Public scanning of unauthorized 3rd-party domains is strictly prohibited and guarded against by internal validation controls.

---

## 🏆 Smart India Hackathon 2026

Developed for **SIH26163 — Security Assessment Platform** by **Team Cloud Alchemists**.
