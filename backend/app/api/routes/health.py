"""
Production health and readiness check endpoints for AegisScan.
Verifies system status, database connectivity, and report storage writeability.
"""

from fastapi import APIRouter, status
from datetime import datetime
from pathlib import Path
from loguru import logger
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Liveness probe endpoint.
    Returns basic application metadata.
    """
    return {
        "status": "healthy",
        "service": "AegisScan API",
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness probe endpoint for load balancers and orchestrators.
    Verifies database connection and report storage filesystem writeability.
    """
    db_status = "ready"
    storage_status = "ready"
    overall_status = "ready"

    # 1. Check Database connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as db_err:
        logger.error(f"HEALTH_CHECK_DB_FAILED: {db_err}")
        db_status = f"error: {str(db_err)}"
        overall_status = "not_ready"

    # 2. Check Storage writeability
    try:
        reports_dir = Path(settings.reports_dir or "./reports").resolve()
        reports_dir.mkdir(parents=True, exist_ok=True)
        test_file = reports_dir / ".health_check.tmp"
        test_file.write_text("ok", encoding="utf-8")
        if test_file.exists():
            test_file.unlink()
    except Exception as st_err:
        logger.error(f"HEALTH_CHECK_STORAGE_FAILED: {st_err}")
        storage_status = f"error: {str(st_err)}"
        overall_status = "not_ready"

    return {
        "status": overall_status,
        "database": db_status,
        "storage": storage_status,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat()
    }
