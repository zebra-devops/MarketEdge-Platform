"""
Permission Resolution Engine for Hierarchical Organizations

This service handles permission resolution across the hierarchical organization structure
supporting role inheritance, permission overrides, and fine-grained access control.
"""
import json
import uuid
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from ..core.logging import logger
from ..data.cache.redis_cache import cache_manager
from ..models.user import User, UserRole, LEGACY_TO_ENHANCED_ROLE_MAPPING
from ..models.organisation import Organisation
from ..models.hierarchy import (
    OrganizationHierarchy, 
    UserHierarchyAssignment, 
    HierarchyRoleAssignment,
    HierarchyPermissionOverride,
    IndustryTemplate,
    OrganizationTemplateApplication,
    EnhancedUserRole,
    PermissionScope,
    HierarchyLevel
)


class PermissionResolutionEngine:
    """
    Core engine for resolving hierarchical permissions
    
    Permission Resolution Order:
    1. User-specific permission overrides (highest priority)
    2. Role-based permissions at current hierarchy level
    3. Inherited permissions from parent hierarchy levels
    4. Industry template defaults (lowest priority)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.cache_prefix = "permissions:"
        
    def resolve_user_permissions(
        self, 
        user_id: uuid.UUID, 
        context_node_id: Optional[uuid.UUID] = None,
        include_inherited: bool = True
    ) -> Dict[str, Any]:
        """
        Resolve all permissions for a user in a specific context
        
        Args:
            user_id: The user's ID
            context_node_id: Specific hierarchy node context (optional)
            include_inherited: Whether to include permissions from parent nodes
            
        Returns:
            Dict containing resolved permissions with metadata
        """
        # Create cache key for permission resolution
        cache_key = f"{self.cache_prefix}user:{user_id}:node:{context_node_id}:inherited:{include_inherited}"
        
        # Check cache first
        try:
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Permission cache hit for user {user_id}")
                return cached_result
        except Exception as e:
            logger.warning(f"Permission cache read error: {str(e)}")
        
        try:
            # Get user with hierarchy assignments
            user = self.db.query(User).options(
                joinedload(User.hierarchy_assignments).joinedload(UserHierarchyAssignment.hierarchy_node),
                joinedload(User.permission_overrides),
                joinedload(User.organisation)
            ).filter(User.id == user_id).first()
            
            if not user:
                logger.warning(f"User not found for permission resolution: {user_id}")
                return {"permissions": [], "context": "user_not_found"}
            
            # Get relevant hierarchy nodes for the user
            if context_node_id:
                context_node = self.db.query(OrganizationHierarchy).filter(
                    OrganizationHierarchy.id == context_node_id
                ).first()
                if not context_node:
                    logger.warning(f"Context node not found: {context_node_id}")
                    return {"permissions": [], "context": "invalid_context"}
                hierarchy_nodes = [context_node]
            else:
                # Use all nodes the user is assigned to
                hierarchy_nodes = user.get_hierarchy_nodes()
            
            resolved_permissions = {}
            resolution_metadata = {
                "user_id": str(user_id),
                "context_node_id": str(context_node_id) if context_node_id else None,
                "resolution_path": [],
                "overrides_applied": [],
                "inheritance_chain": []
            }
            
            for node in hierarchy_nodes:
                node_permissions = self._resolve_permissions_for_node(
                    user, node, include_inherited, resolution_metadata
                )
                
                # Merge permissions (union of all permissions)
                for permission, details in node_permissions.items():
                    if permission not in resolved_permissions:
                        resolved_permissions[permission] = details
                    else:
                        # Keep the higher priority permission
                        if details["priority"] > resolved_permissions[permission]["priority"]:
                            resolved_permissions[permission] = details
            
            result = {
                "permissions": list(resolved_permissions.keys()),
                "detailed_permissions": resolved_permissions,
                "metadata": resolution_metadata
            }
            
            # Cache the result for future requests
            try:
                cache_manager.set(cache_key, result, ttl=self.cache_ttl)
                logger.debug(f"Cached permission resolution for user {user_id}")
            except Exception as e:
                logger.warning(f"Permission cache write error: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error resolving permissions for user {user_id}: {str(e)}")
            return {"permissions": [], "error": str(e)}
    
    def _resolve_permissions_for_node(
        self, 
        user: User, 
        node: OrganizationHierarchy,
        include_inherited: bool,
        metadata: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Resolve permissions for a specific hierarchy node"""
        
        permissions = {}
        
        # 1. Get user's role assignment at this node
        user_assignment = None
        for assignment in user.hierarchy_assignments:
            if assignment.hierarchy_node_id == node.id and assignment.is_active:
                user_assignment = assignment
                break
        
        if not user_assignment:
            logger.debug(f"No active assignment found for user {user.id} at node {node.id}")
            return permissions
        
        user_role = user_assignment.role
        metadata["resolution_path"].append({
            "node_id": str(node.id),
            "node_name": node.name,
            "node_level": node.level.value,
            "user_role": user_role.value
        })
        
        # 2. Get role-based permissions at current level
        role_assignment = self.db.query(HierarchyRoleAssignment).filter(
            and_(
                HierarchyRoleAssignment.hierarchy_node_id == node.id,
                HierarchyRoleAssignment.role == user_role,
                HierarchyRoleAssignment.is_active == True
            )
        ).first()
        
        if role_assignment:
            role_permissions = json.loads(role_assignment.permissions)
            for perm in role_permissions:
                permissions[perm] = {
                    "granted": True,
                    "source": "role_assignment",
                    "source_details": {
                        "node_id": str(node.id),
                        "role": user_role.value,
                        "level": node.level.value
                    },
                    "priority": 3  # Medium priority
                }
        
        # 3. Apply inherited permissions from parent nodes
        if include_inherited and node.parent_id:
            inherited_permissions = self._get_inherited_permissions(
                node.parent, user_role, metadata
            )
            
            for perm, details in inherited_permissions.items():
                if perm not in permissions:
                    permissions[perm] = details
                    permissions[perm]["inherited"] = True
        
        # 4. Apply user-specific permission overrides (highest priority)
        user_overrides = self.db.query(HierarchyPermissionOverride).filter(
            and_(
                HierarchyPermissionOverride.user_id == user.id,
                HierarchyPermissionOverride.hierarchy_node_id == node.id,
                HierarchyPermissionOverride.is_active == True
            )
        ).all()
        
        for override in user_overrides:
            permissions[override.permission] = {
                "granted": override.granted,
                "source": "user_override",
                "source_details": {
                    "node_id": str(node.id),
                    "reason": override.reason,
                    "granted_by": str(override.granted_by) if override.granted_by else None
                },
                "priority": 5  # Highest priority
            }
            
            metadata["overrides_applied"].append({
                "permission": override.permission,
                "granted": override.granted,
                "node_id": str(node.id),
                "reason": override.reason
            })
        
        return permissions
    
    def _get_inherited_permissions(
        self, 
        parent_node: OrganizationHierarchy,
        user_role: EnhancedUserRole,
        metadata: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Get permissions inherited from parent hierarchy levels"""
        
        if not parent_node:
            return {}
        
        permissions = {}
        current_node = parent_node
        depth = 0
        max_depth = 10  # Prevent infinite loops
        
        while current_node and depth < max_depth:
            # Get role assignment that allows inheritance
            role_assignment = self.db.query(HierarchyRoleAssignment).filter(
                and_(
                    HierarchyRoleAssignment.hierarchy_node_id == current_node.id,
                    HierarchyRoleAssignment.role == user_role,
                    HierarchyRoleAssignment.inherits_from_parent == True,
                    HierarchyRoleAssignment.is_active == True
                )
            ).first()
            
            if role_assignment:
                inherited_permissions = json.loads(role_assignment.permissions)
                for perm in inherited_permissions:
                    if perm not in permissions:
                        permissions[perm] = {
                            "granted": True,
                            "source": "inherited",
                            "source_details": {
                                "parent_node_id": str(current_node.id),
                                "parent_node_name": current_node.name,
                                "parent_level": current_node.level.value,
                                "inheritance_depth": depth + 1
                            },
                            "priority": 2  # Lower priority than direct assignments
                        }
                
                metadata["inheritance_chain"].append({
                    "node_id": str(current_node.id),
                    "node_name": current_node.name,
                    "level": current_node.level.value,
                    "depth": depth + 1
                })
            
            current_node = current_node.parent
            depth += 1
        
        return permissions
    
    def check_permission(
        self, 
        user_id: uuid.UUID, 
        permission: str,
        context_node_id: Optional[uuid.UUID] = None
    ) -> bool:
        """
        Check if a user has a specific permission
        
        Args:
            user_id: The user's ID
            permission: Permission to check
            context_node_id: Specific hierarchy node context
            
        Returns:
            True if user has the permission, False otherwise
        """
        try:
            resolved = self.resolve_user_permissions(user_id, context_node_id)
            return permission in resolved.get("permissions", [])
        except Exception as e:
            logger.error(f"Error checking permission {permission} for user {user_id}: {str(e)}")
            return False
    
    def get_accessible_nodes(
        self, 
        user_id: uuid.UUID, 
        minimum_role: Optional[EnhancedUserRole] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all hierarchy nodes the user can access
        
        Args:
            user_id: The user's ID
            minimum_role: Minimum role required (optional)
            
        Returns:
            List of accessible hierarchy nodes with metadata
        """
        try:
            user = self.db.query(User).options(
                joinedload(User.hierarchy_assignments).joinedload(UserHierarchyAssignment.hierarchy_node)
            ).filter(User.id == user_id).first()
            
            if not user:
                return []
            
            accessible_nodes = []
            
            for assignment in user.hierarchy_assignments:
                if not assignment.is_active:
                    continue
                
                if minimum_role and self._compare_roles(assignment.role, minimum_role) < 0:
                    continue
                
                node = assignment.hierarchy_node
                accessible_nodes.append({
                    "node_id": str(node.id),
                    "name": node.name,
                    "level": node.level.value,
                    "hierarchy_path": node.hierarchy_path,
                    "user_role": assignment.role.value,
                    "is_primary": assignment.is_primary
                })
            
            return accessible_nodes
        
        except Exception as e:
            logger.error(f"Error getting accessible nodes for user {user_id}: {str(e)}")
            return []
    
    def _compare_roles(self, role1: EnhancedUserRole, role2: EnhancedUserRole) -> int:
        """
        Compare two roles by authority level
        Returns: -1 if role1 < role2, 0 if equal, 1 if role1 > role2
        """
        role_hierarchy = {
            EnhancedUserRole.viewer: 1,
            EnhancedUserRole.user: 2,
            EnhancedUserRole.department_lead: 3,
            EnhancedUserRole.location_manager: 4,
            EnhancedUserRole.org_admin: 5,
            EnhancedUserRole.super_admin: 6
        }
        
        level1 = role_hierarchy.get(role1, 0)
        level2 = role_hierarchy.get(role2, 0)
        
        if level1 < level2:
            return -1
        elif level1 > level2:
            return 1
        else:
            return 0
    
    def invalidate_user_permissions_cache(self, user_id: uuid.UUID):
        """Invalidate all cached permissions for a specific user"""
        try:
            # Pattern to match all permission cache keys for this user
            pattern = f"{self.cache_prefix}user:{user_id}:*"
            
            # Delete all matching keys
            deleted_count = cache_manager.delete_pattern(pattern)
            
            if deleted_count > 0:
                logger.info(f"Invalidated {deleted_count} permission cache entries for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error invalidating permission cache for user {user_id}: {str(e)}")
    
    def invalidate_node_permissions_cache(self, node_id: uuid.UUID):
        """Invalidate cached permissions for all users affected by a node change"""
        try:
            # Pattern to match all permission cache keys for this node
            pattern = f"{self.cache_prefix}user:*:node:{node_id}:*"
            
            # Delete all matching keys
            deleted_count = cache_manager.delete_pattern(pattern)
            
            if deleted_count > 0:
                logger.info(f"Invalidated {deleted_count} permission cache entries for node {node_id}")
            
        except Exception as e:
            logger.error(f"Error invalidating permission cache for node {node_id}: {str(e)}")


class IndustryTemplateService:
    """Service for managing industry-specific configuration templates"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_template_by_code(self, industry_code: str) -> Optional[IndustryTemplate]:
        """Get industry template by code"""
        return self.db.query(IndustryTemplate).filter(
            and_(
                IndustryTemplate.industry_code == industry_code.upper(),
                IndustryTemplate.is_active == True
            )
        ).first()
    
    def apply_template_to_organization(
        self, 
        organization_id: uuid.UUID,
        template_id: uuid.UUID,
        applied_by: uuid.UUID,
        customizations: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Apply an industry template to an organization
        
        Args:
            organization_id: Organization ID
            template_id: Industry template ID
            applied_by: User applying the template
            customizations: Optional customizations to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            template = self.db.query(IndustryTemplate).filter(
                IndustryTemplate.id == template_id
            ).first()
            
            if not template:
                logger.error(f"Template not found: {template_id}")
                return False
            
            organization = self.db.query(Organisation).filter(
                Organisation.id == organization_id
            ).first()
            
            if not organization:
                logger.error(f"Organization not found: {organization_id}")
                return False
            
            # Create template application record
            application = OrganizationTemplateApplication(
                organization_id=organization_id,
                template_id=template_id,
                applied_settings=template.default_settings,
                customizations=json.dumps(customizations or {}),
                applied_by=applied_by
            )
            
            self.db.add(application)
            
            # Apply template settings to organization
            self._apply_template_settings(organization, template, customizations)
            
            self.db.commit()
            
            logger.info(f"Applied template {template.name} to organization {organization.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying template to organization: {str(e)}")
            self.db.rollback()
            return False
    
    def _apply_template_settings(
        self, 
        organization: Organisation, 
        template: IndustryTemplate,
        customizations: Optional[Dict[str, Any]] = None
    ):
        """Apply template settings to organization"""
        
        # Parse default settings
        default_settings = json.loads(template.default_settings)
        
        # Apply customizations if provided
        if customizations:
            # Merge customizations with defaults
            for key, value in customizations.items():
                if key in json.loads(template.customizable_fields or "[]"):
                    default_settings[key] = value
        
        # Update organization with template settings
        if "industry_type" in default_settings:
            organization.industry_type = default_settings["industry_type"]
        
        if "subscription_plan" in default_settings:
            organization.subscription_plan = default_settings["subscription_plan"]
        
        if "rate_limit_per_hour" in default_settings:
            organization.rate_limit_per_hour = default_settings["rate_limit_per_hour"]
        
        if "burst_limit" in default_settings:
            organization.burst_limit = default_settings["burst_limit"]
    
    def get_organization_templates(self, organization_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get all templates applied to an organization"""
        
        applications = self.db.query(OrganizationTemplateApplication).options(
            joinedload(OrganizationTemplateApplication.template)
        ).filter(
            and_(
                OrganizationTemplateApplication.organization_id == organization_id,
                OrganizationTemplateApplication.is_active == True
            )
        ).all()
        
        return [
            {
                "template_id": str(app.template.id),
                "template_name": app.template.name,
                "industry_code": app.template.industry_code,
                "applied_settings": json.loads(app.applied_settings),
                "customizations": json.loads(app.customizations or "{}"),
                "applied_at": app.created_at,
                "applied_by": str(app.applied_by)
            }
            for app in applications
        ]