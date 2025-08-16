"""
Organization Hierarchy Management API

This module provides comprehensive CRUD APIs for managing hierarchical organizations
supporting parent-child relationships, industry templates, and user assignments.
"""
import json
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func
from pydantic import BaseModel, Field, validator

from ....core.database import get_db
from ....auth.dependencies import (
    get_current_user, 
    require_role,
    require_permission
)
from ....models.user import User, UserRole
from ....models.organisation import Organisation
from ....models.hierarchy import (
    OrganizationHierarchy,
    UserHierarchyAssignment,
    HierarchyRoleAssignment,
    IndustryTemplate,
    EnhancedUserRole,
    HierarchyLevel
)
from ....services.permission_service import PermissionResolutionEngine, IndustryTemplateService
from ....core.logging import logger

router = APIRouter()


# Pydantic Models
class CreateHierarchyNodeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Node name")
    description: Optional[str] = Field(None, max_length=1000, description="Node description")
    parent_id: Optional[uuid.UUID] = Field(None, description="Parent node ID")
    level: HierarchyLevel = Field(..., description="Hierarchy level")
    settings: Optional[Dict[str, Any]] = Field(None, description="Node-specific settings")
    
    @validator('name')
    def name_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class UpdateHierarchyNodeRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class AssignUserToNodeRequest(BaseModel):
    user_id: uuid.UUID = Field(..., description="User ID to assign")
    role: EnhancedUserRole = Field(..., description="Role to assign")
    is_primary: bool = Field(False, description="Whether this is the primary assignment")


class CreateOrganizationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    industry_template_code: Optional[str] = Field(None, description="Industry template to apply")
    customizations: Optional[Dict[str, Any]] = Field(None, description="Template customizations")
    locations: Optional[List[Dict[str, Any]]] = Field(None, description="Initial locations to create")
    admin_user_email: str = Field(..., description="Email of the organization admin")
    admin_user_first_name: str = Field(..., min_length=1, max_length=100)
    admin_user_last_name: str = Field(..., min_length=1, max_length=100)


class HierarchyNodeResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    level: str
    hierarchy_path: str
    depth: int
    parent_id: Optional[uuid.UUID]
    is_active: bool
    settings: Optional[Dict[str, Any]]
    children_count: int
    user_count: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class OrganizationStructureResponse(BaseModel):
    organization: HierarchyNodeResponse
    locations: List[HierarchyNodeResponse]
    departments: List[HierarchyNodeResponse]
    total_users: int
    template_info: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


@router.post("/organizations", response_model=Dict[str, Any])
async def create_organization(
    request: CreateOrganizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin]))
):
    """
    Create a new organization with hierarchical structure
    
    Supports:
    - Industry template application
    - Automatic hierarchy creation
    - Admin user setup
    - Initial location/department creation
    """
    try:
        # Check if organization name already exists
        existing_org = db.query(Organisation).filter(
            Organisation.name == request.name
        ).first()
        
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name already exists"
            )
        
        # Check if admin user already exists
        existing_user = db.query(User).filter(
            User.email == request.admin_user_email
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin user email already exists"
            )
        
        # Create the organization
        organization = Organisation(
            name=request.name,
            is_active=True
        )
        db.add(organization)
        db.flush()  # Get the ID
        
        # Create root hierarchy node
        slug = request.name.lower().replace(" ", "-").replace("_", "-")
        root_node = OrganizationHierarchy(
            name=request.name,
            slug=slug,
            description=f"Root organization node for {request.name}",
            level=HierarchyLevel.ORGANIZATION,
            hierarchy_path=slug,
            depth=0,
            legacy_organisation_id=organization.id,
            is_active=True
        )
        db.add(root_node)
        db.flush()
        
        # Apply industry template if specified
        template_service = IndustryTemplateService(db)
        if request.industry_template_code:
            template = template_service.get_template_by_code(request.industry_template_code)
            if template:
                success = template_service.apply_template_to_organization(
                    organization.id,
                    template.id,
                    current_user.id,
                    request.customizations
                )
                if not success:
                    logger.warning(f"Failed to apply template {request.industry_template_code}")
        
        # Create admin user
        admin_user = User(
            email=request.admin_user_email,
            first_name=request.admin_user_first_name,
            last_name=request.admin_user_last_name,
            organisation_id=organization.id,
            role=UserRole.admin,
            is_active=True
        )
        db.add(admin_user)
        db.flush()
        
        # Assign admin user to root node
        admin_assignment = UserHierarchyAssignment(
            user_id=admin_user.id,
            hierarchy_node_id=root_node.id,
            role=EnhancedUserRole.org_admin,
            is_primary=True,
            is_active=True
        )
        db.add(admin_assignment)
        
        # Create default role assignments for root node
        default_permissions = [
            (EnhancedUserRole.org_admin, ["read", "write", "delete", "admin", "manage_users", "manage_settings", "view_reports", "export_data"]),
            (EnhancedUserRole.location_manager, ["read", "write", "manage_users", "view_reports"]),
            (EnhancedUserRole.department_lead, ["read", "write", "view_reports"]),
            (EnhancedUserRole.user, ["read", "view_reports"]),
            (EnhancedUserRole.viewer, ["read"])
        ]
        
        for role, permissions in default_permissions:
            role_assignment = HierarchyRoleAssignment(
                hierarchy_node_id=root_node.id,
                role=role,
                permissions=str(permissions).replace("'", '"'),  # JSON format
                inherits_from_parent=True,
                is_active=True
            )
            db.add(role_assignment)
        
        # Create initial locations if specified
        created_locations = []
        if request.locations:
            for i, location_data in enumerate(request.locations):
                location_slug = f"{slug}-{location_data.get('name', f'location-{i+1}').lower().replace(' ', '-')}"
                location_node = OrganizationHierarchy(
                    name=location_data.get('name', f'Location {i+1}'),
                    slug=location_slug,
                    description=location_data.get('description'),
                    parent_id=root_node.id,
                    level=HierarchyLevel.LOCATION,
                    hierarchy_path=f"{slug}/{location_slug}",
                    depth=1,
                    legacy_organisation_id=organization.id,
                    is_active=True,
                    settings=str(location_data.get('settings', {})).replace("'", '"') if location_data.get('settings') else None
                )
                db.add(location_node)
                created_locations.append(location_node)
        
        db.commit()
        
        logger.info(f"Created organization {organization.name} with hierarchy structure")
        
        return {
            "organization_id": str(organization.id),
            "root_node_id": str(root_node.id),
            "admin_user_id": str(admin_user.id),
            "locations_created": len(created_locations),
            "template_applied": request.industry_template_code is not None,
            "message": "Organization created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}"
        )


