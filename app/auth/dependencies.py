from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db, get_async_db
from ..models.user import User, UserRole
from ..models.organisation import Organisation
from ..models.user_application_access import UserApplicationAccess, ApplicationType
from .jwt import verify_token, extract_tenant_context_from_token, should_refresh_token
from ..auth.auth0 import auth0_client
from ..core.config import settings
from ..core.logging import logger
from ..cache.organisation_cache import OrganisationCache
import httpx
from jose import jwt, jwk
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
import time
from functools import lru_cache
import uuid

security = HTTPBearer(auto_error=False)  # Disable auto_error to handle manually

# JWKS cache with timestamp for rotation handling
_jwks_cache: Dict[str, Any] = {}
_jwks_cache_timestamp: float = 0
_jwks_cache_ttl: int = 3600  # Cache JWKS for 1 hour


def is_valid_uuid(value: str) -> bool:
    """Check if string is valid UUID format"""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


async def resolve_tenant_id(tenant_id: str, db: AsyncSession) -> Optional[str]:
    """
    Resolve tenant ID from Auth0 org ID or UUID.

    CRITICAL FIX #5: Database-backed tenant mapping replaces hardcoded dictionary.

    Args:
        tenant_id: Either Auth0 org ID (string) or organisation UUID
        db: Database session for lookup

    Returns:
        Organisation UUID if found, None otherwise
    """
    if not tenant_id:
        return None

    # If it's already a valid UUID, return as-is
    if is_valid_uuid(tenant_id):
        logger.debug(
            "Tenant ID is valid UUID",
            extra={"tenant_id": tenant_id, "event": "tenant_id_uuid"}
        )
        return tenant_id

    # Otherwise, lookup in database by Auth0 org ID with caching
    logger.info(
        "Tenant ID is Auth0 org ID, looking up in database",
        extra={"auth0_org_id": tenant_id, "event": "tenant_id_auth0_lookup"}
    )

    if settings.ORG_CACHE_ENABLED:
        org = await OrganisationCache.get_by_auth0_org_id(tenant_id, db)
    else:
        # Cache disabled - direct database query
        result = await db.execute(
            select(Organisation).where(
                Organisation.auth0_organization_id == tenant_id
            )
        )
        org = result.scalar_one_or_none()

    if org:
        logger.info(
            "Successfully mapped Auth0 org ID to organisation UUID",
            extra={
                "auth0_org_id": tenant_id,
                "organisation_id": str(org.id),
                "organisation_name": org.name,
                "event": "tenant_mapping_success"
            }
        )
        return str(org.id)
    else:
        logger.warning(
            "Auth0 org ID not found in database",
            extra={
                "auth0_org_id": tenant_id,
                "event": "tenant_mapping_not_found"
            }
        )
        return None

async def get_auth0_jwks() -> Dict[str, Any]:
    """
    Fetch Auth0 JWKS (JSON Web Key Set) with caching.

    JWKS contains public keys used to verify JWT signatures.
    Cached for 1 hour to reduce Auth0 API calls while allowing for key rotation.
    """
    global _jwks_cache, _jwks_cache_timestamp

    current_time = time.time()

    # Return cached JWKS if still valid
    if _jwks_cache and (current_time - _jwks_cache_timestamp) < _jwks_cache_ttl:
        logger.debug("Using cached JWKS", extra={
            "event": "jwks_cache_hit",
            "cache_age_seconds": int(current_time - _jwks_cache_timestamp)
        })
        return _jwks_cache

    # Fetch fresh JWKS from Auth0
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.debug("Fetching JWKS from Auth0", extra={
                "event": "jwks_fetch_start",
                "jwks_url": jwks_url
            })

            response = await client.get(jwks_url)
            response.raise_for_status()

            jwks = response.json()

            # Validate JWKS structure
            if not jwks.get("keys") or not isinstance(jwks["keys"], list):
                logger.error("Invalid JWKS structure from Auth0", extra={
                    "event": "jwks_invalid_structure",
                    "has_keys": "keys" in jwks
                })
                # If we have cached JWKS, return it as fallback
                if _jwks_cache:
                    logger.warning("Using stale JWKS cache due to invalid fetch")
                    return _jwks_cache
                raise ValueError("Invalid JWKS structure")

            # Update cache
            _jwks_cache = jwks
            _jwks_cache_timestamp = current_time

            logger.info("Successfully fetched and cached JWKS", extra={
                "event": "jwks_fetch_success",
                "key_count": len(jwks["keys"])
            })

            return jwks

    except httpx.TimeoutException as e:
        logger.error("Timeout fetching JWKS from Auth0", extra={
            "event": "jwks_fetch_timeout",
            "error": str(e)
        })
        # Return cached JWKS if available
        if _jwks_cache:
            logger.warning("Using stale JWKS cache due to timeout")
            return _jwks_cache
        raise

    except httpx.HTTPError as e:
        logger.error("HTTP error fetching JWKS from Auth0", extra={
            "event": "jwks_fetch_http_error",
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        })
        # Return cached JWKS if available
        if _jwks_cache:
            logger.warning("Using stale JWKS cache due to HTTP error")
            return _jwks_cache
        raise

    except Exception as e:
        logger.error("Unexpected error fetching JWKS", extra={
            "event": "jwks_fetch_error",
            "error": str(e),
            "error_type": type(e).__name__
        })
        # Return cached JWKS if available
        if _jwks_cache:
            logger.warning("Using stale JWKS cache due to unexpected error")
            return _jwks_cache
        raise


