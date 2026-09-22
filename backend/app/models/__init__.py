"""
Database models package for AegisScan.
"""

from app.models.target import Target, TargetType, TargetEnvironment, AuthorizationStatus, TargetStatus
from app.models.assessment import Assessment, AssessmentStatus, AssessmentEnvironment
from app.models.attack_surface import AttackSurfaceItem, AttackSurfaceType, AttackSurfaceStatus
from app.models.discovery_run import DiscoveryRun, DiscoveryStatus
from app.models.scan_job import (
    ScanJob,
    ScanJobStatus,
    ScanJobPriority,
    ScannerEngineType,
    VALID_JOB_TRANSITIONS,
    validate_job_transition
)
from app.models.scan import Scan, ScanStatus, ScannerType
from app.models.finding import Finding, Severity, VerificationStatus, FindingStatus, FindingCategory, FindingPriority, Exposure
from app.models.asset import Asset, AssetType
from app.models.report import Report, ReportFormat, ReportType
from app.models.verification import Verification, VerificationMethod, VerificationResult
from app.models.remediation import Remediation, RemediationHistory, RemediationStatus, RemediationEffort

__all__ = [
    "Target",
    "TargetType",
    "TargetEnvironment",
    "AuthorizationStatus",
    "TargetStatus",
    "Assessment",
    "AssessmentStatus",
    "AssessmentEnvironment",
    "AttackSurfaceItem",
    "AttackSurfaceType",
    "AttackSurfaceStatus",
    "DiscoveryRun",
    "DiscoveryStatus",
    "ScanJob",
    "ScanJobStatus",
    "ScanJobPriority",
    "ScannerEngineType",
    "VALID_JOB_TRANSITIONS",
    "validate_job_transition",
    "Scan",
    "ScanStatus",
    "ScannerType",
    "Finding",
    "Severity",
    "VerificationStatus",
    "FindingStatus",
    "FindingCategory",
    "FindingPriority",
    "Exposure",
    "Asset",
    "AssetType",
    "Report",
    "ReportFormat",
    "ReportType",
    "Verification",
    "VerificationMethod",
    "VerificationResult",
    "Remediation",
    "RemediationHistory",
    "RemediationStatus",
    "RemediationEffort",
]
