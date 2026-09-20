"""
Pydantic schemas for Scan Jobs and Scan Planning.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.scan_job import ScanJobStatus, ScanJobPriority, ScannerEngineType


class ScanJobCreate(BaseModel):
    """Schema for manually creating a scan job."""
    scanner: ScannerEngineType
    target: str
    priority: ScanJobPriority = ScanJobPriority.NORMAL
    configuration: Optional[Dict[str, Any]] = None


class ScanJobUpdate(BaseModel):
    """Schema for updating a scan job state or priority."""
    status: Optional[ScanJobStatus] = None
    priority: Optional[ScanJobPriority] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    error: Optional[str] = None


class ScanJobResponse(BaseModel):
    """Representation of a Scan Job."""
    id: int
    assessment_id: int
    scanner: ScannerEngineType
    target: str
    status: ScanJobStatus
    priority: ScanJobPriority
    progress: int
    configuration: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    result_location: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScanJobListResponse(BaseModel):
    """List of scan jobs."""
    total: int
    items: List[ScanJobResponse]


class ScanPlanRequest(BaseModel):
    """Request to generate scan plan for an assessment."""
    override_existing: bool = False
    priority: ScanJobPriority = ScanJobPriority.NORMAL


class ScanPlanResponse(BaseModel):
    """Response describing generated scan plan jobs."""
    assessment_id: int
    planned_jobs_count: int
    jobs: List[ScanJobResponse]
    message: str
