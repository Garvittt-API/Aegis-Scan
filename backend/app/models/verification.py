"""
Verification model - represents verification of a finding.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class VerificationResult(str, enum.Enum):
    """Result of finding verification."""
    VERIFIED = "verified"
    LIKELY = "likely"
    UNVERIFIED = "unverified"
    FALSE_POSITIVE = "false_positive"
    NOT_REPRODUCIBLE = "not_reproducible"


# Backward-compatible export retained by the model package initializer.
VerificationMethod = VerificationResult


class Verification(Base):
    """
    Finding verification model.
    Represents an attempt to verify a security finding.
    """
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id"), nullable=False)
    result = Column(SQLEnum(VerificationResult), default=VerificationResult.UNVERIFIED)

    # Verification details
    evidence = Column(Text, nullable=True)
    request = Column(Text, nullable=True)  # HTTP request used for verification
    response = Column(Text, nullable=True)  # HTTP response received
    notes = Column(Text, nullable=True)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)

    # Timestamps
    verified_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    finding = relationship("Finding", back_populates="verifications")

    def __repr__(self):
        return f"<Verification(id={self.id}, result={self.result})>"
