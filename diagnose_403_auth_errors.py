#!/usr/bin/env python3
"""
DEVOPS EMERGENCY: 403 Authentication Error Diagnostic Script
Analyzes the persistent 403 Forbidden errors despite successful Auth0 authentication.
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
from app.models.user import User, UserRole
from app.models.organisation import Organisation
from app.auth.jwt import verify_token, extract_tenant_context_from_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Auth403Diagnostics:
    def __init__(self):
        # Use production database URL from settings
        self.db_engine = create_engine(settings.DATABASE_URL)
        self.Session = sessionmaker(bind=self.db_engine)
        self.base_url = "https://marketedge-platform.onrender.com"
        
    async def test_api_endpoints_without_auth(self):
        """Test if endpoints are reachable without authentication"""
        logger.info("=== Testing API Endpoints Without Authentication ===")
        
        endpoints = [
            "/health",
            "/cors-debug", 
            "/api/v1/organisations/current",
            "/api/v1/organisations/industries",
            "/api/v1/organisations/accessible",
            "/api/v1/tools/"
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = await client.get(url)
                    logger.info(f"GET {endpoint}: {response.status_code} - {response.text[:200]}")
                except Exception as e:
                    logger.error(f"GET {endpoint}: ERROR - {str(e)}")
    
    def check_database_user_organization_linking(self):
        """Check if users are properly linked to organizations"""
        logger.info("=== Checking Database User-Organization Linking ===")
        
        with self.Session() as session:
            # Get all users and their organization status
            result = session.execute(text("""
                SELECT 
                    u.id,
                    u.email,
                    u.role,
                    u.is_active,
                    u.organisation_id,
                    o.name as org_name,
                    o.industry_type,
                    o.is_active as org_active
                FROM users u
                LEFT JOIN organisations o ON u.organisation_id = o.id
                ORDER BY u.created_at DESC
                LIMIT 10
            """))
            
            users = result.fetchall()
            logger.info(f"Found {len(users)} recent users:")
            
            for user in users:
                logger.info(f"User: {user.email}")
                logger.info(f"  ID: {user.id}")
                logger.info(f"  Role: {user.role}")
                logger.info(f"  Active: {user.is_active}")
                logger.info(f"  Org ID: {user.organisation_id}")
                logger.info(f"  Org Name: {user.org_name}")
                logger.info(f"  Org Industry: {user.industry_type}")
                logger.info(f"  Org Active: {user.org_active}")
                logger.info("  ---")
                
            # Check for users without organizations
            orphaned_users = session.execute(text("""
                SELECT COUNT(*) as count FROM users WHERE organisation_id IS NULL
            """)).fetchone()
            
            logger.info(f"Users without organization: {orphaned_users.count}")
            
            # Check organizations
            orgs = session.execute(text("""
                SELECT id, name, industry_type, is_active 
                FROM organisations 
                ORDER BY created_at DESC
            """)).fetchall()
            
            logger.info(f"Available organizations: {len(orgs)}")
            for org in orgs:
                logger.info(f"  Org: {org.name} (ID: {org.id}, Industry: {org.industry_type}, Active: {org.is_active})")
    
    def check_tool_access_configuration(self):
        """Check if tool access is properly configured"""
        logger.info("=== Checking Tool Access Configuration ===")
        
        with self.Session() as session:
            # Check application tools
            tools = session.execute(text("""
                SELECT id, name, is_active FROM application_tools
            """)).fetchall()
            
            logger.info(f"Available tools: {len(tools)}")
            for tool in tools:
                logger.info(f"  Tool: {tool.name} (ID: {tool.id}, Active: {tool.is_active})")
            
            # Check user application access
            access = session.execute(text("""
                SELECT 
                    uaa.user_id,
                    uaa.application_tool_id,
                    uaa.has_access,
                    u.email,
                    at.name as tool_name
                FROM user_application_access uaa
                JOIN users u ON uaa.user_id = u.id
                JOIN application_tools at ON uaa.application_tool_id = at.id
                ORDER BY uaa.created_at DESC
                LIMIT 20
            """)).fetchall()
            
            logger.info(f"User tool access records: {len(access)}")
            for acc in access:
                logger.info(f"  User: {acc.email} -> Tool: {acc.tool_name} -> Access: {acc.has_access}")

    async def test_with_manual_jwt_token(self):
        """Test API endpoints with a manually created JWT token"""
        logger.info("=== Testing with Manual JWT Token ===")
        
        # We would need to get a user ID from database and create a token
        with self.Session() as session:
            user = session.execute(text("""
                SELECT id, email, role, organisation_id 
                FROM users 
                WHERE is_active = true 
                ORDER BY created_at DESC 
                LIMIT 1
            """)).fetchone()
            
            if not user:
                logger.error("No active users found in database")
                return
                
            logger.info(f"Testing with user: {user.email} (ID: {user.id})")
            
            # Import JWT creation function
            from app.auth.jwt import create_access_token
            
            # Create a test token
            token_data = {
                "sub": str(user.id),
                "email": user.email
            }
            
            try:
                token = create_access_token(
                    data=token_data,
                    tenant_id=str(user.organisation_id) if user.organisation_id else None,
                    user_role=user.role,
                    permissions=["read:organisations", "read:tools"]
                )
                
                logger.info(f"Created JWT token: {token[:50]}...")
                
                # Test API calls with this token
                headers = {"Authorization": f"Bearer {token}"}
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    endpoints = [
                        "/api/v1/organisations/current",
                        "/api/v1/organisations/industries", 
                        "/api/v1/organisations/accessible",
                        "/api/v1/tools/"
                    ]
                    
                    for endpoint in endpoints:
                        try:
                            url = f"{self.base_url}{endpoint}"
                            response = await client.get(url, headers=headers)
                            logger.info(f"WITH TOKEN - GET {endpoint}: {response.status_code}")
                            if response.status_code != 200:
                                logger.error(f"  Response: {response.text[:500]}")
                        except Exception as e:
                            logger.error(f"WITH TOKEN - GET {endpoint}: ERROR - {str(e)}")
                            
            except Exception as e:
                logger.error(f"Failed to create token: {str(e)}")

    def check_jwt_configuration(self):
        """Check JWT configuration and settings"""
        logger.info("=== Checking JWT Configuration ===")
        
        logger.info(f"JWT Secret Key configured: {'Yes' if settings.JWT_SECRET_KEY else 'No'}")
        logger.info(f"JWT Algorithm: {settings.JWT_ALGORITHM}")
        logger.info(f"Access Token Expire Minutes: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
        
        # Test token verification
        from app.auth.jwt import create_access_token, verify_token
        
        test_data = {"sub": "test-user", "email": "test@example.com"}
        test_token = create_access_token(test_data)
        
        logger.info(f"Test token created: {test_token[:50]}...")
        
        verified = verify_token(test_token)
        if verified:
            logger.info("Test token verification: SUCCESS")
            logger.info(f"Verified payload: {verified}")
        else:
            logger.error("Test token verification: FAILED")

    async def run_full_diagnosis(self):
        """Run complete diagnostic suite"""
        logger.info("🚨 DEVOPS EMERGENCY: 403 Authentication Error Diagnosis")
        logger.info("=" * 60)
        
        try:
            # Test database connectivity first
            with self.Session() as session:
                result = session.execute(text("SELECT 1")).fetchone()
                logger.info("Database connectivity: ✅ SUCCESS")
        except Exception as e:
            logger.error(f"Database connectivity: ❌ FAILED - {str(e)}")
            return
        
        # Run diagnostic tests
        await self.test_api_endpoints_without_auth()
        logger.info("\n" + "=" * 60)
        
        self.check_database_user_organization_linking()
        logger.info("\n" + "=" * 60)
        
        self.check_tool_access_configuration()
        logger.info("\n" + "=" * 60)
        
        self.check_jwt_configuration()
        logger.info("\n" + "=" * 60)
        
        await self.test_with_manual_jwt_token()
        logger.info("\n" + "=" * 60)
        
        logger.info("🏁 Diagnosis complete!")


async def main():
    diagnostics = Auth403Diagnostics()
    await diagnostics.run_full_diagnosis()


if __name__ == "__main__":
    asyncio.run(main())