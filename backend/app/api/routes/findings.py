"""
Finding API routes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.finding import Finding, Severity, VerificationStatus, FindingStatus, FindingCategory
from app.models.verification import Verification
from app.models.remediation import Remediation, RemediationHistory, RemediationStatus
from app.schemas.finding import (
    FindingResponse,
    FindingListResponse,
    FindingUpdate,
    FindingStatusUpdate,
    RemediationResponse,
    RemediationUpdate,
)
from app.services.findings.risk import calculate_risk
from app.services.findings.verification import verify_finding as run_verification
from app.services.findings.remediation import create_remediation, validate_remediation

router = APIRouter()


@router.get("/remediation/summary")
async def remediation_summary(db: Session = Depends(get_db)):
    """Return real remediation lifecycle counts."""
    return {
        "open_findings": db.query(Finding).filter(Finding.status == FindingStatus.OPEN).count(),
        "with_remediation": db.query(Remediation).count(),
        "in_progress": db.query(Remediation).filter(Remediation.status == RemediationStatus.IN_PROGRESS).count(),
        "ready_for_validation": db.query(Remediation).filter(Remediation.status == RemediationStatus.READY_FOR_VALIDATION).count(),
        "validated": db.query(Remediation).filter(Remediation.status == RemediationStatus.VALIDATED).count(),
        "accepted_risk": db.query(Finding).filter(Finding.status == FindingStatus.ACCEPTED_RISK).count(),
        "false_positives": db.query(Finding).filter(Finding.status == FindingStatus.FALSE_POSITIVE).count(),
    }


@router.get("", response_model=FindingListResponse)
async def list_findings(
    assessment_id: Optional[int] = None,
    severity: Optional[Severity] = None,
    category: Optional[FindingCategory] = None,
    verification_status: Optional[VerificationStatus] = None,
    status: Optional[FindingStatus] = None,
    scanner: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List findings with optional filtering.
    """
    query = db.query(Finding)

    if assessment_id:
        query = query.filter(Finding.assessment_id == assessment_id)
    if severity:
        query = query.filter(Finding.severity == severity)
    if category:
        query = query.filter(Finding.category == category)
    if verification_status:
        query = query.filter(Finding.verification_status == verification_status)
    if status:
        query = query.filter(Finding.status == status)
    if scanner:
        query = query.filter(Finding.scanner == scanner)

    total = query.count()
    items = query.order_by(Finding.severity.desc(), Finding.first_seen.desc()).offset(offset).limit(limit).all()

    return FindingListResponse(total=total, items=items)


@router.get("/assessment/{assessment_id}/summary")
async def finding_summary(assessment_id: int, db: Session = Depends(get_db)):
    """Return evidence-backed finding counts for one assessment."""
    query = db.query(Finding).filter(Finding.assessment_id == assessment_id)
    return {
        "total": query.count(),
        "critical": query.filter(Finding.severity == Severity.CRITICAL).count(),
        "high": query.filter(Finding.severity == Severity.HIGH).count(),
        "medium": query.filter(Finding.severity == Severity.MEDIUM).count(),
        "low": query.filter(Finding.severity == Severity.LOW).count(),
        "informational": query.filter(Finding.severity == Severity.INFORMATIONAL).count(),
        "verified": query.filter(Finding.verification_status == VerificationStatus.VERIFIED).count(),
        "unverified": query.filter(Finding.verification_status == VerificationStatus.UNVERIFIED).count(),
        "likely": query.filter(Finding.verification_status == VerificationStatus.LIKELY).count(),
        "false_positive": query.filter(Finding.verification_status == VerificationStatus.FALSE_POSITIVE).count(),
    }


