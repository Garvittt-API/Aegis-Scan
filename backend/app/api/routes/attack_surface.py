"""
Attack Surface Inventory API routes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.assessment import Assessment
from app.models.attack_surface import AttackSurfaceItem, AttackSurfaceType, AttackSurfaceStatus
from app.schemas.attack_surface import (
    AttackSurfaceItemCreate,
    AttackSurfaceItemResponse,
    AttackSurfaceListResponse,
    AttackSurfaceSummary
)
from app.discovery.normalizer import save_or_merge_attack_surface_item

router = APIRouter()


@router.get("/assessments/{assessment_id}/attack-surface", response_model=AttackSurfaceListResponse)
async def list_attack_surface(
    assessment_id: int,
    type_filter: Optional[AttackSurfaceType] = Query(None, alias="type"),
    method: Optional[str] = None,
    source: Optional[str] = None,
    status_filter: Optional[AttackSurfaceStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated attack surface inventory and breakdown metrics for an assessment.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment {assessment_id} not found")

    query = db.query(AttackSurfaceItem).filter(AttackSurfaceItem.assessment_id == assessment_id)

    if type_filter:
        query = query.filter(AttackSurfaceItem.type == type_filter)
    if method:
        query = query.filter(AttackSurfaceItem.method == method.upper())
    if source:
        query = query.filter(AttackSurfaceItem.source == source)
    if status_filter:
        query = query.filter(AttackSurfaceItem.status == status_filter)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (AttackSurfaceItem.name.ilike(search_fmt)) |
            (AttackSurfaceItem.url.ilike(search_fmt)) |
            (AttackSurfaceItem.path.ilike(search_fmt)) |
            (AttackSurfaceItem.parameter.ilike(search_fmt))
        )

    total = query.count()
    items = query.order_by(AttackSurfaceItem.risk_relevance.desc(), AttackSurfaceItem.last_seen.desc()).offset(offset).limit(limit).all()

    # Calculate summary metrics across all items of this assessment
    all_items = db.query(AttackSurfaceItem).filter(AttackSurfaceItem.assessment_id == assessment_id).all()
    
    summary = AttackSurfaceSummary(
        total_assets=len(all_items),
        urls_count=sum(1 for i in all_items if i.type == AttackSurfaceType.URL),
        apis_count=sum(1 for i in all_items if i.type == AttackSurfaceType.API),
        endpoints_count=sum(1 for i in all_items if i.type == AttackSurfaceType.ENDPOINT),
        parameters_count=sum(1 for i in all_items if i.type == AttackSurfaceType.PARAMETER),
        javascript_count=sum(1 for i in all_items if i.type == AttackSurfaceType.JAVASCRIPT),
        forms_count=sum(1 for i in all_items if i.type == AttackSurfaceType.FORM),
        technologies_count=sum(1 for i in all_items if i.type == AttackSurfaceType.TECHNOLOGY),
        assets_count=sum(1 for i in all_items if i.type == AttackSurfaceType.ASSET),
        services_count=sum(1 for i in all_items if i.type == AttackSurfaceType.SERVICE)
    )

    for item in all_items:
        # Risk breakdown
        if item.risk_relevance in summary.by_risk:
            summary.by_risk[item.risk_relevance] += 1
        # Source breakdown
        for s in (item.discovered_by or [item.source or "unknown"]):
            summary.by_source[s] = summary.by_source.get(s, 0) + 1

    return AttackSurfaceListResponse(
        total=total,
        items=[AttackSurfaceItemResponse.model_validate(i) for i in items],
        summary=summary
    )


@router.post("/assessments/{assessment_id}/attack-surface", response_model=AttackSurfaceItemResponse, status_code=status.HTTP_201_CREATED)
async def create_attack_surface_item(
    assessment_id: int,
    item_in: AttackSurfaceItemCreate,
    db: Session = Depends(get_db)
):
    """
    Manually add or merge an attack surface item.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment {assessment_id} not found")

    item, _ = save_or_merge_attack_surface_item(
        db=db,
        assessment_id=assessment_id,
        asset_type=item_in.type,
        name=item_in.name,
        url=item_in.url,
        method=item_in.method,
        path=item_in.path,
        parameter=item_in.parameter,
        source=item_in.source or "manual_input",
        risk_relevance=item_in.risk_relevance,
        metadata=item_in.metadata
    )

    return AttackSurfaceItemResponse.model_validate(item)
