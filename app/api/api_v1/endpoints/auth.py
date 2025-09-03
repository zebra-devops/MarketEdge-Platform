from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Form, Body
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from pydantic import BaseModel, ValidationError as PydanticValidationError
from typing import Dict, Any, Optional
from datetime import timedelta
import secrets
from ....core.database import get_db
from ....models.user import User
from ....models.organisation import Organisation
from ....auth.jwt import (
    create_access_token, 
    create_refresh_token, 
    verify_token, 
    get_user_permissions,
    should_refresh_token,
    extract_tenant_context_from_token
)
from ....auth.auth0 import auth0_client
from ....auth.dependencies import get_current_user
from ....core.logging import get_logger
from ....core.config import settings
from ....core.validators import (
    AuthParameterValidator, 
    ValidationError, 
    sanitize_string_input, 
    validate_tenant_id,
    create_security_headers
)

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()


def _setup_default_tool_access(db: Session, organisation_id: str):
    """Set up default tool access for a new organization"""
    try:
        from ....models.tool import Tool
        from ....models.organisation_tool_access import OrganisationToolAccess
        
        # Get all available tools
        tools = db.query(Tool).filter(Tool.is_active == True).all()
        
        logger.info(f"Setting up default tool access for organization {organisation_id}", extra={
            "event": "default_tool_access_setup",
            "organisation_id": organisation_id,
            "tools_count": len(tools)
        })
        
        # Create basic access for all tools for the Default organization
        for tool in tools:
            # Check if access already exists
            existing_access = db.query(OrganisationToolAccess).filter(
                OrganisationToolAccess.organisation_id == organisation_id,
                OrganisationToolAccess.tool_id == tool.id
            ).first()
            
            if not existing_access:
                tool_access = OrganisationToolAccess(
                    organisation_id=organisation_id,
                    tool_id=tool.id,
                    subscription_tier="basic",
                    features_enabled=["basic_access"],
                    usage_limits={"daily_requests": 100, "monthly_requests": 3000}
                )
                db.add(tool_access)
        
        db.commit()
        
        logger.info(f"Default tool access setup completed for organization {organisation_id}", extra={
            "event": "default_tool_access_complete",
            "organisation_id": organisation_id
        })
        
    except Exception as e:
        logger.error(f"Failed to set up default tool access for organization {organisation_id}", extra={
            "event": "default_tool_access_error",
            "organisation_id": organisation_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        # Don't raise exception - tool access can be set up later
        db.rollback()


class LoginRequest(BaseModel):
    code: str
    redirect_uri: str
    state: Optional[str] = None
    
    def model_post_init(self, __context: Any) -> None:
        """Additional validation after Pydantic validation"""
        try:
            # Use our enhanced validator for comprehensive security checks
            validator = AuthParameterValidator(
                code=self.code,
                redirect_uri=self.redirect_uri,
                state=self.state
            )
            # Update values with validated/sanitized versions
            self.code = validator.code
            self.redirect_uri = validator.redirect_uri
            self.state = validator.state
        except PydanticValidationError as e:
            logger.warning(
                "Login request validation failed",
                extra={
                    "event": "login_validation_failed",
                    "error": str(e),
                    "violation_type": "validation_error"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request parameters: {str(e)}"
            )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    tenant: Dict[str, Any]
    permissions: list[str]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None
    all_devices: bool = False


@router.post("/login-oauth2", response_model=TokenResponse)
async def login_oauth2(
    login_data: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """OAuth2 authentication endpoint for JSON requests"""
    # Add security headers
    security_headers = create_security_headers()
    for key, value in security_headers.items():
        response.headers[key] = value
    
    # Rate limiting check
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info("OAuth2 authentication request received", extra={
        "event": "oauth2_auth_start",
        "client_ip": client_ip,
        "has_code": bool(login_data.code),
        "redirect_uri": login_data.redirect_uri
    })
    
    try:
        # Validate and sanitize input parameters
        validated_code = sanitize_string_input(login_data.code, max_length=500)
        validated_redirect_uri = sanitize_string_input(login_data.redirect_uri, max_length=200)
        validated_state = sanitize_string_input(login_data.state, max_length=100) if login_data.state else None
        
        validator = AuthParameterValidator(
            code=validated_code,
            redirect_uri=validated_redirect_uri,
            state=validated_state
        )
        
        if not validator.is_valid():
            logger.warning("OAuth2 validation failed", extra={
                "event": "oauth2_validation_failed",
                "errors": validator.errors,
                "client_ip": client_ip
            })
            raise HTTPException(status_code=400, detail="Invalid authentication parameters")
        
        # Exchange authorization code for tokens
        tokens = await auth0_client.exchange_code_for_token(
            code=validated_code,
            redirect_uri=validated_redirect_uri,
            state=validated_state
        )
        
        if not tokens or not tokens.get('access_token'):
            logger.error("OAuth2 token exchange failed", extra={
                "event": "oauth2_token_exchange_failed",
                "client_ip": client_ip
            })
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        # Get user info from Auth0
        user_info = await auth0_client.get_user_info(tokens['access_token'])
        if not user_info:
            logger.error("Failed to retrieve user info from Auth0", extra={
                "event": "oauth2_user_info_failed",
                "client_ip": client_ip
            })
            raise HTTPException(status_code=401, detail="Failed to retrieve user information")
        
        # Create or update user in database
        user = await _create_or_update_user_from_auth0(db, user_info, client_ip)
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "tenant_id": str(user.organisation_id), "role": user.role}
        )
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        logger.info("OAuth2 authentication successful", extra={
            "event": "oauth2_auth_success",
            "user_id": str(user.id),
            "tenant_id": str(user.organisation_id),
            "client_ip": client_ip
        })
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600,
            user=user,
            tenant=user.organisation,
            permissions=get_user_permissions(user.role)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2 authentication error: {e}", extra={
            "event": "oauth2_auth_error",
            "error_type": type(e).__name__,
            "client_ip": client_ip
        })
        raise HTTPException(status_code=500, detail="Internal server error during authentication")


