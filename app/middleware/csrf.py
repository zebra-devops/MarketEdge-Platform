"""CSRF Protection Middleware

Implements double-submit cookie pattern for CSRF protection.

Security Model:
1. CSRF token set in cookie on login (httpOnly=false for JS access)
2. Client reads cookie and sends in X-CSRF-Token header
3. Server validates cookie token matches header token
4. Only state-changing methods (POST/PUT/PATCH/DELETE) are protected

Critical Fix #4: Missing CSRF Validation
- Previous implementation only GENERATED tokens
- This middleware VALIDATES tokens on protected endpoints
- Prevents cross-site logout and account lockout attacks
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
from typing import Set

logger = logging.getLogger(__name__)

# HTTP methods that require CSRF protection (state-changing operations)
CSRF_PROTECTED_METHODS: Set[str] = {"POST", "PUT", "PATCH", "DELETE"}

# Endpoints that are exempt from CSRF (e.g., initial login, public APIs)
CSRF_EXEMPT_PATHS: Set[str] = {
    "/api/v1/auth/login",  # Initial login sets CSRF token
    "/api/v1/auth/login-oauth2",  # OAuth2 login sets CSRF token
    "/api/v1/auth/callback",  # Auth0 callback
    "/api/v1/auth/user-context",  # Auth0 Action callback
    "/api/v1/auth/refresh",  # Token refresh (uses refresh token from cookie)
    "/api/v1/auth/auth0-url",  # Auth0 URL endpoint (GET, but listed for clarity)
    "/api/v1/logging/frontend-errors",  # Frontend error logging (non-state-changing)
    "/health",  # Health check
    "/",  # Root endpoint
    "/docs",  # API documentation
    "/openapi.json",  # OpenAPI schema
    "/redoc",  # ReDoc documentation
}


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware using double-submit cookie pattern.

    Security Model:
    1. CSRF token set in cookie on login (httpOnly=false for JS access)
    2. Client reads cookie and sends in X-CSRF-Token header
    3. Server validates cookie token matches header token
    4. Only state-changing methods (POST/PUT/PATCH/DELETE) are protected

    Exempt Paths:
    - Initial login (sets CSRF token)
    - Auth0 callbacks (external redirect)
    - Public read-only endpoints

    Business Impact:
    - Protects £925K Zebra Associates opportunity from CSRF attacks
    - Prevents cross-site logout attacks
    - Prevents account lockout via forced failed login attempts
    """

    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for exempt paths
        if self._is_exempt(request):
            return await call_next(request)

        # Skip CSRF check for safe methods (GET, HEAD, OPTIONS)
        if request.method not in CSRF_PROTECTED_METHODS:
            return await call_next(request)

        # Validate CSRF token for protected methods
        if not self._validate_csrf_token(request):
            logger.warning(
                "CSRF validation failed",
                extra={
                    "event": "csrf_validation_failed",
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": request.client.host if request.client else "unknown",
                    "has_cookie": "csrf_token" in request.cookies,
                    "has_header": "X-CSRF-Token" in request.headers,
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed. Include X-CSRF-Token header with valid token.",
            )

        # CSRF validation passed
        logger.debug(
            "CSRF validation passed",
            extra={
                "event": "csrf_validation_success",
                "path": request.url.path,
                "method": request.method,
            }
        )

        return await call_next(request)

    def _is_exempt(self, request: Request) -> bool:
        """Check if request path is exempt from CSRF protection."""
        path = request.url.path

        # Exact path match
        if path in CSRF_EXEMPT_PATHS:
            return True

        # Prefix match for OpenAPI/docs
        if path.startswith("/docs") or path.startswith("/redoc"):
            return True

        # Prefix match for API documentation endpoints
        if path.startswith("/api/v1/docs") or path.startswith("/api/v1/redoc"):
            return True

        return False

    def _validate_csrf_token(self, request: Request) -> bool:
        """
        Validate CSRF token using double-submit cookie pattern.

        Returns:
            True if token is valid, False otherwise
        """
        # Get token from cookie
        cookie_token = request.cookies.get("csrf_token")

        # Get token from header (primary method)
        header_token = request.headers.get("X-CSRF-Token")

        # Both must be present
        if not cookie_token or not header_token:
            logger.debug(
                "CSRF tokens missing",
                extra={
                    "has_cookie": bool(cookie_token),
                    "has_header": bool(header_token),
                }
            )
            return False

        # Tokens must match (constant-time comparison)
        if not self._constant_time_compare(cookie_token, header_token):
            logger.warning(
                "CSRF token mismatch",
                extra={
                    "event": "csrf_token_mismatch",
                    "cookie_length": len(cookie_token),
                    "header_length": len(header_token),
                }
            )
            return False

        # Additional validation: token should be non-empty and reasonable length
        if len(cookie_token) < 32:  # Minimum token length
            logger.warning("CSRF token too short", extra={"length": len(cookie_token)})
            return False

        return True

    @staticmethod
    def _constant_time_compare(a: str, b: str) -> bool:
        """
        Constant-time string comparison to prevent timing attacks.

        Args:
            a: First string
            b: Second string

        Returns:
            True if strings are equal, False otherwise
        """
        if len(a) != len(b):
            return False

        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)

        return result == 0
