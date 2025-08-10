from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any
from ....core.database import get_db
from ....models.user import User
from ....models.organisation import Organisation
from ....auth.jwt import create_access_token, create_refresh_token, verify_token
from ....auth.auth0 import auth0_client
from ....auth.dependencies import get_current_user
from ....core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    code: str
    redirect_uri: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login with Auth0 authorization code"""
    try:
        logger.info("Authentication attempt initiated", extra={
            "event": "auth_attempt",
            "redirect_uri_domain": login_data.redirect_uri.split('/')[2] if '//' in login_data.redirect_uri else login_data.redirect_uri
        })
        
        token_data = await auth0_client.exchange_code_for_token(
            login_data.code, 
            login_data.redirect_uri
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
            "event": "token_exchange_success"
        })
    except Exception as e:
        logger.error("Authentication endpoint error", extra={
            "event": "auth_error",
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Login failed: {str(e)}"
        )
    
    user_info = await auth0_client.get_user_info(token_data["access_token"])
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information"
        )
    
    user = db.query(User).filter(User.email == user_info["email"]).first()
    if not user:
        default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
        if not default_org:
            from ....models.organisation import SubscriptionPlan
            default_org = Organisation(
                name="Default", 
                industry="Technology",
                subscription_plan=SubscriptionPlan.basic
            )
            db.add(default_org)
            db.commit()
            db.refresh(default_org)
        
        from ....models.user import UserRole
        user = User(
            email=user_info["email"],
            first_name=user_info.get("given_name", ""),
            last_name=user_info.get("family_name", ""),
            organisation_id=default_org.id,
            role=UserRole.viewer
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    logger.info("Authentication successful", extra={
        "event": "auth_success",
        "user_id": str(user.id),
        "organisation_id": str(user.organisation_id),
        "user_role": user.role.value
    })
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "organisation_id": str(user.organisation_id)
        }
    )


@router.post("/refresh", response_model=Dict[str, str])
async def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token"""
    payload = verify_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "organisation_id": str(current_user.organisation_id),
        "is_active": current_user.is_active
    }


@router.get("/auth0-url")
async def get_auth0_url(redirect_uri: str):
    """Get Auth0 authorization URL"""
    auth_url = auth0_client.get_authorization_url(redirect_uri)
    return {"auth_url": auth_url}