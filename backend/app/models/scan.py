"""
Scan model - represents a single scanner execution.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ScanStatus(str, enum.Enum):
    """Status of a scanner execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ScannerType(str, enum.Enum):
    """Available scanner types."""
    ZAP = "zap"
    NUCLEI = "nuclei"
    SEMGREP = "semgrep"
    DEPENDENCY_CHECK = "dependency_check"
    CUSTOM = "custom"


class Scan(Base):
    """
    Scanner execution model.
    Represents a single run of a security scanner.
    """
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    scanner = Column(SQLEnum(ScannerType), nullable=False)
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100 percentage

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Results
    findings_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    output_path = Column(String(500), nullable=True)  # Path to raw scanner output

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assessment = relationship("Assessment", back_populates="scans")

    def __repr__(self):
        return f"<Scan(id={self.id}, scanner={self.scanner}, status={self.status})>"
