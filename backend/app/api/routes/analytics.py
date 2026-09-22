"""Analytics endpoints backed by stored assessments and execution records."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analytics_service import (
    overview, assessment_history, scanner_coverage, attack_surface_analytics, comparison,
)
from app.models.assessment import Assessment
from app.models.finding import Finding
from app.models.remediation import Remediation, RemediationStatus

router = APIRouter()


def _assessment_exists(db: Session, assessment_id: int):
    if not db.query(Assessment).filter_by(id=assessment_id).first():
        raise HTTPException(status_code=404, detail="Assessment not found")


@router.get("/overview")
async def analytics_overview(db: Session = Depends(get_db)):
    return overview(db)


@router.get("/assessments")
async def analytics_assessments(db: Session = Depends(get_db)):
    items = assessment_history(db)
    return {"items": items, "total": len(items), "message": "No assessments available." if not items else None}


@router.get("/trends")
async def analytics_trends(db: Session = Depends(get_db)):
    items = assessment_history(db)
    if len(items) < 2:
        return {"available": False, "message": "Historical trends require multiple assessments.", "items": items}
    return {"available": True, "items": [{"assessment_id": item["id"], "created_at": item["created_at"], "findings": item["findings"], "verified": item["verified"], "open": item["open"]} for item in items]}


@router.get("/severity")
async def analytics_severity(assessment_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Finding)
    if assessment_id is not None:
        _assessment_exists(db, assessment_id)
        query = query.filter_by(assessment_id=assessment_id)
    items = query.all()
    from app.services.analytics_service import _finding_counts
    return {"available": bool(items), "severity": _finding_counts(items)["severity"]}


@router.get("/categories")
async def analytics_categories(assessment_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Finding)
    if assessment_id is not None:
        _assessment_exists(db, assessment_id)
        query = query.filter_by(assessment_id=assessment_id)
    from app.services.analytics_service import _finding_counts
    return {"categories": _finding_counts(query.all())["categories"]}


@router.get("/verification")
async def analytics_verification(assessment_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Finding)
    if assessment_id is not None:
        _assessment_exists(db, assessment_id)
        query = query.filter_by(assessment_id=assessment_id)
    from app.services.analytics_service import _finding_counts
    return {"verification": _finding_counts(query.all())["verification"]}


@router.get("/remediation")
async def analytics_remediation(assessment_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Remediation)
    if assessment_id is not None:
        _assessment_exists(db, assessment_id)
        query = query.join(Finding).filter(Finding.assessment_id == assessment_id)
    counts = {status.value: 0 for status in RemediationStatus}
    for item in query.all():
        counts[item.status.value] += 1
    eligible = sum(counts.values())
    return {"counts": counts, "coverage": counts[RemediationStatus.VALIDATED.value] / eligible if eligible else None, "coverage_message": None if eligible else "Remediation coverage unavailable."}


@router.get("/scanners")
async def analytics_scanners(assessment_id: int | None = None, db: Session = Depends(get_db)):
    if assessment_id is not None:
        _assessment_exists(db, assessment_id)
    from app.services.analytics_service import scanner_coverage
    items = scanner_coverage(db, assessment_id)
    return {"items": items, "available": bool(items), "message": None if items else "Scanner coverage data unavailable."}


@router.get("/attack-surface")
async def analytics_attack_surface(assessment_id: int | None = None, db: Session = Depends(get_db)):
    if assessment_id is not None:
        _assessment_exists(db, assessment_id)
    return attack_surface_analytics(db, assessment_id)


@router.get("/coverage")
async def analytics_coverage(assessment_id: int | None = None, db: Session = Depends(get_db)):
    """Return only coverage values that have both reliable numerator and denominator."""
    if assessment_id is not None:
        _assessment_exists(db, assessment_id)
    surface = attack_surface_analytics(db, assessment_id)
    scanners = scanner_coverage(db, assessment_id)
    return {
        "attack_surface": "Coverage unavailable." if not surface.get("available") else "Coverage denominator is not recorded for executed checks.",
        "scanner": {"available": bool(scanners), "items": scanners},
    }


@router.get("/recurrence")
async def analytics_recurrence(db: Session = Depends(get_db)):
    items = assessment_history(db)
    if len(items) < 2:
        return {"available": False, "message": "Historical comparison unavailable.", "items": []}
    result = comparison(db, items[-2]["id"], items[-1]["id"])
    return {"available": True, **{key: result[key] for key in ("new", "recurring", "not_present_later", "reopened")}}


@router.get("/comparison/{previous_id}/{current_id}")
async def analytics_comparison(previous_id: int, current_id: int, db: Session = Depends(get_db)):
    try:
        return comparison(db, previous_id, current_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
