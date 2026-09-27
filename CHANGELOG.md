# Changelog — AegisScan

All notable changes to the AegisScan platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.0.0] — 2026-09-27 (Production Release)

### Added
- **Production Authentication & Authorization**:
  - Secure PBKDF2-HMAC-SHA256 password hashing (100,000 iterations).
  - Cryptographically signed JWT Bearer access token issuance and validation.
  - Endpoints for user registration (`/api/auth/register`), login (`/api/auth/login`), profile inspection (`/api/auth/me`), and status.
  - Automatic initial admin assignment for first registered operator.
- **SSRF & Cloud Metadata Safeguards**:
  - DNS resolution validation and destination IP filtering.
  - Strict blocking of AWS, GCP, and Azure cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`).
  - Configurable `ALLOW_PRIVATE_TARGETS` switch for local development vs public SaaS mode.
- **Production Security Middleware**:
  - `SecurityHeadersMiddleware`: Content Security Policy (CSP), X-Frame-Options (`DENY`), X-Content-Type-Options (`nosniff`), Referrer-Policy, Permissions-Policy, HSTS.
  - `RateLimiterMiddleware`: In-memory sliding-window IP rate limiting with stricter limits for authentication endpoints.
  - Global sanitized exception handlers preventing stack trace and database detail leaks.
- **Production Concurrency & Resource Limits**:
  - Async `Semaphore` enforcing `MAX_CONCURRENT_SCANS` bounds.
  - Process execution timeout enforcement and clean termination of child scanner processes.
- **Production Database & Storage Hardening**:
  - PostgreSQL 16 support with connection pooling, pre-ping validation, and schema auto-migration.
  - Storage writeability verification in `/health/ready` probe.
- **Production Docker & Deployment Infrastructure**:
  - Multi-stage production `Dockerfile` (Node 20 Vite builder + Python 3.12 slim non-root runner).
  - `docker-compose.yml` for containerized deployment with PostgreSQL and volume persistence.
  - Production `nginx.conf` for reverse proxy and TLS termination.
- **CI/CD Pipeline**:
  - GitHub Actions workflow (`.github/workflows/ci.yml`) covering backend pytest suite, frontend build, policy scan, and Docker image build.
- **Comprehensive Documentation**:
  - Complete architecture, deployment, security, API, CI/CD, and troubleshooting guides in `docs/`.

### Changed
- Refactored `security_validation.py` to support deep DNS resolution checks and path boundary validation.
- Updated `Settings` in `config.py` to use Pydantic v2 `SettingsConfigDict`.
- Updated frontend `api.js` to automatically attach JWT Bearer tokens from storage.
- Standardized health and readiness check responses with database and storage diagnostics.

### Fixed
- Fixed unhandled email validator dependency in user schemas.
- Fixed passlib bcrypt incompatibility with Python 3.12 by utilizing standard PBKDF2-HMAC-SHA256.
- Fixed root and health endpoint response formats for backward compatibility.

### Security
- Enforced target authorization status checks before scan execution.
- Prevented unauthenticated public scanning against arbitrary internet targets.
- Hardened subprocess command construction with strict argument arrays to prevent shell injection.
