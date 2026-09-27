"""
Database configuration, connection pooling, and session management for AegisScan.
Supports SQLite for lightweight local development and PostgreSQL for production deployments.
"""

import re
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

from app.core.config import settings

# Normalize postgres:// to postgresql:// for SQLAlchemy 2.0+ compatibility
db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine_kwargs = {"echo": settings.debug}

if "sqlite" in db_url:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production PostgreSQL Connection Pooling
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })

# Create database engine
engine = create_engine(db_url, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and synchronize schemas."""
    from app.models.user import User  # noqa: F401
    from app.models.target import Target  # noqa: F401
    from app.models.assessment import Assessment  # noqa: F401
    from app.models.attack_surface import AttackSurfaceItem  # noqa: F401
    from app.models.discovery_run import DiscoveryRun  # noqa: F401
    from app.models.scan_job import ScanJob  # noqa: F401
    from app.models.scan import Scan  # noqa: F401
    from app.models.finding import Finding  # noqa: F401
    from app.models.asset import Asset  # noqa: F401
    from app.models.report import Report  # noqa: F401
    from app.models.verification import Verification  # noqa: F401
    from app.models.remediation import Remediation, RemediationHistory  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_existing_schema()


def _ensure_existing_schema():
    """Add dynamic fields to existing SQLite/Postgres schemas without data loss."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if "findings" not in tables:
            return

        columns = {
            "findings": {
                "scan_job_id": "INTEGER",
                "source_scanners": "TEXT",
                "evidence_type": "VARCHAR(50)",
                "impact": "TEXT",
                "verification_reason": "TEXT",
                "reproducibility": "VARCHAR(50)",
                "verified_at": "DATETIME",
                "last_verified_at": "DATETIME",
                "risk_level": "VARCHAR(20)",
                "priority": "VARCHAR(20)",
                "exposure": "VARCHAR(30) DEFAULT 'UNKNOWN'",
                "risk_explanation": "TEXT",
            },
            "verifications": {
                "old_status": "VARCHAR(50)",
                "new_status": "VARCHAR(50)",
                "reason": "TEXT",
                "source": "VARCHAR(100)",
            },
            "reports": {
                "title": "VARCHAR(255)",
                "report_version": "VARCHAR(20) DEFAULT '1.0'",
                "generated_by": "VARCHAR(100) DEFAULT 'AegisScan'",
                "generated_at": "DATETIME",
                "error": "TEXT",
                "content_hash": "VARCHAR(64)",
            },
        }

        with engine.begin() as connection:
            for table, additions in columns.items():
                if table in tables:
                    existing = {column["name"] for column in inspector.get_columns(table)}
                    for name, definition in additions.items():
                        if name not in existing:
                            try:
                                connection.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {definition}'))
                            except Exception as alter_err:
                                logger.debug(f"Column {name} migration notice: {alter_err}")
    except Exception as e:
        logger.debug(f"Schema check notice: {e}")
