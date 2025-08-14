from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uuid
import secrets
from ....core.database import get_db
from ....models.user import User, UserRole
from ....models.user_application_access import UserApplicationAccess, UserInvitation, ApplicationType, InvitationStatus
from ....models.organisation import Organisation
from ....auth.dependencies import get_current_user, require_admin
from ....services.auth import send_invitation_email

router = APIRouter()


class ApplicationAccess(BaseModel):
    application: ApplicationType
    has_access: bool


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    organisation_id: str
    organisation_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    invitation_status: InvitationStatus
    application_access: Dict[str, bool]

    class Config:
        from_attributes = True


class BulkUserCreate(BaseModel):
    users: List["UserCreate"]
    send_invitations: bool = True


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole = UserRole.viewer
    organisation_id: Optional[str] = None  # For super admin use
    application_access: List[ApplicationAccess] = []
    send_invitation: bool = True


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    application_access: Optional[List[ApplicationAccess]] = None


class InvitationResend(BaseModel):
    organization_name: Optional[str] = None


# Super Admin endpoints for cross-organization user management
@router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    organisation_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get users across all organizations (Super Admin only)"""
    query = db.query(User).options(
        joinedload(User.organisation),
        joinedload(User.application_access),
        joinedload(User.invitations)
    )
    
    if organisation_id:
        query = query.filter(User.organisation_id == organisation_id)
    
    users = query.offset(skip).limit(limit).all()
    
    return [_format_user_response(user) for user in users]


@router.post("/admin/users", response_model=UserResponse)
async def create_user_admin(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create new user in any organization (Super Admin only)"""
    return await _create_user_internal(user_data, background_tasks, db, current_user)


@router.post("/admin/users/bulk", response_model=List[UserResponse])
async def bulk_create_users_admin(
    bulk_data: BulkUserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Bulk create users across organizations (Super Admin only)"""
    created_users = []
    
    for user_data in bulk_data.users:
        user_data.send_invitation = bulk_data.send_invitations
        try:
            created_user = await _create_user_internal(user_data, background_tasks, db, current_user)
            created_users.append(created_user)
        except HTTPException as e:
            # Continue creating other users even if one fails
            print(f"Failed to create user {user_data.email}: {e.detail}")
            continue
    
    return created_users


# Organization-scoped endpoints
@router.get("/organizations/{org_id}/users", response_model=List[UserResponse])
async def get_organization_users(
    org_id: str,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get users in specific organization"""
    # Verify access
    if current_user.role != UserRole.admin and str(current_user.organisation_id) != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    query = db.query(User).options(
        joinedload(User.organisation),
        joinedload(User.application_access),
        joinedload(User.invitations)
    ).filter(User.organisation_id == org_id)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            User.first_name.ilike(search_term) |
            User.last_name.ilike(search_term) |
            User.email.ilike(search_term)
        )
    
    if role and role != "all":
        query = query.filter(User.role == role)
    
    users = query.offset(skip).limit(limit).all()
    
    return [_format_user_response(user) for user in users]


@router.post("/organizations/{org_id}/users", response_model=UserResponse)
async def create_organization_user(
    org_id: str,
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new user in specific organization"""
    # Verify access
    if current_user.role != UserRole.admin and str(current_user.organisation_id) != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    user_data.organisation_id = org_id
    return await _create_user_internal(user_data, background_tasks, db, current_user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user"""
    user = db.query(User).options(
        joinedload(User.organisation),
        joinedload(User.application_access),
        joinedload(User.invitations)
    ).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify access
    if current_user.role != UserRole.admin and user.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this user"
        )
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True, exclude={'application_access'})
    for field, value in update_data.items():
        setattr(user, field, value)
    
    # Update application access if provided
    if user_update.application_access is not None:
        # Remove existing access
        db.query(UserApplicationAccess).filter(UserApplicationAccess.user_id == user.id).delete()
        
        # Add new access
        for access in user_update.application_access:
            db.add(UserApplicationAccess(
                user_id=user.id,
                application=access.application,
                has_access=access.has_access,
                granted_by=current_user.id
            ))
    
    db.commit()
    db.refresh(user)
    
    return _format_user_response(user)


