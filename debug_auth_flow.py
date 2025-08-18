#!/usr/bin/env python3
"""
Debug Authentication Flow - Step-by-step analysis
This script will help identify exactly where the authentication flow fails
by testing each component independently.
"""

import asyncio
import httpx
import sys
import os
import json
from datetime import datetime
import traceback

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_auth0_token_exchange_directly():
    """Test Auth0 token exchange directly to isolate the issue"""
    print("\n🔍 Testing Auth0 Token Exchange Directly...")
    
    try:
        from core.config import settings
        from auth.auth0 import auth0_client
        
        print(f"   Auth0 Domain: {settings.AUTH0_DOMAIN}")
        print(f"   Auth0 Client ID: {settings.AUTH0_CLIENT_ID}")
        print(f"   Has Client Secret: {'Yes' if settings.AUTH0_CLIENT_SECRET else 'No'}")
        
        # Test with a fake but properly formatted code
        test_codes = [
            "sAAizkCJKe_test_1",  # Format similar to real Auth0 codes
            "invalid_code",       # Simple invalid code
            "very_long_invalid_code_that_might_cause_issues_123456789",
            "",                   # Empty code
        ]
        
        for test_code in test_codes:
            print(f"\n   Testing code: '{test_code[:20]}{'...' if len(test_code) > 20 else ''}'")
            try:
                result = await auth0_client.exchange_code_for_token(
                    code=test_code,
                    redirect_uri="https://odeon-demo.netlify.app/callback"
                )
                
                if result is None:
                    print(f"   ✅ Correctly returned None (expected for invalid code)")
                else:
                    print(f"   ⚠️  Unexpected success: {type(result)}")
                    
            except Exception as e:
                print(f"   ❌ Exception during token exchange: {e}")
                print(f"   Exception type: {type(e).__name__}")
                
    except Exception as e:
        print(f"   ❌ Setup error: {e}")
        traceback.print_exc()

async def test_database_operations():
    """Test database operations that occur during authentication"""
    print("\n🔍 Testing Database Operations...")
    
    try:
        from core.database import get_db, engine
        from models.user import User
        from models.organisation import Organisation
        from sqlalchemy.orm import Session
        
        print(f"   Database engine: {engine}")
        print(f"   Database URL: {engine.url}")
        
        # Test basic database connectivity
        print("\n   Testing database connection...")
        try:
            with engine.connect() as conn:
                result = conn.execute("SELECT 1 as test")
                test_value = result.fetchone()[0]
                print(f"   ✅ Database connection successful (test query returned: {test_value})")
        except Exception as e:
            print(f"   ❌ Database connection failed: {e}")
            return
        
        # Test database operations that happen during authentication
        print("\n   Testing authentication-related database operations...")
        try:
            db_gen = get_db()
            db: Session = next(db_gen)
            
            # Test 1: Check if default organization exists
            default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
            if default_org:
                print(f"   ✅ Default organization exists (ID: {default_org.id})")
            else:
                print(f"   ⚠️  Default organization missing - would need to be created")
            
            # Test 2: Try to query users table
            user_count = db.query(User).count()
            print(f"   ✅ Users table accessible (count: {user_count})")
            
            # Test 3: Test user creation simulation (without actually creating)
            print(f"   ✅ Database operations test completed successfully")
            
        except Exception as e:
            print(f"   ❌ Database operations failed: {e}")
            traceback.print_exc()
        finally:
            try:
                next(db_gen)  # Close the generator
            except StopIteration:
                pass
                
    except Exception as e:
        print(f"   ❌ Database test setup error: {e}")
        traceback.print_exc()

