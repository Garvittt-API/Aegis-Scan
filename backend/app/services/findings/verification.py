"""Safe, deterministic verification rules for Phase 6."""

from datetime import datetime
from typing import Dict, Optional

import httpx
from sqlalchemy.orm import Session

from app.models.finding import Finding, VerificationStatus
from app.models.verification import Verification
from app.services.findings.risk import calculate_confidence, calculate_risk, determine_exposure


async def verify_finding(db: Session, finding: Finding) -> Verification:
    """Attempt only non-destructive checks supported by the finding evidence."""
    old_status = finding.verification_status.value if finding.verification_status else VerificationStatus.UNVERIFIED.value
    result = VerificationStatus.UNVERIFIED
    reason = "No safe verification rule matched this finding."
    evidence = finding.evidence
    request = None
    response = None

    if finding.scanner == "custom" and finding.endpoint and finding.endpoint.startswith(("http://", "https://")):
        result, reason, evidence, request, response = await _verify_custom_http(finding)
    elif finding.evidence:
        result = VerificationStatus.LIKELY
        reason = "Scanner evidence is present, but no safe independent verification rule is available."

    finding.verification_status = result
    finding.verification_reason = reason
    finding.verification_evidence = evidence
    finding.reproducibility = "reproduced" if result == VerificationStatus.VERIFIED else "not_attempted" if result == VerificationStatus.UNVERIFIED else "not_reproduced"
    finding.last_verified_at = datetime.utcnow()
    if result == VerificationStatus.VERIFIED:
        finding.verified_at = finding.last_verified_at
    finding.confidence = calculate_confidence(finding, verified=result == VerificationStatus.VERIFIED)
    finding.exposure = determine_exposure(finding.endpoint)
    risk = calculate_risk(finding)
    finding.risk_score = risk["score"]
    finding.risk_level = risk["level"]
    finding.priority = risk["level"]
    finding.risk_explanation = risk["explanation"]

    attempt = Verification(
        finding_id=finding.id,
        result=result.value,
        evidence=evidence,
        request=request,
        response=response,
        notes=reason,
        old_status=old_status,
        new_status=result.value,
        reason=reason,
        source="safe_rule_engine",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


async def _verify_custom_http(finding: Finding):
    """Re-fetch headers only; never submits forms or mutates target state."""
    try:
        async with httpx.AsyncClient(timeout=10, verify=False, follow_redirects=True) as client:
            response = await client.get(finding.endpoint)
        headers = {key.lower(): value for key, value in response.headers.items()}
        title = finding.title.lower()
        still_present = _condition_present(title, headers, response.headers.get_list("set-cookie") if hasattr(response.headers, "get_list") else [])
        request = f"GET {finding.endpoint}"
        response_text = f"HTTP {response.status_code}; headers inspected"
        if still_present is True:
            return VerificationStatus.VERIFIED, "Safe header inspection reproduced the reported condition.", finding.evidence, request, response_text
        if still_present is False:
            return VerificationStatus.FALSE_POSITIVE, "Safe header inspection did not reproduce the reported condition.", "", request, response_text
        return VerificationStatus.NOT_REPRODUCIBLE, "The target response could not establish the reported condition.", finding.evidence, request, response_text
    except (httpx.HTTPError, ValueError) as exc:
        return VerificationStatus.NOT_REPRODUCIBLE, f"Safe verification failed: {exc}", finding.evidence, None, None


def _condition_present(title: str, headers: Dict[str, str], cookies) -> Optional[bool]:
    title = title.lower()
    if "content-security-policy" in title or "csp" in title:
        return not bool(headers.get("content-security-policy"))
    if "x-content-type-options" in title or "nosniff" in title:
        return headers.get("x-content-type-options", "").lower() != "nosniff"
    if "referrer-policy" in title:
        return not bool(headers.get("referrer-policy"))
    if "strict-transport-security" in title or "hsts" in title:
        return not bool(headers.get("strict-transport-security"))
    if "cookie" in title:
        return any("httponly" not in cookie.lower() or "secure" not in cookie.lower() or "samesite" not in cookie.lower() for cookie in cookies)
    if "cors" in title or "access-control" in title:
        return headers.get("access-control-allow-origin") == "*"
    return None