@router.post("/users/{user_id}/invite")
async def send_user_invitation(
    user_id: str,
    invitation_data: InvitationResend,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send or resend invitation to user"""
    user = db.query(User).options(joinedload(User.organisation)).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify access
    if current_user.role != UserRole.admin and user.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this user"
        )
    
    # Create or update invitation
    invitation_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    # Check for existing invitation
    existing_invitation = db.query(UserInvitation).filter(UserInvitation.user_id == user.id).first()
    
    if existing_invitation:
        existing_invitation.invitation_token = invitation_token
        existing_invitation.status = InvitationStatus.PENDING
        existing_invitation.invited_by = current_user.id
        existing_invitation.invited_at = datetime.utcnow()
        existing_invitation.expires_at = expires_at
    else:
        invitation = UserInvitation(
            user_id=user.id,
            invitation_token=invitation_token,
            status=InvitationStatus.PENDING,
            invited_by=current_user.id,
            expires_at=expires_at
        )
        db.add(invitation)
    
    db.commit()
    
    # Send invitation email
    background_tasks.add_task(
        send_invitation_email,
        user.email,
        user.first_name,
        user.organisation.name if user.organisation else invitation_data.organization_name,
        invitation_token
    )
    
    return {"message": "Invitation sent successfully"}


@router.post("/users/{user_id}/resend-invite")
async def resend_user_invitation(
    user_id: str,
    invitation_data: InvitationResend,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resend invitation to user"""
    return await send_user_invitation(user_id, invitation_data, background_tasks, db, current_user)


# Application access management
@router.get("/users/{user_id}/application-access", response_model=List[ApplicationAccess])
async def get_user_application_access(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's application access permissions"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify access
    if current_user.role != UserRole.admin and user.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this user"
        )
    
    access_list = db.query(UserApplicationAccess).filter(UserApplicationAccess.user_id == user.id).all()
    
    return [ApplicationAccess(
        application=access.application,
        has_access=access.has_access
    ) for access in access_list]


@router.put("/users/{user_id}/application-access")
async def update_user_application_access(
    user_id: str,
    access_updates: List[ApplicationAccess],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's application access permissions"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify access
    if current_user.role != UserRole.admin and user.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this user"
        )
    
    # Remove existing access
    db.query(UserApplicationAccess).filter(UserApplicationAccess.user_id == user.id).delete()
    
    # Add new access
    for access in access_updates:
        db.add(UserApplicationAccess(
            user_id=user.id,
            application=access.application,
            has_access=access.has_access,
            granted_by=current_user.id
        ))
    
    db.commit()
    
    return {"message": "Application access updated successfully"}


# Bulk application access management
@router.put("/bulk/application-access")
async def bulk_update_application_access(
    updates: Dict[str, List[ApplicationAccess]],  # user_id -> access list
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk update application access for multiple users"""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform bulk updates"
        )
    
    for user_id, access_list in updates.items():
        user = db.query(User).filter(User.id == user_id).first()
        if user and (current_user.role == UserRole.admin or user.organisation_id == current_user.organisation_id):
            # Remove existing access
            db.query(UserApplicationAccess).filter(UserApplicationAccess.user_id == user.id).delete()
            
            # Add new access
            for access in access_list:
                db.add(UserApplicationAccess(
                    user_id=user.id,
                    application=access.application,
                    has_access=access.has_access,
                    granted_by=current_user.id
                ))
    
    db.commit()
    
    return {"message": f"Application access updated for {len(updates)} users"}


# Helper functions
async def _create_user_internal(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session,
    current_user: User
) -> UserResponse:
    """Internal user creation logic"""
    # Check if user with this email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Determine organization ID
    org_id = user_data.organisation_id or str(current_user.organisation_id)
    
    # Verify organization exists
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization not found"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        organisation_id=org_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Set up application access
    for access in user_data.application_access:
        db.add(UserApplicationAccess(
            user_id=new_user.id,
            application=access.application,
            has_access=access.has_access,
            granted_by=current_user.id
        ))
    
    db.commit()
    
    # Send invitation if requested
    if user_data.send_invitation:
        invitation_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        invitation = UserInvitation(
            user_id=new_user.id,
            invitation_token=invitation_token,
            status=InvitationStatus.PENDING,
            invited_by=current_user.id,
            expires_at=expires_at
        )
        db.add(invitation)
        db.commit()
        
        background_tasks.add_task(
            send_invitation_email,
            new_user.email,
            new_user.first_name,
            org.name,
            invitation_token
        )
    
    # Reload with relationships
    new_user = db.query(User).options(
        joinedload(User.organisation),
        joinedload(User.application_access),
        joinedload(User.invitations)
    ).filter(User.id == new_user.id).first()
    
    return _format_user_response(new_user)


def _format_user_response(user: User) -> UserResponse:
    """Format user object for API response"""
    # Get latest invitation status
    invitation_status = InvitationStatus.ACCEPTED
    if user.invitations:
        latest_invitation = max(user.invitations, key=lambda inv: inv.invited_at)
        invitation_status = latest_invitation.status
    
    # Get application access
    app_access = {}
    for access in user.application_access:
        app_access[access.application.value] = access.has_access
    
    # Default access for applications not explicitly set
    for app_type in ApplicationType:
        if app_type.value not in app_access:
            app_access[app_type.value] = False
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        organisation_id=str(user.organisation_id),
        organisation_name=user.organisation.name if user.organisation else None,
        is_active=user.is_active,
        created_at=user.created_at,
        invitation_status=invitation_status,
        application_access=app_access
    )