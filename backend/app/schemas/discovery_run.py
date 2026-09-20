"""
Pydantic schemas for Discovery Runs.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.discovery_run import DiscoveryStatus


class DiscoveryStartRequest(BaseModel):
    """Parameters for launching a discovery run."""
    enable_crawler: bool = True
    enable_endpoint_discovery: bool = True
    enable_technology_detection: bool = True
    max_pages: Optional[int] = Field(None, ge=5, le=100)
    crawl_depth: Optional[int] = Field(None, ge=1, le=5)
    rate_limit: Optional[str] = Field(None, pattern="^(low|medium|high)$")


class DiscoveryRunResponse(BaseModel):
    """Full DiscoveryRun representation."""
    id: int
    assessment_id: int
    status: DiscoveryStatus
    progress: int
    discovered_count: int
    error_count: int
    configuration: Optional[Dict[str, Any]] = None
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DiscoveryRunListResponse(BaseModel):
    """List of discovery runs for an assessment."""
    total: int
    items: List[DiscoveryRunResponse]
