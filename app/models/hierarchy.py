"""
Enhanced Hierarchical Organization Models for Multi-Tenant Platform

This module defines the hierarchical organization structure supporting:
- Organization → Location → Department → User permission inheritance
- Role-based permissions: super_admin, org_admin, location_manager, department_lead, user
- Row-Level Security (RLS) enforcement
- Permission resolution engine for complex hierarchies
"""
from sqlalchemy import String, Boolean, ForeignKey, Enum, Integer, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from .base import Base
from .database_types import CompatibleUUID
import enum
import uuid


class HierarchyLevel(str, enum.Enum):
    """Hierarchy levels for permission inheritance"""
    ORGANIZATION = "organization"
    LOCATION = "location"
    DEPARTMENT = "department"
    USER = "user"


class EnhancedUserRole(str, enum.Enum):
    """Enhanced roles supporting hierarchical permissions"""
    super_admin = "super_admin"        # Platform-wide access
    org_admin = "org_admin"           # Full organization access
    location_manager = "location_manager"  # Location-specific admin access
    department_lead = "department_lead"    # Department-specific admin access
    user = "user"                     # Basic user access
    viewer = "viewer"                 # Read-only access


class PermissionScope(str, enum.Enum):
    """Permission scopes for fine-grained access control"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"


class OrganizationHierarchy(Base):
    """
    Extended organization model supporting hierarchical structures
    Maintains backward compatibility with existing Organisation model
    """
    __tablename__ = "organization_hierarchy"
    
    # Core fields
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Hierarchy fields
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(CompatibleUUID(), ForeignKey("organization_hierarchy.id"), nullable=True)
    level: Mapped[HierarchyLevel] = mapped_column(Enum(HierarchyLevel), nullable=False, default=HierarchyLevel.ORGANIZATION)
    hierarchy_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)  # e.g., "org1/location1/dept1"
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Legacy compatibility - links to existing organisations table
    legacy_organisation_id: Mapped[Optional[uuid.UUID]] = mapped_column(CompatibleUUID(), ForeignKey("organisations.id"), nullable=True)
    
    # Status and configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[Optional[str]] = mapped_column(Text)  # JSON settings specific to this level
    
    # Relationships
    parent: Mapped[Optional["OrganizationHierarchy"]] = relationship("OrganizationHierarchy", remote_side="OrganizationHierarchy.id", back_populates="children")
    children: Mapped[List["OrganizationHierarchy"]] = relationship("OrganizationHierarchy", back_populates="parent")
    legacy_organisation = relationship("Organisation", back_populates="hierarchy_nodes")
    
    # Permission and user relationships
    user_assignments: Mapped[List["UserHierarchyAssignment"]] = relationship("UserHierarchyAssignment", back_populates="hierarchy_node")
    role_assignments: Mapped[List["HierarchyRoleAssignment"]] = relationship("HierarchyRoleAssignment", back_populates="hierarchy_node")
    permission_overrides: Mapped[List["HierarchyPermissionOverride"]] = relationship("HierarchyPermissionOverride", back_populates="hierarchy_node")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('slug', 'parent_id', name='uq_hierarchy_slug_parent'),
        Index('idx_hierarchy_path', 'hierarchy_path'),
        Index('idx_hierarchy_level_active', 'level', 'is_active'),
        Index('idx_hierarchy_parent_level', 'parent_id', 'level'),
    )


class UserHierarchyAssignment(Base):
    """
    Assigns users to specific nodes in the organization hierarchy
    Supports multiple assignments for users with access to multiple locations/departments
    """
    __tablename__ = "user_hierarchy_assignments"
    
    user_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    hierarchy_node_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("organization_hierarchy.id"), nullable=False)
    role: Mapped[EnhancedUserRole] = mapped_column(Enum(EnhancedUserRole), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Primary assignment for user
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="hierarchy_assignments")
    hierarchy_node: Mapped["OrganizationHierarchy"] = relationship("OrganizationHierarchy", back_populates="user_assignments")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'hierarchy_node_id', name='uq_user_hierarchy_assignment'),
        Index('idx_user_hierarchy_user_active', 'user_id', 'is_active'),
        Index('idx_user_hierarchy_node_role', 'hierarchy_node_id', 'role'),
    )


class HierarchyRoleAssignment(Base):
    """
    Role-based permissions at hierarchy levels
    Defines what roles can do at specific hierarchy nodes
    """
    __tablename__ = "hierarchy_role_assignments"
    
    hierarchy_node_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("organization_hierarchy.id"), nullable=False)
    role: Mapped[EnhancedUserRole] = mapped_column(Enum(EnhancedUserRole), nullable=False)
    permissions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of permissions
    inherits_from_parent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    hierarchy_node: Mapped["OrganizationHierarchy"] = relationship("OrganizationHierarchy", back_populates="role_assignments")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('hierarchy_node_id', 'role', name='uq_hierarchy_role'),
        Index('idx_hierarchy_role_active', 'role', 'is_active'),
        Index('idx_hierarchy_role_node', 'hierarchy_node_id', 'is_active'),
    )


class HierarchyPermissionOverride(Base):
    """
    User-specific permission overrides at hierarchy levels
    Allows granting/revoking specific permissions for individual users
    """
    __tablename__ = "hierarchy_permission_overrides"
    
    user_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    hierarchy_node_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("organization_hierarchy.id"), nullable=False)
    permission: Mapped[str] = mapped_column(String(100), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)  # True = grant, False = revoke
    reason: Mapped[Optional[str]] = mapped_column(String(500))
    granted_by: Mapped[Optional[uuid.UUID]] = mapped_column(CompatibleUUID(), ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="permission_overrides")
    hierarchy_node: Mapped["OrganizationHierarchy"] = relationship("OrganizationHierarchy", back_populates="permission_overrides")
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'hierarchy_node_id', 'permission', name='uq_user_permission_override'),
        Index('idx_permission_override_user_active', 'user_id', 'is_active'),
        Index('idx_permission_override_node_permission', 'hierarchy_node_id', 'permission'),
    )


class IndustryTemplate(Base):
    """
    Industry-specific configuration templates
    Defines default settings, features, and permissions for different industries
    """
    __tablename__ = "industry_templates"
    
    # Template identification
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    industry_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)  # e.g., 'CINEMA', 'HOTEL'
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Template configuration
    default_settings: Mapped[str] = mapped_column(Text, nullable=False)  # JSON configuration
    default_permissions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON role-permission mapping
    default_features: Mapped[str] = mapped_column(Text, nullable=False)  # JSON feature flags
    dashboard_config: Mapped[Optional[str]] = mapped_column(Text)  # JSON dashboard layout
    
    # Template hierarchy
    parent_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(CompatibleUUID(), ForeignKey("industry_templates.id"), nullable=True)
    is_base_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    customizable_fields: Mapped[Optional[str]] = mapped_column(Text)  # JSON list of customizable fields
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    
    # Relationships
    parent_template: Mapped[Optional["IndustryTemplate"]] = relationship("IndustryTemplate", remote_side="IndustryTemplate.id", back_populates="child_templates")
    child_templates: Mapped[List["IndustryTemplate"]] = relationship("IndustryTemplate", back_populates="parent_template")
    organization_applications: Mapped[List["OrganizationTemplateApplication"]] = relationship("OrganizationTemplateApplication", back_populates="template")
    
    # Constraints
    __table_args__ = (
        Index('idx_industry_template_code_active', 'industry_code', 'is_active'),
        Index('idx_industry_template_parent', 'parent_template_id', 'is_active'),
    )


class OrganizationTemplateApplication(Base):
    """
    Tracks which templates have been applied to organizations
    Supports template inheritance and customization history
    """
    __tablename__ = "organization_template_applications"
    
    organization_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("organisations.id"), nullable=False)
    template_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("industry_templates.id"), nullable=False)
    applied_settings: Mapped[str] = mapped_column(Text, nullable=False)  # JSON of applied configuration
    customizations: Mapped[Optional[str]] = mapped_column(Text)  # JSON of customizations made after application
    applied_by: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    organization = relationship("Organisation", back_populates="template_applications")
    template: Mapped["IndustryTemplate"] = relationship("IndustryTemplate", back_populates="organization_applications")
    applied_by_user = relationship("User")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'template_id', name='uq_org_template_application'),
        Index('idx_org_template_org_active', 'organization_id', 'is_active'),
        Index('idx_org_template_template_active', 'template_id', 'is_active'),
    )