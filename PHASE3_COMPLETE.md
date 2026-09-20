# Phase 3 Completion Status: Attack Surface Discovery + Scan Orchestrator Foundation

## ✅ COMPLETED — Phase 3: Attack Surface Discovery & Scan Orchestrator

### 1. Attack Surface Inventory & Provenance Tracking
- **Database Model**: [`AttackSurfaceItem`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/backend/app/models/attack_surface.py) supporting:
  - Asset Types: `url`, `api`, `endpoint`, `parameter`, `javascript`, `asset`, `service`, `technology`, `form`
  - Provenance Tracking: `discovered_by` array storing all discovery vectors (e.g. `["crawler_html_link", "form_parameter", "http_headers"]`)
  - Deterministic Stable Fingerprinting: SHA256 signature calculated over normalized URL, HTTP method, path, and parameter keys
  - Multi-level Risk Relevance: `high`, `medium`, `low`
  - Status lifecycle: `active`, `inactive`, `archived`
- **Deduplication Engine**: [`backend/app/discovery/normalizer.py`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/backend/app/discovery/normalizer.py) ensures duplicate endpoint occurrences are merged into one consolidated asset record with cumulative discovery provenance.

---

### 2. Discovery Runs & Safe Discovery Engine
- **Database Model**: [`DiscoveryRun`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/backend/app/models/discovery_run.py) tracking status (`pending`, `running`, `completed`, `failed`, `cancelled`), progress percentage, discovered counts, and execution logs.
- **Engine Abstraction**: [`DiscoveryEngine`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/backend/app/discovery/engine.py) with [`SafeBasicDiscoveryEngine`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/backend/app/discovery/engine.py):
  - Strict same-origin policy enforcement
  - Non-destructive spidering (GET/HEAD only; no active form POSTs)
  - Configurable crawl depth, page bounds, request rate limiting, and timeouts
  - Real-time progress updates and operator cancellation support

---

### 3. Scan Orchestrator & Scan Planning Foundation
- **Database Model**: [`ScanJob`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/backend/app/models/scan_job.py):
  - Supported Engines: `zap` (DAST), `nuclei` (Templates), `semgrep` (SAST), `sca` (Dependency Check), `custom` (Heuristics)
  - Priority levels: `low`, `normal`, `high`
  - State Machine Lifecycle:
    $$\text{PENDING} \longrightarrow \text{QUEUED} \longrightarrow \text{RUNNING} \longrightarrow \text{COMPLETED} \ / \ \text{FAILED}$$
    $$\text{PENDING / QUEUED / RUNNING} \longrightarrow \text{CANCELLED}$$
  - Terminal state validation: Invalid transitions (e.g. `COMPLETED` $\rightarrow$ `RUNNING`) are strictly rejected.
- **Scan Planner**: [`ScanPlanner`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/backend/app/services/scan_orchestrator.py) automatically generates targeted scan jobs based on assessment modules and attack surface inventory.
- **Modular Scanner Adapters**: [`backend/app/scanners/adapters.py`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/backend/app/scanners/adapters.py) with clean stubs reporting `NOT_IMPLEMENTED` (**ensuring zero fake scan results** until Phase 4 real scanner execution).

---

### 4. API Endpoints Reference

#### Attack Surface & Discovery API
- `GET    /api/assessments/{id}/attack-surface`: List inventory with filtering (`type`, `method`, `source`, `status`), search, pagination, and summary breakdown metrics
- `POST   /api/assessments/{id}/attack-surface`: Manually add an attack surface item
- `POST   /api/assessments/{id}/discovery`: Launch safe background discovery run
- `GET    /api/assessments/{id}/discovery`: List discovery runs for an assessment
- `GET    /api/assessments/{id}/discovery/{run_id}`: Poll run progress and metrics
- `POST   /api/assessments/{id}/discovery/{run_id}/cancel`: Cancel an ongoing discovery run

#### Scan Orchestrator & Scan Jobs API
- `POST   /api/assessments/{id}/scan-jobs/plan`: Generate scan plan and queue scan jobs
- `GET    /api/assessments/{id}/scan-jobs`: List scan jobs for assessment
- `GET    /api/assessments/{id}/scan-jobs/{job_id}`: Get scan job detail
- `POST   /api/assessments/{id}/scan-jobs/{job_id}/cancel`: Cancel a scan job
- `POST   /api/assessments/{id}/scan-jobs/{job_id}/execute`: Execute scan job adapter stub

---

### 5. Frontend Enhancements
- **Attack Surface Explorer** ([`frontend/src/pages/AttackSurface.jsx`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/frontend/src/pages/AttackSurface.jsx)):
  - Real-time discovery control panel with depth/page options and live progress bar
  - Multi-dimension summary metrics (Total, URLs, APIs, Endpoints, Parameters, Forms, JavaScript, Technologies)
  - Filterable inventory table with discovery provenance tags
  - Manual asset addition modal
- **Scan Jobs View** ([`frontend/src/pages/ScanJobs.jsx`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/frontend/src/pages/ScanJobs.jsx)):
  - Displays queued scanner jobs with priority and status badges
  - "Generate Scan Plan" action button
  - State check and cancellation actions
- **Assessment Detail & Pipeline Visualizer** ([`frontend/src/pages/AssessmentDetail.jsx`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/frontend/src/pages/AssessmentDetail.jsx)):
  - Updated 9-stage visual pipeline highlighting `Target`, `Discovery`, `Attack Surface`, `Scan Planning`, and `Scan Jobs` as active stages.
- **Sidebar & App Routing** ([`MainLayout.jsx`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/frontend/src/layouts/MainLayout.jsx), [`App.jsx`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/frontend/src/App.jsx)):
  - Direct routes `/scan-jobs` and `/assessments/:id/scan-jobs`.

---

## 🧪 Testing

Phase 3 tests: [`backend/tests/test_phase3_discovery_orchestrator.py`](file:///c:/Users/Exfil/Downloads/Aegis-Scan/backend/tests/test_phase3_discovery_orchestrator.py)
- URL Normalization (port stripping, redundant slashes, query param sorting)
- Fingerprint generation and deduplication merging
- Discovery run lifecycle & cancellation
- Attack surface inventory retrieval and summary statistics
- Scan planner plan generation
- Scan job state machine transition rules
- Scanner adapter `NOT_IMPLEMENTED` reporting check
