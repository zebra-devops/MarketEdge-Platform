from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext
from ..core.config import settings
from ..core.logging import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None,
    tenant_id: Optional[str] = None,
    user_role: Optional[str] = None,
    permissions: Optional[List[str]] = None,
    industry: Optional[str] = None
) -> str:
    """Create JWT access token with enhanced multi-tenant context"""
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Base token claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": secrets.token_urlsafe(16),  # Unique token identifier
    })
    
    # Multi-tenant context
    if tenant_id:
        to_encode["tenant_id"] = str(tenant_id)
        
    if user_role:
        to_encode["role"] = user_role
        to_encode["user_role"] = user_role  # For backward compatibility with tests
        
    if industry:
        to_encode["industry"] = industry
        
    if permissions:
        to_encode["permissions"] = permissions
    
    # Security claims
    to_encode.update({
        "iss": settings.JWT_ISSUER if hasattr(settings, 'JWT_ISSUER') else "market-edge-platform",
        "aud": settings.JWT_AUDIENCE if hasattr(settings, 'JWT_AUDIENCE') else "market-edge-api"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    logger.debug(
        "Access token created",
        extra={
            "event": "access_token_created",
            "user_id": data.get("sub"),
            "tenant_id": tenant_id,
            "role": user_role,
            "expires_at": expire.isoformat(),
            "has_permissions": bool(permissions)
        }
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any], 
    tenant_id: Optional[str] = None,
    token_family: Optional[str] = None
) -> str:
    """Create JWT refresh token with enhanced security"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Base refresh token claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16),  # Unique token identifier
    })
    
    # Multi-tenant context for refresh validation
    if tenant_id:
        to_encode["tenant_id"] = str(tenant_id)
        
    # Token family for rotation detection
    if token_family:
        to_encode["family"] = token_family
    else:
        to_encode["family"] = secrets.token_urlsafe(16)
    
    # Security claims
    to_encode.update({
        "iss": settings.JWT_ISSUER if hasattr(settings, 'JWT_ISSUER') else "market-edge-platform",
        "aud": settings.JWT_AUDIENCE if hasattr(settings, 'JWT_AUDIENCE') else "market-edge-api"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    logger.debug(
        "Refresh token created",
        extra={
            "event": "refresh_token_created",
            "user_id": data.get("sub"),
            "tenant_id": tenant_id,
            "expires_at": expire.isoformat(),
            "token_family": to_encode["family"]
        }
    )
    
    return encoded_jwt


def verify_token(token: str, expected_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Verify JWT token with enhanced validation"""
    try:
        # Decode and verify token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE if hasattr(settings, 'JWT_AUDIENCE') else "market-edge-api",
            issuer=settings.JWT_ISSUER if hasattr(settings, 'JWT_ISSUER') else "market-edge-platform"
        )
        
        # Verify token type if specified
        if expected_type and payload.get("type") != expected_type:
            logger.warning(
                "Token type mismatch",
                extra={
                    "event": "token_type_mismatch",
                    "expected": expected_type,
                    "actual": payload.get("type"),
                    "token_jti": payload.get("jti")
                }
            )
            return None
            
        # Verify required claims
        required_claims = ["sub", "exp", "iat", "type", "jti"]
        missing_claims = [claim for claim in required_claims if claim not in payload]
        if missing_claims:
            logger.warning(
                "Missing required token claims",
                extra={
                    "event": "missing_token_claims",
                    "missing_claims": missing_claims,
                    "token_jti": payload.get("jti")
                }
            )
            return None
            
        logger.debug(
            "Token verification successful",
            extra={
                "event": "token_verified",
                "token_type": payload.get("type"),
                "user_id": payload.get("sub"),
                "tenant_id": payload.get("tenant_id"),
                "role": payload.get("role"),
                "user_role": payload.get("user_role"),
                "industry": payload.get("industry"),
                "token_jti": payload.get("jti")
            }
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.info(
            "Token expired",
            extra={
                "event": "token_expired",
                "error_type": "expired_signature"
            }
        )
        return None
        
    except jwt.JWTClaimsError as e:
        # Handle audience and issuer validation errors
        error_msg = str(e).lower()
        if "audience" in error_msg:
            logger.warning(
                "Invalid token audience",
                extra={
                    "event": "token_invalid_audience",
                    "error_type": "invalid_audience",
                    "error": str(e)
                }
            )
        elif "issuer" in error_msg:
            logger.warning(
                "Invalid token issuer",
                extra={
                    "event": "token_invalid_issuer",
                    "error_type": "invalid_issuer",
                    "error": str(e)
                }
            )
        else:
            logger.warning(
                "JWT claims validation failed",
                extra={
                    "event": "jwt_claims_validation_failed",
                    "error_type": "jwt_claims_error",
                    "error": str(e)
                }
            )
        return None
        
    except JWTError as e:
        logger.warning(
            "JWT verification failed",
            extra={
                "event": "jwt_verification_failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        return None


def get_user_permissions(user_role: str, tenant_context: Optional[Dict[str, Any]] = None) -> List[str]:
    """Get user permissions based on role and tenant context"""
    permissions = []
    
    # Base permissions by role
    role_permissions = {
        "super_admin": [
            # Super admin has all permissions across all tenants
            "read:users", "write:users", "delete:users",
            "read:organizations", "write:organizations", "delete:organizations",
            "read:audit_logs", "read:system_metrics",
            "manage:feature_flags", "manage:rate_limits",
            "manage:cross_tenant", "manage:super_admin",
            # Full application access for super admin
            "read:market_edge", "read:causal_edge", "read:value_edge",
            "admin:market_edge", "admin:causal_edge", "admin:value_edge",
            # Platform administration
            "manage:platform", "manage:security", "manage:tenants"
        ],
        "admin": [
            "read:users", "write:users", "delete:users",
            "read:organizations", "write:organizations", "delete:organizations",
            "read:audit_logs", "read:system_metrics",
            "manage:feature_flags", "manage:rate_limits",
            # Application permissions for admin
            "read:market_edge", "read:causal_edge", "read:value_edge"
        ],
        "manager": [
            "read:users", "write:users",
            "read:organizations", "write:organizations",
            "read:audit_logs",
            # Application permissions for manager
            "read:market_edge", "read:causal_edge", "read:value_edge"
        ],
        "viewer": [
            "read:organizations",
            # Application permissions for viewer (basic access)
            "read:market_edge"
        ]
    }
    
    permissions.extend(role_permissions.get(user_role, []))
    
    # Add tenant-specific permissions if provided
    if tenant_context and tenant_context.get("industry"):
        industry = tenant_context["industry"].lower()
        industry_permissions = {
            "cinema": [
                "read:cinema_data", "analyze:cinema_metrics",
                # Additional application access for cinema industry
                "read:causal_edge", "read:value_edge"
            ],
            "hotel": [
                "read:hotel_data", "analyze:hotel_metrics",
                "read:causal_edge", "read:value_edge"
            ],
            "gym": [
                "read:gym_data", "analyze:gym_metrics",
                "read:causal_edge", "read:value_edge"
            ],
            "retail": [
                "read:retail_data", "analyze:retail_metrics",
                "read:causal_edge", "read:value_edge"
            ],
            "b2b": [
                "read:b2b_data", "analyze:b2b_metrics",
                "read:causal_edge", "read:value_edge"
            ]
        }
        permissions.extend(industry_permissions.get(industry, []))
    
    return list(set(permissions))  # Remove duplicates


def is_token_expired(payload: Dict[str, Any]) -> bool:
    """Check if token is expired"""
    if "exp" not in payload:
        return True
        
    exp_timestamp = payload["exp"]
    current_timestamp = datetime.utcnow().timestamp()
    
    return current_timestamp >= exp_timestamp


def get_token_remaining_time(payload: Dict[str, Any]) -> Optional[timedelta]:
    """Get remaining time before token expires"""
    if "exp" not in payload:
        return None
        
    exp_timestamp = payload["exp"]
    current_timestamp = datetime.utcnow().timestamp()
    
    if current_timestamp >= exp_timestamp:
        return timedelta(0)
        
    remaining_seconds = exp_timestamp - current_timestamp
    return timedelta(seconds=remaining_seconds)


def should_refresh_token(payload: Dict[str, Any], threshold_minutes: int = 15) -> bool:
    """Check if token should be refreshed based on remaining time"""
    remaining_time = get_token_remaining_time(payload)
    
    if remaining_time is None:
        return True
        
    threshold = timedelta(minutes=threshold_minutes)
    return remaining_time <= threshold


def extract_tenant_context_from_token(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract tenant context from verified token payload"""
    if not payload:
        return None
        
    return {
        "tenant_id": payload.get("tenant_id"),
        "user_role": payload.get("user_role") or payload.get("role"),  # Check both fields
        "user_id": payload.get("sub"),
        "industry": payload.get("industry"),
        "permissions": payload.get("permissions", [])
    }


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)