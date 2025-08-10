"""
Tenant Context Middleware

Automatically enforces tenant data isolation at the API level by:
1. Extracting tenant context from authenticated user
2. Setting database session variables for RLS policies
3. Ensuring all database operations are scoped to user's tenant
4. Supporting super admin cross-tenant access when explicitly allowed
"""
import time
import logging
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..auth.jwt import verify_token
from ..models.user import User, UserRole
from ..core.database import get_db

logger = logging.getLogger(__name__)

# Routes that don't require tenant context
EXCLUDED_ROUTES = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/auth0-url",
    "/api/v1/auth/refresh",
}

class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically sets tenant context for all authenticated requests.
    
    Ensures data isolation by:
    - Extracting user's organisation_id from JWT token
    - Setting PostgreSQL session variables for RLS policies
    - Handling super admin cross-tenant access
    - Providing proper error handling for security violations
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware processing logic."""
        start_time = time.time()
        
        try:
            # Skip tenant context for excluded routes
            if self._should_skip_tenant_context(request):
                return await call_next(request)
            
            # Extract and validate tenant context
            tenant_context = await self._extract_tenant_context(request)
            
            if tenant_context:
                # Set database session variables
                await self._set_database_context(tenant_context)
                
                # Add context to request state for access by endpoints
                request.state.tenant_id = tenant_context["tenant_id"]
                request.state.user_role = tenant_context["user_role"]
                request.state.user_id = tenant_context["user_id"]
                
                logger.info(
                    "Tenant context established",
                    extra={
                        "event": "tenant_context_set",
                        "tenant_id": str(tenant_context["tenant_id"]),
                        "user_role": tenant_context["user_role"],
                        "user_id": str(tenant_context["user_id"]),
                        "path": request.url.path
                    }
                )
            
            # Process the request
            response = await call_next(request)
            
            # Clear database context after request
            if tenant_context:
                await self._clear_database_context()
            
            # Add performance metrics
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            response.headers["X-Tenant-Processing-Time"] = f"{processing_time:.2f}ms"
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            logger.error(
                "Tenant context middleware error",
                extra={
                    "event": "middleware_error",
                    "error": str(e),
                    "path": request.url.path
                },
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error in tenant context processing"
            )
    
    def _should_skip_tenant_context(self, request: Request) -> bool:
        """Check if request should skip tenant context processing."""
        path = request.url.path
        
        # Skip excluded routes
        if path in EXCLUDED_ROUTES:
            return True
        
        # Skip routes that start with excluded patterns
        excluded_prefixes = ["/static/", "/favicon.ico"]
        if any(path.startswith(prefix) for prefix in excluded_prefixes):
            return True
        
        return False
    
    async def _extract_tenant_context(self, request: Request) -> Optional[dict]:
        """Extract tenant context from authenticated user."""
        
        # Get authorization header
        authorization = request.headers.get("authorization")
        if not authorization:
            # For non-authenticated endpoints, continue without tenant context
            return None
        
        try:
            # Extract bearer token
            if not authorization.startswith("Bearer "):
                logger.warning(
                    "Invalid authorization header format",
                    extra={
                        "event": "invalid_auth_header",
                        "path": request.url.path
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization header format"
                )
            
            token = authorization[7:]  # Remove "Bearer " prefix
            
            # Verify JWT token
            payload = verify_token(token)
            if not payload:
                logger.warning(
                    "Invalid JWT token",
                    extra={
                        "event": "invalid_jwt_token",
                        "path": request.url.path
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            
            # Extract user ID from token
            user_id = payload.get("sub")
            if not user_id:
                logger.warning(
                    "Missing user ID in JWT token",
                    extra={
                        "event": "missing_user_id",
                        "path": request.url.path
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user from database to extract tenant context
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    logger.warning(
                        "User not found in database",
                        extra={
                            "event": "user_not_found", 
                            "user_id": user_id,
                            "path": request.url.path
                        }
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found"
                    )
                
                if not user.is_active:
                    logger.warning(
                        "Inactive user attempted access",
                        extra={
                            "event": "inactive_user_access",
                            "user_id": user_id,
                            "path": request.url.path
                        }
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User account is inactive"
                    )
                
                return {
                    "tenant_id": user.organisation_id,
                    "user_role": user.role.value,
                    "user_id": user.id
                }
                
            finally:
                # Ensure session is properly closed
                try:
                    db.close()
                except Exception as e:
                    logger.warning(
                        "Error closing database session in tenant extraction",
                        extra={
                            "event": "db_session_close_error",
                            "error": str(e)
                        }
                    )
                
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(
                "Error extracting tenant context",
                extra={
                    "event": "tenant_context_error",
                    "error": str(e),
                    "path": request.url.path
                },
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not establish tenant context"
            )
    
    async def _set_database_context(self, tenant_context: dict):
        """Set PostgreSQL session variables for RLS policies."""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Set tenant ID for RLS policies
            db.execute(
                text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_context["tenant_id"])}
            )
            
            # Set user role for role-based policies
            db.execute(
                text("SELECT set_config('app.current_user_role', :user_role, true)"),
                {"user_role": tenant_context["user_role"]}
            )
            
            # Set user ID for audit purposes
            db.execute(
                text("SELECT set_config('app.current_user_id', :user_id, true)"),
                {"user_id": str(tenant_context["user_id"])}
            )
            
            # For super admins, allow cross-tenant access to be explicitly enabled per request
            # Default is false for security
            allow_cross_tenant = "false"
            if tenant_context["user_role"] == UserRole.admin.value:
                # Super admins can access cross-tenant data only when explicitly requested
                # This should be handled by specific admin endpoints
                allow_cross_tenant = "false"  # Default to secure mode
            
            db.execute(
                text("SELECT set_config('app.allow_cross_tenant', :allow_cross_tenant, true)"),
                {"allow_cross_tenant": allow_cross_tenant}
            )
            
            db.commit()
            
        except SQLAlchemyError as e:
            logger.error(
                "Database error setting tenant context",
                extra={
                    "event": "db_context_error",
                    "error": str(e),
                    "tenant_id": str(tenant_context["tenant_id"])
                },
                exc_info=True
            )
            # Ensure rollback on error
            try:
                db.rollback()
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to establish database tenant context"
            )
        finally:
            # Ensure session is properly closed
            try:
                db.close()
            except Exception as e:
                logger.warning(
                    "Error closing database session in context setting",
                    extra={
                        "event": "db_session_close_error",
                        "error": str(e)
                    }
                )
    
    async def _clear_database_context(self):
        """Clear PostgreSQL session variables after request."""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Clear all app-specific session variables
            db.execute(text("SELECT set_config('app.current_tenant_id', null, true)"))
            db.execute(text("SELECT set_config('app.current_user_role', null, true)"))
            db.execute(text("SELECT set_config('app.current_user_id', null, true)"))
            db.execute(text("SELECT set_config('app.allow_cross_tenant', null, true)"))
            
            db.commit()
            
        except SQLAlchemyError as e:
            # Log error but don't fail the request
            logger.warning(
                "Failed to clear database tenant context",
                extra={
                    "event": "db_context_clear_error",
                    "error": str(e)
                }
            )
            # Attempt rollback but don't fail if it errors
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            # Ensure session is properly closed
            try:
                db.close()
            except Exception as e:
                logger.warning(
                    "Error closing database session in context clearing",
                    extra={
                        "event": "db_session_close_error",
                        "error": str(e)
                    }
                )


class SuperAdminContextManager:
    """
    Context manager for super admin operations that need cross-tenant access.
    
    Usage:
        async with SuperAdminContextManager(current_user):
            # Operations here can access data across all tenants
            cross_tenant_data = db.query(SomeModel).all()
    """
    
    def __init__(self, user: User):
        if user.role != UserRole.admin:
            raise ValueError("SuperAdminContextManager can only be used by admin users")
        self.user = user
    
    async def __aenter__(self):
        """Enable cross-tenant access for super admin."""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Enable cross-tenant access for this session
            db.execute(
                text("SELECT set_config('app.allow_cross_tenant', 'true', true)")
            )
            db.commit()
            
            logger.info(
                "Cross-tenant access enabled",
                extra={
                    "event": "cross_tenant_enabled",
                    "admin_user_id": str(self.user.id),
                    "justification": "Super admin context manager"
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to enable cross-tenant access",
                extra={
                    "event": "cross_tenant_enable_error",
                    "admin_user_id": str(self.user.id),
                    "error": str(e)
                },
                exc_info=True
            )
            # Ensure rollback on error
            try:
                db.rollback()
            except Exception:
                pass
            raise
        finally:
            # Ensure session is properly closed
            try:
                db.close()
            except Exception as e:
                logger.warning(
                    "Error closing database session in super admin context enter",
                    extra={
                        "event": "db_session_close_error",
                        "error": str(e)
                    }
                )
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Disable cross-tenant access after operation."""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Disable cross-tenant access
            db.execute(
                text("SELECT set_config('app.allow_cross_tenant', 'false', true)")
            )
            db.commit()
            
            logger.info(
                "Cross-tenant access disabled",
                extra={
                    "event": "cross_tenant_disabled",
                    "admin_user_id": str(self.user.id)
                }
            )
            
        except Exception as e:
            logger.warning(
                "Failed to disable cross-tenant access",
                extra={
                    "event": "cross_tenant_disable_error", 
                    "admin_user_id": str(self.user.id),
                    "error": str(e)
                }
            )
            # Attempt rollback but don't fail if it errors
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            # Ensure session is properly closed
            try:
                db.close()
            except Exception as e:
                logger.warning(
                    "Error closing database session in super admin context exit",
                    extra={
                        "event": "db_session_close_error",
                        "error": str(e)
                    }
                )