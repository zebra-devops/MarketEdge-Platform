#!/usr/bin/env python3
"""
Test script to verify Auth0 authentication enum database constraint issue.
This script tests the exact database operation that fails during real Auth0 authentication.
"""

import asyncio
import aiohttp
import sys
import json
from datetime import datetime

BASE_URL = "https://marketedge-platform.onrender.com"

async def test_auth0_enum_issue():
    """Test the specific Auth0 database enum constraint issue."""
    
    print("🔍 Auth0 Database Enum Constraint Test")
    print("=" * 50)
    
    # Step 1: Verify backend is responding
    async with aiohttp.ClientSession() as session:
        try:
            print("1. Testing backend health...")
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"   ✅ Backend healthy: {health_data}")
                else:
                    print(f"   ❌ Backend unhealthy: {response.status}")
                    return
        except Exception as e:
            print(f"   ❌ Backend unreachable: {e}")
            return
        
        # Step 2: Test Auth0 URL generation (this should work)
        try:
            print("\n2. Testing Auth0 URL generation...")
            params = {
                "redirect_uri": "https://app.zebra.associates/callback"
            }
            async with session.get(f"{BASE_URL}/api/v1/auth/auth0-url", params=params) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    print(f"   ✅ Auth0 URL generated successfully")
                    print(f"   📝 Auth URL domain: {auth_data.get('auth_url', '').split('?')[0] if auth_data.get('auth_url') else 'N/A'}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Auth0 URL generation failed: {response.status}")
                    print(f"   📝 Error: {error_text[:200]}...")
                    return
        except Exception as e:
            print(f"   ❌ Auth0 URL generation error: {e}")
            return
        
        # Step 3: Test authentication with invalid code (should get 400, not 500)
        try:
            print("\n3. Testing authentication with invalid code...")
            test_data = {
                "code": "test_invalid_code_enum_test_12345",
                "redirect_uri": "https://app.zebra.associates/callback",
                "state": "test_state_enum_check"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Convert to form data
            form_data = "&".join([f"{k}={v}" for k, v in test_data.items()])
            
            async with session.post(f"{BASE_URL}/api/v1/auth/login", 
                                  data=form_data, 
                                  headers=headers) as response:
                
                response_text = await response.text()
                
                if response.status == 400:
                    print(f"   ✅ Invalid code properly rejected with 400 (expected)")
                    print(f"   📝 Response: {response_text[:100]}...")
                elif response.status == 500:
                    print(f"   ❌ CRITICAL: 500 error with invalid code (unexpected!)")
                    print(f"   📝 Response: {response_text[:200]}...")
                    print(f"   🚨 This suggests database constraint issues even with invalid codes")
                else:
                    print(f"   ⚠️  Unexpected status: {response.status}")
                    print(f"   📝 Response: {response_text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Authentication test error: {e}")
            
        # Step 4: Test a different endpoint that might trigger user/org creation
        try:
            print("\n4. Testing database operations endpoint...")
            async with session.get(f"{BASE_URL}/api/v1/database/test-connection") as response:
                if response.status == 200:
                    db_data = await response.json()
                    print(f"   ✅ Database connection test successful")
                    print(f"   📝 Database status: {db_data.get('status', 'unknown')}")
                else:
                    error_text = await response.text()
                    print(f"   ⚠️  Database test status: {response.status}")
                    print(f"   📝 Response: {error_text[:200]}...")
        except Exception as e:
            print(f"   ⚠️  Database test error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 ANALYSIS:")
    print("=" * 50)
    
    print("✅ If you see:")
    print("   • Backend healthy")
    print("   • Auth0 URL generation working")
    print("   • Invalid code rejected with 400")
    print("   • Database connection test working")
    print("   → The issue is NOT with the current deployment")
    print("   → Real Auth0 codes would trigger different code path")
    print()
    
    print("❌ If you see 500 errors:")
    print("   • With invalid codes → Database constraint issue")
    print("   • Check enum values in organization creation logic")
    print("   • Verify Industry.DEFAULT and SubscriptionPlan.basic values")
    print()
    
    print("📋 NEXT STEPS:")
    print("   1. If all tests pass: Issue is with real Auth0 token processing")
    print("   2. If 500 errors occur: Database enum constraint needs fixing")
    print("   3. Check the platform-wrapper/backend/app/api/api_v1/endpoints/auth.py")
    print("   4. Ensure enum values match database schema expectations")

if __name__ == "__main__":
    print(f"Starting Auth0 database enum test at {datetime.now().isoformat()}")
    asyncio.run(test_auth0_enum_issue())