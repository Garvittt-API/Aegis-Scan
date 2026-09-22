"""
Finding schemas for API validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.finding import Severity, FindingStatus, VerificationStatus, FindingPriority, Exposure


class FindingBase(BaseModel):
    """Base finding fields."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    severity: Severity = Severity.MEDIUM
    confidence: float = Field(0.5, ge=0.0, le=1.0)
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
    scan_job_id: Optional[int]
    source_scanners: Optional[str]
    evidence_type: Optional[str]
    source_file: Optional[str]
    source_line: Optional[int]
    raw_output: Optional[str]
    risk_score: Optional[float]
    risk_level: Optional[FindingPriority]
    priority: Optional[FindingPriority]
    exposure: Optional[Exposure]
    risk_explanation: Optional[str]
    verification_reason: Optional[str]
    reproducibility: Optional[str]
    verified_at: Optional[datetime]
    last_verified_at: Optional[datetime]
    verification_status: VerificationStatus
    status: FindingStatus
    fingerprint: Optional[str]
    duplicate_of: Optional[int]
    remediation: Optional[str]
    impact: Optional[str]
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


class FindingStatusUpdate(BaseModel):
    status: FindingStatus
    reason: Optional[str] = None


class RemediationResponse(BaseModel):
    id: int
    finding_id: int
    title: str
    summary: str
    explanation: Optional[str]
    recommended_action: str
    technical_steps: Optional[str]
    code_guidance: Optional[str]
    configuration_guidance: Optional[str]
    dependency_guidance: Optional[str]
    verification_steps: Optional[str]
    priority: Optional[str]
    estimated_effort: str
    impact: Optional[str]
    references: Optional[str]
    status: str
    validation_evidence: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RemediationUpdate(BaseModel):
    status: Optional[str] = None
    reason: Optional[str] = None