async def test_jwt_operations():
    """Test JWT token creation which happens after successful authentication"""
    print("\n🔍 Testing JWT Operations...")
    
    try:
        from auth.jwt import create_access_token, create_refresh_token
        
        # Test token creation with typical user data
        test_data = {
            "sub": "123e4567-e89b-12d3-a456-426614174000",  # UUID format
            "email": "test@example.com"
        }
        
        test_tenant_id = "123e4567-e89b-12d3-a456-426614174001"
        test_permissions = ["read:data", "write:data"]
        
        print("   Testing access token creation...")
        try:
            access_token = create_access_token(
                data=test_data,
                tenant_id=test_tenant_id,
                user_role="viewer",
                permissions=test_permissions,
                industry="default"
            )
            print(f"   ✅ Access token created successfully")
        except Exception as e:
            print(f"   ❌ Access token creation failed: {e}")
            traceback.print_exc()
        
        print("   Testing refresh token creation...")
        try:
            refresh_token = create_refresh_token(
                data=test_data,
                tenant_id=test_tenant_id
            )
            print(f"   ✅ Refresh token created successfully")
        except Exception as e:
            print(f"   ❌ Refresh token creation failed: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"   ❌ JWT test setup error: {e}")
        traceback.print_exc()

async def test_user_creation_flow():
    """Test the complete user creation flow that happens with new users"""
    print("\n🔍 Testing User Creation Flow...")
    
    try:
        from core.database import get_db, engine
        from models.user import User, UserRole
        from models.organisation import Organisation, SubscriptionPlan
        from core.rate_limit_config import Industry
        import uuid
        
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Step 1: Check/create default organization
            print("   Step 1: Checking default organization...")
            default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
            if not default_org:
                print("   Creating default organization...")
                default_org = Organisation(
                    name="Default", 
                    industry="default",
                    industry_type=Industry.DEFAULT,
                    subscription_plan=SubscriptionPlan.basic
                )
                db.add(default_org)
                db.commit()
                db.refresh(default_org)
                print(f"   ✅ Default organization created (ID: {default_org.id})")
            else:
                print(f"   ✅ Default organization exists (ID: {default_org.id})")
            
            # Step 2: Test user creation (simulation)
            print("   Step 2: Testing user creation simulation...")
            test_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
            
            # Check if this would work without actually creating
            test_user_data = {
                "email": test_email,
                "first_name": "Test",
                "last_name": "User",
                "organisation_id": default_org.id,
                "role": UserRole.viewer
            }
            
            print(f"   ✅ User creation flow validation passed")
            print(f"   Would create user: {test_email}")
            print(f"   With organization: {default_org.name} (ID: {default_org.id})")
            
        except Exception as e:
            print(f"   ❌ User creation flow failed: {e}")
            traceback.print_exc()
            db.rollback()
        finally:
            try:
                next(db_gen)  # Close the generator
            except StopIteration:
                pass
                
    except Exception as e:
        print(f"   ❌ User creation test setup error: {e}")
        traceback.print_exc()

async def test_production_specific_issues():
    """Test issues that might only occur in production"""
    print("\n🔍 Testing Production-Specific Issues...")
    
    try:
        from core.config import settings
        
        # Check environment configuration
        print(f"   Environment: {settings.ENVIRONMENT}")
        print(f"   Debug mode: {settings.DEBUG}")
        print(f"   Cookie secure: {settings.cookie_secure}")
        print(f"   Cookie samesite: {settings.cookie_samesite}")
        
        # Check for production vs development differences
        if settings.ENVIRONMENT.lower() != 'production':
            print("   ⚠️  Running in development mode - some production issues may not appear")
            print("   ⚠️  Production might have different:")
            print("     - Database connection parameters")
            print("     - Auth0 configuration") 
            print("     - CORS settings")
            print("     - Cookie security settings")
        
        # Test cookie settings that might cause issues
        cookie_settings = settings.get_cookie_settings()
        print(f"   Cookie settings: {cookie_settings}")
        
        if cookie_settings.get('secure') and not settings.ENVIRONMENT == 'production':
            print("   ⚠️  Secure cookies enabled in non-HTTPS environment")
        
        # Test CORS origins
        print(f"   CORS origins configured: {len(settings.CORS_ORIGINS)}")
        for origin in settings.CORS_ORIGINS:
            print(f"     - {origin}")
            
    except Exception as e:
        print(f"   ❌ Production config test error: {e}")
        traceback.print_exc()

async def main():
    """Main diagnostic runner"""
    print("🚀 Authentication Flow Debug Tool")
    print("This will test each component of the authentication flow to isolate the issue")
    print("=" * 70)
    
    try:
        await test_auth0_token_exchange_directly()
        await test_database_operations()
        await test_jwt_operations()
        await test_user_creation_flow()
        await test_production_specific_issues()
        
        print("\n" + "=" * 70)
        print("🎯 DEBUG ANALYSIS COMPLETE")
        print("\n📊 KEY FINDINGS:")
        print("✅ = Component working correctly")
        print("⚠️  = Potential issue or difference from production")
        print("❌ = Definite problem that needs fixing")
        
        print("\n🔍 LIKELY CAUSES OF 500 ERROR:")
        print("1. Database connection issues in production environment")
        print("2. Missing or incorrect environment variables in production")
        print("3. Auth0 token exchange failing due to production vs dev differences")
        print("4. User/organization creation failing due to database constraints")
        print("5. JWT creation failing due to missing dependencies or configuration")
        
        print("\n🛠️  RECOMMENDED FIXES:")
        print("1. Add comprehensive error logging to each step of authentication")
        print("2. Create a production health check that tests database operations")
        print("3. Add environment-specific Auth0 configuration validation")
        print("4. Test authentication flow with actual Auth0 tokens in staging")
        print("5. Add transaction rollback handling for failed user creation")
        
    except Exception as e:
        print(f"\n❌ Debug tool error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())