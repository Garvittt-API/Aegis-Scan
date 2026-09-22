"""Evidence-backed assessment analytics and comparison calculations."""
from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.attack_surface import AttackSurfaceItem, AttackSurfaceType
from app.models.discovery_run import DiscoveryRun, DiscoveryStatus
from app.models.finding import Finding, FindingStatus, Severity, VerificationStatus
from app.models.remediation import Remediation, RemediationStatus
from app.models.report import Report, ReportStatus
from app.models.scan_job import ScanJob, ScanJobStatus


def _value(item: Any) -> Any:
    return item.value if hasattr(item, "value") else item


def _finding_counts(findings: list[Finding]) -> dict[str, Any]:
    severity = {item.value: 0 for item in Severity}
    verification = {item.value: 0 for item in VerificationStatus}
    categories = Counter()
    cwes = Counter()
    for finding in findings:
        severity[finding.severity.value] += 1
        verification[finding.verification_status.value] += 1
        categories[finding.category.value] += 1
        if finding.cwe:
            cwes[finding.cwe] += 1
    return {"total": len(findings), "severity": severity, "verification": verification, "categories": dict(categories), "cwes": dict(cwes)}


def _assessment_snapshot(db: Session, assessment: Assessment) -> dict[str, Any]:
    findings = db.query(Finding).filter(Finding.assessment_id == assessment.id).all()
    # Keep the query explicit: scanner execution state is evidence, not inferred coverage.
    scan_jobs = db.query(ScanJob).filter_by(assessment_id=assessment.id).all()
    remediations = db.query(Remediation).join(Finding).filter(Finding.assessment_id == assessment.id).all()
    reports = db.query(Report).filter_by(assessment_id=assessment.id, status=ReportStatus.COMPLETED).count()
    counts = _finding_counts(findings)
    return {
        "id": assessment.id,
        "name": assessment.name,
        "target_id": assessment.target_id,
        "target": assessment.target_name if hasattr(assessment, "target_name") else (assessment.target.name if assessment.target else None),
        "target_url": assessment.target_url,
        "status": assessment.status.value,
        "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
        "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
        "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
        "findings": counts["total"],
        "verified": counts["verification"].get(VerificationStatus.VERIFIED.value, 0),
        "open": sum(1 for finding in findings if finding.status == FindingStatus.OPEN),
        "remediation": Counter(item.status.value for item in remediations),
        "scanner_status": Counter(job.status.value for job in scan_jobs),
        "reports": reports,
    }


def assessment_history(db: Session) -> list[dict[str, Any]]:
    assessments = db.query(Assessment).order_by(Assessment.created_at.asc(), Assessment.id.asc()).all()
    return [_assessment_snapshot(db, item) for item in assessments]


def scanner_coverage(db: Session, assessment_id: int | None = None) -> list[dict[str, Any]]:
    query = db.query(ScanJob)
    if assessment_id is not None:
        query = query.filter_by(assessment_id=assessment_id)
    jobs = query.all()
    findings = db.query(Finding)
    if assessment_id is not None:
        findings = findings.filter_by(assessment_id=assessment_id)
    all_findings = findings.all()
    by_scanner = Counter(finding.scanner for finding in all_findings)
    grouped = {}
    for job in jobs:
        name = job.scanner.value
        grouped.setdefault(name, {"scanner": name, "configured": True, "executed": False, "completed": 0, "failed": 0, "unavailable": 0, "findings": by_scanner.get(name, 0)})
        grouped[name]["executed"] = True
        if job.status.value == "completed": grouped[name]["completed"] += 1
        elif job.status.value == "unavailable": grouped[name]["unavailable"] += 1
        elif job.status.value in {"failed", "timeout"}: grouped[name]["failed"] += 1
    return list(grouped.values())


def attack_surface_analytics(db: Session, assessment_id: int | None = None) -> dict[str, Any]:
    query = db.query(AttackSurfaceItem)
    if assessment_id is not None:
        query = query.filter_by(assessment_id=assessment_id)
    items = query.all()
    if not items:
        return {"available": False, "message": "Attack-surface analytics unavailable."}
    counts = Counter(item.type.value for item in items)
    return {"available": True, "total": len(items), "by_type": dict(counts), "endpoints": counts.get("endpoint", 0), "parameters": counts.get("parameter", 0), "apis": counts.get("api", 0), "forms": counts.get("form", 0), "urls": counts.get("url", 0), "technologies": counts.get("technology", 0)}


def overview(db: Session) -> dict[str, Any]:
    findings = db.query(Finding).all()
    counts = _finding_counts(findings)
    remediations = db.query(Remediation).all()
    discovery = db.query(DiscoveryRun).filter(DiscoveryRun.status == DiscoveryStatus.COMPLETED).count()
    return {
        "assessments": db.query(Assessment).count(),
        "total_findings": counts["total"],
        "verified_findings": counts["verification"].get("verified", 0),
        "open_findings": sum(1 for finding in findings if finding.status == FindingStatus.OPEN),
        "validated_remediations": sum(1 for item in remediations if item.status == RemediationStatus.VALIDATED),
        "severity": counts["severity"],
        "verification": counts["verification"],
        "categories": counts["categories"],
        "discovery_runs_completed": discovery,
        "scanner_checks_executed": len(scanner_coverage(db)),
    }


def comparison(db: Session, previous_id: int, current_id: int) -> dict[str, Any]:
    previous = db.query(Assessment).filter_by(id=previous_id).first()
    current = db.query(Assessment).filter_by(id=current_id).first()
    if not previous or not current:
        raise ValueError("Assessment not found")
    previous_findings = db.query(Finding).filter_by(assessment_id=previous_id).all()
    current_findings = db.query(Finding).filter_by(assessment_id=current_id).all()
    previous_fp = {item.fingerprint for item in previous_findings if item.fingerprint}
    current_fp = {item.fingerprint for item in current_findings if item.fingerprint}
    previously_resolved = {
        item.fingerprint for item in previous_findings
        if item.fingerprint and item.status in {FindingStatus.FIXED, FindingStatus.RESOLVED}
    }
    current_jobs = db.query(ScanJob).filter_by(assessment_id=current_id).all()
    scanner_unknown = any(job.status.value in {"unavailable", "failed", "timeout"} for job in current_jobs)
    return {
        "previous": {"id": previous_id, "findings": _finding_counts(previous_findings)},
        "current": {"id": current_id, "findings": _finding_counts(current_findings)},
        "new": len(current_fp - previous_fp),
        "recurring": len(current_fp & previous_fp),
        "not_present_later": "Unable to determine" if scanner_unknown else len(previous_fp - current_fp),
        "reopened": len(previously_resolved & current_fp),
        "comparison_note": "Changes are descriptive observations, not a security score or automatic improvement claim.",
    }
