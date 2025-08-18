from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Form
from sqlalchemy.orm import Session
from typing import Optional
import traceback
from ....core.database import get_db
from ....auth.auth0 import auth0_client
from ....core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/debug-auth-flow")
async def debug_auth_flow(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None)
):
    """Debug version of auth flow with detailed error capturing"""
    
    debug_info = {
        "step": "initialization",
        "timestamp": "2025-08-18T19:14:19",
        "code_length": len(code) if code else 0,
        "redirect_uri": redirect_uri
    }
    
    try:
        # Step 1: Validate inputs
        debug_info["step"] = "input_validation"
        if not code or not redirect_uri:
            debug_info["error"] = "Missing code or redirect_uri"
            return {"debug": debug_info, "status": "failed", "step": "input_validation"}
        
        # Step 2: Auth0 token exchange
        debug_info["step"] = "auth0_token_exchange"
        debug_info["auth0_domain"] = "dev-g8trhgbfdq2sk2m8.us.auth0.com"
        
        token_data = await auth0_client.exchange_code_for_token(code, redirect_uri)
        
        if not token_data:
            debug_info["error"] = "Auth0 token exchange failed"
            return {"debug": debug_info, "status": "failed", "step": "auth0_token_exchange"}
        
        debug_info["token_exchange_success"] = True
        debug_info["has_access_token"] = "access_token" in token_data
        
        # Step 3: Get user info from Auth0
        debug_info["step"] = "auth0_user_info"
        
        user_info = await auth0_client.get_user_info(token_data["access_token"])
        
        if not user_info:
            debug_info["error"] = "Failed to get user info from Auth0"
            return {"debug": debug_info, "status": "failed", "step": "auth0_user_info"}
        
        debug_info["user_info_success"] = True
        debug_info["user_email"] = user_info.get("email", "unknown")
        debug_info["user_sub"] = user_info.get("sub", "unknown")
        
        # Step 4: Database user lookup/creation
        debug_info["step"] = "database_operations"
        
        from ....models.user import User
        from ....models.organisation import Organisation
        
        user = db.query(User).filter(User.email == user_info["email"]).first()
        debug_info["existing_user"] = bool(user)
        
        if not user:
            # Check for default organization
            debug_info["step"] = "default_org_lookup"
            default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
            debug_info["default_org_exists"] = bool(default_org)
            
            if not default_org:
                debug_info["step"] = "default_org_creation"
                from ....models.organisation import SubscriptionPlan
                from ....core.rate_limit_config import Industry
                
                default_org = Organisation(
                    name="Default",
                    industry="default", 
                    industry_type=Industry.DEFAULT,
                    subscription_plan=SubscriptionPlan.basic
                )
                db.add(default_org)
                db.commit()
                db.refresh(default_org)
                debug_info["default_org_created"] = True
            
            # Create user
            debug_info["step"] = "user_creation"
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
            debug_info["user_created"] = True
        
        # Step 5: JWT token creation
        debug_info["step"] = "jwt_creation"
        
        from ....auth.jwt import create_access_token, create_refresh_token, get_user_permissions
        
        tenant_context = {
            "industry": user.organisation.industry if user.organisation else "default"
        }
        permissions = get_user_permissions(user.role.value, tenant_context)
        
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
        
        debug_info["jwt_created"] = True
        debug_info["permissions_count"] = len(permissions)
        
        return {
            "debug": debug_info,
            "status": "success",
            "step": "completed",
            "user_id": str(user.id),
            "message": "Authentication flow completed successfully"
        }
        
    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
            "step_failed": debug_info.get("step", "unknown")
        }
        
        logger.error("Debug auth flow failed", extra={
            "debug_info": debug_info,
            "error_details": error_details
        })
        
        return {
            "debug": debug_info,
            "error": error_details,
            "status": "crashed",
            "step": debug_info.get("step", "unknown")
        }