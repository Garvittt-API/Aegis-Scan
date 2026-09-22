"""
Finding model - represents a security finding from any scanner.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class Severity(str, enum.Enum):
    """Finding severity levels."""
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationStatus(str, enum.Enum):
    """Verification status of a finding."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    LIKELY = "likely"
    FALSE_POSITIVE = "false_positive"
    NOT_REPRODUCIBLE = "not_reproducible"


class FindingStatus(str, enum.Enum):
    """Status of a finding."""
    OPEN = "open"
    ACCEPTED_RISK = "accepted_risk"
    FIXED = "fixed"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"


class FindingPriority(str, enum.Enum):
    """Action priority derived from the transparent risk score."""
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Exposure(str, enum.Enum):
    """Known exposure of the affected component."""
    INTERNET_EXPOSED = "internet_exposed"
    NETWORK_EXPOSED = "network_exposed"
    LOCAL = "local"
    UNKNOWN = "unknown"


class FindingCategory(str, enum.Enum):
    """Category of security finding."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SESSION_SECURITY = "session_security"
    API_SECURITY = "api_security"
    INPUT_VALIDATION = "input_validation"
    CLIENT_SECURITY = "client_security"
    COMMUNICATIONS = "communications"
    DATA_PRIVACY = "data_privacy"
    CONFIGURATION = "configuration"
    SECRETS = "secrets"
    DEPENDENCY = "dependency"
    OTHER = "other"


class Finding(Base):
    """
    Unified Finding model.
    Represents a security finding from any scanner, normalized.
    """
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id", ondelete="SET NULL"), nullable=True, index=True)

    # Core information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(SQLEnum(Severity), default=Severity.MEDIUM)
    confidence = Column(Float, default=0.5)  # 0.0 - 1.0
    category = Column(SQLEnum(FindingCategory), default=FindingCategory.OTHER)

    # Source information
    scanner = Column(String(100), nullable=False)  # zap, nuclei, semgrep, etc.
    scanner_id = Column(String(255), nullable=True)  # Original scanner finding ID
    source_scanners = Column(Text, nullable=True)  # JSON list of contributing scanners

    # Classification
    cwe = Column(String(50), nullable=True)  # CWE identifier
    cvss_score = Column(Float, nullable=True)  # CVSS score 0.0 - 10.0
    cvss_vector = Column(String(100), nullable=True)

    # Location
    endpoint = Column(String(1000), nullable=True)
    method = Column(String(10), nullable=True)
    parameter = Column(String(255), nullable=True)
    source_file = Column(String(500), nullable=True)
    source_line = Column(Integer, nullable=True)

    # Evidence
    evidence = Column(Text, nullable=True)
    evidence_type = Column(String(50), nullable=True)
    raw_output = Column(Text, nullable=True)

    # Verification
    verification_status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.UNVERIFIED)
    verification_evidence = Column(Text, nullable=True)
    verification_reason = Column(Text, nullable=True)
    reproducibility = Column(String(50), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)

    # Status
    status = Column(SQLEnum(FindingStatus), default=FindingStatus.OPEN)

    # Risk
    risk_score = Column(Float, nullable=True)  # Calculated risk score
    risk_level = Column(SQLEnum(FindingPriority), nullable=True)
    priority = Column(SQLEnum(FindingPriority), nullable=True)
    exposure = Column(SQLEnum(Exposure), default=Exposure.UNKNOWN, nullable=False)
    risk_explanation = Column(Text, nullable=True)

    # Remediation
    remediation = Column(Text, nullable=True)
    references = Column(Text, nullable=True)  # JSON array of reference URLs
    impact = Column(Text, nullable=True)

    # Deduplication
    fingerprint = Column(String(64), nullable=True, index=True)  # SHA256 hash for dedup
    duplicate_of = Column(Integer, ForeignKey("findings.id"), nullable=True)

    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assessment = relationship("Assessment", back_populates="findings")
    scan_job = relationship("ScanJob")
    verifications = relationship("Verification", back_populates="finding", cascade="all, delete-orphan")
    remediations = relationship("Remediation", back_populates="finding", cascade="all, delete-orphan")
    duplicates = relationship("Finding", foreign_keys=[duplicate_of])

    def __repr__(self):
        return f"<Finding(id={self.id}, title='{self.title[:50]}...', severity={self.severity})>"

    @property
    def cvss(self):
        """Compatibility alias for the public finding contract."""
        return self.cvss_score