@router.get("/{finding_id}/risk")
async def get_finding_risk(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    risk = calculate_risk(finding)
    return {
        "score": finding.risk_score if finding.risk_score is not None else risk["score"],
        "risk_level": finding.risk_level.value if finding.risk_level else risk["level"].value,
        "priority": finding.priority.value if finding.priority else risk["level"].value,
        "exposure": finding.exposure.value if finding.exposure else "unknown",
        "explanation": finding.risk_explanation or risk["explanation"],
    }


@router.get("/{finding_id}/remediation", response_model=RemediationResponse)
async def get_remediation(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return create_remediation(db, finding)


@router.post("/{finding_id}/remediation", response_model=RemediationResponse)
async def generate_remediation(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return create_remediation(db, finding)


@router.patch("/{finding_id}/remediation", response_model=RemediationResponse)
async def update_remediation(finding_id: int, update: RemediationUpdate, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    remediation = create_remediation(db, finding)
    if update.status:
        try:
            new_status = RemediationStatus(update.status)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid remediation status") from exc
        allowed = {status.value for status in RemediationStatus}
        if new_status.value not in allowed:
            raise HTTPException(status_code=422, detail="Invalid remediation status")
        previous = remediation.status.value
        remediation.status = new_status
        db.add(RemediationHistory(remediation_id=remediation.id, event="status_changed", previous_status=previous, new_status=new_status.value, reason=update.reason))
        db.commit(); db.refresh(remediation)
    return remediation


@router.post("/{finding_id}/remediation/validate", response_model=RemediationResponse)
async def validate_finding_remediation(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    remediation = create_remediation(db, finding)
    return validate_remediation(db, remediation, finding)


@router.get("/{finding_id}/remediation/history")
async def remediation_history(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    remediation = create_remediation(db, finding)
    return db.query(RemediationHistory).filter(RemediationHistory.remediation_id == remediation.id).order_by(RemediationHistory.created_at.desc()).all()


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific finding by ID.
    """
    finding = db.query(Finding).filter(Finding.id == finding_id).first()

    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    return finding


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: int,
    update_data: FindingUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a finding's status or verification.
    """
    finding = db.query(Finding).filter(Finding.id == finding_id).first()

    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        if field not in {"status", "verification_status"}:
            continue
        old_value = getattr(finding, field).value if getattr(finding, field) else None
        setattr(finding, field, value)
        db.add(Verification(
            finding_id=finding.id,
            old_status=old_value,
            new_status=value.value if hasattr(value, "value") else str(value),
            reason=update_data.notes,
            source="finding_api",
            result=finding.verification_status.value,
        ))

    db.commit()
    db.refresh(finding)

    return finding


@router.post("/{finding_id}/verify", response_model=FindingResponse)
async def verify_finding(
    finding_id: int,
    db: Session = Depends(get_db)
):
    """
    Trigger verification for a finding.
    This will be implemented in Phase 6.
    """
    finding = db.query(Finding).filter(Finding.id == finding_id).first()

    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    await run_verification(db, finding)
    db.refresh(finding)

    return finding


@router.post("/{finding_id}/reverify", response_model=FindingResponse)
async def reverify_finding(finding_id: int, db: Session = Depends(get_db)):
    return await verify_finding(finding_id, db)


@router.patch("/{finding_id}/status", response_model=FindingResponse)
async def update_finding_status(finding_id: int, update: FindingStatusUpdate, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    if update.status == FindingStatus.FALSE_POSITIVE and finding.verification_status != VerificationStatus.FALSE_POSITIVE:
        raise HTTPException(status_code=400, detail="A finding must be marked false positive by verification first")
    old_status = finding.status.value
    finding.status = update.status
    db.add(Verification(
        finding_id=finding.id,
        old_status=old_status,
        new_status=update.status.value,
        reason=update.reason,
        source="status_api",
        result=finding.verification_status.value,
    ))
    db.commit()
    db.refresh(finding)
    return finding


@router.get("/{finding_id}/history")
async def finding_history(finding_id: int, db: Session = Depends(get_db)):
    if not db.query(Finding).filter(Finding.id == finding_id).first():
        raise HTTPException(status_code=404, detail="Finding not found")
    return db.query(Verification).filter(Verification.finding_id == finding_id).order_by(Verification.verified_at.desc()).all()
