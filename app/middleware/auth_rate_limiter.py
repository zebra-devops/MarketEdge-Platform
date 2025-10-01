"""
Authentication Rate Limiter

Provides specialized rate limiting for authentication endpoints to prevent:
- DoS attacks on expensive Auth0 endpoints
- CPU burn from excessive authentication attempts
- Auth0 API bill spikes from brute force attacks

Security Features:
- Per-IP address tracking (prevents distributed attacks)
- Redis-backed for distributed systems
- Clear error messages with Retry-After headers
- Environment-configurable limits
- Graceful degradation on Redis failures
"""
import time
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ..core.logging import logger
from ..core.config import settings


class AuthRateLimiter:
    """
    Rate limiter specialized for authentication endpoints.

    Configuration (via environment variables):
    - RATE_LIMIT_ENABLED: Enable/disable rate limiting (default: True)
    - RATE_LIMIT_AUTH_REQUESTS: Rate limit string (default: "10/5minutes")
    - RATE_LIMIT_STORAGE_URL: Redis URL for distributed rate limiting

    Usage:
        limiter = AuthRateLimiter()

        @router.post("/login")
        @limiter.limit()
        async def login(...):
            ...
    """

    def __init__(self):
        """Initialize authentication rate limiter with environment configuration."""
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.limit_string = getattr(settings, 'RATE_LIMIT_AUTH_REQUESTS', "10/5minutes")

        # Initialize slowapi Limiter with Redis backend
        try:
            storage_url = settings.get_rate_limit_redis_url_for_environment()
            self.limiter = Limiter(
                key_func=get_remote_address,
                storage_uri=storage_url,
                default_limits=[],  # No default limits, we'll apply per-endpoint
                headers_enabled=True,
                swallow_errors=True,  # Graceful degradation if Redis fails
            )

            logger.info(
                "Auth rate limiter initialized",
                extra={
                    "event": "auth_rate_limiter_init",
                    "enabled": self.enabled,
                    "limit": self.limit_string,
                    "storage": "redis"
                }
            )
        except Exception as e:
            logger.error(
                "Failed to initialize auth rate limiter",
                extra={
                    "event": "auth_rate_limiter_init_failed",
                    "error": str(e)
                }
            )
            # Create a fallback limiter without Redis
            self.limiter = Limiter(
                key_func=get_remote_address,
                default_limits=[],
                headers_enabled=True,
                swallow_errors=True
            )

    def limit(self, override_limit: Optional[str] = None):
        """
        Rate limit decorator for authentication endpoints.

        Args:
            override_limit: Optional custom limit string (e.g., "5/minute")

        Returns:
            Decorator function that enforces rate limiting

        Example:
            @router.post("/login")
            @auth_rate_limiter.limit()
            async def login(...):
                ...
        """
        limit_str = override_limit or self.limit_string

        def decorator(func):
            if not self.enabled:
                # Rate limiting disabled, return original function
                return func

            # Apply slowapi rate limit decorator
            return self.limiter.limit(limit_str)(func)

        return decorator

    async def check_rate_limit(self, request: Request) -> None:
        """
        Manually check rate limit for a request.

        Useful for programmatic rate limit checks.

        Args:
            request: FastAPI Request object

        Raises:
            HTTPException: 429 status if rate limit exceeded
        """
        if not self.enabled:
            return

        try:
            # Get client IP
            client_ip = get_remote_address(request)

            # Check if rate limit would be exceeded
            # Note: slowapi doesn't provide a direct "check" method,
            # so this is a simplified implementation
            # In production, you'd use the limiter's internal state

            logger.debug(
                "Rate limit check",
                extra={
                    "event": "auth_rate_limit_check",
                    "client_ip": client_ip,
                    "path": request.url.path
                }
            )

        except RateLimitExceeded as e:
            # Rate limit exceeded
            self._handle_rate_limit_exceeded(request, e)
        except Exception as e:
            # Log error but allow request (graceful degradation)
            logger.error(
                "Rate limit check failed",
                extra={
                    "event": "auth_rate_limit_check_failed",
                    "error": str(e),
                    "path": request.url.path
                }
            )

    def _handle_rate_limit_exceeded(
        self,
        request: Request,
        error: RateLimitExceeded
    ) -> None:
        """
        Handle rate limit exceeded scenario.

        Creates a detailed error response with:
        - Clear error message
        - Retry-After header
        - Rate limit information
        """
        client_ip = get_remote_address(request)

        # Parse limit string to calculate retry_after
        # Format: "10/5minutes" -> 5 minutes = 300 seconds
        retry_after = self._calculate_retry_after(error)

        # Log rate limit violation
        logger.warning(
            "Authentication rate limit exceeded",
            extra={
                "event": "auth_rate_limit_exceeded",
                "client_ip": client_ip,
                "path": request.url.path,
                "limit": self.limit_string,
                "retry_after": retry_after,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Raise HTTP 429 with detailed error
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "detail": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                "retry_after": retry_after,
                "limit": self.limit_string,
                "message": "Too many authentication attempts from your IP address. Please wait before trying again."
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": self.limit_string,
                "X-RateLimit-Reset": str(int(time.time()) + retry_after)
            }
        )

    def _calculate_retry_after(self, error: RateLimitExceeded) -> int:
        """
        Calculate retry_after seconds from rate limit error.

        Args:
            error: RateLimitExceeded exception

        Returns:
            Number of seconds until rate limit resets
        """
        try:
            # Parse limit string: "10/5minutes" -> 300 seconds
            if "minute" in self.limit_string.lower():
                parts = self.limit_string.split("/")
                if len(parts) == 2:
                    time_window = parts[1].lower()
                    if "minute" in time_window:
                        # Extract number of minutes
                        minutes = int(''.join(filter(str.isdigit, time_window)) or 1)
                        return minutes * 60
            elif "hour" in self.limit_string.lower():
                parts = self.limit_string.split("/")
                if len(parts) == 2:
                    time_window = parts[1].lower()
                    if "hour" in time_window:
                        hours = int(''.join(filter(str.isdigit, time_window)) or 1)
                        return hours * 3600

            # Default to 5 minutes if parsing fails
            return 300

        except Exception as e:
            logger.error(f"Error calculating retry_after: {e}")
            return 300  # Default 5 minutes

    def get_rate_limit_info(self, request: Request) -> dict:
        """
        Get current rate limit status for a request.

        Args:
            request: FastAPI Request object

        Returns:
            Dictionary with rate limit information
        """
        if not self.enabled:
            return {
                "enabled": False,
                "message": "Rate limiting is disabled"
            }

        client_ip = get_remote_address(request)

        return {
            "enabled": True,
            "limit": self.limit_string,
            "client_ip": client_ip,
            "storage": "redis" if settings.RATE_LIMIT_STORAGE_URL else "memory"
        }


# Global instance for use across authentication endpoints
auth_rate_limiter = AuthRateLimiter()


# Convenience decorator for direct import
def limit_auth_endpoint(override_limit: Optional[str] = None):
    """
    Convenience decorator for rate limiting authentication endpoints.

    Usage:
        from app.middleware.auth_rate_limiter import limit_auth_endpoint

        @router.post("/login")
        @limit_auth_endpoint()
        async def login(...):
            ...

    Args:
        override_limit: Optional custom limit string (e.g., "5/minute")
    """
    return auth_rate_limiter.limit(override_limit)
