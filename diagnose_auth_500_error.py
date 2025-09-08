#!/usr/bin/env python3
"""
Diagnose the 500 error in production authentication endpoint
"""
import json
import requests
import time
from urllib.parse import urlencode

# Production URLs
BACKEND_URL = "https://marketedge-platform.onrender.com"
FRONTEND_URL = "https://app.zebra.associates"

def test_auth0_url_generation():
    """Test Auth0 URL generation - this should work"""
    print("🔍 Testing Auth0 URL generation...")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/auth/auth0-url",
            params={"redirect_uri": FRONTEND_URL},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Auth0 URL generation successful")
            print(f"   Domain: {data['auth_url'].split('/')[2]}")
            print(f"   Client ID present: {'client_id' in data['auth_url']}")
            print(f"   Redirect URI: {data['redirect_uri']}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_auth_login_with_invalid_code():
    """Test login endpoint with invalid code - should get 400, not 500"""
    print("\n🔍 Testing login endpoint with invalid code...")
    
    try:
        # Use form data like the frontend does
        data = {
            "code": "invalid_code_but_long_enough_to_pass_validation_check_from_pydantic",
            "redirect_uri": FRONTEND_URL
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data=urlencode(data),
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 400:
            print("✅ Expected 400 error for invalid code")
            return True
        elif response.status_code == 500:
            print("❌ Unexpected 500 error - indicates Auth0 configuration issue")
            print("   This suggests AUTH0_CLIENT_SECRET may be missing or invalid")
            return False
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint to confirm service status"""
    print("\n🔍 Testing health endpoint...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful")
            print(f"   Database ready: {data.get('database_ready', 'Unknown')}")
            print(f"   API router included: {data.get('api_router_included', 'Unknown')}")
            print(f"   Authentication endpoints: {data.get('authentication_endpoints', 'Unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check exception: {e}")
        return False

def test_cors_headers():
    """Test CORS headers for the auth endpoint"""
    print("\n🔍 Testing CORS headers...")
    
    try:
        # OPTIONS request to check CORS
        response = requests.options(
            f"{BACKEND_URL}/api/v1/auth/login",
            headers={
                "Origin": FRONTEND_URL,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=10
        )
        
        print(f"CORS Status: {response.status_code}")
        cors_headers = {
            k: v for k, v in response.headers.items() 
            if k.lower().startswith('access-control')
        }
        
        if cors_headers:
            print("✅ CORS headers present:")
            for header, value in cors_headers.items():
                print(f"   {header}: {value}")
            return True
        else:
            print("⚠️  No CORS headers found")
            return False
            
    except Exception as e:
        print(f"❌ CORS test exception: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🚀 Diagnosing Auth0 500 Error in Production")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("Health Check", test_health_endpoint),
        ("Auth0 URL Generation", test_auth0_url_generation),
        ("CORS Headers", test_cors_headers),
        ("Login Endpoint", test_auth_login_with_invalid_code),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        results[test_name] = test_func()
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 DIAGNOSTIC SUMMARY")
    print(f"{'='*50}")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    # Analysis
    print(f"\n{'='*50}")
    print("🔍 ANALYSIS")
    print(f"{'='*50}")
    
    if not results.get("Login Endpoint", False):
        print("❌ CRITICAL: Login endpoint returning 500 error")
        print("   This indicates Auth0 configuration issue")
        print("   Most likely cause: Missing or invalid AUTH0_CLIENT_SECRET")
        print("\n📋 RECOMMENDED ACTIONS:")
        print("   1. Check Render dashboard environment variables")
        print("   2. Verify AUTH0_CLIENT_SECRET is set correctly") 
        print("   3. Ensure Auth0 app configuration matches production domain")
        print("   4. Check Auth0 application logs for token exchange errors")
    else:
        print("✅ Login endpoint responding correctly")
    
    if results.get("Auth0 URL Generation", False) and not results.get("Login Endpoint", False):
        print("\n🎯 SPECIFIC DIAGNOSIS:")
        print("   - Auth0 URL generation works (AUTH0_DOMAIN + AUTH0_CLIENT_ID OK)")
        print("   - Login endpoint fails (AUTH0_CLIENT_SECRET likely missing)")
        print("   - Frontend will be stuck in 'emergency mode' due to 500 errors")
        
    print(f"\n{'='*50}")

if __name__ == "__main__":
    main()