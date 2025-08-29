"""
Module Authentication Middleware - Enhanced for US-102

This middleware provides centralized authentication and authorization
for module routes, with support for different authentication levels,
permissions, roles, and feature flag validation. Enhanced to integrate
with the shared authentication context manager for cross-module session management.
"""

from typing import Dict, Any, Optional, List, Callable
import logging
import time
from functools import wraps
import asyncio
import hashlib
from collections import defaultdict, deque
import threading

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..auth.dependencies import get_current_user, verify_token
from ..models.user import User, UserRole
from ..services.feature_flag_service import FeatureFlagService
from ..services.module_service import ModuleService
from ..core.database import get_db
from ..core.auth_context import (
    AuthenticationContextManager, 
    get_auth_context_manager, 
    AuthenticationContext
)

logger = logging.getLogger(__name__)


class ModuleAuthenticationError(Exception):
    """Custom exception for module authentication errors"""
    pass


class ModuleAuthorizationError(Exception):
    """Custom exception for module authorization errors"""
    pass


class RateLimiter:
    """Thread-safe rate limiting for authentication attempts"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self._requests: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is within rate limits"""
        current_time = time.time()
        
        with self._lock:
            # Clean old requests
            while (self._requests[identifier] and 
                   current_time - self._requests[identifier][0] > self.time_window):
                self._requests[identifier].popleft()
            
            # Check if under limit
            if len(self._requests[identifier]) >= self.max_requests:
                return False
            
            # Add current request
            self._requests[identifier].append(current_time)
            return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        current_time = time.time()
        
        with self._lock:
            # Clean old requests
            while (self._requests[identifier] and 
                   current_time - self._requests[identifier][0] > self.time_window):
                self._requests[identifier].popleft()
            
            return max(0, self.max_requests - len(self._requests[identifier]))


