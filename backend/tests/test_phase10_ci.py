"""Phase 10 deterministic CI policy, output, and security tests."""
from types import SimpleNamespace

from app.models.finding import Severity, VerificationStatus
from app.services.ci_policy import EXIT_POLICY_FAILED, evaluate_policy, load_policy
from app.cli import _sarif


def finding(severity="medium", verification="verified", fingerprint="fp"):
    return SimpleNamespace(severity=Severity(severity), verification_status=VerificationStatus(verification), fingerprint=fingerprint, title="Observed finding", endpoint="http://127.0.0.1:8010", source_file=None, source_line=None, confidence=0.8)


def test_policy_pass_and_fail_are_deterministic():
    passed = evaluate_policy({"max_findings": {"high": 0}}, [finding("medium")])
    failed = evaluate_policy({"fail_on": ["high"]}, [finding("high")])
    assert passed["status"] == "PASS"
    assert failed["status"] == "FAIL"
    assert failed["failed_rules"][0]["rule"] == "fail_on_high"
    assert EXIT_POLICY_FAILED == 1


def test_policy_warn_and_unknown_baseline_states():
    warned = evaluate_policy({"warn_on_unverified": 0}, [finding("low", "unverified")])
    unknown = evaluate_policy({"fail_on_new_findings": True}, [finding()])
    assert warned["status"] == "WARN"
    assert unknown["status"] == "UNKNOWN"
    assert "Baseline unavailable" in unknown["reason"]


def test_scanner_failure_and_required_scanner_gates():
    result = evaluate_policy({"fail_on_scanner_failure": True, "required_scanners": ["zap"]}, [], scanner_items=[{"scanner": "nuclei", "failed": 1, "unavailable": 0}])
    assert result["status"] == "FAIL"
    assert {item["rule"] for item in result["failed_rules"]} == {"fail_on_scanner_failure", "required_scanners"}


def test_sarif_uses_real_finding_fields_without_fake_locations():
    data = _sarif([finding()])
    result = data["runs"][0]["results"][0]
    assert result["ruleId"] == "fp"
    assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"].startswith("http")
    assert result["message"]["text"] == "Observed finding"


def test_malformed_policy_is_rejected(tmp_path):
    path = tmp_path / "policy.yaml"
    path.write_text("- invalid-root", encoding="utf-8")
    try:
        load_policy(str(path))
    except ValueError as exc:
        assert "mapping" in str(exc)
    else:
        raise AssertionError("Malformed policy was accepted")
