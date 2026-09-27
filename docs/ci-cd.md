# AegisScan — CI/CD Integration & Policy Evaluation

AegisScan provides built-in CI/CD scanning with automated security policy evaluation, baseline regression comparison, SARIF generation for GitHub Code Scanning, and deterministic exit codes.

---

## 1. CLI Usage

The CLI command is executed via:
```bash
python -m app ci --target <URL_OR_PATH> --policy <POLICY_YAML> [OPTIONS]
```

### Options:
- `--target`: Required. HTTP(S) URL or local repository path.
- `--policy`: Path to YAML security policy file.
- `--output`: Output directory for generated artifacts (default: `artifacts/`).
- `--format`: Comma-separated output formats (`json,sarif,html,pdf`).
- `--baseline`: Assessment ID to compare against for new vs resolved regressions.

---

## 2. Deterministic Exit Codes

| Exit Code | Status | Meaning |
| :---: | :--- | :--- |
| **`0`** | `PASS` / `WARN` | Scan succeeded and policy evaluation passed or triggered only warnings. |
| **`1`** | `POLICY_FAILED` | Security policy failed (e.g. Critical/High findings exceeded thresholds). |
| **`2`** | `CONFIG_ERROR` | Configuration or invalid arguments (e.g. invalid target URL or missing policy). |
| **`3`** | `RUNTIME_ERROR`| Unhandled runtime error or process execution failure. |

---

## 3. GitHub Actions Integration Example

```yaml
name: Security Assessment
on: [push, pull_request]

jobs:
  aegisscan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install AegisScan
        run: pip install -r backend/requirements.txt

      - name: Run CI Security Scan
        working-directory: backend
        run: >-
          python -m app ci
          --target .
          --policy ../security-policy.example.yaml
          --format json,sarif,html
          --output ../artifacts

      - name: Upload SARIF to GitHub Code Scanning
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: artifacts/aegisscan-results.sarif
```

---

## 4. Policy File Schema (`security-policy.yaml`)

```yaml
version: "1.0"
name: "Production Release Security Policy"

thresholds:
  max_critical: 0
  max_high: 0
  max_medium: 5
  max_low: 20

require_verification: true
fail_on_new_findings: true

modules:
  dast: true
  nuclei: true
  sast: true
  sca: true
  custom_checks: true
```
