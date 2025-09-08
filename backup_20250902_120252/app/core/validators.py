"""
Security validators for comprehensive input validation and injection prevention.

This module provides secure validation functions to prevent:
- SQL injection attacks
- XSS attacks
- Path traversal attacks
- Code injection
- LDAP injection
- Header injection
"""

import re
import urllib.parse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, field_validator, ValidationError
from ..core.logging import logger


class ValidationError(Exception):
    """Custom validation error for security violations"""
    def __init__(self, message: str, field: str = None, violation_type: str = None):
        super().__init__(message)
        self.field = field
        self.violation_type = violation_type


class AuthParameterValidator(BaseModel):
    """Pydantic model for validating authentication parameters"""
    code: str
    redirect_uri: str
    state: Optional[str] = None
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate authorization code parameter"""
        if not v or not isinstance(v, str):
            raise ValueError("Code is required and must be a string")
        
        # Remove any whitespace
        v = v.strip()
        
        # Check length constraints
        if len(v) < 10 or len(v) > 500:
            raise ValueError("Code length must be between 10 and 500 characters")
        
        # Allow only alphanumeric, hyphens, underscores, and dots
        if not re.match(r'^[a-zA-Z0-9\-_\.]+$', v):
            raise ValueError("Code contains invalid characters")
        
        # Check for common injection patterns
        injection_patterns = [
            r'[<>"\']',  # XSS patterns
            r'(union|select|insert|update|delete|drop|create|alter)\s+',  # SQL keywords
            r'javascript:',  # JavaScript scheme
            r'data:',       # Data scheme
            r'vbscript:',   # VBScript scheme
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                logger.warning(
                    "Potentially malicious code parameter detected",
                    extra={
                        "event": "security_validation_failed",
                        "field": "code",
                        "pattern": pattern,
                        "violation_type": "injection_attempt"
                    }
                )
                raise ValueError("Code contains potentially malicious content")
        
        return v
    
    @field_validator('redirect_uri')
    @classmethod
    def validate_redirect_uri(cls, v: str) -> str:
        """Validate redirect URI parameter with comprehensive security checks"""
        if not v or not isinstance(v, str):
            raise ValueError("Redirect URI is required and must be a string")
        
        # Remove any whitespace
        v = v.strip()
        
        # Check length constraints
        if len(v) < 10 or len(v) > 2000:
            raise ValueError("Redirect URI length must be between 10 and 2000 characters")
        
        # URL decode to check for encoded injection attempts
        try:
            decoded_uri = urllib.parse.unquote(v)
        except Exception:
            raise ValueError("Invalid URL encoding in redirect URI")
        
        # Validate URL format
        try:
            parsed = urllib.parse.urlparse(v)
        except Exception:
            raise ValueError("Invalid redirect URI format")
        
        # Check scheme
        if not parsed.scheme or parsed.scheme.lower() not in ['http', 'https']:
            raise ValueError("Redirect URI must use HTTP or HTTPS scheme")
        
        # Check for valid hostname
        if not parsed.netloc:
            raise ValueError("Redirect URI must have a valid hostname")
        
        # Prevent localhost/internal redirects in production
        hostname = parsed.netloc.split(':')[0].lower()
        internal_hosts = [
            'localhost', '127.0.0.1', '0.0.0.0', '::1',
            '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'
        ]
        
        # In production, block internal redirects
        from ..core.config import settings
        if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == 'production':
            if any(hostname.startswith(internal) or hostname == internal for internal in internal_hosts):
                raise ValueError("Redirect to internal hosts not allowed in production")
        
        # Check for injection patterns in the full URI
        injection_patterns = [
            r'[<>"\']',  # XSS patterns
            r'[\x00-\x1f\x7f-\x9f]',  # Control characters
            r'javascript:',  # JavaScript scheme
            r'data:',       # Data scheme
            r'vbscript:',   # VBScript scheme
            r'file:',       # File scheme
            r'ftp:',        # FTP scheme
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, decoded_uri, re.IGNORECASE):
                logger.warning(
                    "Potentially malicious redirect URI detected",
                    extra={
                        "event": "security_validation_failed",
                        "field": "redirect_uri",
                        "pattern": pattern,
                        "violation_type": "injection_attempt"
                    }
                )
                raise ValueError("Redirect URI contains potentially malicious content")
        
        # Validate allowed domains (if configured)
        allowed_domains = getattr(settings, 'ALLOWED_REDIRECT_DOMAINS', [])
        if allowed_domains:
            domain_allowed = False
            for domain in allowed_domains:
                if hostname.endswith(domain):
                    domain_allowed = True
                    break
            
            if not domain_allowed:
                logger.warning(
                    "Redirect URI domain not in allowed list",
                    extra={
                        "event": "security_validation_failed",
                        "field": "redirect_uri",
                        "domain": hostname,
                        "violation_type": "domain_not_allowed"
                    }
                )
                raise ValueError(f"Redirect URI domain '{hostname}' is not allowed")
        
        return v
    
    @field_validator('state')
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        """Validate state parameter for CSRF protection"""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("State must be a string")
        
        # Remove any whitespace
        v = v.strip()
        
        # Check length constraints
        if len(v) > 500:
            raise ValueError("State parameter too long (max 500 characters)")
        
        # Allow only alphanumeric, hyphens, underscores, and dots for state
        if not re.match(r'^[a-zA-Z0-9\-_\.]+$', v):
            raise ValueError("State contains invalid characters")
        
        # Check for injection patterns
        injection_patterns = [
            r'[<>"\']',  # XSS patterns
            r'[;]',      # SQL injection patterns
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                logger.warning(
                    "Potentially malicious state parameter detected",
                    extra={
                        "event": "security_validation_failed",
                        "field": "state",
                        "pattern": pattern,
                        "violation_type": "injection_attempt"
                    }
                )
                raise ValueError("State contains potentially malicious content")
        
        return v


def sanitize_string_input(value: str, max_length: int = 1000, allow_html: bool = False) -> str:
    """
    Sanitize string input to prevent injection attacks
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags (default: False)
    
    Returns:
        Sanitized string
    
    Raises:
        ValidationError: If input fails validation
    """
    if not isinstance(value, str):
        raise ValidationError("Input must be a string", violation_type="type_error")
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Check length
    if len(sanitized) > max_length:
        raise ValidationError(f"Input too long (max {max_length} characters)", violation_type="length_exceeded")
    
    if not allow_html:
        # Escape HTML entities to prevent XSS
        html_escape_map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
        }
        for char, escaped in html_escape_map.items():
            sanitized = sanitized.replace(char, escaped)
    
    # Check for SQL injection patterns
    sql_patterns = [
        r"(union\s+select|insert\s+into|update\s+set|delete\s+from)",
        r"(drop\s+table|create\s+table|alter\s+table)",
        r"(exec\s*\(|execute\s*\()",
        r"(\bor\b\s*\d+\s*=\s*\d+|\band\b\s*\d+\s*=\s*\d+)"
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            logger.warning(
                "SQL injection pattern detected",
                extra={
                    "event": "security_validation_failed",
                    "pattern": pattern,
                    "violation_type": "sql_injection"
                }
            )
            raise ValidationError("Input contains potentially malicious SQL patterns", violation_type="sql_injection")
    
    return sanitized


def validate_tenant_id(tenant_id: str) -> str:
    """Validate tenant ID to ensure proper tenant isolation"""
    if not tenant_id or not isinstance(tenant_id, str):
        raise ValidationError("Tenant ID is required and must be a string", field="tenant_id")
    
    tenant_id = tenant_id.strip()
    
    # Check UUID format (assuming UUIDs for tenant IDs)
    uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    if not re.match(uuid_pattern, tenant_id):
        raise ValidationError("Invalid tenant ID format", field="tenant_id", violation_type="format_error")
    
    return tenant_id


def validate_user_role(role: str) -> str:
    """Validate user role against allowed values"""
    if not role or not isinstance(role, str):
        raise ValidationError("User role is required and must be a string", field="role")
    
    role = role.strip().lower()
    
    allowed_roles = ['viewer', 'analyst', 'admin']
    if role not in allowed_roles:
        raise ValidationError(f"Invalid user role: {role}", field="role", violation_type="invalid_value")
    
    return role


def validate_permission(permission: str) -> str:
    """Validate permission string format"""
    if not permission or not isinstance(permission, str):
        raise ValidationError("Permission is required and must be a string", field="permission")
    
    permission = permission.strip()
    
    # Permission format: action:resource (e.g., read:users, write:organisations)
    if not re.match(r'^[a-z_]+:[a-z_]+$', permission):
        raise ValidationError("Invalid permission format", field="permission", violation_type="format_error")
    
    return permission


def create_security_headers() -> Dict[str, str]:
    """Create security headers for HTTP responses"""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';",
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'Cache-Control': 'no-store, no-cache, must-revalidate, private',
        'Pragma': 'no-cache'
    }


class SecurityHeadersMiddleware:
    """Middleware to add security headers to all responses"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                security_headers = create_security_headers()
                
                for key, value in security_headers.items():
                    headers[key.encode()] = value.encode()
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, receive, send_with_headers)