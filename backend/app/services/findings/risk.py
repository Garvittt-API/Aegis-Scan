"""Deterministic confidence, exposure, and risk calculations."""

import json
from typing import Any, Dict, List

from app.models.finding import Exposure, Finding, FindingPriority, Severity

SEVERITY_WEIGHTS = {
    Severity.INFORMATIONAL: 5,
    Severity.LOW: 20,
    Severity.MEDIUM: 45,
    Severity.HIGH: 70,
    Severity.CRITICAL: 90,
}


def determine_exposure(endpoint: str | None) -> Exposure:
    if not endpoint:
        return Exposure.UNKNOWN
    normalized = endpoint.lower()
    if any(host in normalized for host in ("localhost", "127.0.0.1", "::1", ".local")):
        return Exposure.LOCAL
    return Exposure.UNKNOWN


def calculate_confidence(finding: Finding, verified: bool = False) -> float:
    """Combine scanner confidence, evidence quality, and independent sources."""
    scanner = max(0.0, min(float(finding.confidence or 0.0), 1.0))
    evidence_quality = 0.2 if not finding.evidence else 0.2
    if finding.evidence:
        evidence_quality = 0.35
    try:
        sources = json.loads(finding.source_scanners or "[]")
    except (TypeError, ValueError):
        sources = []
    source_support = min(max(len(sources), 1) * 0.1, 0.2)
    verification_support = 0.25 if verified else 0.0
    return round(min(1.0, 0.5 * scanner + evidence_quality + source_support + verification_support), 2)


def calculate_risk(finding: Finding) -> Dict[str, Any]:
    """Return a transparent 0-100 AegisScan score, level, and explanation."""
    severity_weight = SEVERITY_WEIGHTS.get(finding.severity, 5)
    confidence_factor = 0.5 + (max(0.0, min(finding.confidence or 0.0, 1.0)) * 0.5)
    evidence_factor = 1.0 if finding.evidence else 0.7
    exposure_factor = {
        Exposure.INTERNET_EXPOSED: 1.15,
        Exposure.NETWORK_EXPOSED: 1.0,
        Exposure.LOCAL: 0.8,
        Exposure.UNKNOWN: 0.9,
    }.get(finding.exposure or Exposure.UNKNOWN, 0.9)
    score = round(min(100.0, severity_weight * confidence_factor * evidence_factor * exposure_factor), 2)
    level = _level(score)
    reasons: List[str] = [f"{finding.severity.value.title()} scanner severity", f"{round(finding.confidence * 100)}% confidence"]
    reasons.append("Supporting evidence available" if finding.evidence else "Evidence is limited")
    reasons.append(f"Exposure: {(finding.exposure or Exposure.UNKNOWN).value.replace('_', ' ')}")
    return {"score": score, "level": level, "explanation": "Risk is based on " + "; ".join(reasons) + "."}


def _level(score: float) -> FindingPriority:
    if score >= 80:
        return FindingPriority.CRITICAL
    if score >= 60:
        return FindingPriority.HIGH
    if score >= 40:
        return FindingPriority.MEDIUM
    if score >= 20:
        return FindingPriority.LOW
    return FindingPriority.INFORMATIONAL
