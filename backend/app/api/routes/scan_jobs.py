"""
Scan Job and Scan Planning API routes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.models.assessment import Assessment, AssessmentStatus
from app.models.scan_job import (
    ScanJob,
    ScanJobStatus,
    ScanJobPriority,
    ScannerEngineType,
    validate_job_transition
)
from app.schemas.scan_job import (
    ScanJobCreate,
    ScanJobUpdate,
    ScanJobResponse,
    ScanJobListResponse,
    ScanPlanRequest,
    ScanPlanResponse
)
from app.services.scan_orchestrator import ScanPlanner, ScanOrchestrator

from app.scanners.adapters import list_available_scanners, get_scanner_adapter
from app.scanners.result_storage import get_scan_storage_dir
import json

router = APIRouter()


@router.get("/scanners/status", response_model=List[dict])
async def get_scanner_availability():
    """
    Check real-time installation and PATH availability status for all scanner engines.
    """
    return list_available_scanners()


@router.post("/assessments/{assessment_id}/scan-jobs/plan", response_model=ScanPlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_scan_plan(
    assessment_id: int,
    plan_req: Optional[ScanPlanRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Generate ScanJob queue records for all enabled security modules based on the assessment configuration and discovered attack surface.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment {assessment_id} not found")

    priority = plan_req.priority if plan_req else ScanJobPriority.NORMAL
    override = plan_req.override_existing if plan_req else False

    jobs = ScanPlanner.generate_plan(
        db=db,
        assessment=assessment,
        priority=priority,
        override_existing=override
    )

    # Update assessment status if in configured/draft
    if assessment.status in [AssessmentStatus.CONFIGURED, AssessmentStatus.DRAFT, AssessmentStatus.PENDING]:
        assessment.status = AssessmentStatus.QUEUED
        assessment.current_phase = "Scan Jobs Planned"
        db.commit()

    return ScanPlanResponse(
        assessment_id=assessment_id,
        planned_jobs_count=len(jobs),
        jobs=[ScanJobResponse.model_validate(j) for j in jobs],
        message=f"Successfully planned and queued {len(jobs)} scanner jobs for assessment '{assessment.name}'."
    )


@router.get("/assessments/{assessment_id}/scan-jobs", response_model=ScanJobListResponse)
async def list_scan_jobs(
    assessment_id: int,
    scanner: Optional[ScannerEngineType] = None,
    status_filter: Optional[ScanJobStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    List all scan jobs for an assessment.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment {assessment_id} not found")

    query = db.query(ScanJob).filter(ScanJob.assessment_id == assessment_id)

    if scanner:
        query = query.filter(ScanJob.scanner == scanner)
    if status_filter:
        query = query.filter(ScanJob.status == status_filter)

    jobs = query.order_by(ScanJob.created_at.asc()).all()

    return ScanJobListResponse(
        total=len(jobs),
        items=[ScanJobResponse.model_validate(j) for j in jobs]
    )


@router.get("/assessments/{assessment_id}/scan-jobs/{job_id}", response_model=ScanJobResponse)
async def get_scan_job(
    assessment_id: int,
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific scan job.
    """
    job = db.query(ScanJob).filter(ScanJob.id == job_id, ScanJob.assessment_id == assessment_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ScanJob {job_id} not found")

    return ScanJobResponse.model_validate(job)


@router.get("/assessments/{assessment_id}/scan-jobs/{job_id}/raw", response_model=dict)
async def get_scan_job_raw_output(
    assessment_id: int,
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve stored raw execution artifacts (metadata, stdout, stderr, raw JSON output).
    """
    job = db.query(ScanJob).filter(ScanJob.id == job_id, ScanJob.assessment_id == assessment_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ScanJob {job_id} not found")

    storage_dir = get_scan_storage_dir(assessment_id, job_id)
    metadata = {}
    stdout_content = ""
    stderr_content = ""
    raw_result = None

    if (storage_dir / "metadata.json").is_file():
        try:
            with open(storage_dir / "metadata.json", "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            pass

    if (storage_dir / "stdout.log").is_file():
        try:
            with open(storage_dir / "stdout.log", "r", encoding="utf-8") as f:
                stdout_content = f.read()
        except Exception:
            pass

    if (storage_dir / "stderr.log").is_file():
        try:
            with open(storage_dir / "stderr.log", "r", encoding="utf-8") as f:
                stderr_content = f.read()
        except Exception:
            pass

    if (storage_dir / "result.json").is_file():
        try:
            with open(storage_dir / "result.json", "r", encoding="utf-8") as f:
                raw_result = json.load(f)
        except Exception:
            pass

    return {
        "job_id": job.id,
        "assessment_id": assessment_id,
        "scanner": job.scanner.value,
        "status": job.status.value,
        "result_location": str(storage_dir),
        "metadata": metadata,
        "stdout": stdout_content,
        "stderr": stderr_content,
        "result_data": raw_result
    }


@router.post("/assessments/{assessment_id}/scan-jobs/{job_id}/cancel", response_model=ScanJobResponse)
async def cancel_scan_job(
    assessment_id: int,
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel a pending or queued scan job.
    """
    job = db.query(ScanJob).filter(ScanJob.id == job_id, ScanJob.assessment_id == assessment_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ScanJob {job_id} not found")

    try:
        updated_job = ScanOrchestrator.cancel_scan_job(db=db, job_id=job.id)
        return ScanJobResponse.model_validate(updated_job)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))


@router.post("/assessments/{assessment_id}/scan-jobs/{job_id}/execute", response_model=dict)
async def execute_single_scan_job(
    assessment_id: int,
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Execute a single planned scan job. Real local execution with zero fake results.
    """
    job = db.query(ScanJob).filter(ScanJob.id == job_id, ScanJob.assessment_id == assessment_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ScanJob {job_id} not found")

    if job.status not in [ScanJobStatus.PENDING, ScanJobStatus.QUEUED]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"ScanJob is already {job.status.value}")

    result = await ScanOrchestrator.execute_scan_job(db=db, job_id=job.id)
    return result


@router.post("/assessments/{assessment_id}/scan-jobs/execute-all", response_model=List[dict])
async def execute_all_scan_jobs(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Execute all queued or pending scan jobs for an assessment sequentially with error isolation.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment {assessment_id} not found")

    results = await ScanOrchestrator.run_all_jobs(db=db, assessment_id=assessment_id)
    return results
