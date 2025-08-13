"""
Authentication Service for Multi-Tenant Platform

Provides authentication and authorization functionality for the multi-tenant platform,
integrating with Auth0 and managing tenant-specific permissions.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from fastapi import HTTPException, status
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class User:
    """User data model"""
    id: str
    email: str
    role: str
    tenant_id: Optional[str] = None
    permissions: List[str] = None


@dataclass
class TenantContext:
    """Tenant context data model"""
    id: str
    name: str
    domain: Optional[str] = None


class AuthService:
    """
    Authentication service providing multi-tenant auth functionality
    """
    
    def __init__(self):
        self.authenticated_users: Dict[str, User] = {}
        self.tenant_contexts: Dict[str, TenantContext] = {}
        self.session_timeouts: Dict[str, datetime] = {}
    
    def isAuthenticated(self, user_id: Optional[str] = None) -> bool:
        """Check if user is authenticated"""
        if not user_id:
            return len(self.authenticated_users) > 0
        return user_id in self.authenticated_users
    
    def getCurrentUser(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current user data with tenant context"""
        user = self.authenticated_users.get(user_id)
        if not user:
            return None
            
        tenant = self.tenant_contexts.get(user.tenant_id) if user.tenant_id else None
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role
            },
            "tenant": {
                "id": tenant.id if tenant else None,
                "name": tenant.name if tenant else None
            } if tenant else None,
            "permissions": user.permissions or []
        }
    
    def getUserRole(self, user_id: str) -> Optional[str]:
        """Get user role"""
        user = self.authenticated_users.get(user_id)
        return user.role if user else None
    
    def getUserPermissions(self, user_id: str) -> List[str]:
        """Get user permissions"""
        user = self.authenticated_users.get(user_id)
        return user.permissions or [] if user else []
    
    def hasAnyPermission(self, user_id: str, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        user_permissions = self.getUserPermissions(user_id)
        return any(perm in user_permissions for perm in permissions)
    
    def hasPermission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        return self.hasAnyPermission(user_id, [permission])
    
    def shouldRefreshToken(self, user_id: str) -> bool:
        """Check if token should be refreshed"""
        # Mock implementation - in real service this would check token expiry
        return False
    
    def validateTenantAccess(self, user_id: str, tenant_id: str) -> bool:
        """Validate that user has access to specified tenant"""
        user = self.authenticated_users.get(user_id)
        if not user:
            return False
            
        # Admin users can access any tenant
        if user.role == "admin":
            return True
            
        # Regular users can only access their own tenant
        return user.tenant_id == tenant_id
    
    def authenticateUser(
        self, 
        user_data: Dict[str, Any], 
        tenant_context: Optional[Dict[str, Any]] = None
    ) -> User:
        """Authenticate user and establish session"""
        user = User(
            id=user_data.get("id", ""),
            email=user_data.get("email", ""),
            role=user_data.get("role", "viewer"),
            tenant_id=tenant_context.get("id") if tenant_context else None,
            permissions=user_data.get("permissions", [])
        )
        
        self.authenticated_users[user.id] = user
        
        if tenant_context:
            self.tenant_contexts[tenant_context["id"]] = TenantContext(
                id=tenant_context["id"],
                name=tenant_context.get("name", ""),
                domain=tenant_context.get("domain")
            )
        
        # Set session timeout
        self.session_timeouts[user.id] = datetime.utcnow() + timedelta(hours=8)
        
        return user
    
    def logoutUser(self, user_id: str) -> bool:
        """Logout user and clean up session"""
        if user_id in self.authenticated_users:
            del self.authenticated_users[user_id]
        
        if user_id in self.session_timeouts:
            del self.session_timeouts[user_id]
            
        return True
    
    def checkSessionTimeout(self, user_id: str) -> bool:
        """Check if user session has timed out"""
        if user_id not in self.session_timeouts:
            return True
            
        return datetime.utcnow() > self.session_timeouts[user_id]
    
    def refreshUserSession(self, user_id: str) -> bool:
        """Refresh user session timeout"""
        if user_id in self.session_timeouts:
            self.session_timeouts[user_id] = datetime.utcnow() + timedelta(hours=8)
            return True
        return False
    
    def validateUserRole(self, user_id: str, required_roles: List[str]) -> bool:
        """Validate that user has one of the required roles"""
        user_role = self.getUserRole(user_id)
        return user_role in required_roles if user_role else False


# Global auth service instance
authService = AuthService()