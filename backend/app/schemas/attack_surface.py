"""
Pydantic schemas for Attack Surface Items and inventory.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.attack_surface import AttackSurfaceType, AttackSurfaceStatus


class AttackSurfaceItemBase(BaseModel):
    """Base attack surface item attributes."""
    type: AttackSurfaceType
    name: Optional[str] = None
    url: Optional[str] = Field(None, max_length=2000)
    method: Optional[str] = Field(None, max_length=10)
    path: Optional[str] = Field(None, max_length=1000)
    parameter: Optional[str] = Field(None, max_length=255)
    source: Optional[str] = None
    discovered_by: List[str] = Field(default_factory=list)
    status: AttackSurfaceStatus = AttackSurfaceStatus.ACTIVE
    risk_relevance: str = "medium"
    metadata: Optional[Dict[str, Any]] = None


class AttackSurfaceItemCreate(AttackSurfaceItemBase):
    """Schema for adding an attack surface item."""
    fingerprint: Optional[str] = None


class AttackSurfaceItemResponse(AttackSurfaceItemBase):
    """Full Attack Surface Item response schema."""
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="item_metadata")
    id: int
    assessment_id: int
    fingerprint: str
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class AttackSurfaceSummary(BaseModel):
    """Aggregated metrics of the attack surface inventory."""
    total_assets: int = 0
    urls_count: int = 0
    apis_count: int = 0
    endpoints_count: int = 0
    parameters_count: int = 0
    javascript_count: int = 0
    forms_count: int = 0
    technologies_count: int = 0
    assets_count: int = 0
    services_count: int = 0
    by_risk: Dict[str, int] = Field(default_factory=lambda: {"high": 0, "medium": 0, "low": 0})
    by_source: Dict[str, int] = Field(default_factory=dict)


class AttackSurfaceListResponse(BaseModel):
    """Paginated list of attack surface items with summary statistics."""
    total: int
    items: List[AttackSurfaceItemResponse]
    summary: AttackSurfaceSummary
