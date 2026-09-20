"""
Target model - represents a target system to be assessed.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TargetType(str, enum.Enum):
    """Supported target types."""
    WEB = "web"
    SOURCE_CODE = "source_code"
    REPOSITORY = "repository"
    LOCAL_APPLICATION = "local_application"


class TargetEnvironment(str, enum.Enum):
    """Target deployment environment."""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"
    AUTHORIZED_REMOTE = "authorized_remote"


class AuthorizationStatus(str, enum.Enum):
    """Authorization verification status."""
    AUTHORIZED = "authorized"
    PENDING = "pending"
    UNAUTHORIZED = "unauthorized"


class TargetStatus(str, enum.Enum):
    """Target lifecycle status."""
    ACTIVE = "active"
    ARCHIVED = "archived"


class Target(Base):
    """
    Target model representing an application, repository or environment to be assessed.
    """
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    target_type = Column(SQLEnum(TargetType), default=TargetType.WEB, nullable=False)
    
    # Location fields
    base_url = Column(String(500), nullable=True)
    source_path = Column(String(500), nullable=True)
    repository_path = Column(String(500), nullable=True)
    
    # Environment & Authorization
    environment = Column(SQLEnum(TargetEnvironment), default=TargetEnvironment.LOCAL, nullable=False)
    authorization_status = Column(SQLEnum(AuthorizationStatus), default=AuthorizationStatus.AUTHORIZED, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(SQLEnum(TargetStatus), default=TargetStatus.ACTIVE, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assessments = relationship("Assessment", back_populates="target", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Target(id={self.id}, name='{self.name}', type='{self.target_type}', env='{self.environment}')>"
