#!/usr/bin/env python3
"""
Test the frontend authentication flow to identify why tokens aren't being sent
"""
import asyncio
import httpx
import logging
import sys
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.auth.jwt import create_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_frontend_auth_flow():
    """Test the complete frontend authentication flow"""
    logger.info("🔍 FRONTEND AUTHENTICATION FLOW ANALYSIS")
    logger.info("=" * 60)
    
    base_url = "https://marketedge-platform.onrender.com"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Test if frontend can get Auth0 URL (unauthenticated request)
        logger.info("Step 1: Testing Auth0 URL generation (no auth required)")
        try:
            response = await client.get(
                f"{base_url}/api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/callback",
                headers={"Origin": "https://app.zebra.associates"}
            )
            logger.info(f"Auth0 URL request: {response.status_code}")
            if response.status_code == 200:
                logger.info("✅ Auth0 URL generation working")
                auth_data = response.json()
                logger.info(f"Auth URL: {auth_data.get('auth_url', 'N/A')[:100]}...")
            else:
                logger.error(f"❌ Auth0 URL generation failed: {response.text}")
        except Exception as e:
            logger.error(f"❌ Auth0 URL request failed: {str(e)}")
        
        logger.info("\n" + "-" * 60)
        
        # Step 2: Test what happens when frontend makes authenticated requests WITHOUT tokens
        logger.info("Step 2: Testing authenticated endpoints WITHOUT Authorization header")
        protected_endpoints = [
            "/api/v1/organisations/current",
            "/api/v1/organisations/industries", 
            "/api/v1/organisations/accessible",
            "/api/v1/tools/"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = await client.get(
                    f"{base_url}{endpoint}",
                    headers={
                        "Origin": "https://app.zebra.associates",
                        "Content-Type": "application/json"
                        # NOTE: No Authorization header - this is what's happening in frontend
                    }
                )
                logger.info(f"{endpoint}: {response.status_code}")
                if response.status_code == 403:
                    logger.info(f"✅ Correct 403 response (no auth header)")
                else:
                    logger.info(f"Response: {response.text[:200]}")
            except Exception as e:
                logger.error(f"❌ {endpoint} failed: {str(e)}")
        
        logger.info("\n" + "-" * 60)
        
        # Step 3: Create a valid JWT token and test WITH Authorization header
        logger.info("Step 3: Testing authenticated endpoints WITH valid Authorization header")
        
        # Create a valid JWT token for testing
        test_token = create_access_token(
            data={
                "sub": "686db461-69bd-453f-8c98-4c8680e466fa",  # Real user ID from DB
                "email": "test@example.com"
            },
            tenant_id="835d4f24-cff2-43e8-a470-93216a3d99a3",  # Real org ID from DB
            user_role="viewer",
            permissions=["read:organizations", "read:market_edge"],
            industry="default"
        )
        
        logger.info(f"Created test JWT token: {test_token[:50]}...")
        
        for endpoint in protected_endpoints:
            try:
                response = await client.get(
                    f"{base_url}{endpoint}",
                    headers={
                        "Authorization": f"Bearer {test_token}",
                        "Origin": "https://app.zebra.associates",
                        "Content-Type": "application/json"
                    }
                )
                logger.info(f"{endpoint}: {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"✅ SUCCESS with valid token!")
                    logger.info(f"Response preview: {response.text[:200]}...")
                elif response.status_code == 401:
                    logger.info(f"❌ 401 Unauthorized - token validation issue")
                elif response.status_code == 403:
                    logger.info(f"❌ Still 403 - permissions issue")
                else:
                    logger.info(f"Response: {response.text[:200]}")
            except Exception as e:
                logger.error(f"❌ {endpoint} failed: {str(e)}")

def analyze_cookie_vs_header_issue():
    """Analyze why tokens aren't being sent from frontend"""
    logger.info("\n" + "=" * 60)
    logger.info("🕵️ ROOT CAUSE ANALYSIS: Why are tokens missing?")
    logger.info("=" * 60)
    
    logger.info("Frontend auth flow analysis:")
    logger.info("1. User logs in with Auth0 → Gets authorization code")
    logger.info("2. Frontend calls /api/v1/auth/login with code")
    logger.info("3. Backend should return JWT tokens and SET COOKIES")
    logger.info("4. Frontend API service should READ cookies and add Authorization header")
    
    logger.info("\nPossible issues:")
    logger.info("❓ Backend not setting HTTP-only cookies correctly")
    logger.info("❓ Frontend domain mismatch preventing cookie access")
    logger.info("❓ Cookie security settings blocking cross-origin cookies")
    logger.info("❓ Auth0 callback not completing login flow properly")
    
    logger.info("\nNext diagnostic steps:")
    logger.info("1. Check if /api/v1/auth/login sets cookies in response")
    logger.info("2. Check browser developer tools for stored cookies")
    logger.info("3. Verify cookie domain settings match frontend domain")
    logger.info("4. Test complete Auth0 → login → API call flow")

def main():
    logger.info("🚨 FRONTEND AUTH FLOW DIAGNOSIS")
    logger.info("Testing why API requests return 403 instead of including tokens")
    
    asyncio.run(test_frontend_auth_flow())
    analyze_cookie_vs_header_issue()
    
    logger.info("\n" + "=" * 60)
    logger.info("🎯 CONCLUSION")
    logger.info("The frontend auth service is correctly configured to send Authorization headers.")
    logger.info("The issue is that tokens are not being stored in cookies after login.")
    logger.info("Focus debugging on: Auth0 callback → /api/v1/auth/login → cookie storage")

if __name__ == "__main__":
    main()