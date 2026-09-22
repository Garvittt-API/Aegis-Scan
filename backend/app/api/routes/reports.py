"""Assessment report generation and retrieval endpoints."""
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.assessment import Assessment
from app.models.report import Report, ReportFormat, ReportStatus
from app.schemas.report import ReportCreate, ReportResponse, ReportListResponse
from app.services.report_service import generate_report

router = APIRouter()


def _get_report(db: Session, report_id: int) -> Report:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def _safe_report_path(report: Report) -> Path:
    if not report.file_path:
        raise HTTPException(status_code=404, detail="Report file is not available")
    root = Path(settings.reports_dir or Path("./reports")).resolve()
    path = Path(report.file_path).resolve()
    if root not in path.parents:
        raise HTTPException(status_code=404, detail="Report file is not available")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Report file is not available")
    return path


@router.post("", response_model=ReportResponse, status_code=201)
async def create_report(request: ReportCreate, db: Session = Depends(get_db)):
    if not db.query(Assessment).filter(Assessment.id == request.assessment_id).first():
        raise HTTPException(status_code=404, detail="Assessment not found")
    return generate_report(db, request.assessment_id, request.format)


@router.get("", response_model=ReportListResponse)
async def list_reports(assessment_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Report)
    if assessment_id is not None:
        query = query.filter(Report.assessment_id == assessment_id)
    items = query.order_by(Report.created_at.desc()).all()
    return ReportListResponse(total=len(items), items=items)


@router.get("/assessments/{assessment_id}/report", response_model=ReportResponse)
async def latest_assessment_report(assessment_id: int, db: Session = Depends(get_db)):
    if not db.query(Assessment).filter(Assessment.id == assessment_id).first():
        raise HTTPException(status_code=404, detail="Assessment not found")
    report = db.query(Report).filter(Report.assessment_id == assessment_id).order_by(Report.created_at.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="No report has been generated for this assessment")
    return report


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: Session = Depends(get_db)):
    return _get_report(db, report_id)


@router.get("/{report_id}/html")
async def get_report_html(report_id: int, db: Session = Depends(get_db)):
    report = _get_report(db, report_id)
    if report.format != ReportFormat.HTML:
        raise HTTPException(status_code=400, detail="Report is not an HTML report")
    return FileResponse(_safe_report_path(report), media_type="text/html")


@router.get("/{report_id}/pdf")
async def get_report_pdf(report_id: int, db: Session = Depends(get_db)):
    report = _get_report(db, report_id)
    if report.format != ReportFormat.PDF:
        raise HTTPException(status_code=400, detail="Report is not a PDF report")
    return FileResponse(_safe_report_path(report), media_type="application/pdf")
