"""
Database configuration and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,
)

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
    """Initialize database tables."""
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

    Base.metadata.create_all(bind=engine)
