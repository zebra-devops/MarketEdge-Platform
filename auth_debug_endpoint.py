#!/usr/bin/env python3
"""
Quick debug endpoint to add enhanced logging to the auth endpoint
"""

# Enhanced auth endpoint with detailed logging for debugging
auth_debug_code = '''
@router.post("/auth-debug")
async def debug_auth_login(request: Request, response: Response, db: Session = Depends(get_db)):
    """Debug version of auth login with enhanced logging"""
    import json
    import traceback
    from sqlalchemy.exc import SQLAlchemyError
    
    try:
        # Log the incoming request
        body = await request.body()
        logger.info(f"🔍 AUTH DEBUG: Request received - Content-Type: {request.headers.get('content-type')}")
        logger.info(f"🔍 AUTH DEBUG: Request body: {body.decode('utf-8')[:200]}")
        
        # Parse request data
        content_type = request.headers.get("content-type", "")
        if content_type.startswith("application/x-www-form-urlencoded"):
            form = await request.form()
            code = form.get("code")
            redirect_uri = form.get("redirect_uri")
            state = form.get("state")
        else:
            json_data = json.loads(body.decode('utf-8'))
            code = json_data.get("code")
            redirect_uri = json_data.get("redirect_uri")
            state = json_data.get("state")
        
        logger.info(f"🔍 AUTH DEBUG: Parsed data - code: {code[:10] if code else None}..., redirect_uri: {redirect_uri}")
        
        # Step 1: Test Auth0 token exchange
        try:
            from ....core.auth0_client import auth0_client
            logger.info("🔍 AUTH DEBUG: Starting Auth0 token exchange...")
            
            token_data = await auth0_client.exchange_code_for_token(code, redirect_uri, state)
            logger.info(f"🔍 AUTH DEBUG: Token exchange SUCCESS - expires_in: {token_data.get('expires_in')}")
            
            # Step 2: Get user info
            user_info = await auth0_client.get_user_info(token_data["access_token"])
            logger.info(f"🔍 AUTH DEBUG: User info received: {json.dumps(user_info, indent=2)}")
            
        except Exception as auth_error:
            logger.error(f"🔍 AUTH DEBUG: Auth0 operation failed: {str(auth_error)}")
            return {"debug_status": "auth0_failed", "error": str(auth_error)}
        
        # Step 3: Database operations debug
        try:
            from ....models.user import User, UserRole
            from ....models.organisation import Organisation, SubscriptionPlan
            from ....core.rate_limit_config import Industry
            
            # Extract user data
            email = user_info.get("email", "").strip().lower()
            given_name = user_info.get("given_name", "").strip()
            family_name = user_info.get("family_name", "").strip()
            
            logger.info(f"🔍 AUTH DEBUG: Processing user - email: {email}, given_name: '{given_name}', family_name: '{family_name}'")
            
            # Check if user exists
            existing_user = db.query(User).filter(User.email == email).first()
            logger.info(f"🔍 AUTH DEBUG: Existing user found: {existing_user is not None}")
            
            if not existing_user:
                # Test organization creation
                logger.info("🔍 AUTH DEBUG: Creating default organization...")
                default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
                
                if not default_org:
                    logger.info("🔍 AUTH DEBUG: No default org found, creating new one...")
                    default_org = Organisation(
                        name="Default",
                        industry="Technology", 
                        industry_type=Industry.DEFAULT.value,
                        subscription_plan=SubscriptionPlan.basic.value
                    )
                    db.add(default_org)
                    db.commit()
                    logger.info(f"🔍 AUTH DEBUG: Default org created with ID: {default_org.id}")
                else:
                    logger.info(f"🔍 AUTH DEBUG: Using existing default org: {default_org.id}")
                
                # Test user creation
                logger.info("🔍 AUTH DEBUG: Creating new user...")
                user = User(
                    email=email,
                    first_name=given_name or "Unknown",
                    last_name=family_name or "User", 
                    organisation_id=default_org.id,
                    role=UserRole.viewer
                )
                db.add(user)
                db.commit()
                logger.info(f"🔍 AUTH DEBUG: User created successfully with ID: {user.id}")
            else:
                logger.info(f"🔍 AUTH DEBUG: Using existing user: {existing_user.id}")
            
            return {
                "debug_status": "success",
                "message": "Authentication debug completed successfully",
                "user_email": email,
                "auth0_user_info": user_info
            }
            
        except SQLAlchemyError as db_error:
            logger.error(f"🔍 AUTH DEBUG: DATABASE ERROR: {str(db_error)}")
            logger.error(f"🔍 AUTH DEBUG: Database error details: {traceback.format_exc()}")
            db.rollback()
            return {
                "debug_status": "database_error",
                "error": str(db_error),
                "error_type": type(db_error).__name__,
                "traceback": traceback.format_exc()
            }
            
        except Exception as general_error:
            logger.error(f"🔍 AUTH DEBUG: GENERAL ERROR: {str(general_error)}")
            logger.error(f"🔍 AUTH DEBUG: General error details: {traceback.format_exc()}")
            return {
                "debug_status": "general_error", 
                "error": str(general_error),
                "error_type": type(general_error).__name__,
                "traceback": traceback.format_exc()
            }
            
    except Exception as request_error:
        logger.error(f"🔍 AUTH DEBUG: REQUEST ERROR: {str(request_error)}")
        return {
            "debug_status": "request_error",
            "error": str(request_error),
            "traceback": traceback.format_exc()
        }
'''

print("Auth debug endpoint code generated.")
print("This endpoint will provide detailed logging for real Auth0 token processing.")
print("Add this to database.py to debug the exact failure point.")