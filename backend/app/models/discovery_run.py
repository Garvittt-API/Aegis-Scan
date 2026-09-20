"""
Discovery Run model - tracks an execution of attack surface discovery.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class DiscoveryStatus(str, enum.Enum):
    """Execution status of a discovery run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DiscoveryRun(Base):
    """
    Tracks a discovery execution session for an assessment.
    """
    __tablename__ = "discovery_runs"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status & Progress
    status = Column(SQLEnum(DiscoveryStatus), default=DiscoveryStatus.PENDING, nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=False)  # 0 to 100 percentage
    
    # Metrics
    discovered_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    
    # Configuration & Details
    configuration = Column(JSON, nullable=True)  # Snapshot of crawler depth, rate limits, modules
    logs = Column(JSON, default=list, nullable=False)  # Chronological execution log messages
    error_message = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assessment = relationship("Assessment", back_populates="discovery_runs")

    def __repr__(self):
        return f"<DiscoveryRun(id={self.id}, assessment_id={self.assessment_id}, status='{self.status}', discovered={self.discovered_count})>"
