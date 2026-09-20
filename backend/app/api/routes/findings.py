"""
Finding API routes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.finding import Finding, Severity, VerificationStatus, FindingStatus, FindingCategory
from app.schemas.finding import (
    FindingResponse,
    FindingListResponse,
    FindingUpdate
)

router = APIRouter()


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
        setattr(finding, field, value)

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

    # TODO: Implement actual verification logic in Phase 6
    # For now, just mark as verified
    finding.verification_status = VerificationStatus.VERIFIED
    db.commit()
    db.refresh(finding)

    return finding
