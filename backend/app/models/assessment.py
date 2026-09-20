"""
Assessment model - represents a security assessment project.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class AssessmentStatus(str, enum.Enum):
    """Status of an assessment."""
    DRAFT = "draft"
    CONFIGURED = "configured"
    PENDING = "pending"
    QUEUED = "queued"
    DISCOVERING = "discovering"
    SCANNING = "scanning"
    RUNNING = "running"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssessmentEnvironment(str, enum.Enum):
    """Target environment type."""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"
    AUTHORIZED_REMOTE = "authorized_remote"


class Assessment(Base):
    """
    Security Assessment model.
    Represents a complete security assessment project.
    """
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_url = Column(String(500), nullable=True)
    source_path = Column(String(500), nullable=True)
    environment = Column(SQLEnum(AssessmentEnvironment), default=AssessmentEnvironment.LOCAL)
    authorization_confirmed = Column(Boolean, default=False)
    status = Column(SQLEnum(AssessmentStatus), default=AssessmentStatus.CONFIGURED)
    progress = Column(Integer, default=0)  # 0-100 percentage
    current_phase = Column(String(100), nullable=True)
    created_by = Column(String(100), default="analyst")

    # Legacy & Quick toggles
    enable_zap = Column(Boolean, default=True)
    enable_nuclei = Column(Boolean, default=True)
    enable_semgrep = Column(Boolean, default=True)
    enable_dependency_check = Column(Boolean, default=True)
    enable_custom_checks = Column(Boolean, default=True)

    # Detailed Phase 2 Configuration
    scope = Column(JSON, nullable=True)
    modules = Column(JSON, nullable=True)
    scan_settings = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    target = relationship("Target", back_populates="assessments")
    scans = relationship("Scan", back_populates="assessment", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="assessment", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="assessment", cascade="all, delete-orphan")
    attack_surface_items = relationship("AttackSurfaceItem", back_populates="assessment", cascade="all, delete-orphan")
    discovery_runs = relationship("DiscoveryRun", back_populates="assessment", cascade="all, delete-orphan")
    scan_jobs = relationship("ScanJob", back_populates="assessment", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="assessment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Assessment(id={self.id}, name='{self.name}', status='{self.status}')>"
