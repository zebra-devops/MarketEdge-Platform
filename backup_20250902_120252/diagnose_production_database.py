#!/usr/bin/env python3
"""
Production Database Diagnosis for Auth0 500 Errors
Checks if the database state is causing authentication failures
"""
import asyncio
import httpx
import json

async def diagnose_production_database():
    """Check production database state that could cause auth failures"""
    
    print("========================================")
    print("Production Database Diagnosis")
    print("========================================")
    
    backend_url = "https://marketedge-platform.onrender.com"
    
    # Test 1: Check if we can reach the backend
    print("1. Testing backend connectivity...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{backend_url}/health")
            if response.status_code == 200:
                print("✅ Backend health check passed")
                health_data = response.json()
                print(f"   Service type: {health_data.get('service_type', 'unknown')}")
                print(f"   CORS mode: {health_data.get('cors_mode', 'unknown')}")
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend connectivity error: {e}")
    
    print()
    
    # Test 2: Check if Auth0 URL generation works (no database required)
    print("2. Testing Auth0 configuration...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{backend_url}/api/v1/auth/auth0-url",
                params={"redirect_uri": "https://app.zebra.associates/callback"}
            )
            if response.status_code == 200:
                print("✅ Auth0 configuration working")
                auth_data = response.json()
                print(f"   Domain: {auth_data['auth_url'].split('/')[2]}")
            else:
                print(f"❌ Auth0 configuration failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Auth0 test error: {e}")
    
    print()
    
    # Test 3: Test the exact code that's failing
    print("3. Testing with real-pattern authorization code...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Use a realistic Auth0 code pattern but still invalid
            form_data = {
                "code": "sAAizkCJKe_test_pattern_12345",
                "redirect_uri": "https://app.zebra.associates/callback"
            }
            
            response = await client.post(
                f"{backend_url}/api/v1/auth/login",
                data=form_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": "https://app.zebra.associates"
                }
            )
            
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code == 400:
                print("✅ Expected 400 response - Auth0 exchange working")
            elif response.status_code == 500:
                print("❌ CRITICAL: 500 error with test code")
                print("   This suggests database or environment issues")
                
                # Parse the error response
                try:
                    error_data = response.json()
                    print(f"   Error detail: {error_data.get('detail', 'unknown')}")
                    print(f"   Error type: {error_data.get('type', 'unknown')}")
                except:
                    print("   Could not parse error response as JSON")
            else:
                print(f"⚠️ Unexpected status code: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
    
    print()
    
    # Test 4: Try to trigger the exact same error path
    print("4. Testing different code patterns to isolate failure...")
    
    test_codes = [
        ("short_code", "abc123"),
        ("medium_code", "test_auth_code_12345"),
        ("auth0_pattern", "sAAizkCJKe1234567890"),
        ("long_valid_pattern", "sAAizkCJKeLongValidLookingCode12345")
    ]
    
    for test_name, test_code in test_codes:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                form_data = {
                    "code": test_code,
                    "redirect_uri": "https://app.zebra.associates/callback"
                }
                
                response = await client.post(
                    f"{backend_url}/api/v1/auth/login",
                    data=form_data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Origin": "https://app.zebra.associates"
                    }
                )
                
                print(f"   {test_name}: {response.status_code}")
                
                if response.status_code == 500:
                    print(f"   🚨 500 ERROR with {test_name}")
                    try:
                        error_data = response.json()
                        print(f"      Detail: {error_data.get('detail', 'unknown')}")
                    except:
                        pass
                        
        except Exception as e:
            print(f"   {test_name}: ERROR - {e}")
    
    print()
    print("========================================")
    print("DIAGNOSIS SUMMARY")
    print("========================================")
    print()
    print("If any test returned 500 errors:")
    print("1. Check Render dashboard for database connection issues")
    print("2. Verify environment variables are properly set")
    print("3. Check if 'Default' organization exists in production database")
    print("4. Review production logs for specific error details")
    print()
    print("Next steps:")
    print("1. Access Render dashboard to check logs")
    print("2. Verify database connectivity")
    print("3. Check if recent deployments completed successfully")

if __name__ == "__main__":
    asyncio.run(diagnose_production_database())