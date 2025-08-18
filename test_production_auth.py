#!/usr/bin/env python3
"""
Production Authentication Issue Diagnosis
Test script to identify the exact failure point in our authentication flow
"""

import asyncio
import httpx
import sys
import os
import json
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Production backend URL
PRODUCTION_URL = "https://marketedge-platform.onrender.com"

async def test_auth_endpoints():
    """Test all authentication-related endpoints to identify failure points"""
    print(f"🔍 Testing Production Authentication Flow - {datetime.now()}")
    print(f"Production URL: {PRODUCTION_URL}")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Health check
        print("\n1️⃣ Testing Health Check...")
        try:
            response = await client.get(f"{PRODUCTION_URL}/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            if response.status_code != 200:
                print(f"   ❌ Health check failed!")
                return
            print(f"   ✅ Health check passed")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return
        
        # Test 2: Auth0 URL generation
        print("\n2️⃣ Testing Auth0 URL Generation...")
        try:
            response = await client.get(
                f"{PRODUCTION_URL}/api/v1/auth/auth0-url",
                params={"redirect_uri": "https://odeon-demo.netlify.app/callback"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                auth_data = response.json()
                print(f"   ✅ Auth0 URL generated successfully")
                print(f"   Auth URL: {auth_data.get('auth_url', 'Not provided')[:100]}...")
            else:
                print(f"   ❌ Auth0 URL generation failed")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Auth0 URL error: {e}")
        
        # Test 3: Login with invalid code (expected 400)
        print("\n3️⃣ Testing Login with Invalid Code (Expected 400)...")
        try:
            response = await client.post(
                f"{PRODUCTION_URL}/api/v1/auth/login",
                json={
                    "code": "invalid_test_code",
                    "redirect_uri": "https://odeon-demo.netlify.app/callback"
                }
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            if response.status_code == 400:
                print(f"   ✅ Invalid code correctly rejected (400)")
            else:
                print(f"   ⚠️  Unexpected status code: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Login test error: {e}")
        
        # Test 4: Test database connectivity indirectly
        print("\n4️⃣ Testing Database-dependent Endpoints...")
        try:
            # This endpoint requires database access for user lookup
            response = await client.get(
                f"{PRODUCTION_URL}/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid_token"}
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            if response.status_code in [401, 403]:
                print(f"   ✅ Database-dependent endpoint accessible (proper auth rejection)")
            elif response.status_code == 500:
                print(f"   ❌ Database connection issues detected!")
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Database test error: {e}")

async def test_production_environment():
    """Test production environment configuration"""
    print("\n5️⃣ Testing Production Environment Configuration...")
    
    try:
        # Import after adding to path
        from core.config import settings
        
        print(f"   Environment: {settings.ENVIRONMENT}")
        print(f"   Debug: {settings.DEBUG}")
        print(f"   Auth0 Domain: {settings.AUTH0_DOMAIN}")
        print(f"   Auth0 Client ID: {settings.AUTH0_CLIENT_ID[:10]}...")
        print(f"   Has Auth0 Secret: {'Yes' if settings.AUTH0_CLIENT_SECRET else 'No'}")
        print(f"   Database URL: {settings.DATABASE_URL[:30]}...")
        print(f"   CORS Origins: {settings.CORS_ORIGINS}")
        
        if settings.ENVIRONMENT.lower() == 'production':
            print(f"   ✅ Production environment detected")
        else:
            print(f"   ⚠️  Not in production environment")
            
    except Exception as e:
        print(f"   ❌ Config check error: {e}")

async def simulate_real_auth_failure():
    """Simulate the exact scenario reported by the frontend"""
    print("\n6️⃣ Simulating Real Auth Failure Scenario...")
    
    # This simulates what happens when a real Auth0 code is received
    # but fails during processing (the 500 error case)
    
    real_auth_scenarios = [
        {
            "name": "Frontend-like Request (JSON)",
            "data": {
                "code": "sAAizkCJKe_test_simulation",  # Simulate real Auth0 code format
                "redirect_uri": "https://odeon-demo.netlify.app/callback",
                "state": "test_state_value"
            },
            "headers": {
                "Content-Type": "application/json",
                "Origin": "https://odeon-demo.netlify.app",
                "Referer": "https://odeon-demo.netlify.app/",
                "User-Agent": "Mozilla/5.0 (Chrome Frontend Test)"
            }
        },
        {
            "name": "Form Data Request",
            "data": {
                "code": "sAAizkCJKe_test_simulation",
                "redirect_uri": "https://odeon-demo.netlify.app/callback",
                "state": "test_state_value"
            },
            "headers": {
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://odeon-demo.netlify.app"
            },
            "form_data": True
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for scenario in real_auth_scenarios:
            print(f"\n   Testing: {scenario['name']}")
            try:
                if scenario.get('form_data'):
                    response = await client.post(
                        f"{PRODUCTION_URL}/api/v1/auth/login",
                        data=scenario['data'],
                        headers=scenario['headers']
                    )
                else:
                    response = await client.post(
                        f"{PRODUCTION_URL}/api/v1/auth/login",
                        json=scenario['data'],
                        headers=scenario['headers']
                    )
                
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
                if response.status_code == 500:
                    print(f"   ❌ REPRODUCED 500 ERROR!")
                    print(f"   This is the exact issue the frontend is experiencing")
                elif response.status_code == 400:
                    print(f"   ✅ Expected 400 (invalid test code)")
                else:
                    print(f"   ⚠️  Unexpected status: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Scenario error: {e}")

async def main():
    """Main test runner"""
    print("🚀 Production Authentication Diagnostic Tool")
    print("This tool will identify where real Auth0 authentication fails in production")
    print()
    
    try:
        await test_auth_endpoints()
        await test_production_environment()
        await simulate_real_auth_failure()
        
        print("\n" + "=" * 60)
        print("🎯 DIAGNOSIS SUMMARY:")
        print("1. If health checks pass but auth fails → Backend processing issue")
        print("2. If 500 errors occur → Database or environment configuration issue")
        print("3. If Auth0 URL generation fails → Auth0 configuration issue")
        print("4. Compare test results with frontend console logs")
        print("\n💡 Next Steps:")
        print("- Check production logs for detailed error messages")
        print("- Verify database connectivity in production")
        print("- Confirm Auth0 environment variables are set correctly")
        print("- Test with a real Auth0 code in a controlled environment")
        
    except Exception as e:
        print(f"\n❌ Diagnostic tool error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())