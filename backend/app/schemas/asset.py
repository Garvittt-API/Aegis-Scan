"""
Asset schemas for API validation.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class AssetBase(BaseModel):
    """Base asset fields."""
    asset_type: str = Field(..., max_length=50)
    url: str = Field(..., max_length=1000)
    method: Optional[str] = Field(None, max_length=10)
    metadata: Optional[dict[str, Any]] = None
    risk_relevance: Optional[str] = Field(None, max_length=50)
    source: Optional[str] = Field(None, max_length=100)


class AssetCreate(AssetBase):
    """Schema for creating a new asset."""
    assessment_id: int


class AssetResponse(AssetBase):
    """Schema for asset response."""
    id: int
    assessment_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    """Paginated list of assets."""
    total: int
    items: list[AssetResponse]
