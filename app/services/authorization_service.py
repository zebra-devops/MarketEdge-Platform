"""Authorization service for consistent permission checking"""
from typing import Optional
from ..models.user import User, UserRole
import uuid


class AuthorizationService:
    """Service for handling authorization checks across the application"""
    
    @staticmethod
    def check_organization_access(current_user: User, org_id: str) -> bool:
        """
        Check if user has access to a specific organization

        Returns True if:
        - User is a super admin (has access to all organizations)
        - User is an admin AND belongs to the specified organization
        """
        # Super admin has access to all organizations
        if current_user.role == UserRole.super_admin:
            return True

        # Check if user has admin role
        if current_user.role == UserRole.admin:
            # Admin must belong to the organization
            return str(current_user.organisation_id) == str(org_id)

        # Regular users can only access their own organization
        return str(current_user.organisation_id) == str(org_id)
    
    @staticmethod
    def check_user_management_access(current_user: User, org_id: str) -> bool:
        """
        Check if user can manage users in a specific organization

        Returns True if:
        - User is a super admin
        - User is an admin of the specified organization
        """
        # Super admin can manage users in any organization
        if current_user.role == UserRole.super_admin:
            return True

        # Admin can manage users in their organization
        if current_user.role == UserRole.admin:
            return str(current_user.organisation_id) == str(org_id)

        # Regular users cannot manage other users
        return False
    
    @staticmethod
    def check_import_access(current_user: User, org_id: str) -> bool:
        """
        Check if user can perform bulk imports for an organization
        
        Returns True if:
        - User is a super admin
        - User is an admin of the specified organization
        """
        return AuthorizationService.check_user_management_access(current_user, org_id)
    
    @staticmethod
    def is_super_admin(current_user: User) -> bool:
        """Check if user is a super admin"""
        return current_user.role == UserRole.super_admin
    
    @staticmethod
    def is_organization_admin(current_user: User) -> bool:
        """Check if user is an organization admin (admin or super_admin)"""
        return current_user.role in [UserRole.admin, UserRole.super_admin]