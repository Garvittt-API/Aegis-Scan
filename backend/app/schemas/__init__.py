"""
Pydantic schemas for API request/response validation.
"""

from app.schemas.target import (
    TargetCreate,
    TargetUpdate,
    TargetResponse,
    TargetListResponse,
    TargetSummary
)
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentResponse,
    AssessmentListResponse,
    AssessmentSummary,
    AssessmentScopeConfig,
    AssessmentModuleConfig,
    AssessmentScanSettings,
    AssessmentValidationResult
)
from app.schemas.attack_surface import (
    AttackSurfaceItemCreate,
    AttackSurfaceItemResponse,
    AttackSurfaceSummary,
    AttackSurfaceListResponse
)
from app.schemas.discovery_run import (
    DiscoveryStartRequest,
    DiscoveryRunResponse,
    DiscoveryRunListResponse
)
from app.schemas.scan_job import (
    ScanJobCreate,
    ScanJobUpdate,
    ScanJobResponse,
    ScanJobListResponse,
    ScanPlanRequest,
    ScanPlanResponse
)
from app.schemas.finding import (
    FindingCreate,
    FindingResponse,
    FindingListResponse
)
from app.schemas.asset import (
    AssetCreate,
    AssetResponse,
    AssetListResponse
)

__all__ = [
    # Target schemas
    "TargetCreate",
    "TargetUpdate",
    "TargetResponse",
    "TargetListResponse",
    "TargetSummary",
    # Assessment schemas
    "AssessmentCreate",
    "AssessmentUpdate",
    "AssessmentResponse",
    "AssessmentListResponse",
    "AssessmentSummary",
    "AssessmentScopeConfig",
    "AssessmentModuleConfig",
    "AssessmentScanSettings",
    "AssessmentValidationResult",
    # Attack Surface schemas
    "AttackSurfaceItemCreate",
    "AttackSurfaceItemResponse",
    "AttackSurfaceSummary",
    "AttackSurfaceListResponse",
    # Discovery Run schemas
    "DiscoveryStartRequest",
    "DiscoveryRunResponse",
    "DiscoveryRunListResponse",
    # Scan Job schemas
    "ScanJobCreate",
    "ScanJobUpdate",
    "ScanJobResponse",
    "ScanJobListResponse",
    "ScanPlanRequest",
    "ScanPlanResponse",
    # Finding schemas
    "FindingCreate",
    "FindingResponse",
    "FindingListResponse",
    # Asset schemas
    "AssetCreate",
    "AssetResponse",
    "AssetListResponse",
]
