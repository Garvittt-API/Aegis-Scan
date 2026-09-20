"""
Assessment schemas for API validation and scan configuration.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

from app.models.assessment import AssessmentStatus, AssessmentEnvironment
from app.utils.security_validation import validate_url, validate_and_sanitize_path


class AssessmentScopeConfig(BaseModel):
    """Scope configuration for what parts of the target are assessed."""
    web_application: bool = True
    apis: bool = True
    client_side: bool = True
    source_code: bool = True
    dependencies: bool = True
    configuration: bool = True


class AssessmentModuleConfig(BaseModel):
    """Scanner modules configuration."""
    dast: bool = True
    nuclei: bool = True
    sast: bool = True
    sca: bool = True
    custom_checks: bool = True


class AssessmentScanSettings(BaseModel):
    """Safe scan configuration settings."""
    rate_limit: str = Field(default="low", pattern="^(low|medium|high)$")
    crawl_depth: int = Field(default=2, ge=1, le=5)
    timeout: int = Field(default=60, ge=10, le=300)
    follow_redirects: bool = True
    passive_checks: bool = True
    active_testing: bool = False  # Conservative safe default


class AssessmentBase(BaseModel):
    """Base assessment fields."""
    name: str = Field(..., min_length=1, max_length=255)
    target_id: Optional[int] = None
    description: Optional[str] = None
    target_url: Optional[str] = Field(None, max_length=500)
    source_path: Optional[str] = Field(None, max_length=500)
    environment: AssessmentEnvironment = AssessmentEnvironment.LOCAL
    authorization_confirmed: bool = False
    created_by: str = "analyst"

    # Module toggles (synced for backward compatibility)
    enable_zap: bool = True
    enable_nuclei: bool = True
    enable_semgrep: bool = True
    enable_dependency_check: bool = True
    enable_custom_checks: bool = True

    # Phase 2 Detailed Configurations
    scope: Optional[AssessmentScopeConfig] = Field(default_factory=AssessmentScopeConfig)
    modules: Optional[AssessmentModuleConfig] = Field(default_factory=AssessmentModuleConfig)
    scan_settings: Optional[AssessmentScanSettings] = Field(default_factory=AssessmentScanSettings)

    @field_validator("target_url")
    @classmethod
    def check_target_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            is_valid, err = validate_url(v)
            if not is_valid:
                raise ValueError(err)
            return v.strip()
        return v

    @field_validator("source_path")
    @classmethod
    def check_source_path(cls, v: Optional[str]) -> Optional[str]:
        if v:
            is_valid, sanitized, err = validate_and_sanitize_path(v)
            if not is_valid:
                raise ValueError(err)
            return sanitized
        return v


class AssessmentCreate(AssessmentBase):
    """Schema for creating a new assessment."""
    pass


class AssessmentUpdate(BaseModel):
    """Schema for updating an assessment."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    target_id: Optional[int] = None
    description: Optional[str] = None
    target_url: Optional[str] = Field(None, max_length=500)
    source_path: Optional[str] = Field(None, max_length=500)
    environment: Optional[AssessmentEnvironment] = None
    authorization_confirmed: Optional[bool] = None
    status: Optional[AssessmentStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    current_phase: Optional[str] = None
    scope: Optional[AssessmentScopeConfig] = None
    modules: Optional[AssessmentModuleConfig] = None
    scan_settings: Optional[AssessmentScanSettings] = None

    @field_validator("target_url")
    @classmethod
    def check_target_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            is_valid, err = validate_url(v)
            if not is_valid:
                raise ValueError(err)
            return v.strip()
        return v

    @field_validator("source_path")
    @classmethod
    def check_source_path(cls, v: Optional[str]) -> Optional[str]:
        if v:
            is_valid, sanitized, err = validate_and_sanitize_path(v)
            if not is_valid:
                raise ValueError(err)
            return sanitized
        return v


class AssessmentResponse(AssessmentBase):
    """Schema for assessment response."""
    id: int
    status: AssessmentStatus
    progress: int
    current_phase: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    target_name: Optional[str] = None

    class Config:
        from_attributes = True


class AssessmentSummary(BaseModel):
    """Summary of an assessment with finding counts."""
    id: int
    name: str
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    target_url: Optional[str] = None
    environment: AssessmentEnvironment
    status: AssessmentStatus
    progress: int
    findings_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    created_at: datetime


class AssessmentListResponse(BaseModel):
    """Paginated list of assessments."""
    total: int
    items: List[AssessmentResponse]


class AssessmentValidationResult(BaseModel):
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    safety_checks: Dict[str, bool] = {}
    recommendations: List[str] = []
