"""
Core Rate Limiter Implementation

Provides the main rate limiting interface and coordination between different
rate limiting strategies. This module acts as the central coordination point
for all rate limiting operations.
"""
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.exceptions import RedisError

from .logging import logger
from .config import settings
from .rate_limit_config import Industry, RateLimitRule, RateLimitType
from ..services.rate_limit_service import RateLimitResult, SlidingWindowRateLimiter


class RateLimiterCore:
    """
    Core rate limiter that provides the main interface for all rate limiting operations.
    
    This class coordinates between different rate limiting strategies and provides
    tenant isolation, security, and performance monitoring.
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.sliding_window_limiter: Optional[SlidingWindowRateLimiter] = None
        self._initialized = False
        self._connection_pool = None
        
    async def initialize(self) -> None:
        """Initialize Redis connection with security and performance optimizations."""
        try:
            # Parse Redis URL for security configuration
            redis_config = self._parse_redis_config(self.redis_url)
            
            # Create secure Redis client
            self.redis_client = redis.Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                password=redis_config.get('password'),
                ssl=redis_config.get('ssl', False),
                ssl_cert_reqs=redis_config.get('ssl_cert_reqs'),
                ssl_ca_certs=redis_config.get('ssl_ca_certs'),
                encoding="utf-8",
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=50,  # Connection pooling
                connection_pool=self._connection_pool
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Initialize sliding window limiter
            self.sliding_window_limiter = SlidingWindowRateLimiter(self.redis_client)
            
            self._initialized = True
            logger.info("Rate limiter core initialized successfully with secure connection")
            
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter core: {e}")
            raise
    
    def _parse_redis_config(self, redis_url: str) -> Dict[str, Any]:
        """Parse Redis URL and extract security configuration."""
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
            config['ssl_cert_reqs'] = 'required'  # Require valid certificates
            
            # In production, you would specify ssl_ca_certs path
            if hasattr(settings, 'REDIS_SSL_CA_CERTS'):
                config['ssl_ca_certs'] = settings.REDIS_SSL_CA_CERTS
        
        return config
    
    async def check_rate_limit(
        self,
        identifier: str,
        rule: RateLimitRule,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_cost: int = 1
    ) -> RateLimitResult:
        """
        Check rate limit with tenant isolation and security validation.
        
        Args:
            identifier: Unique identifier for this rate limit check
            rule: Rate limiting rule to apply
            tenant_id: Tenant ID for isolation (must be validated)
            user_id: User ID for user-specific limits
            request_cost: Cost of this request (default 1)
        
        Returns:
            RateLimitResult with decision and metadata
        """
        if not self._initialized:
            logger.warning("Rate limiter not initialized, allowing request")
            return RateLimitResult(
                allowed=True,
                limit=rule.limit,
                remaining=rule.limit,
                reset_time=datetime.now() + rule.window
            )
        
        # Validate tenant isolation
        if tenant_id and not self._validate_tenant_access(tenant_id, user_id):
            logger.error(
                "Tenant isolation violation detected",
                extra={
                    "event": "tenant_isolation_violation",
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "identifier": identifier
                }
            )
            # Deny request on security violation
            return RateLimitResult(
                allowed=False,
                limit=0,
                remaining=0,
                reset_time=datetime.now() + timedelta(hours=1),
                retry_after=3600,
                rule_name="security_violation"
            )
        
        # Create secure rate limit key with tenant isolation
        rate_limit_key = self._create_secure_key(identifier, tenant_id, user_id)
        
        try:
            # Check rate limit using sliding window
            result = await self.sliding_window_limiter.check_limit(
                rate_limit_key,
                rule,
                request_cost=request_cost
            )
            
            # Add audit logging for rate limit decisions
            if not result.allowed:
                logger.info(
                    "Rate limit exceeded",
                    extra={
                        "event": "rate_limit_exceeded",
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "identifier": identifier,
                        "limit": result.limit,
                        "remaining": result.remaining,
                        "rule_name": result.rule_name
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Fail open but log the error for security monitoring
            return RateLimitResult(
                allowed=True,
                limit=rule.limit,
                remaining=rule.limit,
                reset_time=datetime.now() + rule.window
            )
    
    def _validate_tenant_access(self, tenant_id: str, user_id: Optional[str]) -> bool:
        """
        Validate that the user has access to the specified tenant.
        
        This is a critical security check to prevent tenant boundary violations.
        """
        try:
            # In a real implementation, this would:
            # 1. Check if user belongs to the tenant
            # 2. Validate user permissions
            # 3. Check for any access restrictions
            
            # For now, we'll do basic validation
            if not tenant_id or not isinstance(tenant_id, str):
                return False
            
            if user_id and not isinstance(user_id, str):
                return False
            
            # TODO: Add actual tenant-user relationship validation
            # This would typically query the database to verify:
            # - User exists and is active
            # - User belongs to the specified tenant
            # - Tenant is active and not suspended
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating tenant access: {e}")
            return False  # Deny access on validation errors
    
    def _create_secure_key(
        self, 
        identifier: str, 
        tenant_id: Optional[str], 
        user_id: Optional[str]
    ) -> str:
        """
        Create a secure rate limit key with proper tenant isolation.
        
        The key structure ensures that tenants cannot access each other's
        rate limiting data.
        """
        key_parts = ["rate_limit"]
        
        # Always include tenant_id for isolation
        if tenant_id:
            key_parts.extend(["tenant", tenant_id])
        else:
            key_parts.extend(["global"])  # Global rate limits
        
        # Add user_id for user-specific limits
        if user_id:
            key_parts.extend(["user", user_id])
        
        # Add the specific identifier
        key_parts.append(identifier)
        
        return ":".join(key_parts)
    
    async def get_rate_limit_statistics(
        self, 
        tenant_id: str, 
        requesting_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get rate limiting statistics with proper tenant isolation.
        
        Args:
            tenant_id: Tenant ID to get statistics for
            requesting_user_id: ID of user requesting statistics (for authorization)
        
        Returns:
            Dictionary with rate limiting statistics
        """
        if not self._initialized:
            return {"error": "Rate limiter not initialized"}
        
        # Validate tenant access
        if not self._validate_tenant_access(tenant_id, requesting_user_id):
            logger.warning(
                "Unauthorized rate limit statistics access attempt",
                extra={
                    "event": "unauthorized_stats_access",
                    "tenant_id": tenant_id,
                    "requesting_user": requesting_user_id
                }
            )
            return {"error": "Access denied"}
        
        try:
            # Get statistics only for the specified tenant
            tenant_pattern = f"rate_limit:tenant:{tenant_id}:*"
            
            keys = []
            async for key in self.redis_client.scan_iter(match=tenant_pattern):
                keys.append(key)
            
            # Calculate statistics
            active_limits = len(keys)
            current_time = time.time()
            
            # Get more detailed statistics
            stats = {
                "tenant_id": tenant_id,
                "active_rate_limits": active_limits,
                "timestamp": current_time,
                "redis_connected": True
            }
            
            # Add Redis health information
            try:
                info = await self.redis_client.info()
                stats["redis_memory_usage"] = info.get("used_memory_human", "N/A")
                stats["redis_connected_clients"] = info.get("connected_clients", 0)
            except Exception:
                pass  # Non-critical information
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting rate limit statistics: {e}")
            return {"error": str(e)}
    
    async def reset_rate_limits(
        self, 
        tenant_id: str, 
        user_id: Optional[str] = None,
        requesting_admin_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reset rate limits with proper authorization checks.
        
        Args:
            tenant_id: Tenant ID to reset limits for
            user_id: Specific user ID to reset (optional)
            requesting_admin_id: ID of admin requesting reset (required)
        
        Returns:
            Dictionary with reset operation results
        """
        if not self._initialized:
            return {"error": "Rate limiter not initialized"}
        
        # Validate admin authorization
        if not self._validate_admin_authorization(requesting_admin_id, tenant_id):
            logger.warning(
                "Unauthorized rate limit reset attempt",
                extra={
                    "event": "unauthorized_reset_attempt",
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "requesting_admin": requesting_admin_id
                }
            )
            return {"error": "Access denied - admin authorization required"}
        
        try:
            # Build pattern for keys to reset
            if user_id:
                pattern = f"rate_limit:tenant:{tenant_id}:user:{user_id}:*"
            else:
                pattern = f"rate_limit:tenant:{tenant_id}:*"
            
            # Collect keys to delete
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            # Delete the keys
            deleted_count = 0
            if keys:
                deleted_count = await self.redis_client.delete(*keys)
            
            # Log the operation for audit
            logger.info(
                "Rate limits reset",
                extra={
                    "event": "rate_limits_reset",
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "keys_deleted": deleted_count,
                    "admin_id": requesting_admin_id
                }
            )
            
            return {
                "success": True,
                "keys_deleted": deleted_count,
                "tenant_id": tenant_id,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error resetting rate limits: {e}")
            return {"error": str(e)}
    
    def _validate_admin_authorization(
        self, 
        admin_id: Optional[str], 
        tenant_id: str
    ) -> bool:
        """
        Validate that the requesting user has admin permissions for the tenant.
        
        This is critical for emergency bypass operations and rate limit resets.
        """
        try:
            if not admin_id:
                return False
            
            # TODO: Implement actual admin authorization check
            # This should verify:
            # 1. User exists and is active
            # 2. User has admin role
            # 3. User has permission for this tenant
            # 4. User is authorized for emergency operations
            
            # For now, basic validation
            if not isinstance(admin_id, str) or not isinstance(tenant_id, str):
                return False
            
            # In production, this would query the database to verify admin status
            return True
            
        except Exception as e:
            logger.error(f"Error validating admin authorization: {e}")
            return False  # Deny access on validation errors
    
    async def emergency_bypass(
        self, 
        tenant_id: str, 
        duration_minutes: int,
        admin_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Emergency bypass for rate limiting with full audit logging.
        
        Args:
            tenant_id: Tenant to bypass limits for
            duration_minutes: How long to bypass (max 60 minutes)
            admin_id: Admin authorizing the bypass
            reason: Reason for the bypass
        
        Returns:
            Dictionary with bypass operation results
        """
        if not self._initialized:
            return {"error": "Rate limiter not initialized"}
        
        # Validate admin authorization
        if not self._validate_admin_authorization(admin_id, tenant_id):
            return {"error": "Access denied - admin authorization required"}
        
        # Limit bypass duration for security
        duration_minutes = min(duration_minutes, 60)  # Max 1 hour
        
        try:
            # Create bypass key
            bypass_key = f"rate_limit:bypass:tenant:{tenant_id}"
            bypass_data = {
                "admin_id": admin_id,
                "reason": reason,
                "timestamp": time.time(),
                "duration_minutes": duration_minutes
            }
            
            # Set bypass with expiration
            await self.redis_client.setex(
                bypass_key,
                duration_minutes * 60,
                str(bypass_data)
            )
            
            # Log the emergency bypass for audit
            logger.critical(
                "Emergency rate limit bypass activated",
                extra={
                    "event": "emergency_bypass_activated",
                    "tenant_id": tenant_id,
                    "admin_id": admin_id,
                    "reason": reason,
                    "duration_minutes": duration_minutes,
                    "expires_at": time.time() + (duration_minutes * 60)
                }
            )
            
            return {
                "success": True,
                "tenant_id": tenant_id,
                "duration_minutes": duration_minutes,
                "expires_at": time.time() + (duration_minutes * 60)
            }
            
        except Exception as e:
            logger.error(f"Error creating emergency bypass: {e}")
            return {"error": str(e)}
    
    async def check_bypass(self, tenant_id: str) -> bool:
        """Check if tenant has an active emergency bypass."""
        if not self._initialized:
            return False
        
        try:
            bypass_key = f"rate_limit:bypass:tenant:{tenant_id}"
            bypass_data = await self.redis_client.get(bypass_key)
            return bypass_data is not None
        except Exception:
            return False  # Assume no bypass on errors
    
    async def close(self) -> None:
        """Close Redis connection and cleanup resources."""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Rate limiter core closed successfully")
            except Exception as e:
                logger.error(f"Error closing rate limiter core: {e}")