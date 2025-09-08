from .organisation import Organisation
from .user import User, UserRole, LEGACY_TO_ENHANCED_ROLE_MAPPING
from .user_application_access import UserApplicationAccess, UserInvitation, ApplicationType, InvitationStatus
from .tool import Tool
from .organisation_tool_access import OrganisationToolAccess

# Phase 3 models
from .sectors import SICCode, SectorModule, CompetitiveFactorTemplate
from .modules import AnalyticsModule, OrganisationModule, ModuleConfiguration, ModuleUsageLog
# Alias for backward compatibility
Module = AnalyticsModule
from .feature_flags import FeatureFlag, FeatureFlagOverride, FeatureFlagUsage
from .audit_log import AuditLog, AdminAction

# Hierarchical organization models
from .hierarchy import (
    OrganizationHierarchy, UserHierarchyAssignment, HierarchyRoleAssignment,
    HierarchyPermissionOverride, IndustryTemplate, OrganizationTemplateApplication,
    EnhancedUserRole, HierarchyLevel, PermissionScope
)

__all__ = [
    # Core models
    "Organisation", "User", "UserRole", "LEGACY_TO_ENHANCED_ROLE_MAPPING", 
    "UserApplicationAccess", "UserInvitation", "ApplicationType", "InvitationStatus",
    "Tool", "OrganisationToolAccess",
    
    # Phase 3 models
    "SICCode", "SectorModule", "CompetitiveFactorTemplate",
    "AnalyticsModule", "OrganisationModule", "ModuleConfiguration", "ModuleUsageLog", "Module",
    "FeatureFlag", "FeatureFlagOverride", "FeatureFlagUsage",
    "AuditLog", "AdminAction",
    
    # Hierarchical organization models
    "OrganizationHierarchy", "UserHierarchyAssignment", "HierarchyRoleAssignment",
    "HierarchyPermissionOverride", "IndustryTemplate", "OrganizationTemplateApplication",
    "EnhancedUserRole", "HierarchyLevel", "PermissionScope"
]