"""
Health check endpoint.
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns basic system status.
    """
    return {
        "status": "healthy",
        "service": "AegisScan API",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Verifies database and other dependencies are ready.
    """
    from app.core.database import engine
    from sqlalchemy import text

    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ready"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ready" if db_status == "ready" else "not_ready",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }
