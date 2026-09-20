"""
Assessment API routes for assessment management, validation, and preset loading.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.models.assessment import Assessment, AssessmentStatus, AssessmentEnvironment
from app.models.target import Target
from app.models.finding import Finding, Severity
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentResponse,
    AssessmentListResponse,
    AssessmentSummary,
    AssessmentValidationResult
)
from app.services.assessment_service import (
    validate_assessment_configuration,
    get_world_monitor_preset
)

router = APIRouter()


@router.get("/presets/world-monitor", response_model=dict)
async def load_world_monitor_preset():
    """
    Get the predefined World Monitor Security Assessment preset configuration.
    """
    logger.info("PRESET_REQUESTED: world_monitor")
    return get_world_monitor_preset()


@router.post("/validate", response_model=AssessmentValidationResult)
async def validate_new_assessment(
    assessment: AssessmentCreate,
    db: Session = Depends(get_db)
):
    """
    Validate an assessment configuration prior to creation.
    """
    target = None
    if assessment.target_id:
        target = db.query(Target).filter(Target.id == assessment.target_id).first()

    return validate_assessment_configuration(assessment.model_dump(), target)


@router.post("", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    assessment: AssessmentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new security assessment.
    Requires authorization confirmation for target scanning.
    """
    logger.info(f"ASSESSMENT_CREATED_REQUEST: name='{assessment.name}' env='{assessment.environment}'")

    # Validate target if target_id provided
    target = None
    if assessment.target_id:
        target = db.query(Target).filter(Target.id == assessment.target_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target with ID {assessment.target_id} not found"
            )

    # Validate configuration
    validation = validate_assessment_configuration(assessment.model_dump(), target)
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Assessment configuration validation failed", "errors": validation.errors}
        )

    # Prepare dump
    data = assessment.model_dump()
    
    # Extract sub-schemas to json dicts if present
    if assessment.scope:
        data["scope"] = assessment.scope.model_dump()
    if assessment.modules:
        data["modules"] = assessment.modules.model_dump()
        # Synchronize legacy boolean flags
        data["enable_zap"] = assessment.modules.dast
        data["enable_nuclei"] = assessment.modules.nuclei
        data["enable_semgrep"] = assessment.modules.sast
        data["enable_dependency_check"] = assessment.modules.sca
        data["enable_custom_checks"] = assessment.modules.custom_checks
    if assessment.scan_settings:
        data["scan_settings"] = assessment.scan_settings.model_dump()

    # Inherit target URL / source path from target if empty
    if target:
        if not data.get("target_url") and target.base_url:
            data["target_url"] = target.base_url
        if not data.get("source_path") and target.source_path:
            data["source_path"] = target.source_path

    db_assessment = Assessment(**data)
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)

    logger.info(f"ASSESSMENT_CREATED: id={db_assessment.id} name='{db_assessment.name}' target_id={db_assessment.target_id}")

    resp = AssessmentResponse.model_validate(db_assessment)
    if target:
        resp.target_name = target.name
    return resp


@router.get("", response_model=AssessmentListResponse)
async def list_assessments(
    status_filter: Optional[AssessmentStatus] = Query(None, alias="status"),
    target_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all assessments with optional filtering.
    """
    query = db.query(Assessment)

    if status_filter:
        query = query.filter(Assessment.status == status_filter)
    if target_id:
        query = query.filter(Assessment.target_id == target_id)

    total = query.count()
    items_raw = query.order_by(Assessment.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for a in items_raw:
        item = AssessmentResponse.model_validate(a)
        if a.target_id:
            target = db.query(Target).filter(Target.id == a.target_id).first()
            if target:
                item.target_name = target.name
        items.append(item)

    return AssessmentListResponse(total=total, items=items)


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific assessment by ID.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    resp = AssessmentResponse.model_validate(assessment)
    if assessment.target_id:
        target = db.query(Target).filter(Target.id == assessment.target_id).first()
        if target:
            resp.target_name = target.name

    return resp


@router.post("/{assessment_id}/validate", response_model=AssessmentValidationResult)
async def validate_existing_assessment(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Validate the configuration of an existing assessment.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    target = None
    if assessment.target_id:
        target = db.query(Target).filter(Target.id == assessment.target_id).first()

    data = {
        "name": assessment.name,
        "target_url": assessment.target_url,
        "source_path": assessment.source_path,
        "authorization_confirmed": assessment.authorization_confirmed,
        "scope": assessment.scope,
        "modules": assessment.modules,
        "scan_settings": assessment.scan_settings
    }
    return validate_assessment_configuration(data, target)


@router.put("/{assessment_id}", response_model=AssessmentResponse)
@router.patch("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: int,
    update_data: AssessmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an assessment configuration or status.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    update_dict = update_data.model_dump(exclude_unset=True)

    if "modules" in update_dict and update_dict["modules"]:
        modules_obj = update_dict["modules"]
        setattr(assessment, "modules", modules_obj)
        # Sync legacy booleans
        setattr(assessment, "enable_zap", modules_obj.get("dast", True))
        setattr(assessment, "enable_nuclei", modules_obj.get("nuclei", True))
        setattr(assessment, "enable_semgrep", modules_obj.get("sast", True))
        setattr(assessment, "enable_dependency_check", modules_obj.get("sca", True))
        setattr(assessment, "enable_custom_checks", modules_obj.get("custom_checks", True))
        update_dict.pop("modules")

    for field, value in update_dict.items():
        setattr(assessment, field, value)

    db.commit()
    db.refresh(assessment)
    logger.info(f"ASSESSMENT_UPDATED: id={assessment.id} name='{assessment.name}' status='{assessment.status}'")

    resp = AssessmentResponse.model_validate(assessment)
    if assessment.target_id:
        target = db.query(Target).filter(Target.id == assessment.target_id).first()
        if target:
            resp.target_name = target.name
    return resp


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an assessment and all associated data.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    name = assessment.name
    db.delete(assessment)
    db.commit()

    logger.info(f"ASSESSMENT_DELETED: id={assessment_id} name='{name}'")
    return None


@router.get("/{assessment_id}/summary", response_model=AssessmentSummary)
async def get_assessment_summary(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get assessment summary with finding counts.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    # Count findings by severity
    findings_query = db.query(Finding).filter(Finding.assessment_id == assessment_id)

    target_name = None
    if assessment.target_id:
        target = db.query(Target).filter(Target.id == assessment.target_id).first()
        if target:
            target_name = target.name

    return AssessmentSummary(
        id=assessment.id,
        name=assessment.name,
        target_id=assessment.target_id,
        target_name=target_name,
        target_url=assessment.target_url,
        environment=assessment.environment,
        status=assessment.status,
        progress=assessment.progress,
        findings_count=findings_query.count(),
        critical_count=findings_query.filter(Finding.severity == Severity.CRITICAL).count(),
        high_count=findings_query.filter(Finding.severity == Severity.HIGH).count(),
        medium_count=findings_query.filter(Finding.severity == Severity.MEDIUM).count(),
        low_count=findings_query.filter(Finding.severity == Severity.LOW).count(),
        created_at=assessment.created_at
    )