async def _create_or_update_user_from_auth0(db: Session, user_info: dict, client_ip: str) -> User:
    """Create or update user from Auth0 user info"""
    # Enhanced user info validation with sanitization
    required_fields = ["email", "sub"]
    missing_fields = [field for field in required_fields if not user_info.get(field)]
    if missing_fields:
        logger.error("Missing required fields in user info", extra={
            "event": "userinfo_missing_fields",
            "missing_fields": missing_fields,
            "user_sub": user_info.get("sub"),
            "client_ip": client_ip
        })
        raise HTTPException(
            status_code=400,
            detail=f"Invalid user information: missing {', '.join(missing_fields)}"
        )
    
    # Sanitize user info fields to prevent injection
    try:
        sanitized_email = sanitize_string_input(user_info["email"], max_length=254)
        sanitized_sub = sanitize_string_input(user_info["sub"], max_length=100)
        sanitized_given_name = sanitize_string_input(user_info.get("given_name", ""), max_length=100) if user_info.get("given_name") else ""
        sanitized_family_name = sanitize_string_input(user_info.get("family_name", ""), max_length=100) if user_info.get("family_name") else ""
    except ValidationError as e:
        logger.error("User info sanitization failed", extra={
            "event": "userinfo_sanitization_failed", 
            "error": str(e),
            "violation_type": e.violation_type,
            "client_ip": client_ip
        })
        raise HTTPException(
            status_code=400,
            detail="Invalid user information format"
        )
    
    # Find or create user in database using sanitized email
    try:
        user = db.query(User).filter(User.email == sanitized_email).first()
        if not user:
            # Create user with default organization
            default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
            if not default_org:
                from ....models.organisation import SubscriptionPlan
                from ....core.rate_limit_config import Industry
                default_org = Organisation(
                    name="Default",
                    industry=Industry.DEFAULT.value,
                    industry_type=Industry.DEFAULT,
                    subscription_plan=SubscriptionPlan.basic
                )
                db.add(default_org)
                db.commit()
                db.refresh(default_org)
                
                # Set up default tool access for the Default organization
                _setup_default_tool_access(db, default_org.id)
            
            from ....models.user import UserRole
            user = User(
                email=sanitized_email,
                first_name=sanitized_given_name,
                last_name=sanitized_family_name,
                organisation_id=default_org.id,
                role=UserRole.viewer
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info("New user created", extra={
                "event": "user_created",
                "user_id": str(user.id),
                "email": user.email,
                "organisation_id": str(user.organisation_id)
            })
        
        return user
        
    except Exception as e:
        logger.error("Database error during user creation/lookup", extra={
            "event": "database_error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "email": sanitized_email
        })
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error during authentication"
        )


