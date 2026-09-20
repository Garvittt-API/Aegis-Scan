"""
Discovery API routes for executing, tracking, and cancelling attack surface discovery runs.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db, SessionLocal
from app.models.assessment import Assessment, AssessmentStatus
from app.models.discovery_run import DiscoveryRun, DiscoveryStatus
from app.schemas.discovery_run import (
    DiscoveryStartRequest,
    DiscoveryRunResponse,
    DiscoveryRunListResponse
)
from app.discovery.engine import SafeBasicDiscoveryEngine

router = APIRouter()

# Global engine instance for safe discovery
_discovery_engine = SafeBasicDiscoveryEngine()


async def _execute_discovery_background_task(assessment_id: int, target_url: str, run_id: int):
    """Background task runner for safe discovery engine."""
    db = SessionLocal()
    try:
        await _discovery_engine.discover(
            assessment_id=assessment_id,
            target_url=target_url,
            db=db,
            run_id=run_id
        )
    except Exception as e:
        logger.error(f"Background discovery task crashed: {e}")
        run = db.query(DiscoveryRun).filter(DiscoveryRun.id == run_id).first()
        if run:
            run.status = DiscoveryStatus.FAILED
            run.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/assessments/{assessment_id}/discovery", response_model=DiscoveryRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_discovery_run(
    assessment_id: int,
    request_cfg: Optional[DiscoveryStartRequest] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Launch a safe attack surface discovery run against the assessment's target.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment {assessment_id} not found")

    if not assessment.target_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment has no target URL configured. Web URL is required for attack surface discovery."
        )

    if not assessment.authorization_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment authorization must be explicitly confirmed before running discovery."
        )

    # Prepare configuration from scan settings or request
    scan_settings = assessment.scan_settings or {}
    config_snapshot = {
        "crawl_depth": (request_cfg.crawl_depth if request_cfg and request_cfg.crawl_depth else scan_settings.get("crawl_depth", 2)),
        "max_pages": (request_cfg.max_pages if request_cfg and request_cfg.max_pages else 50),
        "rate_limit": (request_cfg.rate_limit if request_cfg and request_cfg.rate_limit else scan_settings.get("rate_limit", "low")),
        "target_url": assessment.target_url
    }

    # Create DiscoveryRun record
    discovery_run = DiscoveryRun(
        assessment_id=assessment_id,
        status=DiscoveryStatus.PENDING,
        progress=0,
        discovered_count=0,
        error_count=0,
        configuration=config_snapshot,
        logs=[{"time": "now", "msg": f"Discovery queued for {assessment.target_url}"}]
    )
    db.add(discovery_run)
    db.commit()
    db.refresh(discovery_run)

    logger.info(f"DISCOVERY_QUEUED: run_id={discovery_run.id} assessment_id={assessment_id}")

    # Launch in background
    if background_tasks:
        background_tasks.add_task(
            _execute_discovery_background_task,
            assessment_id=assessment_id,
            target_url=assessment.target_url,
            run_id=discovery_run.id
        )

    return DiscoveryRunResponse.model_validate(discovery_run)


@router.get("/assessments/{assessment_id}/discovery", response_model=DiscoveryRunListResponse)
async def list_discovery_runs(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    List all discovery runs for an assessment.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment {assessment_id} not found")

    runs = (
        db.query(DiscoveryRun)
        .filter(DiscoveryRun.assessment_id == assessment_id)
        .order_by(DiscoveryRun.created_at.desc())
        .all()
    )

    return DiscoveryRunListResponse(
        total=len(runs),
        items=[DiscoveryRunResponse.model_validate(r) for r in runs]
    )


@router.get("/assessments/{assessment_id}/discovery/{run_id}", response_model=DiscoveryRunResponse)
async def get_discovery_run(
    assessment_id: int,
    run_id: int,
    db: Session = Depends(get_db)
):
    """
    Get progress and status of a specific discovery run.
    """
    run = (
        db.query(DiscoveryRun)
        .filter(DiscoveryRun.id == run_id, DiscoveryRun.assessment_id == assessment_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Discovery run {run_id} not found")

    return DiscoveryRunResponse.model_validate(run)


@router.post("/assessments/{assessment_id}/discovery/{run_id}/cancel", response_model=DiscoveryRunResponse)
async def cancel_discovery_run(
    assessment_id: int,
    run_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel an ongoing discovery run.
    """
    run = (
        db.query(DiscoveryRun)
        .filter(DiscoveryRun.id == run_id, DiscoveryRun.assessment_id == assessment_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Discovery run {run_id} not found")

    if run.status in [DiscoveryStatus.COMPLETED, DiscoveryStatus.FAILED, DiscoveryStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel discovery run in '{run.status.value}' state."
        )

    _discovery_engine.cancel(run_id)
    run.status = DiscoveryStatus.CANCELLED
    db.commit()
    db.refresh(run)

    return DiscoveryRunResponse.model_validate(run)
