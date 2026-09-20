"""
Target schemas for API request and response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.models.target import TargetType, TargetEnvironment, AuthorizationStatus, TargetStatus
from app.utils.security_validation import validate_url, validate_and_sanitize_path


class TargetBase(BaseModel):
    """Base schema for Target."""
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable name of the target")
    description: Optional[str] = Field(None, max_length=2000, description="Optional target description")
    target_type: TargetType = Field(default=TargetType.WEB, description="Target type: web, source_code, repository, local_application")
    base_url: Optional[str] = Field(None, max_length=500, description="Base URL for web targets")
    source_path: Optional[str] = Field(None, max_length=500, description="Filesystem source path for SAST")
    repository_path: Optional[str] = Field(None, max_length=500, description="Git repository URL or local checkout path")
    environment: TargetEnvironment = Field(default=TargetEnvironment.LOCAL, description="Deployment environment")
    authorization_status: AuthorizationStatus = Field(default=AuthorizationStatus.AUTHORIZED, description="Target authorization status")
    notes: Optional[str] = Field(None, max_length=2000, description="Operator security notes or compliance scope")
    status: TargetStatus = Field(default=TargetStatus.ACTIVE, description="Target lifecycle state")

    @field_validator("base_url")
    @classmethod
    def check_base_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            is_valid, err = validate_url(v)
            if not is_valid:
                raise ValueError(err)
        return v.strip() if v else v

    @field_validator("source_path", "repository_path")
    @classmethod
    def check_paths(cls, v: Optional[str]) -> Optional[str]:
        if v:
            is_valid, sanitized, err = validate_and_sanitize_path(v)
            if not is_valid:
                raise ValueError(err)
            return sanitized
        return v


class TargetCreate(TargetBase):
    """Schema for creating a new Target."""
    pass


class TargetUpdate(BaseModel):
    """Schema for updating an existing Target."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_type: Optional[TargetType] = None
    base_url: Optional[str] = Field(None, max_length=500)
    source_path: Optional[str] = Field(None, max_length=500)
    repository_path: Optional[str] = Field(None, max_length=500)
    environment: Optional[TargetEnvironment] = None
    authorization_status: Optional[AuthorizationStatus] = None
    notes: Optional[str] = None
    status: Optional[TargetStatus] = None

    @field_validator("base_url")
    @classmethod
    def check_base_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            is_valid, err = validate_url(v)
            if not is_valid:
                raise ValueError(err)
            return v.strip()
        return v

    @field_validator("source_path", "repository_path")
    @classmethod
    def check_paths(cls, v: Optional[str]) -> Optional[str]:
        if v:
            is_valid, sanitized, err = validate_and_sanitize_path(v)
            if not is_valid:
                raise ValueError(err)
            return sanitized
        return v


class TargetResponse(TargetBase):
    """Full Target response representation."""
    id: int
    created_at: datetime
    updated_at: datetime
    assessments_count: int = 0
    last_assessment_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class TargetSummary(BaseModel):
    """Summary representation for target selection lists."""
    id: int
    name: str
    target_type: TargetType
    environment: TargetEnvironment
    base_url: Optional[str]
    authorization_status: AuthorizationStatus
    status: TargetStatus
    assessments_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class TargetListResponse(BaseModel):
    """Paginated list of Targets."""
    total: int
    items: List[TargetResponse]
