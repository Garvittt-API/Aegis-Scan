"""
Assets API routes for attack surface discovery.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.asset import Asset, AssetType
from app.models.assessment import Assessment

router = APIRouter()


class AssetResponse(BaseModel):
    """Schema for asset response."""
    id: int
    assessment_id: int
    type: str
    url: Optional[str]
    path: Optional[str]
    method: Optional[str]
    name: Optional[str]
    source: Optional[str]
    risk_relevance: str
    metadata: Optional[dict]

    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    """Schema for list of assets."""
    total: int
    items: List[AssetResponse]
    stats: dict


class DiscoveryRequest(BaseModel):
    """Request to start discovery."""
    target_url: str
    enable_crawler: bool = True
    enable_endpoint_discovery: bool = True
    enable_technology_detection: bool = True


class DiscoveryStatus(BaseModel):
    """Status of a discovery operation."""
    assessment_id: int
    status: str
    progress: int
    assets_found: int
    errors: List[str]


@router.get("/assessments/{assessment_id}/assets", response_model=AssetListResponse)
async def list_assets(
    assessment_id: int,
    type: Optional[str] = None,
    risk_relevance: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List discovered assets for an assessment.
    """
    # Verify assessment exists
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Build query
    query = db.query(Asset).filter(Asset.assessment_id == assessment_id)

    if type:
        try:
            asset_type = AssetType(type)
            query = query.filter(Asset.type == asset_type)
        except ValueError:
            pass

    if risk_relevance:
        query = query.filter(Asset.risk_relevance == risk_relevance)

    if source:
        query = query.filter(Asset.source == source)

    # Get total count
    total = query.count()

    # Get assets
    assets = query.order_by(Asset.risk_relevance.desc(), Asset.created_at.desc()).offset(offset).limit(limit).all()

    # Calculate stats
    all_assets = db.query(Asset).filter(Asset.assessment_id == assessment_id).all()
    stats = {
        "total": len(all_assets),
        "by_type": {},
        "by_risk": {"high": 0, "medium": 0, "low": 0}
    }

    for asset in all_assets:
        type_key = asset.type.value if hasattr(asset.type, 'value') else str(asset.type)
        stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
        stats["by_risk"][asset.risk_relevance] = stats["by_risk"].get(asset.risk_relevance, 0) + 1

    return AssetListResponse(
        total=total,
        items=[AssetResponse.model_validate(a) for a in assets],
        stats=stats
    )


@router.post("/assessments/{assessment_id}/discover", response_model=dict)
async def start_discovery(
    assessment_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start attack surface discovery for an assessment.
    Runs in the background.
    """
    from app.discovery.orchestrator import run_discovery

    # Verify assessment exists
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if not assessment.target_url:
        raise HTTPException(status_code=400, detail="Assessment has no target URL configured")

    # Update assessment status
    assessment.status = "discovering"
    assessment.current_phase = "Attack Surface Discovery"
    db.commit()

    # Run discovery in background
    async def discovery_task():
        from app.core.database import SessionLocal
        db_task = SessionLocal()
        try:
            await run_discovery(assessment.target_url, db_task, assessment_id)
        except Exception as e:
            assessment.status = "failed"
            db_task.commit()
        finally:
            db_task.close()

    background_tasks.add_task(discovery_task)

    return {
        "message": "Discovery started",
        "assessment_id": assessment_id,
        "status": "discovering"
    }


@router.get("/assessments/{assessment_id}/discover/status", response_model=DiscoveryStatus)
async def get_discovery_status(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the status of discovery for an assessment.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Count discovered assets
    assets_count = db.query(Asset).filter(Asset.assessment_id == assessment_id).count()

    return DiscoveryStatus(
        assessment_id=assessment_id,
        status=assessment.status,
        progress=assessment.progress if assessment.status == "discovering" else (100 if assessment.status == "completed" else 0),
        assets_found=assets_count,
        errors=[]
    )
