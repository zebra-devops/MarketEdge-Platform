#!/usr/bin/env python3
"""
403 Forbidden Error Debugging Script
Verify user permissions and token handling for admin endpoints
"""

import requests
import json
import jwt
import time
from datetime import datetime

BASE_URL = "https://marketedge-platform.onrender.com"

def check_auth0_token_structure():
    """Check if we can get an Auth0 token from browser storage"""
    print("=" * 70)
    print("AUTH0 TOKEN STRUCTURE ANALYSIS")
    print("=" * 70)
    
    print("📋 Expected Auth0 JWT Token Structure:")
    print("   Header: { 'alg': 'RS256', 'typ': 'JWT' }")
    print("   Payload: {")
    print("     'sub': 'auth0|user-id',")
    print("     'email': 'matt.lindop@zebra.associates',")
    print("     'role': 'super_admin',")
    print("     'iss': 'https://your-auth0-domain/',")
    print("     'aud': 'your-api-identifier',")
    print("     'exp': timestamp,")
    print("     'iat': timestamp")
    print("   }")
    
    print("\n🔍 To get your actual token:")
    print("   1. Open https://app.zebra.associates in browser")
    print("   2. Open DevTools (F12)")
    print("   3. Go to Application/Storage tab")
    print("   4. Check localStorage for 'access_token'")
    print("   5. Check Cookies for 'access_token'")
    
    return True

def test_auth_endpoint():
    """Test authentication endpoint"""
    print("\n" + "=" * 70)
    print("AUTHENTICATION ENDPOINT TEST")
    print("=" * 70)
    
    auth_url = f"{BASE_URL}/api/v1/auth/me"
    
    print(f"Testing: {auth_url}")
    
    # Test without auth
    print("\n1. Testing without authentication:")
    response = requests.get(auth_url)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
    
    # Expected: Should return 401 Unauthorized
    if response.status_code == 401:
        print("   ✅ Correctly rejects unauthenticated requests")
    else:
        print(f"   ⚠️ Unexpected status code: {response.status_code}")
    
    return response.status_code == 401

def test_admin_endpoints_without_auth():
    """Test admin endpoints without authentication"""
    print("\n" + "=" * 70)
    print("ADMIN ENDPOINTS WITHOUT AUTH TEST")
    print("=" * 70)
    
    admin_endpoints = [
        "/api/v1/admin/feature-flags",
        "/api/v1/admin/dashboard/stats",
        "/api/v1/admin/modules",
        "/api/v1/admin/audit-logs"
    ]
    
    results = {}
    
    for endpoint in admin_endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n🔸 Testing: {endpoint}")
        
        try:
            response = requests.get(url, timeout=10)
            results[endpoint] = {
                'status': response.status_code,
                'response': response.text[:100] if response.text else 'No content'
            }
            
            if response.status_code == 401:
                print(f"   ✅ {response.status_code}: Correctly requires authentication")
            elif response.status_code == 403:
                print(f"   ⚠️ {response.status_code}: Authentication required but permission denied")
            elif response.status_code == 500:
                print(f"   ❌ {response.status_code}: Internal server error")
            else:
                print(f"   ❓ {response.status_code}: Unexpected response")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timeout")
            results[endpoint] = {'status': 'timeout', 'response': 'Request timed out'}
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[endpoint] = {'status': 'error', 'response': str(e)}
    
    return results

def simulate_valid_token_request():
    """Simulate request with a properly formatted token"""
    print("\n" + "=" * 70)
    print("SIMULATED VALID TOKEN REQUEST")
    print("=" * 70)
    
    # Create a mock token that looks like Auth0 format
    mock_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0.eyJzdWIiOiJhdXRoMHxNYXR0TGluZG9wIiwiZW1haWwiOiJtYXR0LmxpbmRvcEB6ZWJyYS5hc3NvY2lhdGVzIiwicm9sZSI6InN1cGVyX2FkbWluIiwiaXNzIjoiaHR0cHM6Ly90ZXN0LWF1dGgwLmF1dGgwLmNvbS8iLCJhdWQiOiJ0ZXN0LWFwaS1pZGVudGlmaWVyIiwiZXhwIjoxNzI2MDc2NDAwLCJpYXQiOjE3MjYwNzI4MDB9.test-signature"
    
    endpoint = "/api/v1/admin/feature-flags"
    url = f"{BASE_URL}{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {mock_token}",
        "Content-Type": "application/json",
        "Origin": "https://app.zebra.associates"
    }
    
    print(f"🚀 Making request to: {endpoint}")
    print(f"📝 Headers:")
    print(f"   Authorization: Bearer <mock-token>")
    print(f"   Origin: https://app.zebra.associates")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"\n📊 Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 401:
            print("   ✅ Token validation working (rejects mock token)")
        elif response.status_code == 403:
            print("   ⚠️ Authentication succeeded but permission denied")
            print("   💡 This suggests role/permission issue")
        elif response.status_code == 200:
            print("   🎉 Request successful!")
        elif response.status_code == 500:
            print("   ❌ Internal server error")
        
        # Show response headers
        print(f"\n📋 Response Headers:")
        cors_headers = {k: v for k, v in response.headers.items() 
                       if 'access-control' in k.lower() or 'cors' in k.lower()}
        
        if cors_headers:
            for header, value in cors_headers.items():
                print(f"   {header}: {value}")
        else:
            print("   No CORS headers found")
        
        print(f"\n📄 Response Body: {response.text[:200]}...")
        
        return response.status_code
        
    except requests.exceptions.Timeout:
        print("   ⏰ Request timed out")
        return 'timeout'
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return 'error'

