"""
Asset model - represents a discovered asset in the attack surface.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class AssetType(str, enum.Enum):
    """Type of discovered asset."""
    PAGE = "page"
    ENDPOINT = "endpoint"
    API_ENDPOINT = "api_endpoint"
    JAVASCRIPT_FILE = "javascript_file"
    CSS_FILE = "css_file"
    IMAGE = "image"
    FORM = "form"
    PARAMETER = "parameter"
    COOKIE = "cookie"
    HEADER = "header"
    EXTERNAL_DOMAIN = "external_domain"
    TECHNOLOGY = "technology"
    CONFIG_FILE = "config_file"
    SOURCE_MAP = "source_map"


class Asset(Base):
    """
    Asset model.
    Represents a discovered asset in the application's attack surface.
    """
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)

    # Asset identification
    type = Column(SQLEnum(AssetType), nullable=False)
    url = Column(String(2000), nullable=True)
    path = Column(String(1000), nullable=True)
    method = Column(String(10), nullable=True)
    name = Column(String(500), nullable=True)

    # Discovery
    source = Column(String(100), nullable=True)  # How it was discovered: crawl, spider, etc.
    risk_relevance = Column(String(50), default="medium")  # low, medium, high

    # Additional data
    # SQLAlchemy reserves the attribute name ``metadata`` on declarative models.
    # Keep the database column/API payload name while using a safe Python attribute.
    metadata_ = Column("metadata", JSON, nullable=True)  # Flexible storage for additional info

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assessment = relationship("Assessment", back_populates="assets")

    def __repr__(self):
        return f"<Asset(id={self.id}, type={self.type}, path='{self.path}')>"
