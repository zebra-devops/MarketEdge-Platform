"""
Authentication Rate Limiter - SECURITY HARDENED

Provides specialized rate limiting for authentication endpoints with:
- CRITICAL FIX #1: IP Spoofing Prevention - X-Forwarded-For validation
- CRITICAL FIX #2: Fail-Closed Security - Redis failure returns 503
- CRITICAL FIX #3: Redis Namespace Isolation - Environment-specific keys
- CRITICAL FIX #4: /auth0-url Protection - Rate limited endpoint
- HIGH FIX #5: Per-User Rate Limiting - Authenticated user higher limits
- MEDIUM FIX #6: Environment-Aware Defaults - Development testing friendly

Security Features:
- Trusted proxy validation for X-Forwarded-For headers
- Fail-closed on Redis failures (503 instead of bypass)
- Environment namespace isolation (staging/production separation)
- Per-user and per-IP tracking
- Clear error messages with Retry-After headers
- Environment-configurable limits
"""
import time
import ipaddress
from typing import Optional, Callable
from datetime import datetime
from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
import redis

from ..core.logging import logger
from ..core.config import settings


def get_real_client_ip(request: Request) -> str:
    """
    Get real client IP with trusted proxy validation (CRITICAL FIX #1).

    Security features:
    - Validates X-Forwarded-For against TRUSTED_PROXIES CIDR blocks
    - Uses last IP in chain (closest to server, hardest to spoof)
    - Falls back to direct connection IP if not from trusted proxy
    - Prevents IP rotation bypass attacks

    Args:
        request: FastAPI Request object

    Returns:
        Real client IP address (validated)

    Raises:
        None - returns direct IP on validation failure
    """
    # Get direct connection IP
    direct_ip = request.client.host if request.client else "127.0.0.1"

    # Get trusted proxy CIDR blocks
    trusted_cidrs = settings.get_trusted_proxy_cidrs()
    if not trusted_cidrs:
        # No trusted proxies configured, use direct IP
        return direct_ip

    try:
        # Check if direct connection is from trusted proxy
        direct_ip_obj = ipaddress.ip_address(direct_ip)
        is_trusted = False

        for cidr_str in trusted_cidrs:
            try:
                cidr = ipaddress.ip_network(cidr_str, strict=False)
                if direct_ip_obj in cidr:
                    is_trusted = True
                    break
            except ValueError:
                logger.warning(
                    f"Invalid CIDR in TRUSTED_PROXIES: {cidr_str}",
                    extra={"event": "invalid_trusted_proxy_cidr"}
                )
                continue

        if not is_trusted:
            # Not from trusted proxy, use direct IP (don't trust X-Forwarded-For)
            logger.debug(
                f"Request not from trusted proxy, using direct IP",
                extra={
                    "event": "untrusted_proxy_request",
                    "direct_ip": direct_ip
                }
            )
            return direct_ip

        # Trusted proxy - extract real IP from X-Forwarded-For
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take last IP in chain (closest to server, hardest to spoof)
            # Format: "client, proxy1, proxy2" -> use "proxy2" (last trusted hop)
            ips = [ip.strip() for ip in forwarded_for.split(",")]
            if ips:
                real_ip = ips[-1]

                # Validate it's a real IP address
                try:
                    ipaddress.ip_address(real_ip)
                    logger.debug(
                        f"Using X-Forwarded-For IP from trusted proxy",
                        extra={
                            "event": "trusted_forwarded_for",
                            "real_ip": real_ip,
                            "proxy_ip": direct_ip
                        }
                    )
                    return real_ip
                except ValueError:
                    logger.warning(
                        f"Invalid IP in X-Forwarded-For: {real_ip}",
                        extra={"event": "invalid_forwarded_for_ip"}
                    )

        # Fallback to direct IP if X-Forwarded-For parsing fails
        return direct_ip

    except Exception as e:
        logger.error(
            f"Error validating client IP: {e}",
            extra={
                "event": "client_ip_validation_error",
                "error": str(e),
                "direct_ip": direct_ip
            }
        )
        # On error, use direct IP (safe fallback)
        return direct_ip


