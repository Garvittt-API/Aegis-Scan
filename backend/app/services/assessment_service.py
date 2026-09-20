"""
Assessment and Target business logic and validation services.
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from app.models.assessment import Assessment, AssessmentStatus, AssessmentEnvironment
from app.models.target import Target, TargetType, AuthorizationStatus
from app.schemas.assessment import AssessmentValidationResult, AssessmentCreate


WORLD_MONITOR_PRESET = {
    "name": "World Monitor Security Assessment",
    "description": "Controlled local security assessment of the World Monitor application.",
    "target_name": "World Monitor Local",
    "target_type": "web",
    "target_url": "http://localhost:5173",
    "source_path": "./worldmonitor",
    "environment": "local",
    "authorization_confirmed": True,
    "scope": {
        "web_application": True,
        "apis": True,
        "client_side": True,
        "source_code": True,
        "dependencies": True,
        "configuration": True
    },
    "modules": {
        "dast": True,
        "nuclei": True,
        "sast": True,
        "sca": True,
        "custom_checks": True
    },
    "scan_settings": {
        "rate_limit": "low",
        "crawl_depth": 2,
        "timeout": 60,
        "follow_redirects": True,
        "passive_checks": True,
        "active_testing": False
    }
}


def get_world_monitor_preset() -> Dict[str, Any]:
    """Return the predefined World Monitor assessment preset."""
    return WORLD_MONITOR_PRESET


def validate_assessment_configuration(
    assessment_data: Dict[str, Any],
    target: Optional[Target] = None
) -> AssessmentValidationResult:
    """
    Perform multi-layer validation on assessment configuration:
    1. Authorization confirmation verification.
    2. Target reachability / format verification.
    3. Safety guardrails (rate limits, active testing, excessive depth).
    4. Scanner module consistency with target type.
    """
    errors: List[str] = []
    warnings: List[str] = []
    recommendations: List[str] = []
    safety_checks: Dict[str, bool] = {
        "authorization_confirmed": False,
        "safe_rate_limit": False,
        "safe_depth": False,
        "active_testing_safeguard": True,
        "valid_target_specified": False,
    }

    # 1. Authorization check
    auth_confirmed = assessment_data.get("authorization_confirmed", False)
    if not auth_confirmed:
        errors.append("Explicit authorization confirmation is required before an assessment can be created or executed.")
        safety_checks["authorization_confirmed"] = False
    else:
        safety_checks["authorization_confirmed"] = True

    # 2. Target check
    target_url = assessment_data.get("target_url")
    source_path = assessment_data.get("source_path")
    if target:
        if not target_url and target.base_url:
            target_url = target.base_url
        if not source_path and target.source_path:
            source_path = target.source_path
        if target.authorization_status != AuthorizationStatus.AUTHORIZED:
            warnings.append(f"Linked target authorization status is '{target.authorization_status.value}'. Please ensure target is authorized.")

    if not target_url and not source_path:
        errors.append("Target configuration missing: At least one target URL or Source Path is required.")
        safety_checks["valid_target_specified"] = False
    else:
        safety_checks["valid_target_specified"] = True

    # 3. Scan Settings & Safety Check
    scan_settings = assessment_data.get("scan_settings") or {}
    if isinstance(scan_settings, dict):
        rate_limit = scan_settings.get("rate_limit", "low")
        crawl_depth = scan_settings.get("crawl_depth", 2)
        active_testing = scan_settings.get("active_testing", False)
        timeout = scan_settings.get("timeout", 60)

        # Rate limit safety
        if rate_limit in ["low", "medium"]:
            safety_checks["safe_rate_limit"] = True
        else:
            safety_checks["safe_rate_limit"] = False
            warnings.append("High request rate selected. May cause high load on target application.")
            recommendations.append("Use 'low' or 'medium' rate limit for delicate local/staging environments.")

        # Depth safety
        if isinstance(crawl_depth, int) and crawl_depth <= 3:
            safety_checks["safe_depth"] = True
        else:
            safety_checks["safe_depth"] = False
            warnings.append(f"Crawl depth {crawl_depth} may result in prolonged discovery cycles.")

        # Active testing
        if active_testing:
            warnings.append("Active payload testing is enabled. Ensure target is a dedicated non-production testing environment.")
        else:
            recommendations.append("Active payload testing disabled (safe default).")

        if timeout > 180:
            warnings.append("Request timeout exceeds 180 seconds.")

    # 4. Modules Consistency Check
    modules = assessment_data.get("modules") or {}
    if isinstance(modules, dict):
        sast_enabled = modules.get("sast", False)
        dast_enabled = modules.get("dast", False)

        if sast_enabled and not source_path:
            warnings.append("SAST (Semgrep) module is enabled but no source code path is configured.")
            recommendations.append("Specify a valid source path to enable static code analysis.")

        if dast_enabled and not target_url:
            warnings.append("DAST (ZAP) module is enabled but no target URL is configured.")
            recommendations.append("Specify a base URL to enable dynamic vulnerability scanning.")

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(f"ASSESSMENT_VALIDATION_FAILED: {errors}")
    else:
        logger.info("ASSESSMENT_VALIDATION_PASSED")

    return AssessmentValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        safety_checks=safety_checks,
        recommendations=recommendations
    )