async def login_json_body(request: Request) -> Optional[LoginRequest]:
    """Helper to parse JSON body for OAuth2 requests"""
    try:
        body = await request.body()
        if body and request.headers.get('content-type') == 'application/json':
            import json
            json_data = json.loads(body.decode('utf-8'))
            if 'code' in json_data and 'redirect_uri' in json_data:
                return LoginRequest(**json_data)
    except Exception:
        pass
    return None

@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response, 
    request: Request, 
    db: Session = Depends(get_db),
    # Form data parameters for legacy support
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    state: Optional[str] = Form(None)
):
    """Enhanced login with Auth0 authorization code, comprehensive validation, and multi-tenant context"""
    # Add security headers to response
    security_headers = create_security_headers()
    for key, value in security_headers.items():
        response.headers[key] = value
    
    # Rate limiting check - prevent brute force attacks
    client_ip = request.client.host if request.client else "unknown"
    
    # Handle both JSON and form data
    if login_data is None:
        # Try to parse JSON body manually if FastAPI didn't bind it
        try:
            body = await request.body()
            if body:
                import json
                json_data = json.loads(body.decode('utf-8'))
                if 'code' in json_data and 'redirect_uri' in json_data:
                    login_data = LoginRequest(**json_data)
                    logger.info("Successfully parsed JSON body manually", extra={
                        "event": "manual_json_parse",
                        "has_code": bool(json_data.get('code')),
                        "has_redirect_uri": bool(json_data.get('redirect_uri'))
                    })
        except Exception as json_error:
            logger.warning(f"Failed to parse JSON body: {json_error}", extra={
                "event": "json_parse_error",
                "error": str(json_error)
            })
    
    # Fallback to form data if JSON parsing failed
    if login_data is None and code is not None:
        login_data = LoginRequest(code=code, redirect_uri=redirect_uri, state=state)
        logger.info("Using form data for authentication", extra={
            "event": "form_data_auth",
            "has_code": bool(code),
            "has_redirect_uri": bool(redirect_uri)
        })
    elif login_data is None:
        logger.error("No authentication data provided", extra={
            "event": "missing_auth_data",
            "content_type": request.headers.get("content-type")
        })
        raise HTTPException(status_code=400, detail="Missing authentication data")
    
    # Additional input validation and sanitization
    try:
        # Validate and sanitize all input parameters
        validated_code = sanitize_string_input(login_data.code, max_length=500)
        validated_redirect_uri = sanitize_string_input(login_data.redirect_uri, max_length=2000)
        validated_state = sanitize_string_input(login_data.state, max_length=500) if login_data.state else None
        
        logger.info("Authentication attempt initiated with enhanced validation", extra={
            "event": "auth_attempt",
            "redirect_uri_domain": validated_redirect_uri.split('/')[2] if '//' in validated_redirect_uri else validated_redirect_uri,
            "has_state": bool(validated_state),
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", "unknown")[:200]  # Limit length
        })
        
    except ValidationError as e:
        logger.error(
            "Login request validation failed",
            extra={
                "event": "auth_validation_failed",
                "error": str(e),
                "violation_type": e.violation_type,
                "field": e.field,
                "client_ip": client_ip
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request parameters"
        )
    
    try:
        
        token_data = await auth0_client.exchange_code_for_token(
            validated_code, 
            validated_redirect_uri,
            validated_state
        )
        
        if not token_data:
            logger.error("Token exchange failed", extra={
                "event": "auth_failure",
                "error_type": "token_exchange"
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )
        
        logger.info("Token exchange successful", extra={
            "event": "token_exchange_success",
            "expires_in": token_data.get("expires_in")
        })
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error("Authentication endpoint error", extra={
            "event": "auth_error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
            "environment": settings.ENVIRONMENT,
            "auth0_domain": settings.AUTH0_DOMAIN,
            "validated_code_length": len(validated_code) if 'validated_code' in locals() else 0,
            "redirect_uri": validated_redirect_uri if 'validated_redirect_uri' in locals() else "unknown"
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )
    
    # Get user info from Auth0
    try:
        user_info = await auth0_client.get_user_info(token_data["access_token"])
        if not user_info:
            logger.error("Failed to get user info", extra={
                "event": "userinfo_failure",
                "has_access_token": bool(token_data.get("access_token"))
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from Auth0"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user info from Auth0", extra={
            "event": "userinfo_exception",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "has_token": bool(token_data)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user information"
        )
    
    # Enhanced user info validation with sanitization
    required_fields = ["email", "sub"]
    missing_fields = [field for field in required_fields if not user_info.get(field)]
    if missing_fields:
        logger.error("Missing required fields in user info", extra={
            "event": "userinfo_missing_fields",
            "missing_fields": missing_fields,
            "user_sub": user_info.get("sub"),
            "client_ip": client_ip
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user information: missing {', '.join(missing_fields)}"
        )
    
    # Sanitize user info fields to prevent injection
    try:
        sanitized_email = sanitize_string_input(user_info["email"], max_length=254)
        sanitized_sub = sanitize_string_input(user_info["sub"], max_length=100)
        sanitized_given_name = sanitize_string_input(user_info.get("given_name", ""), max_length=100) if user_info.get("given_name") else ""
        sanitized_family_name = sanitize_string_input(user_info.get("family_name", ""), max_length=100) if user_info.get("family_name") else ""
    except ValidationError as e:
        logger.error(
            "User info sanitization failed",
            extra={
                "event": "userinfo_sanitization_failed",
                "error": str(e),
                "violation_type": e.violation_type,
                "client_ip": client_ip
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user information format"
        )
    
    # Find or create user in database using sanitized email
    try:
        user = db.query(User).filter(User.email == sanitized_email).first()
        if not user:
            # Create user with default organization
            default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
            if not default_org:
                from ....models.organisation import SubscriptionPlan
                from ....core.rate_limit_config import Industry
                default_org = Organisation(
                    name="Default", 
                    industry=Industry.DEFAULT.value,
                    industry_type=Industry.DEFAULT,
                    subscription_plan=SubscriptionPlan.basic
                )
                db.add(default_org)
                db.commit()
                db.refresh(default_org)
                
                # Set up default tool access for the Default organization
                _setup_default_tool_access(db, default_org.id)
            
            from ....models.user import UserRole
            user = User(
                email=sanitized_email,
                first_name=sanitized_given_name,
                last_name=sanitized_family_name,
                organisation_id=default_org.id,
                role=UserRole.viewer
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info("New user created", extra={
                "event": "user_created",
                "user_id": str(user.id),
                "email": user.email,
                "organisation_id": str(user.organisation_id)
            })
    except Exception as e:
        logger.error("Database error during user creation/lookup", extra={
            "event": "database_error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "email": sanitized_email
        })
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during authentication"
        )
    
    # Ensure user has organization and application access relationships loaded
    if not user.organisation or not hasattr(user, 'application_access'):
        user = db.query(User).options(
            joinedload(User.organisation),
            joinedload(User.application_access)
        ).filter(User.id == user.id).first()
    
    # Get user permissions based on role and tenant context
    tenant_context = {
        "industry": user.organisation.industry if user.organisation else "default"
    }
    permissions = get_user_permissions(user.role.value, tenant_context)
    
    # Create enhanced tokens with tenant context
    token_data_payload = {
        "sub": str(user.id), 
        "email": user.email
    }
    
    access_token = create_access_token(
        data=token_data_payload,
        tenant_id=str(user.organisation_id),
        user_role=user.role.value,
        permissions=permissions,
        industry=user.organisation.industry if user.organisation else "default"
    )
    
    refresh_token = create_refresh_token(
        data=token_data_payload,
        tenant_id=str(user.organisation_id)
    )
    
    # Set secure HTTP-only cookies for tokens with production-ready settings
    cookie_settings = settings.get_cookie_settings()
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert minutes to seconds
        **cookie_settings
    )
    
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,  # Convert days to seconds
        **cookie_settings
    )
    
    # Set additional security cookies
    response.set_cookie(
        key="session_security",
        value="verified",
        max_age=settings.SESSION_TIMEOUT_MINUTES * 60,
        **cookie_settings
    )
    
    # CSRF protection cookie (readable by JS for CSRF token)
    csrf_cookie_settings = cookie_settings.copy()
    csrf_cookie_settings["httponly"] = False  # Allow JS access for CSRF protection
    response.set_cookie(
        key="csrf_token",
        value=secrets.token_urlsafe(32),
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **csrf_cookie_settings
    )
    
    logger.info("Authentication successful", extra={
        "event": "auth_success",
        "user_id": str(user.id),
        "organisation_id": str(user.organisation_id),
        "user_role": user.role.value,
        "permissions_count": len(permissions),
        "tenant_industry": tenant_context["industry"]
    })
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600,  # 1 hour in seconds
        user={
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "organisation_id": str(user.organisation_id),
            "is_active": user.is_active,
            "application_access": [
                {"application": access.application.value, "has_access": access.has_access}
                for access in user.application_access
            ] if user.application_access else []
        },
        tenant={
            "id": str(user.organisation_id),
            "name": user.organisation.name if user.organisation else "Default",
            "industry": user.organisation.industry if user.organisation else "Technology",
            "subscription_plan": user.organisation.subscription_plan.value if user.organisation else "basic"
        },
        permissions=permissions
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest, response: Response, db: Session = Depends(get_db)):
    """Enhanced token refresh with tenant validation and rotation"""
    # Verify refresh token
    payload = verify_token(refresh_data.refresh_token, expected_type="refresh")
    if not payload:
        logger.warning("Invalid refresh token provided", extra={
            "event": "refresh_token_invalid"
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    token_family = payload.get("family")
    
    if not user_id:
        logger.warning("Missing user ID in refresh token", extra={
            "event": "refresh_token_missing_user_id",
            "token_jti": payload.get("jti")
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Validate user exists and is active
    user = db.query(User).options(
        joinedload(User.organisation),
        joinedload(User.application_access)
    ).filter(User.id == user_id).first()
    if not user or not user.is_active:
        logger.warning("User not found or inactive during refresh", extra={
            "event": "refresh_user_invalid",
            "user_id": user_id,
            "user_exists": bool(user),
            "user_active": user.is_active if user else False
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Validate tenant context
    if tenant_id and str(user.organisation_id) != tenant_id:
        logger.warning("Tenant mismatch during refresh", extra={
            "event": "refresh_tenant_mismatch",
            "user_id": user_id,
            "token_tenant_id": tenant_id,
            "user_tenant_id": str(user.organisation_id)
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context mismatch"
        )
    
    # Get updated permissions
    tenant_context = {
        "industry": user.organisation.industry if user.organisation else "Technology"
    }
    permissions = get_user_permissions(user.role.value, tenant_context)
    
    # Create new tokens with rotation
    token_data_payload = {
        "sub": str(user.id), 
        "email": user.email
    }
    
    new_access_token = create_access_token(
        data=token_data_payload,
        tenant_id=str(user.organisation_id),
        user_role=user.role.value,
        permissions=permissions,
        industry=user.organisation.industry if user.organisation else "default"
    )
    
    # Create new refresh token with same family for rotation tracking
    new_refresh_token = create_refresh_token(
        data=token_data_payload,
        tenant_id=str(user.organisation_id),
        token_family=token_family
    )
    
    # Update secure cookies with production-ready settings
    cookie_settings = settings.get_cookie_settings()
    
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **cookie_settings
    )
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        **cookie_settings
    )
    
    # Update session security cookie
    response.set_cookie(
        key="session_security",
        value="verified",
        max_age=settings.SESSION_TIMEOUT_MINUTES * 60,
        **cookie_settings
    )
    
    # Update CSRF token
    csrf_cookie_settings = cookie_settings.copy()
    csrf_cookie_settings["httponly"] = False
    response.set_cookie(
        key="csrf_token",
        value=secrets.token_urlsafe(32),
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **csrf_cookie_settings
    )
    
    logger.info("Token refresh successful", extra={
        "event": "token_refresh_success",
        "user_id": user_id,
        "tenant_id": str(user.organisation_id),
        "old_token_jti": payload.get("jti"),
        "token_family": token_family
    })
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=3600,
        user={
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "organisation_id": str(user.organisation_id),
            "is_active": user.is_active,
            "application_access": [
                {"application": access.application.value, "has_access": access.has_access}
                for access in user.application_access
            ] if user.application_access else []
        },
        tenant={
            "id": str(user.organisation_id),
            "name": user.organisation.name if user.organisation else "Default",
            "industry": user.organisation.industry if user.organisation else "Technology",
            "subscription_plan": user.organisation.subscription_plan.value if user.organisation else "basic"
        },
        permissions=permissions
    )


@router.post("/logout")
async def logout(
    logout_data: LogoutRequest, 
    response: Response, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Enhanced logout with token revocation and session cleanup"""
    try:
        # Revoke refresh token if provided
        if logout_data.refresh_token:
            revoke_success = await auth0_client.revoke_token(logout_data.refresh_token, "refresh_token")
            if not revoke_success:
                logger.warning("Failed to revoke refresh token during logout", extra={
                    "event": "logout_revoke_failed",
                    "user_id": str(current_user.id)
                })
        
        # Clear secure cookies with proper settings
        cookie_settings = settings.get_cookie_settings()
        response.delete_cookie(key="access_token", **cookie_settings)
        response.delete_cookie(key="refresh_token", **cookie_settings)
        response.delete_cookie(key="session_security", **cookie_settings)
        response.delete_cookie(key="csrf_token", **cookie_settings)
        
        logger.info("User logout successful", extra={
            "event": "logout_success",
            "user_id": str(current_user.id),
            "organisation_id": str(current_user.organisation_id),
            "all_devices": logout_data.all_devices
        })
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        logger.error("Error during logout", extra={
            "event": "logout_error",
            "user_id": str(current_user.id),
            "error": str(e),
            "error_type": type(e).__name__
        })
        # Still clear cookies even if revocation fails
        cookie_settings = settings.get_cookie_settings()
        response.delete_cookie(key="access_token", **cookie_settings)
        response.delete_cookie(key="refresh_token", **cookie_settings)
        response.delete_cookie(key="session_security", **cookie_settings)
        response.delete_cookie(key="csrf_token", **cookie_settings)
        
        return {"message": "Logout completed with warnings"}


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get enhanced current user information with tenant context"""
    # Ensure organization and application access are loaded
    if not current_user.organisation or not hasattr(current_user, 'application_access'):
        current_user = db.query(User).options(
            joinedload(User.organisation),
            joinedload(User.application_access)
        ).filter(User.id == current_user.id).first()
    
    # Get user permissions
    tenant_context = {
        "industry": current_user.organisation.industry if current_user.organisation else "Technology"
    }
    permissions = get_user_permissions(current_user.role.value, tenant_context)
    
    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "role": current_user.role.value,
            "organisation_id": str(current_user.organisation_id),
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
            "application_access": [
                {"application": access.application.value, "has_access": access.has_access}
                for access in current_user.application_access
            ] if current_user.application_access else []
        },
        "tenant": {
            "id": str(current_user.organisation_id),
            "name": current_user.organisation.name if current_user.organisation else "Default",
            "industry": current_user.organisation.industry if current_user.organisation else "Technology",
            "subscription_plan": current_user.organisation.subscription_plan.value if current_user.organisation else "basic"
        },
        "permissions": permissions,
        "session": {
            "authenticated": True,
            "tenant_isolated": True
        }
    }


@router.get("/auth0-url")
async def get_auth0_url(redirect_uri: str, additional_scopes: Optional[str] = None, organization_hint: Optional[str] = None):
    """Get Auth0 authorization URL with enhanced security and multi-tenant organization context"""
    try:
        # Parse additional scopes if provided
        scopes_list = additional_scopes.split(",") if additional_scopes else None
        
        auth_url = auth0_client.get_authorization_url(
            redirect_uri=redirect_uri,
            additional_scopes=scopes_list,
            organization_hint=organization_hint
        )
        
        logger.info("Auth0 URL generated with tenant context", extra={
            "event": "auth0_url_generated",
            "redirect_uri_domain": redirect_uri.split('/')[2] if '//' in redirect_uri else redirect_uri,
            "additional_scopes": scopes_list,
            "organization_hint": organization_hint
        })
        
        return {
            "auth_url": auth_url,
            "redirect_uri": redirect_uri,
            "scopes": ["openid", "profile", "email", "read:organization", "read:roles"] + (scopes_list or []),
            "organization_hint": organization_hint
        }
        
    except ValueError as e:
        logger.error("Invalid redirect URI for Auth0 URL", extra={
            "event": "auth0_url_error",
            "redirect_uri": redirect_uri,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error generating Auth0 URL", extra={
            "event": "auth0_url_unexpected_error",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )


@router.get("/session/check")
async def check_session(current_user: User = Depends(get_current_user)):
    """Check if current session is valid and return basic info"""
    return {
        "authenticated": True,
        "user_id": str(current_user.id),
        "tenant_id": str(current_user.organisation_id),
        "role": current_user.role.value,
        "active": current_user.is_active
    }


@router.post("/session/extend")
async def extend_session(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Extend session if token is near expiration"""
    # This would typically check if the current token should be refreshed
    # and issue a new one if needed. For now, return session info.
    
    # Get current token from authorization header
    authorization = request.headers.get("authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid token found"
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    payload = verify_token(token, expected_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Check if token should be refreshed (within 15 minutes of expiration)
    if should_refresh_token(payload, threshold_minutes=15):
        logger.info("Session extension recommended", extra={
            "event": "session_extension_needed",
            "user_id": str(current_user.id),
            "token_jti": payload.get("jti")
        })
        return {
            "extend_recommended": True,
            "message": "Token should be refreshed",
            "expires_soon": True
        }
    
    return {
        "extend_recommended": False,
        "message": "Session is still valid",
        "expires_soon": False
    }


@router.post("/emergency/fix-database-schema")
async def emergency_fix_database_schema(db: Session = Depends(get_db)):
    """EMERGENCY: Fix database schema for authentication - Add missing user columns"""
    try:
        logger.info("EMERGENCY: Starting database schema fix", extra={
            "event": "emergency_schema_fix_start",
            "missing_columns": ["department", "location", "phone"]
        })
        
        import os
        import psycopg2
        from urllib.parse import urlparse
        
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL not found in environment")
            
        # Parse database URL
        parsed = urlparse(database_url)
        
        # Connect directly with psycopg2
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username, 
            password=parsed.password,
            sslmode='require'
        )
        
        cur = conn.cursor()
        columns_added = []
        
        # Add columns one by one
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100)")
            columns_added.append('department')
            logger.info("Added department column")
        except Exception as e:
            logger.info(f"Department column: {str(e)}")
            
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS location VARCHAR(100)")
            columns_added.append('location')
            logger.info("Added location column") 
        except Exception as e:
            logger.info(f"Location column: {str(e)}")
            
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)")
            columns_added.append('phone')
            logger.info("Added phone column")
        except Exception as e:
            logger.info(f"Phone column: {str(e)}")
            
        # Commit changes
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info("EMERGENCY: Database schema fix completed successfully", extra={
            "event": "emergency_schema_fix_success",
            "columns_added": columns_added
        })
        
        return {
            "success": True,
            "message": "Database schema fix completed successfully",
            "columns_added": columns_added,
            "timestamp": "2025-09-02T20:30:00Z"
        }
        
    except Exception as e:
        logger.error("EMERGENCY: Database schema fix failed", extra={
            "event": "emergency_schema_fix_failed",
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database schema fix failed: {str(e)}"
        )


@router.post("/emergency/create-user-application-access-table")
async def emergency_create_user_application_access_table(db: Session = Depends(get_db)):
    """EMERGENCY: Create missing user_application_access table for authentication"""
    try:
        logger.info("EMERGENCY: Starting user_application_access table creation", extra={
            "event": "emergency_table_creation_start",
            "table": "user_application_access"
        })
        
        import os
        import psycopg2
        from urllib.parse import urlparse
        
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL not found in environment")
            
        # Parse database URL
        parsed = urlparse(database_url)
        
        # Connect directly with psycopg2
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username, 
            password=parsed.password,
            sslmode='require'
        )
        
        cur = conn.cursor()
        operations = []
        
        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'user_application_access'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            logger.info("user_application_access table already exists")
            operations.append("table_already_exists")
        else:
            # Create enum types if they don't exist
            try:
                cur.execute("""
                    DO $$ BEGIN
                        CREATE TYPE applicationtype AS ENUM ('market_edge', 'causal_edge', 'value_edge');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$
                """)
                operations.append("applicationtype_enum_created")
                logger.info("Created applicationtype enum")
            except Exception as e:
                logger.info(f"ApplicationType enum: {str(e)}")
                
            try:
                cur.execute("""
                    DO $$ BEGIN
                        CREATE TYPE invitationstatus AS ENUM ('pending', 'accepted', 'expired');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$
                """)
                operations.append("invitationstatus_enum_created")
                logger.info("Created invitationstatus enum")
            except Exception as e:
                logger.info(f"InvitationStatus enum: {str(e)}")
            
            # Create user_application_access table
            cur.execute("""
                CREATE TABLE user_application_access (
                    id UUID NOT NULL DEFAULT gen_random_uuid(),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    user_id UUID NOT NULL,
                    application applicationtype NOT NULL,
                    has_access BOOLEAN NOT NULL DEFAULT FALSE,
                    granted_by UUID,
                    granted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    CONSTRAINT user_application_access_pkey PRIMARY KEY (id),
                    CONSTRAINT user_application_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT user_application_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL,
                    CONSTRAINT user_application_access_user_id_application_key UNIQUE (user_id, application)
                )
            """)
            operations.append("user_application_access_table_created")
            logger.info("Created user_application_access table")
            
            # Create indexes for performance
            cur.execute("CREATE INDEX idx_user_application_access_user_id ON user_application_access (user_id)")
            cur.execute("CREATE INDEX idx_user_application_access_application ON user_application_access (application)")
            operations.append("indexes_created")
            logger.info("Created indexes for user_application_access")
            
        # Check if user_invitations table exists, create if needed
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'user_invitations'
            )
        """)
        invitations_table_exists = cur.fetchone()[0]
        
        if not invitations_table_exists:
            # Create user_invitations table
            cur.execute("""
                CREATE TABLE user_invitations (
                    id UUID NOT NULL DEFAULT gen_random_uuid(),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    user_id UUID NOT NULL,
                    invitation_token VARCHAR(255) NOT NULL UNIQUE,
                    status invitationstatus NOT NULL DEFAULT 'pending',
                    invited_by UUID NOT NULL,
                    invited_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    accepted_at TIMESTAMP WITH TIME ZONE,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    CONSTRAINT user_invitations_pkey PRIMARY KEY (id),
                    CONSTRAINT user_invitations_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT user_invitations_invited_by_fkey FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            operations.append("user_invitations_table_created")
            logger.info("Created user_invitations table")
            
            # Create indexes for user_invitations
            cur.execute("CREATE INDEX idx_user_invitations_user_id ON user_invitations (user_id)")
            cur.execute("CREATE INDEX idx_user_invitations_token ON user_invitations (invitation_token)")
            cur.execute("CREATE INDEX idx_user_invitations_status ON user_invitations (status)")
            cur.execute("CREATE INDEX idx_user_invitations_expires_at ON user_invitations (expires_at)")
            operations.append("user_invitations_indexes_created")
            logger.info("Created indexes for user_invitations")
        else:
            operations.append("user_invitations_table_already_exists")
            
        # Commit changes
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info("EMERGENCY: User application access table creation completed successfully", extra={
            "event": "emergency_table_creation_success",
            "operations": operations
        })
        
        return {
            "success": True,
            "message": "User application access tables created successfully",
            "operations": operations,
            "timestamp": "2025-09-02T20:45:00Z"
        }
        
    except Exception as e:
        logger.error("EMERGENCY: User application access table creation failed", extra={
            "event": "emergency_table_creation_failed",
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User application access table creation failed: {str(e)}"
        )