def get_rate_limit_key(request: Request, user_id: Optional[str] = None) -> str:
    """
    Generate Redis key with environment namespace (CRITICAL FIX #3).

    Key format: {environment}:rate_limit:auth:{identifier}:{path}

    Examples:
    - production:rate_limit:auth:192.168.1.1:/api/v1/auth/login
    - staging:rate_limit:auth:user_123:/api/v1/auth/refresh
    - development:rate_limit:auth:10.0.0.1:/api/v1/auth/auth0-url

    Args:
        request: FastAPI Request object
        user_id: Optional authenticated user ID (for per-user limits)

    Returns:
        Namespaced Redis key
    """
    # Get environment name for namespace isolation
    env_name = settings.ENV_NAME

    # Determine identifier (user ID or IP)
    if user_id:
        identifier = f"user_{user_id}"
    else:
        identifier = get_real_client_ip(request)

    # Get path for endpoint-specific tracking
    path = request.url.path

    # Format: {env}:rate_limit:auth:{identifier}:{path}
    key = f"{env_name}:rate_limit:auth:{identifier}:{path}"

    return key


class AuthRateLimiter:
    """
    Rate limiter specialized for authentication endpoints (SECURITY HARDENED).

    CRITICAL SECURITY FIXES:
    1. IP Spoofing Prevention - X-Forwarded-For validation
    2. Fail-Closed on Redis Failure - 503 instead of bypass
    3. Redis Namespace Isolation - Environment-specific keys
    4. Per-User Rate Limiting - Higher limits for authenticated users
    5. Environment-Aware Defaults - Development-friendly limits

    Configuration (via environment variables):
    - RATE_LIMIT_ENABLED: Enable/disable rate limiting (default: True)
    - RATE_LIMIT_AUTH_REQUESTS: Per-IP rate limit (default: "10/5minutes")
    - RATE_LIMIT_AUTH_REQUESTS_USER: Per-user rate limit (default: "50/5minutes")
    - RATE_LIMIT_STORAGE_URL: Redis URL for distributed rate limiting
    - TRUSTED_PROXIES: CIDR blocks for trusted proxies (default: RFC1918)
    - ENV_NAME: Environment namespace (default: "development")

    Usage:
        limiter = AuthRateLimiter()

        @router.post("/login")
        @limiter.limit()
        async def login(...):
            ...
    """

    def __init__(self):
        """Initialize authentication rate limiter with security hardening."""
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.redis_available = False  # Track Redis availability

        # Use environment-aware defaults (MEDIUM FIX #6)
        self.limit_string = settings.rate_limit_auth_default
        self.user_limit_string = getattr(settings, 'RATE_LIMIT_AUTH_REQUESTS_USER', "50/5minutes")

        # Redis connection for health checks (CRITICAL FIX #2)
        self.redis_client: Optional[redis.Redis] = None

        # Initialize slowapi Limiter with custom key function
        try:
            storage_url = settings.get_rate_limit_redis_url_for_environment()

            # Custom key function using secure IP extraction
            def key_func(request: Request) -> str:
                # Try to get user ID from request state (if authenticated)
                user_id = getattr(request.state, "user_id", None)
                return get_rate_limit_key(request, user_id)

            self.limiter = Limiter(
                key_func=key_func,
                storage_uri=storage_url,
                default_limits=[],  # No default limits, we'll apply per-endpoint
                headers_enabled=True,
                swallow_errors=False,  # CRITICAL FIX #2: Fail-closed, not fail-open
            )

            # Initialize Redis client for health checks
            try:
                self.redis_client = redis.from_url(
                    storage_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=1
                )
                # Test connection
                self.redis_client.ping()
                self.redis_available = True
            except Exception as redis_error:
                logger.error(
                    "Redis connection failed during rate limiter init",
                    extra={
                        "event": "rate_limiter_redis_failed",
                        "error": str(redis_error),
                        "storage_url": storage_url,
                        "environment": settings.ENV_NAME
                    }
                )
                # Continue without Redis client
                self.redis_client = None
                self.redis_available = False

                # In non-production environments, disable rate limiting if Redis unavailable
                if settings.ENV_NAME in ["development", "test", "testing"]:
                    logger.info(
                        "Rate limiting disabled due to Redis unavailability in test/dev environment",
                        extra={
                            "event": "rate_limiter_disabled_no_redis",
                            "environment": settings.ENV_NAME
                        }
                    )
                    self.enabled = False

            logger.info(
                "Auth rate limiter initialized (SECURITY HARDENED)",
                extra={
                    "event": "auth_rate_limiter_init",
                    "enabled": self.enabled,
                    "redis_available": self.redis_available,
                    "ip_limit": self.limit_string,
                    "user_limit": self.user_limit_string,
                    "storage": "redis" if self.redis_available else "none",
                    "fail_mode": "closed" if settings.ENV_NAME == "production" else "disabled",
                    "trusted_proxies": len(settings.get_trusted_proxy_cidrs()),
                    "environment": settings.ENV_NAME
                }
            )
        except Exception as e:
            logger.error(
                "Failed to initialize auth rate limiter",
                extra={
                    "event": "auth_rate_limiter_init_failed",
                    "error": str(e),
                    "environment": settings.ENV_NAME
                }
            )
            # CRITICAL: In production, fail-closed. In test/dev, disable and continue.
            if settings.ENV_NAME == "production":
                raise
            else:
                logger.warning(
                    "Rate limiting disabled due to initialization failure in non-production environment",
                    extra={
                        "event": "rate_limiter_disabled_init_error",
                        "environment": settings.ENV_NAME
                    }
                )
                self.enabled = False
                self.redis_available = False

    def _check_redis_health(self) -> None:
        """
        Check Redis health before rate limiting (CRITICAL FIX #2).

        In production: Fail-closed (raise 503 if Redis unavailable)
        In test/dev: Skip health check (rate limiting disabled if Redis unavailable)

        Raises:
            HTTPException: 503 Service Unavailable if Redis is down (production only)
        """
        # If Redis is not available and we're not in production, skip health check
        # (rate limiting should be disabled in __init__)
        if not self.redis_available and settings.ENV_NAME in ["development", "test", "testing"]:
            logger.debug(
                "Skipping Redis health check in non-production environment",
                extra={
                    "event": "rate_limit_health_check_skipped",
                    "environment": settings.ENV_NAME
                }
            )
            return

        # In production, fail-closed if Redis unavailable
        if not self.redis_client or not self.redis_available:
            logger.error(
                "Redis client not available for rate limiting in production",
                extra={
                    "event": "rate_limit_redis_unavailable",
                    "environment": settings.ENV_NAME
                }
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "detail": "Rate limiting service temporarily unavailable",
                    "message": "Please try again in a few moments"
                }
            )

        try:
            # Ping Redis with short timeout
            self.redis_client.ping()
        except Exception as e:
            logger.error(
                "Redis health check failed",
                extra={
                    "event": "rate_limit_redis_health_failed",
                    "error": str(e),
                    "environment": settings.ENV_NAME
                }
            )
            # In production, fail-closed
            if settings.ENV_NAME == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "detail": "Rate limiting service temporarily unavailable",
                        "message": "Please try again in a few moments"
                    }
                )
            # In test/dev, log warning but continue
            else:
                logger.warning(
                    "Redis health check failed in non-production, continuing anyway",
                    extra={
                        "event": "rate_limit_health_check_failed_continue",
                        "environment": settings.ENV_NAME
                    }
                )

    def limit(self, override_limit: Optional[str] = None, check_user_auth: bool = True):
        """
        Rate limit decorator for authentication endpoints (SECURITY HARDENED).

        HIGH FIX #5: Per-user rate limiting
        - If user is authenticated: use higher per-user limit
        - If user is unauthenticated: use lower per-IP limit
        - Prevents corporate NAT blocking issues

        Args:
            override_limit: Optional custom limit string (e.g., "5/minute")
            check_user_auth: If True, use per-user limit for authenticated requests

        Returns:
            Decorator function that enforces rate limiting

        Example:
            @router.post("/login")
            @auth_rate_limiter.limit()
            async def login(...):
                ...

            @router.get("/auth0-url")
            @auth_rate_limiter.limit("30/5minute")
            async def get_auth0_url(...):
                ...
        """
        # Import asyncio and functools for proper async wrapping
        import asyncio
        from functools import wraps

        def decorator(func):
            if not self.enabled:
                # Rate limiting disabled, return original function
                return func

            @wraps(func)  # CRITICAL FIX: Properly preserve function signature for FastAPI
            async def wrapper(*args, **kwargs):
                # Extract request from args
                request: Optional[Request] = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if not request and 'request' in kwargs:
                    request = kwargs['request']

                if not request:
                    # No request object, skip rate limiting
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    return func(*args, **kwargs)

                # CRITICAL FIX #2: Check Redis health before proceeding
                self._check_redis_health()

                # HIGH FIX #5: Determine limit based on authentication status
                limit_str = override_limit
                if not limit_str and check_user_auth:
                    # Check if user is authenticated
                    user_id = getattr(request.state, "user_id", None)
                    if user_id:
                        limit_str = self.user_limit_string
                        logger.debug(
                            f"Using per-user rate limit for authenticated user",
                            extra={
                                "event": "rate_limit_user_authenticated",
                                "user_id": user_id,
                                "limit": limit_str
                            }
                        )
                    else:
                        limit_str = self.limit_string
                else:
                    limit_str = limit_str or self.limit_string

                # Apply slowapi rate limit check manually (not as decorator)
                try:
                    # Get rate limit key
                    key = get_rate_limit_key(request, getattr(request.state, "user_id", None))

                    # Check if limit exceeded using limiter's storage
                    # Storage is accessed via self.limiter.limiter.storage (slowapi wraps limits library)
                    if self.limiter.limiter and self.limiter.limiter.storage is not None:
                        now = time.time()
                        window = self._parse_limit_window(limit_str)
                        max_requests = self._parse_limit_requests(limit_str)

                        # Get current request count
                        current_count = self.limiter.limiter.storage.incr(
                            key,
                            window,
                            amount=1
                        )

                        if current_count > max_requests:
                            # Rate limit exceeded
                            error = RateLimitExceeded(f"Rate limit exceeded: {limit_str}")
                            self._handle_rate_limit_exceeded(request, error, limit_str)

                    # Call original function
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    return func(*args, **kwargs)

                except RateLimitExceeded as e:
                    self._handle_rate_limit_exceeded(request, e, limit_str)
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Rate limit error: {e}", extra={
                        "event": "rate_limit_error",
                        "error": str(e),
                        "path": request.url.path if request else "unknown"
                    })
                    # On error, fail-closed (block request)
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Rate limiting service error"
                    )

            return wrapper

        return decorator

    def _handle_rate_limit_exceeded(
        self,
        request: Request,
        error: RateLimitExceeded,
        limit: str
    ) -> None:
        """
        Handle rate limit exceeded scenario.

        Creates a detailed error response with:
        - Clear error message
        - Retry-After header
        - Rate limit information
        """
        client_ip = get_real_client_ip(request)
        user_id = getattr(request.state, "user_id", None)

        # Parse limit string to calculate retry_after
        retry_after = self._calculate_retry_after(limit)

        # Log rate limit violation
        logger.warning(
            "Authentication rate limit exceeded",
            extra={
                "event": "auth_rate_limit_exceeded",
                "client_ip": client_ip,
                "user_id": user_id,
                "path": request.url.path,
                "limit": limit,
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
                "limit": limit,
                "message": "Too many authentication attempts. Please wait before trying again."
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": limit,
                "X-RateLimit-Reset": str(int(time.time()) + retry_after)
            }
        )

    def _parse_limit_requests(self, limit_string: str) -> int:
        """
        Parse the number of requests from limit string.

        Args:
            limit_string: Rate limit string (e.g., "30/5minutes")

        Returns:
            Number of allowed requests
        """
        try:
            parts = limit_string.split("/")
            if len(parts) >= 1:
                return int(parts[0])
            return 10  # Default
        except Exception as e:
            logger.error(f"Error parsing limit requests: {e}")
            return 10  # Default

    def _parse_limit_window(self, limit_string: str) -> int:
        """
        Parse the time window from limit string.

        Args:
            limit_string: Rate limit string (e.g., "30/5minutes")

        Returns:
            Time window in seconds
        """
        try:
            parts = limit_string.split("/")
            if len(parts) >= 2:
                time_part = parts[1].lower()

                if "minute" in time_part:
                    minutes = int(''.join(filter(str.isdigit, time_part)) or 1)
                    return minutes * 60
                elif "hour" in time_part:
                    hours = int(''.join(filter(str.isdigit, time_part)) or 1)
                    return hours * 3600
                elif "second" in time_part:
                    seconds = int(''.join(filter(str.isdigit, time_part)) or 1)
                    return seconds
                elif "day" in time_part:
                    days = int(''.join(filter(str.isdigit, time_part)) or 1)
                    return days * 86400

            return 300  # Default to 5 minutes
        except Exception as e:
            logger.error(f"Error parsing limit window: {e}")
            return 300  # Default to 5 minutes

    def _calculate_retry_after(self, limit_string: str) -> int:
        """
        Calculate retry_after seconds from rate limit string.

        Args:
            limit_string: Rate limit string (e.g., "10/5minutes")

        Returns:
            Number of seconds until rate limit resets
        """
        return self._parse_limit_window(limit_string)

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

        client_ip = get_real_client_ip(request)
        user_id = getattr(request.state, "user_id", None)

        return {
            "enabled": True,
            "ip_limit": self.limit_string,
            "user_limit": self.user_limit_string,
            "client_ip": client_ip,
            "user_id": user_id,
            "storage": "redis",
            "environment": settings.ENV_NAME,
            "fail_mode": "closed",
            "trusted_proxies": len(settings.get_trusted_proxy_cidrs())
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
