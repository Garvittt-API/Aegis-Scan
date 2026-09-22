"""Deterministic remediation generation and evidence-based validation."""
import json
from datetime import datetime
from app.models.remediation import Remediation, RemediationHistory, RemediationStatus, RemediationEffort

RULES = {
    "configuration": ("Correct the configuration issue", "Review the observed configuration and apply the smallest safe change at the application or server layer.", "Re-run the same scanner or custom check and compare its new evidence with the original result."),
    "dependency": ("Upgrade the affected dependency", "Identify the package and installed version from the finding evidence. Upgrade only to a version supported by the advisory evidence; no fixed version is invented.", "Re-run dependency analysis and confirm the vulnerable component is no longer reported."),
    "secrets": ("Remove the exposed secret", "Move the secret out of source code into an approved secret-management mechanism and rotate it through the authorized operational process.", "Re-run the source scan and confirm the original location is no longer reported."),
    "input_validation": ("Apply contextual input controls", "Use parameterized APIs and context-aware output encoding appropriate to the affected component. Do not rely on client-side checks.", "Re-run the originating scanner and compare the new evidence."),
}

def generate_remediation(finding):
    category = getattr(finding.category, "value", str(finding.category)).lower()
    title, action, validation = RULES.get(category, ("Review the reported security issue", "Address the specific condition shown in the preserved scanner evidence without changing unrelated behavior.", "Re-run the originating check and compare new evidence with the original finding."))
    evidence = finding.evidence or "No additional evidence was preserved."
    return {"title": title, "summary": f"Remediation for the evidence-backed finding: {finding.title}.", "explanation": f"Observed evidence: {evidence}", "recommended_action": action, "technical_steps": "1. Review the finding location and preserved evidence.\n2. Apply a minimal authorized change.\n3. Run the relevant test suite and assessment.", "configuration_guidance": action if category == "configuration" else None, "dependency_guidance": action if category == "dependency" else None, "verification_steps": validation, "priority": getattr(finding.priority, "value", None), "estimated_effort": RemediationEffort.MEDIUM if category in {"dependency", "secrets"} else RemediationEffort.LOW, "impact": "medium", "references": finding.references}

def create_remediation(db, finding):
    existing = db.query(Remediation).filter(Remediation.finding_id == finding.id).first()
    if existing: return existing
    data = generate_remediation(finding)
    item = Remediation(finding_id=finding.id, **data)
    db.add(item); db.flush()
    db.add(RemediationHistory(remediation_id=item.id, event="remediation_generated", new_status=item.status.value, reason="deterministic_rule_engine"))
    db.commit(); db.refresh(item)
    return item

def validate_remediation(db, remediation, finding):
    previous = remediation.status.value
    evidence = finding.verification_evidence or ""
    if finding.verification_status.value == "verified" and evidence and finding.verification_status.value != "false_positive":
        remediation.status = RemediationStatus.NOT_VALIDATED
        reason = "The finding remains verified; remediation is not demonstrated by new evidence."
    elif finding.verification_status.value == "false_positive":
        remediation.status = RemediationStatus.INCONCLUSIVE
        reason = "The source finding was classified false positive; remediation validation is inconclusive."
    else:
        remediation.status = RemediationStatus.INCONCLUSIVE
        reason = "No new safe reassessment evidence demonstrates that the condition is resolved."
    remediation.validation_evidence = evidence or None
    db.add(RemediationHistory(remediation_id=remediation.id, event="validation_performed", previous_status=previous, new_status=remediation.status.value, reason=reason, evidence_reference=evidence or None))
    db.commit(); db.refresh(remediation)
    return remediation
