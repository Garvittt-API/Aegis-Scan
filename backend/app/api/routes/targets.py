"""
Target Management API routes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from app.core.database import get_db
from app.models.target import Target, TargetType, TargetEnvironment, TargetStatus, AuthorizationStatus
from app.models.assessment import Assessment
from app.schemas.target import (
    TargetCreate,
    TargetUpdate,
    TargetResponse,
    TargetListResponse,
    TargetSummary
)

router = APIRouter()


@router.post("", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_in: TargetCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new target in the system.
    Requires that the target be explicitly authorized.
    """
    logger.info(f"TARGET_CREATED_REQUEST: name='{target_in.name}' type='{target_in.target_type}' env='{target_in.environment}'")

    # Verify at least one location is provided
    if not target_in.base_url and not target_in.source_path and not target_in.repository_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one target location must be specified (base_url, source_path, or repository_path)"
        )

    db_target = Target(**target_in.model_dump())
    db.add(db_target)
    db.commit()
    db.refresh(db_target)

    logger.info(f"TARGET_CREATED: id={db_target.id} name='{db_target.name}'")
    
    resp = TargetResponse.model_validate(db_target)
    resp.assessments_count = 0
    return resp


@router.get("", response_model=TargetListResponse)
async def list_targets(
    target_type: Optional[TargetType] = None,
    environment: Optional[TargetEnvironment] = None,
    status_filter: Optional[TargetStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all targets with optional filtering and pagination.
    """
    query = db.query(Target)

    if target_type:
        query = query.filter(Target.target_type == target_type)
    if environment:
        query = query.filter(Target.environment == environment)
    if status_filter:
        query = query.filter(Target.status == status_filter)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (Target.name.ilike(search_fmt)) |
            (Target.base_url.ilike(search_fmt)) |
            (Target.source_path.ilike(search_fmt))
        )

    total = query.count()
    targets = query.order_by(Target.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for t in targets:
        # Calculate assessment count and last assessment
        assessments_query = db.query(Assessment).filter(Assessment.target_id == t.id)
        count = assessments_query.count()
        last_assessment = assessments_query.order_by(Assessment.created_at.desc()).first()
        
        t_resp = TargetResponse.model_validate(t)
        t_resp.assessments_count = count
        t_resp.last_assessment_date = last_assessment.created_at if last_assessment else None
        items.append(t_resp)

    return TargetListResponse(total=total, items=items)


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a target by ID.
    """
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target with ID {target_id} not found")

    assessments_query = db.query(Assessment).filter(Assessment.target_id == target.id)
    count = assessments_query.count()
    last_assessment = assessments_query.order_by(Assessment.created_at.desc()).first()

    resp = TargetResponse.model_validate(target)
    resp.assessments_count = count
    resp.last_assessment_date = last_assessment.created_at if last_assessment else None
    return resp


@router.put("/{target_id}", response_model=TargetResponse)
@router.patch("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    update_data: TargetUpdate,
    db: Session = Depends(get_db)
):
    """
    Update target parameters.
    """
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target with ID {target_id} not found")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(target, field, value)

    db.commit()
    db.refresh(target)
    logger.info(f"TARGET_UPDATED: id={target.id} name='{target.name}'")

    assessments_query = db.query(Assessment).filter(Assessment.target_id == target.id)
    count = assessments_query.count()
    last_assessment = assessments_query.order_by(Assessment.created_at.desc()).first()

    resp = TargetResponse.model_validate(target)
    resp.assessments_count = count
    resp.last_assessment_date = last_assessment.created_at if last_assessment else None
    return resp


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a target and its associated assessments.
    """
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target with ID {target_id} not found")

    target_name = target.name
    db.delete(target)
    db.commit()

    logger.info(f"TARGET_DELETED: id={target_id} name='{target_name}'")
    return None
