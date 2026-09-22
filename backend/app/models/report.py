"""
Report model - represents a generated assessment report.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ReportFormat(str, enum.Enum):
    """Report output formats."""
    HTML = "html"
    PDF = "pdf"
    JSON = "json"


# Backward-compatible name used by the model package exports.
ReportType = ReportFormat


class ReportStatus(str, enum.Enum):
    """Report generation status."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    """
    Generated assessment report model.
    """
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    format = Column(SQLEnum(ReportFormat), nullable=False)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING)
    title = Column(String(255), nullable=True)
    report_version = Column(String(20), default="1.0", nullable=False)
    generated_by = Column(String(100), default="AegisScan", nullable=False)
    generated_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)

    # File information
    file_path = Column(String(1000), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    assessment = relationship("Assessment", back_populates="reports")

    def __repr__(self):
        return f"<Report(id={self.id}, format={self.format}, status={self.status})>"

    @property
    def file_size(self):
        return self.file_size_bytes
