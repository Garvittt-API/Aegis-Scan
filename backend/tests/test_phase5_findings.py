"""Focused Phase 5 parser and fingerprint contracts."""

from app.services.findings.parsers import (
    parse_custom,
    parse_dependency_check,
    parse_nuclei,
    parse_semgrep,
    parse_zap,
)
from app.services.findings.service import fingerprint


def test_zap_parser_maps_risk_and_preserves_evidence():
    findings = parse_zap({"site": [{"@name": "https://example.test", "alerts": [{
        "alert": "Missing CSP",
        "riskdesc": "Medium (3)",
        "confidence": "High",
        "uri": "https://example.test/",
        "evidence": "header absent",
    }]}]})
    assert findings[0]["severity"] == "medium"
    assert findings[0]["confidence"] == 0.9
    assert findings[0]["evidence"] == "header absent"


def test_other_parsers_emit_only_real_records():
    assert len(parse_nuclei([{"template-id": "tpl", "info": {"name": "Issue", "severity": "high"}}])) == 1
    assert len(parse_semgrep({"results": [{"check_id": "rule", "path": "a.py", "start": {"line": 4}, "extra": {"message": "Issue"}}]})) == 1
    assert len(parse_dependency_check({"dependencies": [{"vulnerabilities": [{"name": "CVE-1", "severity": "high"}]}]})) == 1
    assert parse_custom({"results": [{"check_id": "ok", "status": "not_applicable"}]}) == []


def test_fingerprint_is_stable_and_scanner_independent():
    base = {"title": "Missing CSP", "category": "configuration", "endpoint": "https://example.test"}
    assert fingerprint({**base, "scanner_id": "zap-1"}) == fingerprint({**base, "scanner_id": "nuclei-1"})
