"""
Rate Limiting Middleware

Provides tenant-aware rate limiting with Redis-based sliding window algorithm.
Supports different rate limits per tenant tier and provides detailed metrics.

Features:
- Tenant-aware rate limiting with isolation
- Sliding window algorithm for smooth rate limiting
- Configurable limits per tenant tier
- Rate limit headers in responses
- Emergency bypass for admin operations
- Comprehensive metrics and monitoring
"""
import time
import json
import logging
from typing import Callable, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from redis.exceptions import RedisError

from ..core.config import settings
from ..models.user import UserRole
from ..models.organisation import Organisation

logger = logging.getLogger(__name__)

# Default rate limits by tenant tier (requests per hour)
DEFAULT_RATE_LIMITS = {
    "standard": 1000,
    "premium": 5000,
    "enterprise": 10000,
    "admin": float('inf')  # No limits for admin operations
}

# Routes exempt from rate limiting
EXEMPT_ROUTES = {
    "/health",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# Admin endpoints that bypass rate limiting
ADMIN_BYPASS_PATTERNS = [
    "/api/v1/admin/",
    "/api/v1/emergency/",
]


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Redis-based rate limiting middleware with tenant awareness.
    
    Implements sliding window rate limiting with:
    - Tenant-specific rate limits
    - Role-based exemptions
    - Detailed rate limit headers
    - Performance monitoring (<5ms overhead)
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.redis_client: Optional[redis.Redis] = None
        self.default_limits = DEFAULT_RATE_LIMITS.copy()
        self.window_size = timedelta(hours=1)  # Sliding window size
        self.key_prefix = "rate_limit:"
    
    def _parse_redis_url(self, redis_url: str) -> dict:
        """Parse Redis URL and extract connection parameters."""
        import urllib.parse as urlparse
        
        parsed = urlparse.urlparse(redis_url)
        
        config = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 6379,
        }
        
        # Extract password from URL
        if parsed.password:
            config['password'] = parsed.password
        
        # Check for SSL/TLS configuration
        if parsed.scheme in ('rediss', 'redis+ssl'):
            config['ssl'] = True
        
        return config
        
    async def initialize_redis(self):
        """Initialize Redis connection for rate limiting."""
        if self.redis_client:
            return
            
        try:
            # Parse Redis URL for security configuration
            redis_config = self._parse_redis_url(settings.REDIS_URL)
            
            self.redis_client = redis.Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                password=redis_config.get('password') or settings.REDIS_PASSWORD,
                ssl=settings.REDIS_SSL_ENABLED or redis_config.get('ssl', False),
                ssl_cert_reqs=settings.REDIS_SSL_CERT_REQS if settings.REDIS_SSL_ENABLED else None,
                ssl_ca_certs=settings.REDIS_SSL_CA_CERTS if settings.REDIS_SSL_ENABLED else None,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                retry_on_timeout=True,
                max_connections=settings.REDIS_CONNECTION_POOL_SIZE,
                health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Rate limiter Redis connection established")
            
        except RedisError as e:
            logger.error(f"Failed to initialize Redis for rate limiting: {e}")
            # Continue without rate limiting rather than failing
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing rate limiter Redis: {e}")
            self.redis_client = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware processing logic."""
        start_time = time.time()
        
        try:
            # Initialize Redis connection if not already done
            await self.initialize_redis()
            
            # Skip rate limiting for exempt routes
            if self._should_skip_rate_limiting(request):
                return await call_next(request)
            
            # Extract tenant and user context
            tenant_context = self._extract_context(request)
            if not tenant_context:
                # No context means no authentication - let other middleware handle
                return await call_next(request)
            
            # Check rate limit
            rate_limit_result = await self._check_rate_limit(request, tenant_context)
            
            if rate_limit_result["blocked"]:
                # Rate limit exceeded - return 429
                response = Response(
                    content=json.dumps({
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": rate_limit_result["retry_after"]
                    }),
                    status_code=429,
                    media_type="application/json"
                )
                self._add_rate_limit_headers(response, rate_limit_result)
                return response
            
            # Process the request
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            self._add_rate_limit_headers(response, rate_limit_result)
            
            # Add performance monitoring
            processing_time = (time.time() - start_time) * 1000
            response.headers["X-RateLimit-Processing-Time"] = f"{processing_time:.2f}ms"
            
            # Log performance if over threshold
            if processing_time > 5.0:  # 5ms threshold
                logger.warning(
                    "Rate limiting overhead exceeded threshold",
                    extra={
                        "event": "rate_limit_performance_warning",
                        "processing_time_ms": processing_time,
                        "tenant_id": tenant_context.get("tenant_id"),
                        "path": request.url.path
                    }
                )
            
            return response
            
        except Exception as e:
            logger.error(
                "Rate limiter middleware error",
                extra={
                    "event": "rate_limiter_error",
                    "error": str(e),
                    "path": request.url.path
                },
                exc_info=True
            )
            # Continue without rate limiting on errors to avoid blocking requests
            return await call_next(request)
    
    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """Check if request should skip rate limiting."""
        path = request.url.path
        
        # Skip exempt routes
        if path in EXEMPT_ROUTES:
            return True
        
        # Skip static files and other non-API paths
        exempt_prefixes = ["/static/", "/favicon.ico", "/assets/"]
        if any(path.startswith(prefix) for prefix in exempt_prefixes):
            return True
        
        # Check admin bypass patterns
        if any(path.startswith(pattern) for pattern in ADMIN_BYPASS_PATTERNS):
            return True
        
        return False
    
    def _extract_context(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract tenant and user context from request state."""
        try:
            # Check if tenant context is available from TenantContextMiddleware
            if hasattr(request.state, 'tenant_id') and hasattr(request.state, 'user_role'):
                return {
                    "tenant_id": str(request.state.tenant_id),
                    "user_role": request.state.user_role,
                    "user_id": str(getattr(request.state, 'user_id', 'unknown'))
                }
            return None
        except AttributeError:
            return None
    
    async def _check_rate_limit(
        self, 
        request: Request, 
        tenant_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check rate limit using sliding window algorithm."""
        if not self.redis_client:
            # No Redis available - allow request but log warning
            logger.warning("Rate limiting disabled - Redis unavailable")
            return {
                "blocked": False,
                "limit": 0,
                "remaining": 0,
                "reset_time": 0,
                "retry_after": 0
            }
        
        try:
            # Get rate limit for tenant
            rate_limit = await self._get_tenant_rate_limit(tenant_context)
            
            # Admin users bypass rate limiting
            if tenant_context["user_role"] == UserRole.admin.value:
                return {
                    "blocked": False,
                    "limit": rate_limit,
                    "remaining": rate_limit,
                    "reset_time": int(time.time() + 3600),
                    "retry_after": 0
                }
            
            # Create rate limit key
            rate_limit_key = self._create_rate_limit_key(tenant_context, request)
            
            # Implement sliding window rate limiting
            current_time = time.time()
            window_start = current_time - self.window_size.total_seconds()
            
            # Use Redis pipeline for atomic operations
            async with self.redis_client.pipeline(transaction=True) as pipe:
                # Remove expired entries
                await pipe.zremrangebyscore(rate_limit_key, 0, window_start)
                
                # Count current requests in window
                await pipe.zcard(rate_limit_key)
                
                # Add current request
                await pipe.zadd(rate_limit_key, {str(current_time): current_time})
                
                # Set expiry
                await pipe.expire(rate_limit_key, int(self.window_size.total_seconds()) + 10)
                
                # Execute pipeline
                results = await pipe.execute()
            
            current_count = results[1]  # Count after cleanup
            
            # Check if rate limit exceeded
            if current_count >= rate_limit:
                # Get oldest request time for retry calculation
                oldest_requests = await self.redis_client.zrange(
                    rate_limit_key, 0, 0, withscores=True
                )
                
                retry_after = 0
                if oldest_requests:
                    oldest_time = oldest_requests[0][1]
                    retry_after = int(oldest_time + self.window_size.total_seconds() - current_time)
                    retry_after = max(retry_after, 1)  # Minimum 1 second
                
                # Log rate limit violation
                logger.info(
                    "Rate limit exceeded",
                    extra={
                        "event": "rate_limit_exceeded",
                        "tenant_id": tenant_context["tenant_id"],
                        "user_id": tenant_context["user_id"],
                        "rate_limit": rate_limit,
                        "current_count": current_count,
                        "path": request.url.path,
                        "ip": self._get_client_ip(request)
                    }
                )
                
                return {
                    "blocked": True,
                    "limit": rate_limit,
                    "remaining": 0,
                    "reset_time": int(current_time + retry_after),
                    "retry_after": retry_after
                }
            
            # Request allowed
            remaining = max(0, rate_limit - (current_count + 1))
            reset_time = int(current_time + self.window_size.total_seconds())
            
            return {
                "blocked": False,
                "limit": rate_limit,
                "remaining": remaining,
                "reset_time": reset_time,
                "retry_after": 0
            }
            
        except RedisError as e:
            logger.error(
                "Redis error during rate limiting",
                extra={
                    "event": "rate_limit_redis_error",
                    "error": str(e),
                    "tenant_id": tenant_context["tenant_id"]
                }
            )
            # Allow request on Redis errors
            return {
                "blocked": False,
                "limit": 0,
                "remaining": 0,
                "reset_time": 0,
                "retry_after": 0
            }
        except Exception as e:
            logger.error(
                "Unexpected error during rate limiting",
                extra={
                    "event": "rate_limit_unexpected_error",
                    "error": str(e),
                    "tenant_id": tenant_context["tenant_id"]
                },
                exc_info=True
            )
            # Allow request on unexpected errors
            return {
                "blocked": False,
                "limit": 0,
                "remaining": 0,
                "reset_time": 0,
                "retry_after": 0
            }
    
    async def _get_tenant_rate_limit(self, tenant_context: Dict[str, Any]) -> int:
        """Get rate limit for tenant based on their tier."""
        try:
            tenant_id = tenant_context["tenant_id"]
            
            # Check for cached tenant rate limit
            cache_key = f"tenant_rate_limit:{tenant_id}"
            cached_limit = await self.redis_client.get(cache_key) if self.redis_client else None
            
            if cached_limit:
                return int(cached_limit)
            
            # For now, use default limits based on user role
            # In production, this would query the organisation table for tier
            user_role = tenant_context["user_role"]
            
            if user_role == UserRole.admin.value:
                rate_limit = self.default_limits["admin"]
            else:
                # Default to standard tier for regular users
                # TODO: Query Organisation table for actual tier
                rate_limit = self.default_limits["standard"]
            
            # Cache the rate limit for 5 minutes
            if self.redis_client:
                await self.redis_client.setex(cache_key, 300, rate_limit)
            
            return rate_limit
            
        except Exception as e:
            logger.error(
                "Error getting tenant rate limit",
                extra={
                    "event": "rate_limit_config_error",
                    "error": str(e),
                    "tenant_id": tenant_context["tenant_id"]
                }
            )
            # Return default standard limit on errors
            return self.default_limits["standard"]
    
    def _create_rate_limit_key(
        self, 
        tenant_context: Dict[str, Any], 
        request: Request
    ) -> str:
        """Create Redis key for rate limiting."""
        tenant_id = tenant_context["tenant_id"]
        user_id = tenant_context["user_id"]
        
        # Create tenant-scoped rate limit key
        # Using both tenant and user for more granular control
        return f"{self.key_prefix}tenant:{tenant_id}:user:{user_id}"
    
    def _add_rate_limit_headers(
        self, 
        response: Response, 
        rate_limit_result: Dict[str, Any]
    ):
        """Add rate limit headers to response."""
        if rate_limit_result["limit"] > 0:
            response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_result["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_limit_result["reset_time"])
        
        if rate_limit_result["retry_after"] > 0:
            response.headers["Retry-After"] = str(rate_limit_result["retry_after"])
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers first (load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client address
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    def _validate_tenant_access(self, tenant_id: str, user_id: Optional[str]) -> bool:
        """Validate that user has access to tenant's rate limiting data."""
        try:
            # Basic validation
            if not tenant_id or not isinstance(tenant_id, str):
                return False
            
            if user_id and not isinstance(user_id, str):
                return False
            
            # TODO: Add actual tenant-user relationship validation
            # This should verify:
            # 1. User exists and is active
            # 2. User belongs to the specified tenant
            # 3. User has permission to view rate limit data
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating tenant access: {e}")
            return False
    
    def _validate_admin_authorization(self, admin_id: Optional[str], tenant_id: str) -> bool:
        """Validate that user has admin permissions for rate limit operations."""
        try:
            if not admin_id:
                return False
            
            # Basic validation
            if not isinstance(admin_id, str) or not isinstance(tenant_id, str):
                return False
            
            # TODO: Add actual admin authorization check
            # This should verify:
            # 1. User exists and is active
            # 2. User has admin role
            # 3. User has permission for this tenant
            # 4. User is authorized for emergency operations
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating admin authorization: {e}")
            return False
    
    async def get_rate_limit_stats(self, tenant_id: str, requesting_user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get rate limiting statistics for a tenant with proper authorization."""
        if not self.redis_client:
            return {}
        
        # Validate tenant access
        if not self._validate_tenant_access(tenant_id, requesting_user_id):
            logger.warning(
                "Unauthorized rate limit statistics access",
                extra={
                    "event": "unauthorized_stats_access",
                    "tenant_id": tenant_id,
                    "requesting_user": requesting_user_id
                }
            )
            return {"error": "Access denied"}
        
        try:
            stats = {}
            
            # Get all rate limit keys for tenant
            pattern = f"{self.key_prefix}tenant:{tenant_id}:*"
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            current_time = time.time()
            window_start = current_time - self.window_size.total_seconds()
            
            total_requests = 0
            active_users = 0
            
            for key in keys:
                # Count requests in current window
                count = await self.redis_client.zcount(key, window_start, current_time)
                if count > 0:
                    active_users += 1
                    total_requests += count
            
            stats = {
                "tenant_id": tenant_id,
                "total_requests_current_window": total_requests,
                "active_users": active_users,
                "window_size_hours": self.window_size.total_seconds() / 3600
            }
            
            return stats
            
        except Exception as e:
            logger.error(
                "Error getting rate limit stats",
                extra={
                    "event": "rate_limit_stats_error",
                    "error": str(e),
                    "tenant_id": tenant_id
                }
            )
            return {}
    
    async def reset_rate_limit(self, tenant_id: str, user_id: Optional[str] = None, admin_user_id: Optional[str] = None) -> bool:
        """Reset rate limit for tenant or specific user with authorization checks."""
        if not self.redis_client:
            return False
        
        # Validate admin authorization
        if not self._validate_admin_authorization(admin_user_id, tenant_id):
            logger.warning(
                "Unauthorized rate limit reset attempt",
                extra={
                    "event": "unauthorized_reset_attempt",
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "admin_user": admin_user_id
                }
            )
            return False
        
        try:
            if user_id:
                # Reset specific user
                key = f"{self.key_prefix}tenant:{tenant_id}:user:{user_id}"
                deleted = await self.redis_client.delete(key)
                
                logger.info(
                    "Rate limit reset for user",
                    extra={
                        "event": "rate_limit_reset",
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "reset_successful": deleted > 0
                    }
                )
                
                return deleted > 0
            else:
                # Reset all users for tenant
                pattern = f"{self.key_prefix}tenant:{tenant_id}:*"
                keys = []
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys.append(key)
                
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    
                    logger.info(
                        "Rate limit reset for tenant",
                        extra={
                            "event": "rate_limit_tenant_reset",
                            "tenant_id": tenant_id,
                            "keys_deleted": deleted
                        }
                    )
                    
                    return deleted > 0
                
                return True
                
        except Exception as e:
            logger.error(
                "Error resetting rate limit",
                extra={
                    "event": "rate_limit_reset_error",
                    "error": str(e),
                    "tenant_id": tenant_id,
                    "user_id": user_id
                },
                exc_info=True
            )
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Rate limiter Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing rate limiter Redis connection: {e}")