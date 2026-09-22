"""Structured, deterministic remediation guidance for findings."""
from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base

class RemediationStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    READY_FOR_VALIDATION = "ready_for_validation"
    VALIDATED = "validated"
    REJECTED = "rejected"
    NOT_APPLICABLE = "not_applicable"
    NOT_VALIDATED = "not_validated"
    INCONCLUSIVE = "inconclusive"

class RemediationEffort(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"

class Remediation(Base):
    __tablename__ = "remediations"
    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=False)
    technical_steps = Column(Text, nullable=True)
    code_guidance = Column(Text, nullable=True)
    configuration_guidance = Column(Text, nullable=True)
    dependency_guidance = Column(Text, nullable=True)
    verification_steps = Column(Text, nullable=True)
    priority = Column(String(20), nullable=True)
    estimated_effort = Column(SQLEnum(RemediationEffort), default=RemediationEffort.UNKNOWN)
    impact = Column(String(20), default="unknown")
    references = Column(Text, nullable=True)
    status = Column(SQLEnum(RemediationStatus), default=RemediationStatus.NOT_STARTED, nullable=False)
    validation_evidence = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    finding = relationship("Finding", back_populates="remediations")
    history = relationship("RemediationHistory", back_populates="remediation", cascade="all, delete-orphan")

class RemediationHistory(Base):
    __tablename__ = "remediation_history"
    id = Column(Integer, primary_key=True, index=True)
    remediation_id = Column(Integer, ForeignKey("remediations.id", ondelete="CASCADE"), nullable=False)
    event = Column(String(100), nullable=False)
    previous_status = Column(String(40), nullable=True)
    new_status = Column(String(40), nullable=True)
    reason = Column(Text, nullable=True)
    evidence_reference = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    remediation = relationship("Remediation", back_populates="history")
