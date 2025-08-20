"""
Rate limiting for file upload endpoints

Provides stricter rate limiting for file upload operations to prevent abuse.
"""
import time
import logging
from typing import Optional
from functools import wraps
from fastapi import Request, HTTPException, status, Depends
import redis.asyncio as redis
from redis.exceptions import RedisError

from ..core.config import settings

logger = logging.getLogger(__name__)

# Upload-specific rate limits
UPLOAD_RATE_LIMITS = {
    "csv_import": {
        "requests_per_hour": 10,  # Max 10 CSV imports per hour
        "requests_per_day": 50,    # Max 50 CSV imports per day
    },
    "file_upload": {
        "requests_per_hour": 30,   # Max 30 file uploads per hour
        "requests_per_day": 100,   # Max 100 file uploads per day
    }
}


class UploadRateLimiter:
    """Rate limiter for file upload operations"""
    
    def __init__(self):
        self.redis_client = None
        self._connect_redis()
    
    def _connect_redis(self):
        """Connect to Redis for rate limiting"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL or "redis://localhost:6379",
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Failed to connect to Redis for rate limiting: {e}")
            self.redis_client = None
    
    async def check_rate_limit(
        self, 
        user_id: str, 
        limit_type: str = "csv_import",
        custom_limits: Optional[dict] = None
    ) -> tuple[bool, dict]:
        """
        Check if user has exceeded rate limit for uploads
        
        Returns:
            Tuple of (is_allowed, metadata)
        """
        if not self.redis_client:
            # If Redis is not available, allow but log warning
            logger.warning("Redis not available for rate limiting, allowing request")
            return True, {"warning": "Rate limiting unavailable"}
        
        limits = custom_limits or UPLOAD_RATE_LIMITS.get(limit_type, UPLOAD_RATE_LIMITS["file_upload"])
        
        try:
            # Check hourly limit
            hourly_key = f"upload_rate:{limit_type}:{user_id}:hour:{int(time.time() // 3600)}"
            hourly_count = await self.redis_client.incr(hourly_key)
            
            if hourly_count == 1:
                # Set expiry for 1 hour
                await self.redis_client.expire(hourly_key, 3600)
            
            if hourly_count > limits["requests_per_hour"]:
                return False, {
                    "limit_exceeded": "hourly",
                    "limit": limits["requests_per_hour"],
                    "count": hourly_count,
                    "retry_after": 3600
                }
            
            # Check daily limit
            daily_key = f"upload_rate:{limit_type}:{user_id}:day:{int(time.time() // 86400)}"
            daily_count = await self.redis_client.incr(daily_key)
            
            if daily_count == 1:
                # Set expiry for 24 hours
                await self.redis_client.expire(daily_key, 86400)
            
            if daily_count > limits["requests_per_day"]:
                return False, {
                    "limit_exceeded": "daily",
                    "limit": limits["requests_per_day"],
                    "count": daily_count,
                    "retry_after": 86400
                }
            
            return True, {
                "hourly_remaining": limits["requests_per_hour"] - hourly_count,
                "daily_remaining": limits["requests_per_day"] - daily_count
            }
            
        except RedisError as e:
            logger.error(f"Redis error during rate limit check: {e}")
            # On Redis error, allow request but log
            return True, {"error": "Rate limit check failed"}
        except Exception as e:
            logger.error(f"Unexpected error during rate limit check: {e}")
            return True, {"error": "Rate limit check failed"}
    
    async def reset_limits(self, user_id: str, limit_type: str = "csv_import"):
        """Reset rate limits for a user (admin function)"""
        if not self.redis_client:
            return
        
        try:
            hourly_key = f"upload_rate:{limit_type}:{user_id}:hour:{int(time.time() // 3600)}"
            daily_key = f"upload_rate:{limit_type}:{user_id}:day:{int(time.time() // 86400)}"
            
            await self.redis_client.delete(hourly_key, daily_key)
            logger.info(f"Reset rate limits for user {user_id} on {limit_type}")
            
        except Exception as e:
            logger.error(f"Failed to reset rate limits: {e}")


# Global rate limiter instance
upload_rate_limiter = UploadRateLimiter()


async def check_csv_import_rate_limit(request: Request, current_user = Depends(lambda: None)):
    """
    FastAPI dependency for rate limiting CSV imports
    """
    from ..auth.dependencies import get_current_user
    
    # Try to get authenticated user
    try:
        if not current_user:
            # This will be populated by FastAPI's dependency injection
            pass
        user_id = str(current_user.id) if current_user else request.client.host
    except:
        user_id = request.client.host
    
    # Check rate limit
    is_allowed, metadata = await upload_rate_limiter.check_rate_limit(
        user_id, "csv_import"
    )
    
    if not is_allowed:
        retry_after = metadata.get("retry_after", 3600)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {metadata.get('limit')} imports per {metadata.get('limit_exceeded')}. Try again in {retry_after} seconds.",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(metadata.get("limit")),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + retry_after)
            }
        )
    
    return metadata


def rate_limit_upload(limit_type: str = "file_upload", custom_limits: Optional[dict] = None):
    """
    Decorator for rate limiting upload endpoints
    
    Usage:
        @rate_limit_upload("csv_import")
        async def upload_csv(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get user from request (assumes authentication middleware has run)
            user = getattr(request.state, "user", None)
            if not user:
                # If no user, use IP address for rate limiting
                user_id = request.client.host
            else:
                user_id = str(user.id)
            
            # Check rate limit
            is_allowed, metadata = await upload_rate_limiter.check_rate_limit(
                user_id, limit_type, custom_limits
            )
            
            if not is_allowed:
                retry_after = metadata.get("retry_after", 3600)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(metadata.get("limit")),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                    }
                )
            
            # Add rate limit headers to response
            response = await func(request, *args, **kwargs)
            if isinstance(response, Response):
                response.headers["X-RateLimit-Remaining-Hourly"] = str(metadata.get("hourly_remaining", ""))
                response.headers["X-RateLimit-Remaining-Daily"] = str(metadata.get("daily_remaining", ""))
            
            return response
        
        return wrapper
    return decorator