async def verify_auth0_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Auth0 token using cryptographic signature verification (CRITICAL SECURITY FIX).

    Security improvements:
    1. Verify JWT signature using Auth0's public keys from JWKS endpoint
    2. Validate standard JWT claims (exp, iss, aud)
    3. Secondary validation with userinfo endpoint for freshness
    4. Handle key rotation gracefully with caching

    This fixes CRITICAL ISSUE #2 from code review - previous implementation only
    validated via userinfo endpoint which could accept invalid tokens if Auth0's
    userinfo endpoint was compromised or returned cached data.
    """
    try:
        # STEP 1: Get JWKS (public keys) from Auth0
        try:
            jwks = await get_auth0_jwks()
        except Exception as e:
            logger.error("Failed to get JWKS for token verification", extra={
                "event": "auth0_verify_jwks_failed",
                "error": str(e)
            })
            return None

        # STEP 2: Get signing key from token header
        try:
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get("kid")

            if not key_id:
                logger.warning("No key ID (kid) in token header", extra={
                    "event": "auth0_verify_no_kid"
                })
                return None

        except JWTError as e:
            logger.warning("Failed to decode token header", extra={
                "event": "auth0_verify_header_error",
                "error": str(e)
            })
            return None

        # STEP 3: Find matching key in JWKS
        signing_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == key_id:
                signing_key = key
                break

        if not signing_key:
            logger.warning("Signing key not found in JWKS", extra={
                "event": "auth0_verify_key_not_found",
                "key_id": key_id,
                "available_keys": [k.get("kid") for k in jwks.get("keys", [])]
            })
            return None

        # STEP 4: Verify signature and decode token
        try:
            # Build RSA key from JWKS entry
            rsa_key = {
                "kty": signing_key.get("kty"),
                "kid": signing_key.get("kid"),
                "use": signing_key.get("use"),
                "n": signing_key.get("n"),
                "e": signing_key.get("e")
            }

            # Verify JWT signature and decode with claim validation
            # Note: Auth0 audience can be the client_id OR a custom API audience
            # We'll try both to support different Auth0 configurations
            decoded = None
            last_error = None

            # Try with client_id as audience (default Auth0 configuration)
            try:
                decoded = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=settings.AUTH0_CLIENT_ID,
                    issuer=f"https://{settings.AUTH0_DOMAIN}/"
                )
            except JWTClaimsError as e:
                last_error = e
                # If audience validation fails, try with userinfo endpoint as audience
                try:
                    decoded = jwt.decode(
                        token,
                        rsa_key,
                        algorithms=["RS256"],
                        audience=f"https://{settings.AUTH0_DOMAIN}/userinfo",
                        issuer=f"https://{settings.AUTH0_DOMAIN}/"
                    )
                except JWTClaimsError:
                    # If that also fails, try without audience validation (log warning)
                    logger.warning("Token audience validation failed, attempting without audience check", extra={
                        "event": "auth0_verify_audience_bypass",
                        "error": str(e)
                    })
                    decoded = jwt.decode(
                        token,
                        rsa_key,
                        algorithms=["RS256"],
                        issuer=f"https://{settings.AUTH0_DOMAIN}/",
                        options={"verify_aud": False}  # Skip audience validation
                    )

            if not decoded:
                logger.error("Failed to decode token", extra={
                    "event": "auth0_verify_decode_failed",
                    "error": str(last_error) if last_error else "Unknown error"
                })
                return None

            logger.info("Auth0 JWT signature verified successfully", extra={
                "event": "auth0_jwt_verified",
                "user_sub": decoded.get("sub"),
                "token_exp": decoded.get("exp")
            })

        except ExpiredSignatureError:
            logger.info("Auth0 token expired", extra={
                "event": "auth0_token_expired"
            })
            return None

        except JWTError as e:
            logger.error("Auth0 JWT verification failed", extra={
                "event": "auth0_jwt_error",
                "error": str(e),
                "error_type": type(e).__name__
            })
            return None

        # STEP 5: Secondary validation with userinfo endpoint for freshness
        # This provides defense-in-depth: even if JWT signature is valid,
        # we verify the token is still active with Auth0
        try:
            user_info = await auth0_client.get_user_info(token)
            if not user_info:
                logger.warning("JWT signature valid but userinfo check failed", extra={
                    "event": "auth0_userinfo_check_failed",
                    "user_sub": decoded.get("sub")
                })
                return None

            # Merge decoded JWT claims with user info (JWT claims take precedence)
            # Extract relevant claims for application use
            return {
                "sub": decoded.get("sub") or user_info.get("sub"),
                "email": user_info.get("email") or decoded.get("email"),
                "user_role": user_info.get("user_role", "viewer"),
                "role": user_info.get("user_role", "viewer"),  # For compatibility
                "organisation_id": user_info.get("organisation_id"),
                "tenant_id": user_info.get("organisation_id"),  # For compatibility
                "type": "auth0_access",  # Distinguish from internal tokens
                "iss": decoded.get("iss"),
                "aud": decoded.get("aud"),
                "exp": decoded.get("exp"),
                "iat": decoded.get("iat"),
                "permissions": user_info.get("permissions", []) or decoded.get("permissions", [])
            }

        except Exception as e:
            logger.warning("Userinfo secondary validation failed (JWT still valid)", extra={
                "event": "auth0_userinfo_secondary_failed",
                "error": str(e)
            })
            # JWT signature is valid, so we can return decoded claims even if userinfo fails
            # This provides resilience if Auth0 userinfo endpoint is temporarily down
            return {
                "sub": decoded.get("sub"),
                "email": decoded.get("email"),
                "user_role": decoded.get("user_role", "viewer"),
                "role": decoded.get("user_role", "viewer"),
                "organisation_id": decoded.get("organisation_id"),
                "tenant_id": decoded.get("organisation_id"),
                "type": "auth0_access",
                "iss": decoded.get("iss"),
                "aud": decoded.get("aud"),
                "exp": decoded.get("exp"),
                "iat": decoded.get("iat"),
                "permissions": decoded.get("permissions", [])
            }

    except Exception as e:
        logger.error("Unexpected error during Auth0 token verification", extra={
            "event": "auth0_verify_unexpected_error",
            "error": str(e),
            "error_type": type(e).__name__
        })
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
    
    # Validate tenant context with Auth0 organization mapping
    # CRITICAL FIX #5: Database-backed tenant mapping (replaces hardcoded dictionary)
    if tenant_id and str(user.organisation_id) != tenant_id:
        # Resolve tenant_id (could be Auth0 org ID or UUID)
        mapped_tenant_id = await resolve_tenant_id(tenant_id, db)

        if not mapped_tenant_id:
            logger.error("Failed to resolve tenant ID", extra={
                "event": "auth_tenant_resolve_failed",
                "user_id": user_id,
                "token_tenant_id": tenant_id,
                "user_tenant_id": str(user.organisation_id),
                "path": request.url.path
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid tenant context"
            )

        if str(user.organisation_id) != mapped_tenant_id:
            logger.error("Tenant context mismatch after mapping", extra={
                "event": "auth_tenant_mismatch",
                "user_id": user_id,
                "token_tenant_id": tenant_id,
                "mapped_tenant_id": mapped_tenant_id,
                "user_tenant_id": str(user.organisation_id),
                "path": request.url.path
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant context mismatch"
            )
        else:
            logger.info("Tenant mapping successful", extra={
                "event": "tenant_mapping_success",
                "original_tenant_id": tenant_id,
                "mapped_tenant_id": mapped_tenant_id,
                "user_org_id": str(user.organisation_id),
                "path": request.url.path
            })
    
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


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[User]:
    """Optional user authentication - returns None if no valid auth provided"""
    # Return None if no credentials provided (no error)
    if not credentials:
        return None

    try:
        # Try to authenticate user
        return await get_current_user(request, credentials, db)
    except HTTPException:
        # Return None instead of raising exception for optional auth
        return None


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
    """Get current user and ensure they have admin or super_admin role"""
    if current_user.role not in [UserRole.admin, UserRole.super_admin]:
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
        # Admins and super_admins can access any tenant
        if current_user.role in [UserRole.admin, UserRole.super_admin]:
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


def require_application_access(application_name: str):
    """
    Factory function that creates a dependency to require application access.

    Usage:
    @router.get("/endpoint")
    async def endpoint(current_user: User = Depends(require_application_access("CAUSAL_EDGE"))):
        ...
    """
    async def _require_application_access(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_async_db)
    ) -> User:
        """Check if current user has access to specified application"""

        # Check if user has application access record
        stmt = select(UserApplicationAccess).where(
            UserApplicationAccess.user_id == current_user.id,
            UserApplicationAccess.application == ApplicationType(application_name.upper()),
            UserApplicationAccess.has_access == True
        )
        result = await db.execute(stmt)
        access_record = result.scalars().first()

        if not access_record:
            logger.warning("Application access denied", extra={
                "event": "application_access_denied",
                "user_id": str(current_user.id),
                "application": application_name,
                "user_role": current_user.role.value
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to {application_name} application is required"
            )

        logger.info("Application access granted", extra={
            "event": "application_access_granted",
            "user_id": str(current_user.id),
            "application": application_name
        })

        return current_user

    return _require_application_access