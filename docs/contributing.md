# Contributing to AegisScan

Thank you for your interest in contributing to AegisScan!

---

## 1. Code of Conduct & Responsible Use

AegisScan is an evidence-driven security assessment platform built for authorized environments. All contributions must adhere to:
- **Zero-Fabrication Principle**: Never introduce simulated, hardcoded, or fabricated vulnerabilities or findings.
- **Defensive Engineering**: Ensure SSRF prevention, command sanitization, and authorization verification are preserved.

---

## 2. Development Workflow

1. Fork the repository and create a descriptive feature branch:
   ```bash
   git checkout -b feature/scanner-adapter-enhancement
   ```

2. Follow coding standards:
   - Backend: Python 3.12, PEP 8, Pydantic v2 schemas, type annotations.
   - Frontend: React 18, Tailwind CSS, WCAG-conscious contrast.

3. Run automated tests before submitting a Pull Request:
   ```bash
   # Backend Pytest
   pytest backend/tests -v

   # Frontend Build Validation
   npm --prefix frontend run build
   ```

---

## 3. Reporting Security Vulnerabilities

Please do not disclose security issues through public GitHub issues. Report vulnerabilities responsibly to security@aegisscan.local or open a confidential Security Advisory.
