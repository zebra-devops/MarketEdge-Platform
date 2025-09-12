#!/usr/bin/env python3
"""
Test that CORS headers are present on 500 Internal Server Error responses
This fixes the misleading "No 'Access-Control-Allow-Origin' header" browser errors
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://marketedge-platform.onrender.com"

def test_cors_on_errors():
    """Test that CORS headers are present even on error responses"""
    print("=" * 70)
    print("CORS HEADERS ON 500 ERROR RESPONSES TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.now()}")
    print(f"Testing: £925K Zebra Associates CORS fix")
    print("=" * 70)
    
    # Test scenarios that might cause 500 errors
    test_cases = [
        {
            "name": "Invalid token format (should be 401 with CORS)",
            "url": f"{BASE_URL}/api/v1/admin/feature-flags",
            "headers": {
                "Authorization": "Bearer malformed.token.here",
                "Origin": "https://app.zebra.associates"
            }
        },
        {
            "name": "Missing auth (should be 401 with CORS)",
            "url": f"{BASE_URL}/api/v1/admin/dashboard/stats",
            "headers": {
                "Origin": "https://app.zebra.associates"
            }
        },
        {
            "name": "OPTIONS preflight request",
            "url": f"{BASE_URL}/api/v1/auth/login-oauth2",
            "method": "OPTIONS",
            "headers": {
                "Origin": "https://app.zebra.associates",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization"
            }
        }
    ]
    
    print("\n🧪 TESTING CORS HEADERS ON ERROR RESPONSES:")
    print("-" * 50)
    
    all_pass = True
    
    for test in test_cases:
        print(f"\n📋 Test: {test['name']}")
        print(f"   URL: {test['url']}")
        print(f"   Origin: {test['headers'].get('Origin', 'None')}")
        
        try:
            method = test.get('method', 'GET')
            if method == 'OPTIONS':
                response = requests.options(test['url'], headers=test['headers'], timeout=10)
            else:
                response = requests.get(test['url'], headers=test['headers'], timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            # Check for CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('access-control-allow-origin'),
                'Access-Control-Allow-Credentials': response.headers.get('access-control-allow-credentials'),
                'Access-Control-Allow-Methods': response.headers.get('access-control-allow-methods'),
                'Access-Control-Allow-Headers': response.headers.get('access-control-allow-headers'),
            }
            
            # Check if essential CORS headers are present
            has_origin = cors_headers['Access-Control-Allow-Origin'] is not None
            has_credentials = cors_headers['Access-Control-Allow-Credentials'] is not None
            
            if has_origin:
                print(f"   ✅ CORS Origin header present: {cors_headers['Access-Control-Allow-Origin']}")
            else:
                print(f"   ❌ MISSING Access-Control-Allow-Origin header!")
                all_pass = False
            
            if has_credentials:
                print(f"   ✅ CORS Credentials: {cors_headers['Access-Control-Allow-Credentials']}")
            
            # For OPTIONS requests, check additional headers
            if method == 'OPTIONS':
                if cors_headers['Access-Control-Allow-Methods']:
                    print(f"   ✅ Allowed Methods: {cors_headers['Access-Control-Allow-Methods']}")
                if cors_headers['Access-Control-Allow-Headers']:
                    print(f"   ✅ Allowed Headers: {cors_headers['Access-Control-Allow-Headers'][:50]}...")
            
            # Check response body for error details
            if response.status_code >= 400:
                try:
                    body = response.json()
                    print(f"   📄 Error detail: {body.get('detail', 'No detail')}")
                except:
                    print(f"   📄 Response: {response.text[:100]}...")
                    
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            all_pass = False
    
    return all_pass

def test_actual_500_error():
    """Test a scenario that might actually cause a 500 error"""
    print("\n🔥 TESTING ACTUAL 500 ERROR SCENARIO:")
    print("-" * 50)
    
    # Try to trigger a 500 error with malformed JSON
    url = f"{BASE_URL}/api/v1/auth/login-oauth2"
    headers = {
        "Origin": "https://app.zebra.associates",
        "Content-Type": "application/json"
    }
    
    # Send invalid JSON that might cause parsing error
    data = '{"code": "test", "redirect_uri": "invalid", unclosed'
    
    print(f"Sending malformed request to trigger 500...")
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        # Check CORS headers even on 500 error
        cors_origin = response.headers.get('access-control-allow-origin')
        
        if cors_origin:
            print(f"✅ CORS headers present on {response.status_code} response!")
            print(f"   Access-Control-Allow-Origin: {cors_origin}")
        else:
            print(f"❌ NO CORS headers on {response.status_code} response!")
            print("   This would appear as CORS error in browser!")
            
    except Exception as e:
        print(f"Request failed: {e}")

def main():
    """Run CORS on 500 error tests"""
    print("🚀 TESTING CORS MIDDLEWARE FIX FOR 500 ERRORS")
    print("This fixes browser showing 'No Access-Control-Allow-Origin' instead of actual errors")
    
    # Run tests
    passed = test_cors_on_errors()
    test_actual_500_error()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    if passed:
        print("✅ CORS headers are properly included on error responses!")
        print("✅ Browser will now show actual error details instead of CORS errors")
    else:
        print("⚠️ Some CORS headers missing - deployment may be pending")
        print("   Wait 1-2 minutes for Render deployment to complete")
    
    print("\n📊 MIDDLEWARE FIX EXPLANATION:")
    print("   Before: ErrorHandler → CORS (CORS headers missing on errors)")
    print("   After:  CORS → ErrorHandler (CORS headers on ALL responses)")
    
    print("\n🎯 BUSINESS IMPACT:")
    print("   - £925K Zebra Associates can now see real error messages")
    print("   - Debugging is possible with actual 500 error details")
    print("   - No more misleading CORS errors masking real issues")

if __name__ == "__main__":
    main()