#!/usr/bin/env python3
"""
CRITICAL: Debug the exact authentication issue causing 403 errors
The issue is that the API returns "Not authenticated" but Auth0 is working
"""

import asyncio
import httpx
import logging
import sys
import os
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "app"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthDebugger:
    def __init__(self):
        self.db_engine = create_engine(settings.DATABASE_URL)
        self.Session = sessionmaker(bind=self.db_engine)
        self.base_url = "https://marketedge-platform.onrender.com"
        
    def check_actual_database_structure(self):
        """Check the real database structure"""
        logger.info("=== Checking Actual Database Structure ===")
        
        with self.Session() as session:
            # Check tools table
            tools = session.execute(text("""
                SELECT id, name, is_active FROM tools LIMIT 5
            """)).fetchall()
            
            logger.info(f"Tools in database: {len(tools)}")
            for tool in tools:
                logger.info(f"  Tool: {tool.name} (ID: {tool.id}, Active: {tool.is_active})")
            
            # Check organisation_tool_access table
            try:
                access = session.execute(text("""
                    SELECT ota.organisation_id, ota.tool_id, ota.subscription_tier, t.name as tool_name
                    FROM organisation_tool_access ota
                    JOIN tools t ON ota.tool_id = t.id
                    LIMIT 10
                """)).fetchall()
                
                logger.info(f"Organisation tool access records: {len(access)}")
                for acc in access:
                    logger.info(f"  Org: {acc.organisation_id} -> Tool: {acc.tool_name} -> Tier: {acc.subscription_tier}")
                    
            except Exception as e:
                logger.error(f"Error checking tool access: {str(e)}")

    async def test_with_auth0_style_token(self):
        """Create a token similar to what Auth0 would provide"""
        logger.info("=== Testing with Auth0-style Token ===")
        
        # Get user from database
        with self.Session() as session:
            user = session.execute(text("""
                SELECT id, email, role, organisation_id 
                FROM users 
                WHERE is_active = true 
                LIMIT 1
            """)).fetchone()
            
            if not user:
                logger.error("No active users found")
                return
                
            logger.info(f"Testing with user: {user.email}")
            logger.info(f"  User ID: {user.id}")
            logger.info(f"  Role: {user.role}")
            logger.info(f"  Org ID: {user.organisation_id}")
            
            # Import JWT functions
            from app.auth.jwt import create_access_token, get_user_permissions
            
            # Create token similar to Auth0
            token_data = {
                "sub": str(user.id),  # Auth0 uses 'sub' for user ID
                "email": user.email,
                "iat": 1755553814,  # Issued at time
                "exp": 1755557414,  # Expires in 1 hour
            }
            
            # Get user permissions based on role
            permissions = get_user_permissions(user.role)
            logger.info(f"User permissions: {permissions}")
            
            try:
                # Create access token
                token = create_access_token(
                    data=token_data,
                    tenant_id=str(user.organisation_id),
                    user_role=user.role,
                    permissions=permissions,
                    industry="default"
                )
                
                logger.info(f"Created JWT token: {token[:100]}...")
                
                # Test the token verification
                from app.auth.jwt import verify_token
                verified = verify_token(token, expected_type="access")
                if verified:
                    logger.info("✅ Token verification: SUCCESS")
                    logger.info(f"Verified payload keys: {list(verified.keys())}")
                else:
                    logger.error("❌ Token verification: FAILED")
                    return
                
                # Test API endpoints with the token
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Origin": "https://app.zebra.associates"
                }
                
                endpoints_to_test = [
                    "/api/v1/organisations/current",
                    "/api/v1/organisations/industries", 
                    "/api/v1/organisations/accessible",
                    "/api/v1/tools/"
                ]
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    for endpoint in endpoints_to_test:
                        try:
                            url = f"{self.base_url}{endpoint}"
                            logger.info(f"\nTesting: {endpoint}")
                            
                            response = await client.get(url, headers=headers)
                            logger.info(f"Status: {response.status_code}")
                            
                            if response.status_code == 200:
                                logger.info("✅ SUCCESS!")
                                # Only show first 200 chars of response
                                logger.info(f"Response: {response.text[:200]}...")
                            else:
                                logger.error(f"❌ FAILED: {response.text}")
                                
                        except Exception as e:
                            logger.error(f"❌ REQUEST ERROR: {str(e)}")
                            
            except Exception as e:
                logger.error(f"Failed to create or test token: {str(e)}")

    def check_auth_dependency_chain(self):
        """Analyze the authentication dependency chain"""
        logger.info("=== Checking Authentication Dependency Chain ===")
        
        # Show what endpoints require authentication
        endpoints_auth = {
            "/api/v1/organisations/current": "get_current_user",
            "/api/v1/organisations/industries": "get_current_user", 
            "/api/v1/organisations/accessible": "get_current_user",
            "/api/v1/tools/": "get_current_user"
        }
        
        logger.info("Endpoint authentication requirements:")
        for endpoint, auth_req in endpoints_auth.items():
            logger.info(f"  {endpoint} -> {auth_req}")
        
        # Show the authentication flow
        logger.info("\nAuthentication flow:")
        logger.info("1. Frontend sends request with Authorization: Bearer <token>")
        logger.info("2. FastAPI HTTPBearer security extracts token")
        logger.info("3. get_current_user() calls verify_token()")
        logger.info("4. verify_token() validates JWT signature and claims")
        logger.info("5. User is loaded from database using token 'sub' claim")
        logger.info("6. User organization and role are validated")
        
        # Check if middleware might be interfering
        logger.info("\nCurrent middleware configuration:")
        logger.info("- CORS: FastAPI CORSMiddleware (emergency mode)")
        logger.info("- TrustedHostMiddleware: allowed_hosts=['*']")
        logger.info("- ErrorHandlerMiddleware: custom error handling")
        logger.info("- LoggingMiddleware: request logging")
        logger.info("- TenantContextMiddleware: DISABLED (commented out)")
        logger.info("- RateLimitMiddleware: DISABLED (commented out)")

    async def test_cors_and_options(self):
        """Test CORS and OPTIONS requests"""
        logger.info("=== Testing CORS and OPTIONS ===")
        
        test_origin = "https://app.zebra.associates"
        headers = {
            "Origin": test_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test OPTIONS preflight
            try:
                response = await client.options(
                    f"{self.base_url}/api/v1/organisations/current",
                    headers=headers
                )
                logger.info(f"OPTIONS preflight: {response.status_code}")
                logger.info(f"CORS headers: {dict(response.headers)}")
                
                if "access-control-allow-origin" in response.headers:
                    logger.info("✅ CORS preflight working")
                else:
                    logger.error("❌ CORS preflight failed")
                    
            except Exception as e:
                logger.error(f"OPTIONS request failed: {str(e)}")

    async def run_diagnosis(self):
        """Run focused authentication diagnosis"""
        logger.info("🔍 CRITICAL AUTH DIAGNOSIS: Why 'Not authenticated'?")
        logger.info("=" * 60)
        
        try:
            with self.Session() as session:
                session.execute(text("SELECT 1")).fetchone()
                logger.info("✅ Database connectivity OK")
        except Exception as e:
            logger.error(f"❌ Database failed: {str(e)}")
            return
        
        self.check_actual_database_structure()
        logger.info("\n" + "=" * 60)
        
        self.check_auth_dependency_chain()
        logger.info("\n" + "=" * 60)
        
        await self.test_cors_and_options()
        logger.info("\n" + "=" * 60)
        
        await self.test_with_auth0_style_token()
        logger.info("\n" + "=" * 60)
        
        logger.info("🏁 Focused diagnosis complete!")

async def main():
    debugger = AuthDebugger()
    await debugger.run_diagnosis()

if __name__ == "__main__":
    asyncio.run(main())