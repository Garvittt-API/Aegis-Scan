# AegisScan — Security Architecture & Threat Model

AegisScan is designed with defense-in-depth principles to prevent abuse, command injection, SSRF, data leakage, and resource exhaustion.

---

## 1. Threat Model & Safeguards

| Threat Vector | Potential Impact | AegisScan Safeguard |
| :--- | :--- | :--- |
| **Unauthorized Public Scanning** | Abuse of infrastructure to attack 3rd-party websites | Explicit authorization requirement (`authorization_status: "authorized"`). Unverified targets cannot be scanned. |
| **Server-Side Request Forgery (SSRF)** | Access to AWS/GCP metadata (`169.254.169.254`) or internal VPC networks | DNS resolution checks, explicit IP range filtering, `ALLOW_PRIVATE_TARGETS=false` in SaaS mode. |
| **Command / Shell Injection** | Compromise of host system during tool execution | `asyncio.create_subprocess_exec` argument arrays exclusively. No `shell=True` or shell string interpolation. |
| **Path Traversal / Arbitrary File Read** | Unauthorized access to host filesystem (`/etc/passwd`) | Strict path normalization and boundary verification (`root in path.parents`). |
| **Denial of Service / Resource Exhaustion** | Heavy scans crashing server or network bandwidth | Semaphore concurrency limiter (`MAX_CONCURRENT_SCANS`), scan execution timeouts (300s), and IP rate limiting. |
| **Information Disclosure / Secret Leakage** | Exposing API keys or database stack traces | Sanitized global error handlers in production, log masking of tokens, `.env` exclusion from version control. |
| **Fake Vulnerability Fabrication** | Inaccurate security data and false credibility | Zero-fabrication policy: findings exist only when raw scanner evidence is persisted on disk. |

---

## 2. Authentication & Credential Storage

- **Password Hashing**: PBKDF2-HMAC-SHA256 with 100,000 rounds and unique 16-byte random salts.
- **JWT Access Tokens**: Cryptographically signed with HS256 using `SECRET_KEY`, 24-hour expiration, carrying authenticated user IDs.
- **Role-Based Access**: Distinguishes between standard Security Operators and Administrators.

---

## 3. Responsible Disclosure

If you discover a security vulnerability within AegisScan, please do not open a public GitHub issue. Send a report to security@aegisscan.local or open a confidential Security Advisory on GitHub.