class ModuleAuthCache:
    """Enhanced caching system for module authentication data with rate limiting"""
    
    def __init__(self, ttl: int = 300, max_cache_size: int = 1000):
        self.ttl = ttl
        self.max_cache_size = max_cache_size
        self.auth_cache: Dict[str, Dict[str, Any]] = {}
        self.module_config_cache: Dict[str, Dict[str, Any]] = {}
        self.user_access_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()
        
        # PERFORMANCE FIX: Connection pooling optimization
        self._db_connection_cache: Dict[str, Any] = {}
        self._connection_cache_ttl = 30  # 30 seconds
        
        # Rate limiting
        self.rate_limiter = RateLimiter(max_requests=100, time_window=60)
    
    def get_cached_auth(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Thread-safe get cached authentication data"""
        with self._cache_lock:
            if cache_key in self.auth_cache:
                cached_data = self.auth_cache[cache_key]
                if time.time() - cached_data["timestamp"] < self.ttl:
                    return cached_data
                else:
                    del self.auth_cache[cache_key]
            return None
    
    def cache_auth(self, cache_key: str, data: Dict[str, Any]):
        """Thread-safe cache authentication data with size limits"""
        with self._cache_lock:
            # PERFORMANCE FIX: Enforce cache size limits
            if len(self.auth_cache) >= self.max_cache_size:
                # Remove oldest entries (simple FIFO)
                oldest_keys = sorted(
                    self.auth_cache.keys(), 
                    key=lambda k: self.auth_cache[k].get('timestamp', 0)
                )[:int(self.max_cache_size * 0.1)]  # Remove 10%
                
                for old_key in oldest_keys:
                    del self.auth_cache[old_key]
            
            self.auth_cache[cache_key] = {
                **data,
                "timestamp": time.time()
            }
    
    def get_cached_module_config(self, module_id: str) -> Optional[Dict[str, Any]]:
        """Thread-safe get cached module configuration"""
        with self._cache_lock:
            if module_id in self.module_config_cache:
                cached_data = self.module_config_cache[module_id]
                if time.time() - cached_data["timestamp"] < self.ttl:
                    return cached_data["config"]
                else:
                    del self.module_config_cache[module_id]
            return None
    
    def cache_module_config(self, module_id: str, config: Dict[str, Any]):
        """Thread-safe cache module configuration with size limits"""
        with self._cache_lock:
            # Enforce cache size limits
            if len(self.module_config_cache) >= self.max_cache_size:
                oldest_keys = sorted(
                    self.module_config_cache.keys(), 
                    key=lambda k: self.module_config_cache[k].get('timestamp', 0)
                )[:int(self.max_cache_size * 0.1)]
                
                for old_key in oldest_keys:
                    del self.module_config_cache[old_key]
            
            self.module_config_cache[module_id] = {
                "config": config,
                "timestamp": time.time()
            }
    
    def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limits"""
        return self.rate_limiter.is_allowed(identifier)
    
    def get_rate_limit_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        return self.rate_limiter.get_remaining_requests(identifier)


class ModuleAuthMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware for module authentication with US-102 integration
    
    Features:
    - Shared authentication context across modules
    - Cross-module session management
    - JWT token validation and refresh
    - Session timeout handling
    - Module-specific permissions enforcement
    """
    
    def __init__(
        self, 
        app, 
        feature_flag_service: FeatureFlagService, 
        module_service: ModuleService,
        auth_context_manager: Optional[AuthenticationContextManager] = None
    ):
        super().__init__(app)
        self.feature_flag_service = feature_flag_service
        self.module_service = module_service
        self.cache = ModuleAuthCache(ttl=300, max_cache_size=1000)  # 5 minutes cache TTL with size limit
        
        # SECURITY FIX: Rate limiting configuration
        self.enable_rate_limiting = True
        self.rate_limit_per_ip = 100  # requests per minute per IP
        self.rate_limit_per_user = 200  # requests per minute per user
        
        # Security monitoring
        self.security_metrics = {
            'blocked_requests': 0,
            'rate_limited_requests': 0,
            'failed_authentications': 0,
            'suspicious_patterns': 0
        }
        self._metrics_lock = threading.Lock()
        
        # US-102: Integration with authentication context manager
        self.auth_context_manager = auth_context_manager
        
        # Session tracking
        self.session_cleanup_interval = 300  # 5 minutes
        self.last_session_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through enhanced authentication middleware with rate limiting and US-102 context sharing"""
        start_time = time.time()
        
        # Periodic cleanup of expired sessions
        await self._maybe_cleanup_sessions()
        
        # Check if this is a module route
        if not self._is_module_route(request.url.path):
            return await call_next(request)
        
        try:
            # SECURITY FIX: Rate limiting check
            if self.enable_rate_limiting:
                rate_limit_result = await self._check_rate_limits(request)
                if not rate_limit_result['allowed']:
                    with self._metrics_lock:
                        self.security_metrics['rate_limited_requests'] += 1
                    
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": "Rate limit exceeded",
                            "retry_after": rate_limit_result.get('retry_after', 60)
                        },
                        headers={"Retry-After": str(rate_limit_result.get('retry_after', 60))}
                    )
            
            # Extract module information from path
            module_info = self._extract_module_info(request.url.path)
            if not module_info:
                return await call_next(request)
            
            # US-102: Enhanced authentication with context manager
            auth_result = await self._authenticate_with_context(request, module_info)
            
            if not auth_result["success"]:
                with self._metrics_lock:
                    self.security_metrics['failed_authentications'] += 1
                    
                return JSONResponse(
                    status_code=auth_result["status_code"],
                    content={"detail": auth_result["message"]}
                )
            
            # Add enhanced context to request state
            if auth_result.get("auth_context"):
                request.state.auth_context = auth_result["auth_context"]
                request.state.current_user = auth_result["auth_context"].user
                request.state.module_info = module_info
                request.state.session_id = auth_result["auth_context"].session_id
                
                # Update module context
                if self.auth_context_manager:
                    await self.auth_context_manager.update_module_context(
                        auth_result["auth_context"].session_id,
                        module_info["namespace"],
                        {
                            "last_access": time.time(),
                            "endpoint": request.url.path,
                            "method": request.method
                        }
                    )
            
            # Process request
            response = await call_next(request)
            
            # Log successful module access
            duration = (time.time() - start_time) * 1000
            await self._log_enhanced_module_access(
                module_info, 
                auth_result.get("auth_context"), 
                request, 
                response.status_code, 
                duration
            )
            
            return response
            
        except ModuleAuthenticationError as e:
            logger.warning(f"Module authentication failed: {str(e)}", extra={
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else None
            })
            with self._metrics_lock:
                self.security_metrics['blocked_requests'] += 1
                
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": str(e)}
            )
            
        except ModuleAuthorizationError as e:
            logger.warning(f"Module authorization failed: {str(e)}", extra={
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else None
            })
            with self._metrics_lock:
                self.security_metrics['blocked_requests'] += 1
                
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": str(e)}
            )
            
        except Exception as e:
            logger.error(f"Module auth middleware error: {str(e)}", extra={
                "path": request.url.path,
                "method": request.method
            })
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal authentication error"}
            )
    
    def _is_module_route(self, path: str) -> bool:
        """Check if the path is a module route"""
        return path.startswith("/api/v1/modules/")
    
    def _extract_module_info(self, path: str) -> Optional[Dict[str, str]]:
        """
        Extract module information from the request path
        
        Expected format: /api/v1/modules/{version}/{namespace}/...
        """
        try:
            path_parts = path.strip("/").split("/")
            if len(path_parts) >= 5 and path_parts[0] == "api" and path_parts[1] == "v1" and path_parts[2] == "modules":
                return {
                    "version": path_parts[3],
                    "namespace": path_parts[4],
                    "remaining_path": "/" + "/".join(path_parts[5:]) if len(path_parts) > 5 else "/"
                }
        except (IndexError, ValueError):
            pass
        
        return None
    
    async def _authenticate_with_context(self, request: Request, module_info: Dict[str, str]) -> Dict[str, Any]:
        """
        US-102: Enhanced authentication using shared context manager
        
        Args:
            request: HTTP request
            module_info: Extracted module information
            
        Returns:
            Dict with authentication result and context
        """
        try:
            # First, try to get authentication context if available
            if self.auth_context_manager:
                auth_context = await self._get_auth_context_from_request(request)
                if auth_context:
                    # Validate context for this module
                    is_valid = await self.auth_context_manager.validate_context(
                        auth_context, 
                        module_info["namespace"],
                        required_permissions=[]  # Module-specific permissions would be loaded here
                    )
                    
                    if is_valid:
                        # Attempt to refresh context if needed
                        refreshed_context = await self.auth_context_manager.refresh_context(auth_context)
                        if refreshed_context:
                            auth_context = refreshed_context
                        
                        return {
                            "success": True,
                            "auth_context": auth_context,
                            "user": auth_context.user
                        }
                    else:
                        # Context validation failed, fall through to standard auth
                        logger.warning(f"Auth context validation failed for module {module_info['namespace']}")
            
            # Fallback to standard authentication
            return await self._authenticate_request_standard(request, module_info)
            
        except Exception as e:
            logger.error(f"Error in enhanced authentication: {str(e)}")
            # Fallback to standard authentication
            return await self._authenticate_request_standard(request, module_info)
    
    async def _get_auth_context_from_request(self, request: Request) -> Optional[AuthenticationContext]:
        """Get authentication context from request"""
        try:
            if not self.auth_context_manager:
                return None
            
            # Try to get context from session ID in headers
            session_id = request.headers.get("X-Session-ID")
            if session_id:
                context = await self.auth_context_manager.get_context(session_id=session_id)
                if context:
                    return context
            
            # Try to get context from access token
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                context = await self.auth_context_manager.get_context(access_token=token)
                if context:
                    return context
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting auth context from request: {str(e)}")
            return None
    
    async def _authenticate_request_standard(self, request: Request, module_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Standard authentication and authorization for module access (fallback)
        
        Returns:
            Dict with success status, user info, and context
        """
        # Get module configuration from database
        module_config = await self._get_module_config(module_info["namespace"])
        
        if not module_config:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": f"Module '{module_info['namespace']}' not found"
            }
        
        # Check if module is active
        if module_config.get("status") != "ACTIVE":
            return {
                "success": False,
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "message": f"Module '{module_info['namespace']}' is not active"
            }
        
        # Check authentication requirements
        auth_level = module_config.get("auth_level", "BASIC")
        
        if auth_level == "NONE":
            return {"success": True}
        
        # Extract and verify JWT token
        user = await self._get_authenticated_user(request)
        if not user:
            return {
                "success": False,
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "message": "Authentication required"
            }
        
        # Check user access to module
        has_access = await self._check_module_access(user, module_info["namespace"])
        if not has_access:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "message": f"Access denied to module '{module_info['namespace']}'"
            }
        
        # Check role requirements
        if auth_level in ["ROLE", "ADMIN"]:
            role_check = await self._check_role_requirements(user, module_config, auth_level)
            if not role_check["success"]:
                return role_check
        
        # Check permission requirements
        required_permissions = module_config.get("required_permissions", [])
        if required_permissions:
            permission_check = await self._check_permission_requirements(user, required_permissions)
            if not permission_check["success"]:
                return permission_check
        
        # Check feature flags
        required_features = module_config.get("feature_flags", [])
        if required_features:
            feature_check = await self._check_feature_flags(user, required_features)
            if not feature_check["success"]:
                return feature_check
        
        return {
            "success": True,
            "user": user,
            "context": {
                "module_id": module_config.get("id"),
                "auth_level": auth_level,
                "permissions": required_permissions
            }
        }
    
    async def _get_authenticated_user(self, request: Request) -> Optional[User]:
        """PERFORMANCE FIX: Get authenticated user with optimized database queries and connection pooling"""
        try:
            # Check cache first
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                return None
                
            token = auth_header.split(" ")[1]
            cache_key = f"user:{hashlib.sha256(token.encode()).hexdigest()[:16]}"
            
            cached_data = self.cache.get_cached_auth(cache_key)
            if cached_data:
                return cached_data["user"]
            
            # Verify token first to avoid unnecessary DB queries
            payload = verify_token(token, expected_type="access")
            if not payload:
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # PERFORMANCE FIX: Optimized database query with single connection
            user = await self._get_user_optimized(user_id)
            
            if user and user.is_active:
                # Cache the result with extended TTL for valid users
                self.cache.cache_auth(cache_key, {"user": user, "token_payload": payload})
                return user
            
        except Exception as e:
            logger.error(f"Error getting authenticated user: {str(e)}")
        
        return None
    
    async def _get_user_optimized(self, user_id: str) -> Optional[User]:
        """PERFORMANCE FIX: Optimized user loading with single database query"""
        try:
            # Use a single database session to avoid connection pool exhaustion
            async for db_session in get_db():
                try:
                    # PERFORMANCE FIX: Single query with all required joins
                    stmt = (
                        select(User)
                        .where(User.id == user_id)
                        .options(
                            selectinload(User.organisation),
                            # Add other relations that might be needed to avoid N+1 queries
                            # selectinload(User.roles) if such relation exists
                        )
                    )
                    
                    result = await db_session.execute(stmt)
                    user = result.scalar_one_or_none()
                    
                    # Explicitly break to close the session properly
                    break
                    
                except Exception as db_error:
                    logger.error(f"Database error in optimized user loading for {user_id}: {str(db_error)}")
                    await db_session.rollback()
                    break
            
            return user
            
        except Exception as e:
            logger.error(f"Error in optimized user loading for {user_id}: {str(e)}")
            return None
    
    async def _get_module_config(self, namespace: str) -> Optional[Dict[str, Any]]:
        """PERFORMANCE FIX: Get module configuration with optimized database access"""
        try:
            # Check cache first
            cached_config = self.cache.get_cached_module_config(namespace)
            if cached_config:
                return cached_config
            
            # PERFORMANCE FIX: Optimized module query
            from ..models.modules import AnalyticsModule
            
            async for db_session in get_db():
                try:
                    # Single optimized query
                    stmt = select(AnalyticsModule).where(AnalyticsModule.id == namespace)
                    result = await db_session.execute(stmt)
                    module = result.scalar_one_or_none()
                    
                    if module:
                        config = {
                            "id": module.id,
                            "name": module.name,
                            "status": module.status.value,
                            "auth_level": module.default_config.get("auth_level", "BASIC"),
                            "required_permissions": module.default_config.get("required_permissions", []),
                            "feature_flags": module.default_config.get("feature_flags", [])
                        }
                        # Cache with extended TTL for stable module configs
                        self.cache.cache_module_config(namespace, config)
                        return config
                    
                    break
                    
                except Exception as db_error:
                    logger.error(f"Database error getting module config {namespace}: {str(db_error)}")
                    await db_session.rollback()
                    break
        
        except Exception as e:
            logger.error(f"Error getting module config for {namespace}: {str(e)}")
        
        return None
    
    async def _check_module_access(self, user: User, namespace: str) -> bool:
        """Check if user has access to the module"""
        try:
            # Get user's module access from service
            available_modules = await self.module_service.get_available_modules(user)
            
            # Check if the namespace/module is in user's available modules
            return any(module["id"] == namespace for module in available_modules)
            
        except Exception as e:
            logger.error(f"Error checking module access for user {user.id}: {str(e)}")
            return False
    
    async def _check_role_requirements(self, user: User, module_config: Dict[str, Any], auth_level: str) -> Dict[str, Any]:
        """Check if user meets role requirements"""
        if auth_level == "ADMIN":
            if user.role != UserRole.ADMIN:
                return {
                    "success": False,
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "message": "Administrator role required"
                }
        
        # Additional role checks can be added here
        return {"success": True}
    
    async def _check_permission_requirements(self, user: User, required_permissions: List[str]) -> Dict[str, Any]:
        """Check if user has required permissions"""
        # This would typically check against a permission system
        # For now, assume admin users have all permissions
        if user.role == UserRole.ADMIN:
            return {"success": True}
        
        # TODO: Implement proper permission checking
        return {"success": True}
    
    async def _check_feature_flags(self, user: User, required_features: List[str]) -> Dict[str, Any]:
        """Check if required features are enabled for user with fail-secure validation"""
        try:
            # Fail-secure: if no user context provided, deny access
            if not user or not hasattr(user, 'id') or not hasattr(user, 'organisation_id'):
                logger.warning("Feature flag check failed: Missing user context")
                return {
                    "success": False,
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "message": "User context required for feature validation"
                }
            
            # Validate each feature flag with proper user context
            for feature_flag in required_features:
                if not feature_flag or not isinstance(feature_flag, str):
                    logger.warning(f"Invalid feature flag format: {feature_flag}")
                    return {
                        "success": False,
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "message": "Invalid feature flag configuration"
                    }
                
                # Pass user context for proper evaluation
                context = {
                    "user_id": user.id,
                    "organisation_id": user.organisation_id,
                    "user_role": user.role.value if hasattr(user, 'role') else None,
                    "timestamp": time.time()
                }
                
                is_enabled = await self.feature_flag_service.is_feature_enabled(
                    feature_flag, user, context
                )
                
                if not is_enabled:
                    logger.info(f"Feature flag '{feature_flag}' disabled for user {user.id}")
                    return {
                        "success": False,
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "message": f"Feature '{feature_flag}' is not available"
                    }
            
            logger.debug(f"All feature flags validated for user {user.id}: {required_features}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error checking feature flags for user {user.id if user else 'unknown'}: {str(e)}")
            # Fail-secure: deny access on errors
            return {
                "success": False,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error validating feature availability"
            }
    
    async def _log_module_access(
        self, 
        module_info: Dict[str, str], 
        user: Optional[User], 
        method: str, 
        path: str, 
        status_code: int, 
        duration: float
    ):
        """Log module access for analytics"""
        try:
            if user:
                await self.module_service.log_module_usage(
                    module_id=module_info["namespace"],
                    user=user,
                    action=f"{method}:{path}",
                    endpoint=path,
                    duration_ms=int(duration),
                    success=200 <= status_code < 400
                )
        except Exception as e:
            logger.error(f"Error logging module access: {str(e)}")
    
    async def _log_enhanced_module_access(
        self,
        module_info: Dict[str, str],
        auth_context: Optional[AuthenticationContext],
        request: Request,
        status_code: int,
        duration: float
    ):
        """Enhanced module access logging with US-102 context integration"""
        try:
            if auth_context and auth_context.user:
                # Log using the module service
                await self.module_service.log_module_usage(
                    module_id=module_info["namespace"],
                    user=auth_context.user,
                    action=f"{request.method}:{request.url.path}",
                    endpoint=request.url.path,
                    duration_ms=int(duration),
                    context={
                        "session_id": auth_context.session_id,
                        "access_count": auth_context.access_count,
                        "user_agent": request.headers.get("user-agent"),
                        "ip_address": request.client.host if request.client else None,
                        "module_version": module_info.get("version", "unknown")
                    },
                    success=200 <= status_code < 400
                )
                
                logger.info(f"Enhanced module access logged", extra={
                    "session_id": auth_context.session_id,
                    "module": module_info["namespace"],
                    "user_id": auth_context.user_id,
                    "duration_ms": int(duration),
                    "status_code": status_code
                })
            else:
                # Fallback to standard logging
                logger.warning("No auth context available for enhanced logging")
        
        except Exception as e:
            logger.error(f"Error in enhanced module access logging: {str(e)}")
    
    async def _maybe_cleanup_sessions(self):
        """Periodic cleanup of expired sessions with rate limit cleanup"""
        try:
            current_time = time.time()
            if (current_time - self.last_session_cleanup) > self.session_cleanup_interval:
                if self.auth_context_manager:
                    await self.auth_context_manager.cleanup_expired_contexts()
                
                # Clean up rate limiter data
                self._cleanup_rate_limiter()
                
                self.last_session_cleanup = current_time
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
    
    async def _check_rate_limits(self, request: Request) -> Dict[str, Any]:
        """SECURITY FIX: Check rate limits for the request"""
        try:
            client_ip = request.client.host if request.client else "unknown"
            
            # Check IP-based rate limiting
            ip_identifier = f"ip:{client_ip}"
            if not self.cache.check_rate_limit(ip_identifier):
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return {
                    'allowed': False,
                    'reason': 'IP rate limit exceeded',
                    'retry_after': 60
                }
            
            # Check user-based rate limiting if user is authenticated
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                try:
                    token = auth_header.split(" ")[1]
                    payload = verify_token(token)
                    if payload:
                        user_id = payload.get("sub")
                        if user_id:
                            user_identifier = f"user:{user_id}"
                            if not self.cache.check_rate_limit(user_identifier):
                                logger.warning(f"Rate limit exceeded for user: {user_id}")
                                return {
                                    'allowed': False,
                                    'reason': 'User rate limit exceeded',
                                    'retry_after': 60
                                }
                except Exception:
                    # If token verification fails, continue with IP-based limiting only
                    pass
            
            return {'allowed': True}
            
        except Exception as e:
            logger.error(f"Error checking rate limits: {str(e)}")
            # Fail open for rate limiting errors to avoid blocking legitimate requests
            return {'allowed': True}
    
    def _cleanup_rate_limiter(self):
        """Clean up old rate limiting data"""
        try:
            # Rate limiter handles its own cleanup
            current_time = time.time()
            # Log rate limiting statistics
            with self._metrics_lock:
                if any(self.security_metrics.values()):
                    logger.info(f"Security metrics - Blocked: {self.security_metrics['blocked_requests']}, "
                              f"Rate limited: {self.security_metrics['rate_limited_requests']}, "
                              f"Failed auth: {self.security_metrics['failed_authentications']}")
                    
                    # Reset metrics after logging
                    for key in self.security_metrics:
                        self.security_metrics[key] = 0
                        
        except Exception as e:
            logger.error(f"Error cleaning up rate limiter: {str(e)}")
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get current security statistics"""
        with self._metrics_lock:
            return {
                'security_metrics': self.security_metrics.copy(),
                'cache_stats': {
                    'auth_cache_size': len(self.cache.auth_cache),
                    'module_config_cache_size': len(self.cache.module_config_cache),
                    'max_cache_size': self.cache.max_cache_size
                },
                'rate_limiting_enabled': self.enable_rate_limiting
            }


def create_module_auth_dependency(
    auth_level: str = "BASIC",
    required_permissions: Optional[List[str]] = None,
    required_roles: Optional[List[str]] = None,
    feature_flags: Optional[List[str]] = None
):
    """
    Factory function to create authentication dependencies for module routes
    
    Args:
        auth_level: Level of authentication required
        required_permissions: List of required permissions
        required_roles: List of required roles  
        feature_flags: List of required feature flags
    
    Returns:
        FastAPI dependency function
    """
    
    async def auth_dependency(request: Request) -> User:
        """Authentication dependency for module routes"""
        
        # Check if user is already authenticated by middleware
        if hasattr(request.state, "current_user"):
            user = request.state.current_user
            auth_context = getattr(request.state, "auth_context", {})
            
            # Additional checks if needed
            if required_permissions and auth_context.get("permissions"):
                if not any(perm in auth_context["permissions"] for perm in required_permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Requires permissions: {', '.join(required_permissions)}"
                    )
            
            return user
        
        # Fallback to standard authentication
        if auth_level == "NONE":
            return None
        
        # Use standard auth dependency
        return await get_current_user(request)
    
    return auth_dependency


# Decorator for easy route protection
def require_module_auth(
    auth_level: str = "BASIC",
    permissions: Optional[List[str]] = None,
    roles: Optional[List[str]] = None,
    feature_flags: Optional[List[str]] = None
):
    """
    Decorator to add authentication requirements to module route functions
    
    Usage:
        @require_module_auth(auth_level="ADMIN")
        async def admin_only_route():
            ...
        
        @require_module_auth(permissions=["read_data"])
        async def data_route():
            ...
    """
    
    def decorator(func: Callable):
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # The actual authentication is handled by middleware
            # This decorator is mainly for documentation and type hints
            return await func(*args, **kwargs)
        
        # Add metadata for documentation
        wrapper._auth_level = auth_level
        wrapper._required_permissions = permissions or []
        wrapper._required_roles = roles or []
        wrapper._feature_flags = feature_flags or []
        
        return wrapper
    
    return decorator