@router.get("/organizations/{organization_id}/structure", response_model=OrganizationStructureResponse)
async def get_organization_structure(
    organization_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete hierarchical structure of an organization"""
    
    # Check access permissions
    permission_engine = PermissionResolutionEngine(db)
    if not permission_engine.check_permission(current_user.id, "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view organization structure"
        )
    
    # Get organization
    organization = db.query(Organisation).filter(
        Organisation.id == organization_id
    ).first()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get root hierarchy node
    root_node = db.query(OrganizationHierarchy).filter(
        and_(
            OrganizationHierarchy.legacy_organisation_id == organization_id,
            OrganizationHierarchy.level == HierarchyLevel.ORGANIZATION,
            OrganizationHierarchy.parent_id.is_(None)
        )
    ).first()
    
    if not root_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization hierarchy not found"
        )
    
    # Get all child nodes
    all_nodes = db.query(OrganizationHierarchy).filter(
        OrganizationHierarchy.legacy_organisation_id == organization_id
    ).all()
    
    # Separate by level
    locations = [node for node in all_nodes if node.level == HierarchyLevel.LOCATION]
    departments = [node for node in all_nodes if node.level == HierarchyLevel.DEPARTMENT]
    
    # Count users
    total_users = db.query(func.count(User.id)).filter(
        User.organisation_id == organization_id,
        User.is_active == True
    ).scalar()
    
    # Get template information
    template_service = IndustryTemplateService(db)
    template_info = template_service.get_organization_templates(organization_id)
    
    def node_to_response(node: OrganizationHierarchy) -> HierarchyNodeResponse:
        # Count children and users for this node
        children_count = db.query(func.count(OrganizationHierarchy.id)).filter(
            OrganizationHierarchy.parent_id == node.id
        ).scalar()
        
        user_count = db.query(func.count(UserHierarchyAssignment.id)).filter(
            and_(
                UserHierarchyAssignment.hierarchy_node_id == node.id,
                UserHierarchyAssignment.is_active == True
            )
        ).scalar()
        
        return HierarchyNodeResponse(
            id=node.id,
            name=node.name,
            slug=node.slug,
            description=node.description,
            level=node.level.value,
            hierarchy_path=node.hierarchy_path,
            depth=node.depth,
            parent_id=node.parent_id,
            is_active=node.is_active,
            settings=json.loads(node.settings) if node.settings else None,
            children_count=children_count,
            user_count=user_count,
            created_at=node.created_at.isoformat(),
            updated_at=node.updated_at.isoformat()
        )
    
    return OrganizationStructureResponse(
        organization=node_to_response(root_node),
        locations=[node_to_response(loc) for loc in locations],
        departments=[node_to_response(dept) for dept in departments],
        total_users=total_users,
        template_info=template_info[0] if template_info else None
    )


@router.post("/hierarchy-nodes", response_model=HierarchyNodeResponse)
async def create_hierarchy_node(
    request: CreateHierarchyNodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["admin", "manage_settings"]))
):
    """Create a new hierarchy node (location, department, etc.)"""
    
    try:
        # Validate parent node if specified
        parent_node = None
        if request.parent_id:
            parent_node = db.query(OrganizationHierarchy).filter(
                OrganizationHierarchy.id == request.parent_id
            ).first()
            
            if not parent_node:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent node not found"
                )
            
            # Validate hierarchy level consistency
            expected_child_levels = {
                HierarchyLevel.ORGANIZATION: [HierarchyLevel.LOCATION],
                HierarchyLevel.LOCATION: [HierarchyLevel.DEPARTMENT],
                HierarchyLevel.DEPARTMENT: []  # Departments can't have children in this model
            }
            
            if request.level not in expected_child_levels.get(parent_node.level, []):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot create {request.level.value} under {parent_node.level.value}"
                )
        
        # Generate slug
        base_slug = request.name.lower().replace(" ", "-").replace("_", "-")
        if parent_node:
            slug = f"{parent_node.hierarchy_path}/{base_slug}"
            depth = parent_node.depth + 1
        else:
            slug = base_slug
            depth = 0
        
        # Check for duplicate slug
        existing_node = db.query(OrganizationHierarchy).filter(
            OrganizationHierarchy.slug == base_slug,
            OrganizationHierarchy.parent_id == request.parent_id
        ).first()
        
        if existing_node:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Node with this name already exists at this level"
            )
        
        # Create the node
        new_node = OrganizationHierarchy(
            name=request.name,
            slug=base_slug,
            description=request.description,
            parent_id=request.parent_id,
            level=request.level,
            hierarchy_path=slug,
            depth=depth,
            legacy_organisation_id=parent_node.legacy_organisation_id if parent_node else None,
            is_active=True,
            settings=str(request.settings).replace("'", '"') if request.settings else None
        )
        
        db.add(new_node)
        db.commit()
        
        logger.info(f"Created hierarchy node: {new_node.name} at level {new_node.level.value}")
        
        return HierarchyNodeResponse(
            id=new_node.id,
            name=new_node.name,
            slug=new_node.slug,
            description=new_node.description,
            level=new_node.level.value,
            hierarchy_path=new_node.hierarchy_path,
            depth=new_node.depth,
            parent_id=new_node.parent_id,
            is_active=new_node.is_active,
            settings=json.loads(new_node.settings) if new_node.settings else None,
            children_count=0,
            user_count=0,
            created_at=new_node.created_at.isoformat(),
            updated_at=new_node.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating hierarchy node: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create hierarchy node: {str(e)}"
        )


@router.put("/hierarchy-nodes/{node_id}", response_model=HierarchyNodeResponse)
async def update_hierarchy_node(
    node_id: uuid.UUID = Path(...),
    request: UpdateHierarchyNodeRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["admin", "manage_settings"]))
):
    """Update a hierarchy node"""
    
    node = db.query(OrganizationHierarchy).filter(
        OrganizationHierarchy.id == node_id
    ).first()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hierarchy node not found"
        )
    
    try:
        # Update fields if provided
        if request.name is not None:
            node.name = request.name
        if request.description is not None:
            node.description = request.description
        if request.is_active is not None:
            node.is_active = request.is_active
        if request.settings is not None:
            node.settings = str(request.settings).replace("'", '"')
        
        db.commit()
        
        logger.info(f"Updated hierarchy node: {node.name}")
        
        # Return updated node (reuse logic from create)
        children_count = db.query(func.count(OrganizationHierarchy.id)).filter(
            OrganizationHierarchy.parent_id == node.id
        ).scalar()
        
        user_count = db.query(func.count(UserHierarchyAssignment.id)).filter(
            and_(
                UserHierarchyAssignment.hierarchy_node_id == node.id,
                UserHierarchyAssignment.is_active == True
            )
        ).scalar()
        
        return HierarchyNodeResponse(
            id=node.id,
            name=node.name,
            slug=node.slug,
            description=node.description,
            level=node.level.value,
            hierarchy_path=node.hierarchy_path,
            depth=node.depth,
            parent_id=node.parent_id,
            is_active=node.is_active,
            settings=json.loads(node.settings) if node.settings else None,
            children_count=children_count,
            user_count=user_count,
            created_at=node.created_at.isoformat(),
            updated_at=node.updated_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating hierarchy node: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update hierarchy node: {str(e)}"
        )


@router.delete("/hierarchy-nodes/{node_id}")
async def delete_hierarchy_node(
    node_id: uuid.UUID = Path(...),
    force: bool = Query(False, description="Force delete even if node has children"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["admin"]))
):
    """Delete a hierarchy node"""
    
    node = db.query(OrganizationHierarchy).filter(
        OrganizationHierarchy.id == node_id
    ).first()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hierarchy node not found"
        )
    
    # Check if node has children
    children_count = db.query(func.count(OrganizationHierarchy.id)).filter(
        OrganizationHierarchy.parent_id == node_id
    ).scalar()
    
    if children_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete node with children. Use force=true to override."
        )
    
    try:
        # If force delete, recursively delete all children
        if force and children_count > 0:
            def delete_recursively(parent_id: uuid.UUID):
                children = db.query(OrganizationHierarchy).filter(
                    OrganizationHierarchy.parent_id == parent_id
                ).all()
                
                for child in children:
                    delete_recursively(child.id)
                    
                    # Delete user assignments for this child
                    db.query(UserHierarchyAssignment).filter(
                        UserHierarchyAssignment.hierarchy_node_id == child.id
                    ).delete()
                    
                    # Delete role assignments for this child
                    db.query(HierarchyRoleAssignment).filter(
                        HierarchyRoleAssignment.hierarchy_node_id == child.id
                    ).delete()
                    
                    db.delete(child)
            
            delete_recursively(node_id)
        
        # Delete user assignments for the main node
        db.query(UserHierarchyAssignment).filter(
            UserHierarchyAssignment.hierarchy_node_id == node_id
        ).delete()
        
        # Delete role assignments for the main node
        db.query(HierarchyRoleAssignment).filter(
            HierarchyRoleAssignment.hierarchy_node_id == node_id
        ).delete()
        
        # Delete the main node
        db.delete(node)
        db.commit()
        
        logger.info(f"Deleted hierarchy node: {node.name} (force={force})")
        
        return {"message": "Hierarchy node deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting hierarchy node: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete hierarchy node: {str(e)}"
        )


@router.post("/hierarchy-nodes/{node_id}/assign-user")
async def assign_user_to_node(
    node_id: uuid.UUID = Path(...),
    request: AssignUserToNodeRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["admin", "manage_users"]))
):
    """Assign a user to a hierarchy node with specific role"""
    
    # Validate node exists
    node = db.query(OrganizationHierarchy).filter(
        OrganizationHierarchy.id == node_id
    ).first()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hierarchy node not found"
        )
    
    # Validate user exists
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Check for existing assignment
        existing_assignment = db.query(UserHierarchyAssignment).filter(
            and_(
                UserHierarchyAssignment.user_id == request.user_id,
                UserHierarchyAssignment.hierarchy_node_id == node_id
            )
        ).first()
        
        if existing_assignment:
            # Update existing assignment
            existing_assignment.role = request.role
            existing_assignment.is_active = True
            if request.is_primary:
                existing_assignment.is_primary = True
        else:
            # Create new assignment
            assignment = UserHierarchyAssignment(
                user_id=request.user_id,
                hierarchy_node_id=node_id,
                role=request.role,
                is_primary=request.is_primary,
                is_active=True
            )
            db.add(assignment)
        
        # If this is marked as primary, unmark other primary assignments for this user
        if request.is_primary:
            db.query(UserHierarchyAssignment).filter(
                and_(
                    UserHierarchyAssignment.user_id == request.user_id,
                    UserHierarchyAssignment.hierarchy_node_id != node_id
                )
            ).update({"is_primary": False})
        
        db.commit()
        
        logger.info(f"Assigned user {user.email} to node {node.name} with role {request.role.value}")
        
        return {
            "message": "User assigned successfully",
            "user_id": str(request.user_id),
            "node_id": str(node_id),
            "role": request.role.value,
            "is_primary": request.is_primary
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning user to node: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign user to node: {str(e)}"
        )


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: uuid.UUID = Path(...),
    context_node_id: Optional[uuid.UUID] = Query(None, description="Specific context node"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get resolved permissions for a user"""
    
    # Users can only view their own permissions unless they're admin
    if str(current_user.id) != str(user_id) and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own permissions"
        )
    
    permission_engine = PermissionResolutionEngine(db)
    resolved_permissions = permission_engine.resolve_user_permissions(
        user_id, context_node_id
    )
    
    return resolved_permissions


@router.get("/users/{user_id}/accessible-nodes")
async def get_user_accessible_nodes(
    user_id: uuid.UUID = Path(...),
    minimum_role: Optional[EnhancedUserRole] = Query(None, description="Minimum role filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all hierarchy nodes accessible to a user"""
    
    # Users can only view their own accessible nodes unless they're admin
    if str(current_user.id) != str(user_id) and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own accessible nodes"
        )
    
    permission_engine = PermissionResolutionEngine(db)
    accessible_nodes = permission_engine.get_accessible_nodes(user_id, minimum_role)
    
    return {"accessible_nodes": accessible_nodes}