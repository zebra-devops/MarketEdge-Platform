from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid
import enum

from .base import Base
from .database_types import CompatibleUUID, CompatibleJSON


class FeatureFlagScope(str, enum.Enum):
    """Scope levels for feature flags"""
    GLOBAL = "global"           # Platform-wide
    ORGANISATION = "organisation"  # Organisation-specific
    SECTOR = "sector"           # Sector-specific (SIC code based)
    USER = "user"              # Individual user


class FeatureFlagStatus(str, enum.Enum):
    """Feature flag status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class FeatureFlag(Base):
    """
    Feature flag system for controlling feature rollouts
    Supports percentage-based rollouts and sector-specific restrictions
    """
    __tablename__ = "feature_flags"

    id: Mapped[str] = mapped_column(CompatibleUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic flag information
    flag_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Flag configuration
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rollout_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100
    scope: Mapped[FeatureFlagScope] = mapped_column(SQLEnum(FeatureFlagScope), default=FeatureFlagScope.GLOBAL)
    status: Mapped[FeatureFlagStatus] = mapped_column(SQLEnum(FeatureFlagStatus), default=FeatureFlagStatus.ACTIVE)
    
    # JSON configuration for complex rules
    config: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON(), nullable=False, default=dict)
    
    # Sector restrictions (SIC codes)
    allowed_sectors: Mapped[List[str]] = mapped_column(CompatibleJSON(), nullable=False, default=list)
    blocked_sectors: Mapped[List[str]] = mapped_column(CompatibleJSON(), nullable=False, default=list)
    
    # Module association
    module_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # Audit fields
    created_by: Mapped[str] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_feature_flags")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_feature_flags")
    usage_analytics = relationship("FeatureFlagUsage", back_populates="feature_flag", cascade="all, delete-orphan")
    overrides = relationship("FeatureFlagOverride", back_populates="feature_flag", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FeatureFlag(flag_key='{self.flag_key}', enabled={self.is_enabled}, rollout={self.rollout_percentage}%)>"


class FeatureFlagOverride(Base):
    """
    Organisation or user-specific overrides for feature flags
    Allows fine-grained control over feature access
    """
    __tablename__ = "feature_flag_overrides"

    id: Mapped[str] = mapped_column(CompatibleUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # References
    feature_flag_id: Mapped[str] = mapped_column(CompatibleUUID(), ForeignKey("feature_flags.id"), nullable=False)
    organisation_id: Mapped[Optional[str]] = mapped_column(CompatibleUUID(), ForeignKey("organisations.id"), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=True)
    
    # Override configuration
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_by: Mapped[str] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    feature_flag = relationship("FeatureFlag", back_populates="overrides")
    organisation = relationship("Organisation", back_populates="feature_flag_overrides")
    user = relationship("User", foreign_keys=[user_id], back_populates="feature_flag_overrides")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        target = f"org:{self.organisation_id}" if self.organisation_id else f"user:{self.user_id}"
        return f"<FeatureFlagOverride(flag={self.feature_flag.flag_key}, target={target}, enabled={self.is_enabled})>"


class FeatureFlagUsage(Base):
    """
    Track feature flag usage for analytics and adoption metrics
    """
    __tablename__ = "feature_flag_usage"

    id: Mapped[str] = mapped_column(CompatibleUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # References
    feature_flag_id: Mapped[str] = mapped_column(CompatibleUUID(), ForeignKey("feature_flags.id"), nullable=False)
    organisation_id: Mapped[str] = mapped_column(CompatibleUUID(), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    
    # Usage tracking
    was_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evaluation_context: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON(), nullable=False, default=dict)
    
    # Timestamp
    accessed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    feature_flag = relationship("FeatureFlag", back_populates="usage_analytics")
    organisation = relationship("Organisation", back_populates="feature_flag_usage")
    user = relationship("User", back_populates="feature_flag_usage")

    def __repr__(self):
        return f"<FeatureFlagUsage(flag={self.feature_flag.flag_key}, enabled={self.was_enabled}, accessed={self.accessed_at})>"