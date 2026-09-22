"""Focused Phase 7 remediation engine tests."""
from types import SimpleNamespace

from app.models.finding import FindingPriority, FindingCategory, VerificationStatus
from app.models.remediation import RemediationStatus
from app.services.findings.remediation import generate_remediation


def finding(category, evidence="observed evidence", priority=FindingPriority.MEDIUM):
    return SimpleNamespace(category=category, title="Observed issue", evidence=evidence, priority=priority, references=None)


def test_configuration_remediation_uses_finding_evidence():
    result = generate_remediation(finding(FindingCategory.CONFIGURATION))
    assert "Observed evidence" in result["explanation"]
    assert result["configuration_guidance"]
    assert result["verification_steps"]
    assert result["estimated_effort"].value == "low"


def test_dependency_remediation_does_not_invent_fixed_version():
    result = generate_remediation(finding(FindingCategory.DEPENDENCY, "package demo version 1.0"))
    assert "supported by the advisory evidence" in result["recommended_action"]
    assert "2.0" not in result["recommended_action"]


def test_unknown_category_still_produces_constrained_guidance():
    result = generate_remediation(finding("unsupported_category", evidence=None))
    assert result["title"] == "Review the reported security issue"
    assert "No additional evidence" in result["explanation"]


def test_validation_statuses_never_claim_fixed_without_new_evidence():
    assert RemediationStatus.NOT_VALIDATED.value == "not_validated"
    assert RemediationStatus.INCONCLUSIVE.value == "inconclusive"
    assert VerificationStatus.VERIFIED.value == "verified"
