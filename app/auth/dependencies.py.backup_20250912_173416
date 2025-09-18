from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db, get_async_db
from ..models.user import User, UserRole
from ..models.organisation import Organisation
from .jwt import verify_token, extract_tenant_context_from_token, should_refresh_token
from ..auth.auth0 import auth0_client
from ..core.config import settings
from ..core.logging import logger
import httpx

security = HTTPBearer(auto_error=False)  # Disable auto_error to handle manually

async def verify_auth0_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify Auth0 token directly by calling Auth0 userinfo endpoint"""
    try:
        # Get user info from Auth0 using the token
        user_info = await auth0_client.get_user_info(token)
        if not user_info:
            logger.warning("Failed to verify Auth0 token - no user info returned")
            return None
        
        # Extract relevant claims from Auth0 user info
        # Auth0 tokens have different structure than internal tokens
        return {
            "sub": user_info.get("sub"),
            "email": user_info.get("email"), 
            "user_role": user_info.get("user_role", "viewer"),
            "role": user_info.get("user_role", "viewer"),  # For compatibility
            "organisation_id": user_info.get("organisation_id"),
            "tenant_id": user_info.get("organisation_id"),  # For compatibility
            "type": "auth0_access",  # Distinguish from internal tokens
            "iss": user_info.get("iss", f"https://{settings.AUTH0_DOMAIN}/"),
            "aud": [f"https://{settings.AUTH0_DOMAIN}/userinfo"],
            "permissions": user_info.get("permissions", [])
        }
        
    except Exception as e:
        logger.warning(f"Auth0 token verification failed: {e}")
        return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """Enhanced user authentication with multi-tenant context validation - ASYNC version"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Handle missing Authorization header with proper 401 status
    if not credentials:
        logger.warning("No credentials provided", extra={
            "event": "auth_no_credentials",
            "path": request.url.path
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token with enhanced validation
    payload = verify_token(credentials.credentials, expected_type="access")
    
    # CRITICAL FIX: Fallback to Auth0 token verification if internal JWT fails
    # This supports Matt.Lindop's Auth0 tokens for the £925K Zebra opportunity
    if payload is None:
        logger.info("Internal JWT verification failed, trying Auth0 token verification", extra={
            "event": "auth_fallback_to_auth0",
            "path": request.url.path
        })
        
        payload = await verify_auth0_token(credentials.credentials)
        if payload is None:
            logger.warning("Both internal JWT and Auth0 token verification failed", extra={
                "event": "auth_token_invalid_both",
                "path": request.url.path
            })
            raise credentials_exception
        else:
            logger.info("Auth0 token verification successful", extra={
                "event": "auth0_token_verified",
                "path": request.url.path,
                "user_email": payload.get("email")
            })
    
    user_id: str = payload.get("sub")
    tenant_id: str = payload.get("tenant_id")
    user_role: str = payload.get("role")
    
    if user_id is None:
        logger.warning("Missing user ID in token", extra={
            "event": "auth_missing_user_id",
            "token_jti": payload.get("jti"),
            "path": request.url.path
        })
        raise credentials_exception
    
    # Get user with organization loaded - using async query
    result = await db.execute(
        select(User)
        .options(selectinload(User.organisation))
        .filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        logger.warning("User not found", extra={
            "event": "auth_user_not_found",
            "user_id": user_id,
            "path": request.url.path
        })
        raise credentials_exception
    
    if not user.is_active:
        logger.warning("Inactive user attempted access", extra={
            "event": "auth_user_inactive",
            "user_id": user_id,
            "path": request.url.path
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Validate tenant context
    if tenant_id and str(user.organisation_id) != tenant_id:
        logger.error("Tenant context mismatch", extra={
            "event": "auth_tenant_mismatch",
            "user_id": user_id,
            "token_tenant_id": tenant_id,
            "user_tenant_id": str(user.organisation_id),
            "path": request.url.path
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context mismatch"
        )
    
    # Validate role consistency
    if user_role and user.role.value != user_role:
        logger.warning("Role mismatch detected", extra={
            "event": "auth_role_mismatch",
            "user_id": user_id,
            "token_role": user_role,
            "user_role": user.role.value,
            "path": request.url.path
        })
        # Update user role if it changed (but log it for security audit)
        
    # Check if token needs refresh
    if should_refresh_token(payload, threshold_minutes=5):
        logger.info("Token approaching expiration", extra={
            "event": "auth_token_expiring",
            "user_id": user_id,
            "token_jti": payload.get("jti")
        })
        # Could set a header to indicate refresh needed
        # response.headers["X-Token-Refresh-Recommended"] = "true"
    
    # Store tenant context in request state for use by endpoints
    request.state.tenant_context = extract_tenant_context_from_token(payload)
    
    logger.debug("User authentication successful", extra={
        "event": "auth_success",
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": user_role,
        "path": request.url.path
    })
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user - redundant check as get_current_user already validates this"""
    return current_user


def require_permission(required_permissions: List[str]):
    """Decorator factory to require specific permissions"""
    def permission_dependency(
        request: Request,
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check if user has required permissions"""
        tenant_context = getattr(request.state, 'tenant_context', {})
        user_permissions = tenant_context.get('permissions', [])
        
        # Check if user has any of the required permissions
        if not any(perm in user_permissions for perm in required_permissions):
            logger.warning("Insufficient permissions", extra={
                "event": "auth_insufficient_permissions",
                "user_id": str(current_user.id),
                "required_permissions": required_permissions,
                "user_permissions": user_permissions,
                "path": request.url.path
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(required_permissions)}"
            )
        
        return current_user
    
    return permission_dependency


def require_role(required_roles: List[UserRole]):
    """Decorator factory to require specific roles"""
    def role_dependency(
        request: Request,
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check if user has required role"""
        if current_user.role not in required_roles:
            logger.warning("Insufficient role", extra={
                "event": "auth_insufficient_role",
                "user_id": str(current_user.id),
                "required_roles": [role.value for role in required_roles],
                "user_role": current_user.role.value,
                "path": request.url.path
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(role.value for role in required_roles)}"
            )
        
        return current_user
    
    return role_dependency


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role (admin or super_admin) - ASYNC version"""
    if current_user.role not in [UserRole.admin, UserRole.super_admin]:
        logger.warning("Admin role required", extra={
            "event": "auth_admin_required",
            "user_id": str(current_user.id),
            "user_role": current_user.role.value
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    return current_user


async def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require super admin role for cross-tenant operations"""
    if current_user.role != UserRole.super_admin:
        logger.warning("Super admin role required", extra={
            "event": "auth_super_admin_required",
            "user_id": str(current_user.id),
            "user_role": current_user.role.value
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super administrator privileges required for cross-tenant operations"
        )
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and ensure they have admin role"""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    return current_user


# Synchronous versions for backwards compatibility
def get_current_user_sync(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Synchronous version of get_current_user for sync endpoints"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Handle missing Authorization header with proper 401 status
    if not credentials:
        logger.warning("No credentials provided", extra={
            "event": "auth_no_credentials",
            "path": request.url.path
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token with enhanced validation
    payload = verify_token(credentials.credentials, expected_type="access")
    
    # NOTE: Sync version doesn't support Auth0 fallback - use async endpoints for Auth0 tokens
    if payload is None:
        logger.warning("Token verification failed in sync context", extra={
            "event": "auth_token_invalid_sync",
            "path": request.url.path,
            "note": "Use async endpoints for Auth0 token support"
        })
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    tenant_id: str = payload.get("tenant_id")
    user_role: str = payload.get("role")
    
    if user_id is None:
        logger.warning("Missing user ID in token", extra={
            "event": "auth_missing_user_id",
            "token_jti": payload.get("jti"),
            "path": request.url.path
        })
        raise credentials_exception
    
    # Get user with organization loaded - using sync query
    user = db.query(User).options(joinedload(User.organisation)).filter(User.id == user_id).first()
    if user is None:
        logger.warning("User not found", extra={
            "event": "auth_user_not_found",
            "user_id": user_id,
            "path": request.url.path
        })
        raise credentials_exception
    
    if not user.is_active:
        logger.warning("Inactive user attempted access", extra={
            "event": "auth_user_inactive",
            "user_id": user_id,
            "path": request.url.path
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Validate tenant context
    if tenant_id and str(user.organisation_id) != tenant_id:
        logger.error("Tenant context mismatch", extra={
            "event": "auth_tenant_mismatch",
            "user_id": user_id,
            "token_tenant_id": tenant_id,
            "user_tenant_id": str(user.organisation_id),
            "path": request.url.path
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context mismatch"
        )
    
    # Validate role consistency
    if user_role and user.role.value != user_role:
        logger.warning("Role mismatch detected", extra={
            "event": "auth_role_mismatch",
            "user_id": user_id,
            "token_role": user_role,
            "user_role": user.role.value,
            "path": request.url.path
        })
    
    # Check if token needs refresh
    if should_refresh_token(payload, threshold_minutes=5):
        logger.info("Token approaching expiration", extra={
            "event": "auth_token_expiring",
            "user_id": user_id,
            "token_jti": payload.get("jti")
        })
    
    # Store tenant context in request state for use by endpoints
    request.state.tenant_context = extract_tenant_context_from_token(payload)
    
    logger.debug("User authentication successful", extra={
        "event": "auth_success",
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": user_role,
        "path": request.url.path
    })
    
    return user


def require_admin_sync(current_user: User = Depends(get_current_user_sync)) -> User:
    """Synchronous version of require_admin for sync endpoints"""
    if current_user.role not in [UserRole.admin, UserRole.super_admin]:
        logger.warning("Admin role required", extra={
            "event": "auth_admin_required",
            "user_id": str(current_user.id),
            "user_role": current_user.role.value
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    return current_user


def require_same_tenant_or_admin(target_tenant_id: str = None):
    """Require user to be in same tenant or be an admin"""
    def tenant_dependency(
        request: Request,
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Check tenant access permissions"""
        # Admins can access any tenant
        if current_user.role == UserRole.admin:
            return current_user
            
        # Get target tenant ID from request if not provided
        if target_tenant_id is None:
            # Try to get from path params or query params
            tenant_id_from_request = request.path_params.get('tenant_id') or request.query_params.get('tenant_id')
        else:
            tenant_id_from_request = target_tenant_id
            
        if tenant_id_from_request and str(current_user.organisation_id) != str(tenant_id_from_request):
            logger.warning("Cross-tenant access denied", extra={
                "event": "auth_cross_tenant_denied",
                "user_id": str(current_user.id),
                "user_tenant_id": str(current_user.organisation_id),
                "target_tenant_id": tenant_id_from_request,
                "path": request.url.path
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cross-tenant operation not allowed"
            )
            
        return current_user
        
    return tenant_dependency


def get_tenant_context(request: Request) -> Optional[Dict[str, Any]]:
    """Get tenant context from request state"""
    return getattr(request.state, 'tenant_context', None)


async def validate_api_key(
    request: Request,
    api_key: Optional[str] = None
) -> bool:
    """Validate API key for service-to-service authentication"""
    # This would typically validate against a database of API keys
    # For now, just log the attempt
    logger.info("API key validation attempt", extra={
        "event": "api_key_validation",
        "has_api_key": bool(api_key),
        "path": request.url.path
    })
    
    # Implement actual API key validation logic here
    return False  # Disabled for now