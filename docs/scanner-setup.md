# AegisScan — Security Scanner Setup & Integration Guide

AegisScan orchestrates multiple industry-standard security scanners alongside custom application security heuristics.

---

## 1. Scanner Overview & Binary Requirements

| Scanner Engine | Engine Type | Installation Command / Binary Source |
| :--- | :--- | :--- |
| **OWASP ZAP** | DAST | [zaproxy.org/download](https://www.zaproxy.org/download/) or `zap.sh` / `zap.bat` |
| **Nuclei** | DAST / Templates | `go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| **Semgrep** | SAST | `pip install semgrep` |
| **OWASP Dependency-Check** | SCA | [jeremylong.github.io/DependencyCheck](https://jeremylong.github.io/DependencyCheck/) |
| **Custom Checks** | Heuristic | Built-in native Python security heuristics |

---

## 2. Configuration via Environment Variables

If scanner binaries are installed in non-standard directories or system PATH is not configured, specify absolute paths in `.env`:

```ini
# Scanner Executable Paths
ZAP_PATH=/opt/zaproxy/zap.sh
NUCLEI_PATH=/usr/local/bin/nuclei
SEMGREP_PATH=/usr/local/bin/semgrep
DEPENDENCY_CHECK_PATH=/opt/dependency-check/bin/dependency-check.sh
```

---

## 3. Availability Detection & Failure Isolation

AegisScan automatically tests executable presence and permissions on system startup:
- If a scanner is installed and executable: Status shows as **`Available`** (`COMPLETED` upon execution).
- If an optional scanner is missing: Status shows as **`Not Configured` / `Unavailable`**.
- **Important**: Scanner unavailability never causes the entire assessment to crash; other available scanners and custom checks continue executing with complete fault isolation.
