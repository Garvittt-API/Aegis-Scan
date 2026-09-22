"""Focused Phase 6 verification and risk rules."""

from types import SimpleNamespace

import pytest

from app.models.finding import Exposure, FindingPriority, Severity, VerificationStatus
from app.services.findings.risk import calculate_confidence, calculate_risk, determine_exposure
from app.services.findings.verification import _condition_present


def make_finding(**overrides):
    values = {
        "severity": Severity.HIGH,
        "confidence": 0.8,
        "evidence": "header absent",
        "exposure": Exposure.LOCAL,
        "source_scanners": '["custom"]',
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_risk_is_separate_from_severity_and_explained():
    result = calculate_risk(make_finding())
    assert 0 < result["score"] < 100
    assert result["level"] == FindingPriority.MEDIUM
    assert "confidence" in result["explanation"]
    assert "Exposure" in result["explanation"]


def test_exposure_does_not_guess_remote_targets():
    assert determine_exposure("http://127.0.0.1:8000") == Exposure.LOCAL
    assert determine_exposure("https://example.test") == Exposure.UNKNOWN
    assert determine_exposure(None) == Exposure.UNKNOWN


def test_confidence_increases_only_with_verified_support():
    finding = make_finding()
    baseline = calculate_confidence(finding)
    verified = calculate_confidence(finding, verified=True)
    assert verified > baseline
    assert verified <= 1.0


def test_safe_header_rules_are_deterministic():
    assert _condition_present("Missing Content-Security-Policy", {}, []) is True
    assert _condition_present("Missing Content-Security-Policy", {"content-security-policy": "default-src 'self'"}, []) is False
    assert _condition_present("Unsupported alert", {}, []) is None


def test_missing_evidence_stays_unverified_by_policy():
    finding = make_finding(evidence=None)
    assert finding.evidence is None
    assert VerificationStatus.UNVERIFIED.value == "unverified"