def check_require_admin_logic():
    """Analyze the require_admin dependency logic"""
    print("\n" + "=" * 70)
    print("REQUIRE_ADMIN LOGIC ANALYSIS")
    print("=" * 70)
    
    print("📋 Current require_admin dependency logic (from previous fixes):")
    print("   def require_admin(current_user: User = Depends(get_current_user)) -> User:")
    print("       if current_user.role not in [UserRole.admin, UserRole.super_admin]:")
    print("           raise HTTPException(status_code=403, detail='Admin privileges required')")
    print("       return current_user")
    
    print("\n✅ This logic should accept:")
    print("   - UserRole.admin")
    print("   - UserRole.super_admin")
    
    print("\n❌ This logic will reject (403 Forbidden):")
    print("   - UserRole.analyst") 
    print("   - UserRole.viewer")
    print("   - Any other role")
    
    print("\n🎯 For Matt Lindop (matt.lindop@zebra.associates):")
    print("   Required: super_admin role in database")
    print("   Expected: Should be accepted by require_admin")
    
    return True

def analyze_403_causes():
    """Analyze possible causes of 403 Forbidden"""
    print("\n" + "=" * 70)
    print("403 FORBIDDEN ERROR ANALYSIS")
    print("=" * 70)
    
    causes = [
        {
            "cause": "Missing Authorization header",
            "description": "Frontend not sending Bearer token",
            "fix": "Check frontend auth service token retrieval"
        },
        {
            "cause": "Invalid/Expired token", 
            "description": "Auth0 token is malformed or expired",
            "fix": "Logout and login again to get fresh token"
        },
        {
            "cause": "Wrong user role",
            "description": "User has 'admin' instead of 'super_admin'",
            "fix": "Update user role in database"
        },
        {
            "cause": "Token validation failure",
            "description": "Backend can't validate Auth0 signature",
            "fix": "Check Auth0 configuration and JWT validation"
        },
        {
            "cause": "User not found in database",
            "description": "Auth0 user exists but not in app database",
            "fix": "Ensure user record exists with correct email"
        }
    ]
    
    print("🔍 Possible causes of 403 Forbidden:")
    for i, cause in enumerate(causes, 1):
        print(f"\n{i}. {cause['cause']}")
        print(f"   Description: {cause['description']}")
        print(f"   Fix: {cause['fix']}")
    
    return causes

def main():
    """Run comprehensive 403 debugging"""
    print("🚨 403 FORBIDDEN ERROR DEBUGGING")
    print("=" * 70)
    print(f"Timestamp: {datetime.now()}")
    print(f"Target: https://app.zebra.associates admin endpoints")
    print("=" * 70)
    
    # Run all checks
    check_auth0_token_structure()
    test_auth_endpoint()
    results = test_admin_endpoints_without_auth()
    simulate_valid_token_request()
    check_require_admin_logic()
    analyze_403_causes()
    
    # Summary
    print("\n" + "=" * 70)
    print("DEBUGGING SUMMARY & NEXT STEPS")
    print("=" * 70)
    
    print("🔧 IMMEDIATE ACTIONS NEEDED:")
    print("1. Get real Auth0 token from browser:")
    print("   - Open https://app.zebra.associates")
    print("   - Login as matt.lindop@zebra.associates") 
    print("   - Check DevTools → Application → localStorage['access_token']")
    
    print("\n2. Verify token in Authorization header:")
    print("   - Open DevTools → Network tab")
    print("   - Make admin request")
    print("   - Check if 'Authorization: Bearer <token>' header present")
    
    print("\n3. Test token manually:")
    print("   - Use token in: curl -H 'Authorization: Bearer <your-token>' \\")
    print("     https://marketedge-platform.onrender.com/api/v1/admin/feature-flags")
    
    print("\n4. If still 403, check user role:")
    print("   - Verify matt.lindop@zebra.associates has 'super_admin' role")
    print("   - Check user is active and verified")
    
    print("\n💡 Expected Behavior:")
    print("   - With valid super_admin token: 200 OK with data")
    print("   - With invalid token: 401 Unauthorized") 
    print("   - With valid token, wrong role: 403 Forbidden")
    
    print("\n🎯 Key Files to Check:")
    print("   - Frontend: /src/services/auth.ts (token handling)")
    print("   - Backend: /app/auth/dependencies.py (require_admin)")

if __name__ == "__main__":
    main()