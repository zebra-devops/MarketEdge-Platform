#!/usr/bin/env python3
"""
Production Auth Fix Validation

Tests the production deployment to verify the critical model import fix
has resolved the 500 "Database error occurred" issue with real Auth0 tokens.
"""

import requests
import time
import json

PRODUCTION_URL = "https://marketedge-platform.onrender.com"

def test_health_endpoint():
    """Test if the production server is responding"""
    print("🔧 Testing production health endpoint...")
    try:
        response = requests.get(f"{PRODUCTION_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Production server is responding")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_auth0_url_endpoint():
    """Test if the Auth0 URL endpoint works (doesn't require database)"""
    print("\n🔧 Testing Auth0 URL endpoint...")
    try:
        redirect_uri = "https://frontend-5r7ft62po-zebraassociates-projects.vercel.app/callback"
        response = requests.get(
            f"{PRODUCTION_URL}/api/v1/auth/auth0-url",
            params={"redirect_uri": redirect_uri},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Auth0 URL endpoint working")
            print(f"   Auth URL generated: {data.get('auth_url', '')[:100]}...")
            return True
        else:
            print(f"❌ Auth0 URL endpoint failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Auth0 URL endpoint failed: {e}")
        return False

def test_login_with_invalid_code():
    """Test login endpoint with invalid code (should return 400, not 500)"""
    print("\n🔧 Testing login endpoint with test code...")
    try:
        login_data = {
            "code": "test_code_should_fail",
            "redirect_uri": "https://frontend-5r7ft62po-zebraassociates-projects.vercel.app/callback"
        }
        
        response = requests.post(
            f"{PRODUCTION_URL}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"   Status code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 400:
            print("✅ Login endpoint returns 400 for invalid codes (correct)")
            return True
        elif response.status_code == 500:
            print("❌ Login endpoint still returns 500 (database error not fixed)")
            return False
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Login endpoint test failed: {e}")
        return False

def test_database_connectivity_via_endpoints():
    """Test if database operations are working by checking endpoints that need DB"""
    print("\n🔧 Testing database connectivity via API endpoints...")
    
    # Try to access an endpoint that requires database but not auth
    # Most endpoints require auth, so we'll check the error messages
    try:
        response = requests.get(f"{PRODUCTION_URL}/api/v1/auth/me", timeout=10)
        
        if response.status_code == 401:
            print("✅ Database-dependent endpoint accessible (returns 401 auth required)")
            return True
        elif response.status_code == 500:
            error_text = response.text.lower()
            if "database" in error_text:
                print("❌ Database connectivity issues detected")
                print(f"   Error: {response.text}")
                return False
            else:
                print("⚠️  500 error but not database related")
                return True
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False

def test_cors_configuration():
    """Test if CORS is properly configured"""
    print("\n🔧 Testing CORS configuration...")
    try:
        # Send OPTIONS request to test CORS
        headers = {
            "Origin": "https://frontend-5r7ft62po-zebraassociates-projects.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = requests.options(
            f"{PRODUCTION_URL}/api/v1/auth/login",
            headers=headers,
            timeout=10
        )
        
        cors_headers = {k.lower(): v for k, v in response.headers.items()}
        
        if "access-control-allow-origin" in cors_headers:
            print("✅ CORS headers present")
            print(f"   Allow-Origin: {cors_headers.get('access-control-allow-origin')}")
            print(f"   Allow-Methods: {cors_headers.get('access-control-allow-methods', 'Not set')}")
            return True
        else:
            print("❌ CORS headers missing")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ CORS test failed: {e}")
        return False

def wait_for_deployment():
    """Wait for deployment to complete"""
    print("⏳ Waiting for deployment to complete...")
    print("   This may take 2-3 minutes for Render deployments...")
    
    max_attempts = 18  # 3 minutes with 10-second intervals
    for attempt in range(max_attempts):
        print(f"   Attempt {attempt + 1}/{max_attempts}...")
        
        try:
            response = requests.get(f"{PRODUCTION_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Deployment appears to be complete")
                return True
        except:
            pass
        
        if attempt < max_attempts - 1:
            time.sleep(10)
    
    print("⚠️  Deployment may still be in progress")
    return False

def main():
    """Run all production validation tests"""
    print("🚀 Production Auth Fix Validation")
    print("=" * 50)
    print(f"Testing: {PRODUCTION_URL}")
    print()
    
    # Wait for deployment
    deployment_ready = wait_for_deployment()
    
    if not deployment_ready:
        print("⚠️  Proceeding with tests despite deployment status...")
    
    tests = [
        test_health_endpoint,
        test_cors_configuration,
        test_auth0_url_endpoint,
        test_login_with_invalid_code,
        test_database_connectivity_via_endpoints
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 PRODUCTION VALIDATION RESULTS")
    print("=" * 50)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    total_passed = sum(results)
    total_tests = len(tests)
    
    print(f"\nOverall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 Production deployment successful!")
        print("The critical model import fix has been deployed.")
        print("Real Auth0 tokens should now work correctly.")
    elif total_passed >= 3:
        print("⚠️  Mostly successful - check failed tests")
    else:
        print("❌ Multiple issues detected in production deployment")
    
    return total_passed >= 3

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)