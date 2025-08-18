#!/usr/bin/env python3
"""
Enhanced Auth Logging Patch
===========================

This script applies enhanced logging to the authentication endpoint to capture
detailed information about real Auth0 token failures in production.

STRATEGY:
1. Add detailed logging for Auth0 user info structure
2. Add database operation logging with error details
3. Capture SQLAlchemy error specifics
4. Log sanitization process details
"""

import os
import sys


def apply_enhanced_logging():
    """Apply enhanced logging patches to authentication endpoint"""
    
    auth_file_path = "backend/app/api/api_v1/endpoints/auth.py"
    error_handler_path = "backend/app/middleware/error_handler.py"
    
    print("🔧 APPLYING ENHANCED AUTH LOGGING PATCHES")
    print("=" * 50)
    
    # Read current auth endpoint
    if not os.path.exists(auth_file_path):
        print(f"❌ Auth file not found: {auth_file_path}")
        return False
    
    with open(auth_file_path, 'r') as f:
        auth_content = f.read()
    
    # Check if patches already applied
    if "auth0_userinfo_debug" in auth_content:
        print("✅ Enhanced logging already applied")
        return True
    
    print("📝 Applying Auth0 user info logging patch...")
    
    # Patch 1: Add detailed Auth0 user info logging
    user_info_patch = '''    # Get user info from Auth0
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
    
    # ENHANCED LOGGING: Capture Auth0 user info structure for debugging
    logger.info("Auth0 user info received - DEBUGGING", extra={
        "event": "auth0_userinfo_debug",
        "user_info_keys": list(user_info.keys()),
        "user_sub": user_info.get("sub"),
        "user_email": user_info.get("email"),
        "has_given_name": bool(user_info.get("given_name")),
        "has_family_name": bool(user_info.get("family_name")),
        "given_name_value": user_info.get("given_name", ""),
        "family_name_value": user_info.get("family_name", ""),
        "email_verified": user_info.get("email_verified"),
        "all_user_info": user_info  # Full structure for debugging
    })'''
    
    # Find and replace user info section
    original_user_info = '''    # Get user info from Auth0
    user_info = await auth0_client.get_user_info(token_data["access_token"])
    if not user_info:
        logger.error("Failed to get user info", extra={
            "event": "userinfo_failure",
            "has_access_token": bool(token_data.get("access_token"))
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information from Auth0"
        )'''
    
    if original_user_info in auth_content:
        auth_content = auth_content.replace(original_user_info, user_info_patch)
        print("   ✅ Auth0 user info logging patch applied")
    else:
        print("   ⚠️ Could not find user info section to patch")
    
    print("📝 Applying database operations logging patch...")
    
    # Patch 2: Add detailed database operations logging
    db_ops_patch = '''    # ENHANCED LOGGING: Database operation debugging
    logger.info("Starting database user lookup/creation", extra={
        "event": "db_operations_start",
        "sanitized_email": sanitized_email,
        "sanitized_given_name": sanitized_given_name,
        "sanitized_family_name": sanitized_family_name
    })
    
    # Find or create user in database using sanitized email
    try:
        user = db.query(User).filter(User.email == sanitized_email).first()
        if not user:
            logger.info("User not found, creating new user", extra={
                "event": "db_user_create_start",
                "email": sanitized_email
            })
            
            # Create user with default organization
            default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
            if not default_org:
                logger.info("Creating default organization", extra={
                    "event": "db_org_create_start"
                })
                from ....models.organisation import SubscriptionPlan
                from ....core.rate_limit_config import Industry
                default_org = Organisation(
                    name="Default", 
                    industry="Technology",
                    industry_type=Industry.DEFAULT,
                    subscription_plan=SubscriptionPlan.basic
                )
                db.add(default_org)
                db.commit()
                db.refresh(default_org)
                logger.info("Default organization created", extra={
                    "event": "db_org_created",
                    "org_id": str(default_org.id)
                })
            
            from ....models.user import UserRole
            user = User(
                email=sanitized_email,
                first_name=sanitized_given_name,
                last_name=sanitized_family_name,
                organisation_id=default_org.id,
                role=UserRole.viewer
            )
            
            logger.info("Adding user to database", extra={
                "event": "db_user_add",
                "user_email": user.email,
                "user_first_name": user.first_name,
                "user_last_name": user.last_name,
                "org_id": str(user.organisation_id)
            })
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info("New user created", extra={
                "event": "user_created",
                "user_id": str(user.id),
                "email": user.email,
                "organisation_id": str(user.organisation_id)
            })
        else:
            logger.info("Existing user found", extra={
                "event": "db_user_found",
                "user_id": str(user.id),
                "email": user.email
            })
            
    except Exception as db_error:
        logger.error("CRITICAL: Database operation failed during user creation", extra={
            "event": "db_user_creation_critical_error",
            "error": str(db_error),
            "error_type": type(db_error).__name__,
            "sanitized_email": sanitized_email,
            "sanitized_given_name": sanitized_given_name,
            "sanitized_family_name": sanitized_family_name,
            "traceback": traceback.format_exc() if 'traceback' in globals() else "No traceback available"
        })
        raise  # Re-raise to let error handler catch it'''
    
    # Find and replace database operations section
    original_db_ops = '''    # Find or create user in database using sanitized email
    user = db.query(User).filter(User.email == sanitized_email).first()
    if not user:
        # Create user with default organization
        default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
        if not default_org:
            from ....models.organisation import SubscriptionPlan
            from ....core.rate_limit_config import Industry
            default_org = Organisation(
                name="Default", 
                industry="Technology",
                industry_type=Industry.DEFAULT,
                subscription_plan=SubscriptionPlan.basic
            )
            db.add(default_org)
            db.commit()
            db.refresh(default_org)
        
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
        })'''
    
    if original_db_ops in auth_content:
        auth_content = auth_content.replace(original_db_ops, db_ops_patch)
        print("   ✅ Database operations logging patch applied")
    else:
        print("   ⚠️ Could not find database operations section to patch")
    
    # Add traceback import if not present
    if "import traceback" not in auth_content:
        # Find imports section and add traceback
        import_section = "from ....core.validators import ("
        if import_section in auth_content:
            auth_content = auth_content.replace(
                import_section, 
                f"import traceback\nfrom ....core.validators import ("
            )
            print("   ✅ Traceback import added")
    
    # Write patched file
    try:
        with open(auth_file_path, 'w') as f:
            f.write(auth_content)
        print("✅ Enhanced logging patches applied successfully")
        
        print("\n📋 PATCHES APPLIED:")
        print("   1. Detailed Auth0 user info structure logging")
        print("   2. Step-by-step database operations logging") 
        print("   3. Critical error logging with full context")
        print("   4. Traceback capture for debugging")
        
        print("\n🎯 NEXT STEPS:")
        print("   1. Deploy these changes to production")
        print("   2. Test with real Auth0 token")
        print("   3. Check logs for detailed error information")
        print("   4. Use log output to identify exact failure point")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to write patched file: {str(e)}")
        return False


def main():
    """Main patch application function"""
    if apply_enhanced_logging():
        print("\n🚀 Ready to debug real Auth0 token failures!")
    else:
        print("\n❌ Failed to apply patches")


if __name__ == "__main__":
    main()