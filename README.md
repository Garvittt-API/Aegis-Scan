# 🛡️ AegisScan

<div align="center">

### Automated Application Security Assessment & Verification Platform

**Discover • Scan • Verify • Prioritize • Remediate • Report**

Built for **Smart India Hackathon 2026**  
**SIH26163 — Security Assessment of the World Monitor application**

**Cloud Alchemists**
<<<<<<< HEAD

=======
  
>>>>>>> 64c7669880efde7309617ff5ad69ce3be2a63b62
![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=flat-square&logo=react)
![Security](https://img.shields.io/badge/Application-Security-purple?style=flat-square)

</div>

---

## 🚀 What is AegisScan?

**AegisScan** is a local-first application security assessment platform that brings multiple security testing tools into one structured workflow.

Instead of manually analyzing separate scanner outputs, AegisScan collects, normalizes, correlates and verifies security results before providing risk and remediation information.

```text
Target
  ↓
Discovery
  ↓
Security Scanning
  ↓
Evidence
  ↓
Normalize & Correlate
  ↓
Verify
  ↓
Risk
  ↓
Remediation
  ↓
Report
````

---

## ✨ Key Features

* 🎯 **Target Management** — Manage authorized assessment targets and scope.
* 🗺️ **Attack Surface Discovery** — Discover URLs, endpoints, APIs, forms and parameters.
* 🔍 **Multi-Engine Scanning** — Integrate DAST, SAST, SCA and custom security checks.
* 🧩 **Finding Normalization** — Convert different scanner outputs into one finding model.
* 🔗 **Correlation & Deduplication** — Reduce duplicate findings across security engines.
* 🛡️ **Evidence-Based Verification** — Separate scanner alerts from verified findings.
* 📊 **Risk Intelligence** — Analyze severity, confidence and available evidence.
* 🔧 **Remediation Guidance** — Provide actionable security fixes.
* 📑 **Security Reports** — Generate HTML, JSON, SARIF and optional PDF reports.
* 📈 **Security Analytics** — Track findings, verification, remediation and assessment history.
* 🔄 **CI/CD Integration** — Run policy-based security checks from the CLI.

---

## 🔍 Integrated Security Engines

| Tool                      | Purpose                                |
| ------------------------- | -------------------------------------- |
| 🕷️ OWASP ZAP             | Dynamic Application Security Testing   |
| 🎯 Nuclei                 | Template-based vulnerability detection |
| 🔬 Semgrep                | Static Application Security Testing    |
| 📦 OWASP Dependency-Check | Software Composition Analysis          |
| 🧪 Custom Checks          | Application-specific security checks   |

Scanner failures and unavailable tools are explicitly reported instead of being treated as clean results.

---

## 🧠 Architecture

```text
                    ┌─────────────────┐
                    │     Target      │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │   Discovery     │
                    └────────┬────────┘
                             ↓
              ┌────────────────────────────┐
              │      Security Engines      │
              │ ZAP • Nuclei • Semgrep     │
              │ Dependency-Check • Custom  │
              └─────────────┬──────────────┘
                            ↓
                    ┌─────────────────┐
                    │ Raw Evidence    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Normalize       │
                    │ Correlate       │
                    │ Verify          │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Risk &          │
                    │ Remediation     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Reports / CI    │
                    └─────────────────┘
```

---

## 🛠️ Tech Stack

**Frontend**

* React
* Vite
* Tailwind CSS
* Recharts

**Backend**

* Python
* FastAPI
* Pydantic
* SQLAlchemy

**Security**

* OWASP ZAP
* Nuclei
* Semgrep
* OWASP Dependency-Check
* Custom Python checks

**Database**

* SQLite

---

## ⚡ Quick Start

### Backend

```bash
cd backend

python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Dashboard:

```text
http://127.0.0.1:5173
```

API documentation:

```text
http://127.0.0.1:8000/api/docs
```

---

## 🔄 CI/CD

AegisScan can be executed from CI pipelines using its CLI:

```powershell
python -m app ci `
  --target http://127.0.0.1:8010 `
  --policy ../security-policy.example.yaml `
  --format json,sarif `
  --output ../artifacts
```

### Exit Codes

| Code | Meaning                      |
| ---: | ---------------------------- |
|  `0` | Policy passed                |
|  `1` | Policy failed                |
|  `2` | Configuration error          |
|  `3` | Runtime / assessment failure |

---

## 🧪 Testing

```bash
cd backend
python -m pytest -q
```

Frontend:

```bash
cd frontend
npm run build
```

---

## 🔐 Responsible Use

AegisScan is intended for **authorized security testing only**.

Use it against:

* Applications you own
* Authorized testing environments
* Local security labs
* Explicitly permitted targets

**Scanner failure ≠ clean result.**
**Zero findings ≠ guaranteed security.**

---

## 🗺️ Roadmap

* [x] Target Management
* [x] Attack Surface Discovery
* [x] Scanner Orchestration
* [x] Finding Normalization
* [x] Verification & Risk
* [x] Remediation
* [x] Reporting
* [x] Analytics
* [x] CI/CD Integration
* [ ] Continuous Assessment

---

## 🏆 Smart India Hackathon 2026

Developed for:

**SIH26163 — Security Assessment of the World Monitor application**

### Team Cloud Alchemists

> Turning fragmented security testing into one structured security assessment workflow.

---

<div align="center">

### 🛡️ AegisScan

**Discover • Verify • Secure**

Made with ❤️ by **Cloud Alchemists**

</div>
```

### This is the version I'd actually use.

The **detailed API list, phase-by-phase implementation details, raw evidence structure, full finding schema, etc.** should go into separate documentation:

```text
docs/
├── architecture.md
├── api.md
├── development.md
├── security.md
└── ci-cd.md
```

That gives you a clean GitHub landing page while still keeping the technical depth available for judges/developers who want it.

**README = sell/explain the project.**
**`docs/` = explain everything about the project.**
