"""
Attack Surface Item model - represents discovered attack surface components.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class AttackSurfaceType(str, enum.Enum):
    """Types of discovered attack surface items."""
    URL = "url"
    API = "api"
    ENDPOINT = "endpoint"
    PARAMETER = "parameter"
    JAVASCRIPT = "javascript"
    ASSET = "asset"
    SERVICE = "service"
    TECHNOLOGY = "technology"
    FORM = "form"


class AttackSurfaceStatus(str, enum.Enum):
    """Lifecycle status of an attack surface item."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AttackSurfaceItem(Base):
    """
    Attack surface item discovered during discovery phase.
    Supports deduplication, stable fingerprinting, and multi-source tracking.
    """
    __tablename__ = "attack_surface_items"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Identification & Fingerprinting
    fingerprint = Column(String(255), nullable=False, index=True)  # Hash / unique key for deduplication
    type = Column(SQLEnum(AttackSurfaceType), nullable=False, index=True)
    name = Column(String(500), nullable=True)
    
    # HTTP & Endpoint Details
    url = Column(String(2000), nullable=True, index=True)
    method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE, etc.
    path = Column(String(1000), nullable=True)
    parameter = Column(String(255), nullable=True)  # Specific parameter if type == parameter
    
    # Discovery provenance
    source = Column(String(100), nullable=True)  # Initial discovery vector: crawler, endpoints, tech, etc.
    discovered_by = Column(JSON, default=list, nullable=False)  # List of all discovering sources: ["crawler", "openapi"]
    
    # Status & Risk Relevance
    status = Column(SQLEnum(AttackSurfaceStatus), default=AttackSurfaceStatus.ACTIVE, nullable=False)
    risk_relevance = Column(String(50), default="medium")  # low, medium, high
    
    # Metadata & Timestamps
    item_metadata = Column("metadata", JSON, nullable=True)  # Renamed attribute to item_metadata, mapped to 'metadata' column
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assessment = relationship("Assessment", back_populates="attack_surface_items")

    __table_args__ = (
        Index("idx_assessment_fingerprint", "assessment_id", "fingerprint"),
        Index("idx_assessment_type", "assessment_id", "type"),
    )

    def __repr__(self):
        return f"<AttackSurfaceItem(id={self.id}, type='{self.type}', url='{self.url}', method='{self.method}')>"
