"""
Pydantic schemas for Report model.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.models.report import ReportFormat


class ReportBase(BaseModel):
    """Base schema for Report."""
    format: ReportFormat
    title: Optional[str] = None


class ReportCreate(ReportBase):
    """Schema for creating a Report."""
    assessment_id: int


class ReportResponse(ReportBase):
    """Schema for Report response."""
    id: int
    assessment_id: int
    file_path: Optional[str]
    file_size: Optional[int]
    generated_at: datetime
    generation_time_seconds: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for list of reports."""
    total: int
    items: List[ReportResponse]
