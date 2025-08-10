from sqlalchemy import String, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    organisation_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.viewer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    organisation: Mapped["Organisation"] = relationship("Organisation", back_populates="users")
    
    # Feature flag relationships
    created_feature_flags = relationship("FeatureFlag", foreign_keys="FeatureFlag.created_by", back_populates="creator")
    updated_feature_flags = relationship("FeatureFlag", foreign_keys="FeatureFlag.updated_by", back_populates="updater")
    feature_flag_overrides = relationship("FeatureFlagOverride", foreign_keys="FeatureFlagOverride.user_id", back_populates="user")
    feature_flag_usage = relationship("FeatureFlagUsage", back_populates="user")
    
    # Module relationships
    created_modules = relationship("AnalyticsModule", back_populates="creator")
    module_usage_logs = relationship("ModuleUsageLog", back_populates="user")
    
    # Audit relationships
    audit_logs = relationship("AuditLog", back_populates="user")
    admin_actions = relationship("AdminAction", foreign_keys="AdminAction.admin_user_id", back_populates="admin_user")