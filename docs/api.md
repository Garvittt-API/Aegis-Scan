# AegisScan — REST API Reference

The AegisScan REST API provides full programmatic access to targets, discovery, scan planning, findings, remediation, and reporting.

Interactive Swagger documentation is available at `/api/docs` and Redoc at `/api/redoc`.

---

## 1. Authentication Endpoints

### `POST /api/auth/register`
Register a new operator account.
```json
{
  "email": "analyst@example.com",
  "username": "analyst",
  "password": "StrongPassword123!",
  "full_name": "Security Analyst"
}
```

### `POST /api/auth/login`
Authenticate and obtain JWT Bearer access token.
```json
{
  "username_or_email": "analyst@example.com",
  "password": "StrongPassword123!"
}
```
Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": { ... }
}
```

### `GET /api/auth/me`
Retrieve profile of currently authenticated user. Requires `Authorization: Bearer <token>`.

---

## 2. Target Management Endpoints

### `GET /api/targets`
List registered targets with filtering and pagination (`?limit=50&offset=0&search=...`).

### `POST /api/targets`
Create and declare an authorized assessment target.
```json
{
  "name": "World Monitor Web Application",
  "target_type": "web",
  "base_url": "https://staging.example.com",
  "environment": "staging",
  "authorization_status": "authorized"
}
```

---

## 3. Assessments & Discovery Endpoints

### `POST /api/assessments`
Create a security assessment linked to a target.
```json
{
  "name": "Sprint 42 Security Audit",
  "target_id": 1,
  "authorization_confirmed": true,
  "modules": {
    "dast": true,
    "nuclei": true,
    "sast": true,
    "sca": true,
    "custom_checks": true
  }
}
```

### `POST /api/assessments/{id}/discovery`
Initiate non-destructive attack surface spidering.

### `POST /api/assessments/{id}/scan-jobs/plan`
Generate structured scan jobs for all enabled modules.

### `POST /api/assessments/{id}/scan-jobs/execute-all`
Execute all planned scan jobs asynchronously with error isolation.

---

## 4. Findings & Reporting Endpoints

### `GET /api/findings?assessment_id={id}`
Query normalized findings by severity, status, category, or verification state.

### `POST /api/reports`
Generate an evidence-backed report.
```json
{
  "assessment_id": 1,
  "format": "html"
}
```
Supported formats: `html`, `sarif`, `json`, `pdf`.

### `GET /api/reports/{id}/html`
Download or view the generated HTML assessment report.

---

## 5. System Probes

- `GET /health`: Basic service liveness.
- `GET /health/ready`: Database & storage readiness check.
- `GET /api/scanners/status`: Real-time host scanner tool availability.
