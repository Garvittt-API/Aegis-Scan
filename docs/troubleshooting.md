# AegisScan — Production Troubleshooting Guide

This guide covers common operational questions and troubleshooting steps.

---

## 1. Scanner Availability & Tool Detection

### Symptom: Scanner shows as "Not Configured" in Settings or logs.
- **Explanation**: AegisScan scans without crashing even when optional third-party CLI tools (ZAP, Nuclei, Semgrep) are not installed on the system PATH.
- **Resolution**:
  - Install scanner binaries (e.g. `pip install semgrep`, or download Nuclei binary).
  - Explicitly specify the binary path in `.env` (e.g., `SEMGREP_PATH=/usr/local/bin/semgrep` or `NUCLEI_PATH=/usr/bin/nuclei`).

---

## 2. SSRF or Target Validation Rejection

### Symptom: `Target URL validation failed: Destination IP is a private, loopback, or internal address.`
- **Explanation**: In production SaaS mode, scanning loopback (`127.0.0.1`) or private VPC ranges (`10.x.x.x`, `192.168.x.x`) is blocked by default to prevent internal network abuse.
- **Resolution**:
  - If running in a local staging or development test environment, set `ALLOW_PRIVATE_TARGETS=true` in `.env`.

---

## 3. Database Connection Issues

### Symptom: `HEALTH_CHECK_DB_FAILED` or `OperationalError: could not connect to server`.
- **Resolution**:
  - Verify PostgreSQL container is healthy: `docker-compose ps`.
  - Ensure `DATABASE_URL` matches the credentials configured in `docker-compose.yml` or `.env`.
  - Check that the database port (`5432`) is reachable from the application container.

---

## 4. Rate Limiting `429 Too Many Requests`

### Symptom: API returns HTTP status `429 Too Many Requests`.
- **Resolution**:
  - Check `RATE_LIMIT_PER_MINUTE` and `AUTH_RATE_LIMIT_PER_MINUTE` in `.env`.
  - If deploying behind a reverse proxy (e.g., Cloudflare or AWS ALB), ensure `X-Forwarded-For` header is properly forwarded so rate limiting tracks individual client IPs rather than the proxy's IP.

---

## 5. Storage Directory Permissions

### Symptom: Readiness probe reports `storage: error`.
- **Resolution**:
  - Ensure the user running the process has write permissions to `REPORTS_DIR` (e.g., `chown -R aegis:aegis /app/backend/reports`).
