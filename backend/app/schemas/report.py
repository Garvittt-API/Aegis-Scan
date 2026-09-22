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
    status: str
    file_path: Optional[str]
    file_size: Optional[int]
    file_size_bytes: Optional[int] = None
    generated_at: Optional[datetime] = None
    report_version: str = "1.0"
    generated_by: str = "AegisScan"
    error: Optional[str] = None
    content_hash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for list of reports."""
    total: int
    items: List[ReportResponse]
