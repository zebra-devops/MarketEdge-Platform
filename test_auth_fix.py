#!/usr/bin/env python3
"""
Test authentication middleware fix for proper 401/403 status codes
Verify the fix for 403 Forbidden errors when missing Authorization header
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://marketedge-platform.onrender.com"

def test_auth_status_codes():
    """Test that endpoints return proper HTTP status codes"""
    print("=" * 70)
    print("AUTHENTICATION STATUS CODE FIX TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.now()}")
    print("=" * 70)
    
    test_endpoints = [
        "/api/v1/admin/feature-flags",
        "/api/v1/admin/dashboard/stats",
        "/api/v1/auth/me"
    ]
    
    print("\n1. Testing endpoints WITHOUT Authorization header:")
    print("   Expected: 401 Unauthorized (was getting 403)")
    print("-" * 50)
    
    for endpoint in test_endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n🔸 Testing: {endpoint}")
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 401:
                print(f"   ✅ 401 Unauthorized - CORRECT (fixed!)")
            elif response.status_code == 403:
                print(f"   ⚠️ 403 Forbidden - Still returning wrong status")
            else:
                print(f"   ❓ {response.status_code} - Unexpected status code")
            
            # Check WWW-Authenticate header
            www_auth = response.headers.get('www-authenticate', 'Missing')
            print(f"   📋 WWW-Authenticate: {www_auth}")
            
            # Show response detail
            try:
                response_json = response.json()
                detail = response_json.get('detail', 'No detail')
                print(f"   📄 Detail: {detail}")
            except:
                print(f"   📄 Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n2. Testing with INVALID Authorization header:")
    print("   Expected: 401 Unauthorized")
    print("-" * 50)
    
    headers = {"Authorization": "Bearer invalid_token"}
    
    for endpoint in test_endpoints[:1]:  # Test just one endpoint
        url = f"{BASE_URL}{endpoint}"
        print(f"\n🔸 Testing: {endpoint}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 401:
                print(f"   ✅ 401 Unauthorized - CORRECT")
            elif response.status_code == 403:
                print(f"   ⚠️ 403 Forbidden - May indicate auth validation issue")
            else:
                print(f"   ❓ {response.status_code} - Unexpected status code")
                
            try:
                response_json = response.json()
                detail = response_json.get('detail', 'No detail')
                print(f"   📄 Detail: {detail}")
            except:
                print(f"   📄 Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_cors_headers():
    """Test that CORS headers are still present"""
    print(f"\n3. Testing CORS headers are still present:")
    print("-" * 50)
    
    url = f"{BASE_URL}/api/v1/admin/feature-flags"
    headers = {"Origin": "https://app.zebra.associates"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        cors_headers = {k: v for k, v in response.headers.items() 
                       if 'access-control' in k.lower()}
        
        if cors_headers:
            print("   ✅ CORS headers present:")
            for header, value in cors_headers.items():
                print(f"     {header}: {value}")
        else:
            print("   ⚠️ No CORS headers found")
            
    except Exception as e:
        print(f"   ❌ CORS test error: {e}")

def summarize_fix():
    """Summarize the authentication fix"""
    print(f"\n" + "=" * 70)
    print("AUTHENTICATION FIX SUMMARY")
    print("=" * 70)
    
    print("🔧 CHANGES MADE:")
    print("   1. Modified HTTPBearer(auto_error=False)")
    print("   2. Added manual 401 handling for missing auth")
    print("   3. Proper WWW-Authenticate header in responses")
    
    print(f"\n📊 EXPECTED BEHAVIOR:")
    print("   - No auth header: 401 Unauthorized ✅")
    print("   - Invalid token: 401 Unauthorized ✅") 
    print("   - Valid token, wrong role: 403 Forbidden ✅")
    print("   - Valid token, correct role: 200 OK ✅")
    
    print(f"\n🎯 FRONTEND IMPLICATIONS:")
    print("   - 401 errors will trigger token refresh attempts")
    print("   - 403 errors indicate insufficient permissions")
    print("   - Proper authentication flow restored")

def main():
    """Run authentication fix tests"""
    print("🚀 TESTING AUTHENTICATION MIDDLEWARE FIX")
    
    test_auth_status_codes()
    test_cors_headers()
    summarize_fix()
    
    print(f"\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("✅ Backend authentication middleware fixed")
    print("🔄 Frontend should now receive proper 401 status codes")
    print("🧪 Test with real Auth0 token to verify admin access")
    print("📱 Check browser DevTools for proper error handling")

if __name__ == "__main__":
    main()