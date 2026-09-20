"""
Scan Job model - represents a planned, queued or executing security scanner job.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ScanJobStatus(str, enum.Enum):
    """Execution status of a scan job."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NOT_IMPLEMENTED = "not_implemented"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"


class ScanJobPriority(str, enum.Enum):
    """Job execution priority."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class ScannerEngineType(str, enum.Enum):
    """Supported scanner engines."""
    ZAP = "zap"
    NUCLEI = "nuclei"
    SEMGREP = "semgrep"
    SCA = "sca"
    CUSTOM = "custom"


# Valid state transitions for the ScanJob state machine
VALID_JOB_TRANSITIONS = {
    ScanJobStatus.PENDING: {ScanJobStatus.QUEUED, ScanJobStatus.RUNNING, ScanJobStatus.CANCELLED, ScanJobStatus.UNAVAILABLE, ScanJobStatus.NOT_IMPLEMENTED},
    ScanJobStatus.QUEUED: {ScanJobStatus.RUNNING, ScanJobStatus.CANCELLED, ScanJobStatus.UNAVAILABLE, ScanJobStatus.NOT_IMPLEMENTED},
    ScanJobStatus.RUNNING: {ScanJobStatus.COMPLETED, ScanJobStatus.FAILED, ScanJobStatus.CANCELLED, ScanJobStatus.UNAVAILABLE, ScanJobStatus.TIMEOUT},
    ScanJobStatus.NOT_IMPLEMENTED: set(),  # Terminal state for Phase 3 stubs
    ScanJobStatus.UNAVAILABLE: set(),      # Terminal state when tool missing
    ScanJobStatus.TIMEOUT: set(),          # Terminal state when execution times out
    ScanJobStatus.COMPLETED: set(),        # Terminal state
    ScanJobStatus.FAILED: set(),           # Terminal state
    ScanJobStatus.CANCELLED: set()         # Terminal state
}


def validate_job_transition(current_status: ScanJobStatus, target_status: ScanJobStatus) -> bool:
    """
    Validate if a state transition is permitted by the job state machine.
    """
    if current_status == target_status:
        return True
    return target_status in VALID_JOB_TRANSITIONS.get(current_status, set())


class ScanJob(Base):
    """
    Represents a planned, queued, or running scanner job.
    """
    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Engine & Target
    scanner = Column(SQLEnum(ScannerEngineType), nullable=False, index=True)
    target = Column(String(500), nullable=False)
    
    # Lifecycle & Priority
    status = Column(SQLEnum(ScanJobStatus), default=ScanJobStatus.PENDING, nullable=False, index=True)
    priority = Column(SQLEnum(ScanJobPriority), default=ScanJobPriority.NORMAL, nullable=False)
    progress = Column(Integer, default=0, nullable=False)  # 0 to 100 percentage
    
    # Configuration & Outputs
    configuration = Column(JSON, nullable=True)  # Prepared scanner parameters
    error = Column(Text, nullable=True)
    logs = Column(JSON, default=list, nullable=False)
    result_location = Column(String(500), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assessment = relationship("Assessment", back_populates="scan_jobs")

    __table_args__ = (
        Index("idx_assessment_scanner_status", "assessment_id", "scanner", "status"),
    )

    def transition_to(self, new_status: ScanJobStatus) -> bool:
        """
        Attempt a state transition according to the state machine rules.
        """
        if not validate_job_transition(self.status, new_status):
            raise ValueError(f"Invalid scan job transition: Cannot move from {self.status.value} to {new_status.value}")
        self.status = new_status
        return True

    def __repr__(self):
        return f"<ScanJob(id={self.id}, scanner='{self.scanner}', status='{self.status}', priority='{self.priority}')>"
