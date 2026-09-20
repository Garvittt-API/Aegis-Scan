"""
Finding schemas for API validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.finding import Severity, FindingStatus, VerificationStatus


class FindingBase(BaseModel):
    """Base finding fields."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    severity: Severity = Severity.MEDIUM
    confidence: int = Field(50, ge=0, le=100)
    category: str = Field(..., max_length=100)
    scanner: str = Field(..., max_length=100)
    endpoint: Optional[str] = Field(None, max_length=500)
    method: Optional[str] = Field(None, max_length=10)
    parameter: Optional[str] = Field(None, max_length=200)
    evidence: Optional[str] = None
    cwe: Optional[str] = Field(None, max_length=20)
    cvss: Optional[float] = Field(None, ge=0.0, le=10.0)


class FindingCreate(FindingBase):
    """Schema for creating a new finding."""
    assessment_id: int


class FindingResponse(FindingBase):
    """Schema for finding response."""
    id: int
    assessment_id: int
    verification_status: VerificationStatus
    status: FindingStatus
    fingerprint: Optional[str]
    duplicate_of: Optional[int]
    remediation: Optional[str]
    references: Optional[str]
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class FindingListResponse(BaseModel):
    """Paginated list of findings."""
    total: int
    items: list[FindingResponse]


class FindingUpdate(BaseModel):
    """Schema for updating a finding."""
    status: Optional[FindingStatus] = None
    verification_status: Optional[VerificationStatus] = None
    notes: Optional[str] = None
