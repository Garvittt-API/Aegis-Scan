"""Phase 8 report dataset, redaction, and honest output tests."""
from types import SimpleNamespace

from app.models.finding import Severity, VerificationStatus
from app.services.report_service import redact, render_html


def test_sensitive_evidence_is_redacted_for_presentation():
    value = "Authorization: Bearer secret-token Cookie: session=abcdef API-Key: secret123 password=letmein"
    output = redact(value)
    assert "secret-token" not in output
    assert "session=abcdef" not in output
    assert "secret123" not in output
    assert "letmein" not in output
    assert output.count("[REDACTED]") >= 4


def test_zero_finding_report_is_honest():
    dataset = {
        "report_version": "1.0",
        "generated_at": "2026-09-22T00:00:00",
        "assessment": {"id": 1, "name": "Clean", "target": "Local", "target_url": None, "authorization_confirmed": True},
        "summary": {
            "findings": 0,
            "severity": {level.value: 0 for level in Severity},
            "verification": {state.value: 0 for state in VerificationStatus},
            "remediation": {},
        },
        "tools": [{"component": "nuclei", "status": "UNAVAILABLE", "evidence": False, "run_id": 1}],
        "findings": [],
        "methodology": ["Scanner execution"],
        "limitations": ["Scanner availability can affect coverage."],
    }
    html = render_html(dataset)
    assert "No security findings were produced by the executed assessment." in html
    assert "UNAVAILABLE" in html
    assert "No vulnerabilities exist" not in html


def test_report_renders_actual_finding_values_without_recalculation():
    dataset = {
        "report_version": "1.0", "generated_at": "now",
        "assessment": {"id": 2, "name": "Assessment", "target": "Target", "target_url": "http://127.0.0.1", "authorization_confirmed": True},
        "summary": {"findings": 1, "severity": {"critical": 0, "high": 0, "medium": 1, "low": 0, "informational": 0}, "verification": {}, "remediation": {}},
        "tools": [], "methodology": [], "limitations": [],
        "findings": [{"id": 7, "title": "Missing Header", "severity": "medium", "confidence": 0.75, "verification_status": "unverified", "risk_score": 43.2, "priority": "medium", "category": "configuration", "evidence": "header absent", "raw_evidence_reference": "scan_job:4", "remediation": None}],
    }
    html = render_html(dataset)
    assert "43.2" in html
    assert "Missing Header" in html
    assert "scan_job:4" in html
