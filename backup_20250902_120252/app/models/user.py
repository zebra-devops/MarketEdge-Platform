from sqlalchemy import String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base
from .database_types import CompatibleUUID
from .hierarchy import EnhancedUserRole
import enum
import uuid


class UserRole(str, enum.Enum):
    """Legacy user roles - maintained for backward compatibility"""
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


# Mapping between legacy and enhanced roles
LEGACY_TO_ENHANCED_ROLE_MAPPING = {
    UserRole.admin: EnhancedUserRole.org_admin,
    UserRole.analyst: EnhancedUserRole.user,
    UserRole.viewer: EnhancedUserRole.viewer,
}


class User(Base):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    organisation_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("organisations.id"), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.viewer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Extended fields for CSV import
    department: Mapped[str] = mapped_column(String(100), nullable=True)
    location: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    
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
    
    # Hierarchical organization relationships
    hierarchy_assignments = relationship("UserHierarchyAssignment", back_populates="user")
    permission_overrides = relationship("HierarchyPermissionOverride", foreign_keys="HierarchyPermissionOverride.user_id", back_populates="user")
    
    # Application access relationships
    application_access = relationship("UserApplicationAccess", foreign_keys="UserApplicationAccess.user_id", back_populates="user")
    invitations = relationship("UserInvitation", foreign_keys="UserInvitation.user_id", back_populates="user")
    
    def get_enhanced_role(self) -> EnhancedUserRole:
        """Convert legacy role to enhanced role"""
        return LEGACY_TO_ENHANCED_ROLE_MAPPING.get(self.role, EnhancedUserRole.user)
        
    def get_hierarchy_nodes(self, active_only: bool = True):
        """Get all hierarchy nodes this user is assigned to"""
        assignments = self.hierarchy_assignments
        if active_only:
            assignments = [a for a in assignments if a.is_active]
        return [a.hierarchy_node for a in assignments]
        
    def get_primary_hierarchy_assignment(self):
        """Get the user's primary hierarchy assignment"""
        for assignment in self.hierarchy_assignments:
            if assignment.is_primary and assignment.is_active:
                return assignment
        # Fallback to first active assignment
        active_assignments = [a for a in self.hierarchy_assignments if a.is_active]
        return active_assignments[0] if active_assignments else None
    
    def get_application_access(self):
        """Get user's application access permissions"""
        return {access.application.value: access.has_access for access in self.application_access}
    
    def has_application_access(self, application: str) -> bool:
        """Check if user has access to specific application"""
        for access in self.application_access:
            if access.application.value == application:
                return access.has_access
        return False