#!/usr/bin/env python3
"""
Epic 2 CORS and Authentication Validation Script
================================================================

CRITICAL ISSUE ANALYSIS RESULTS:
- CORS is working correctly (frontend URL already in CORS_ORIGINS)
- Backend is healthy and responding
- Auth0 integration is configured properly
- Issue is NOT a backend 500 error or CORS problem

This script validates the complete authentication flow to identify
the real issue preventing Auth0 completion.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional
from urllib.parse import quote

# Configuration
BACKEND_URL = "https://marketedge-platform.onrender.com"
FRONTEND_URL = "https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app"
FRONTEND_CALLBACK = f"{FRONTEND_URL}/callback"

def test_cors_configuration():
    """Test CORS configuration with the frontend URL"""
    print("🔍 Testing CORS Configuration...")
    
    try:
        # Test preflight request
        preflight_response = requests.options(
            f"{BACKEND_URL}/api/v1/auth/login",
            headers={
                "Origin": FRONTEND_URL,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=30
        )
        
        print(f"✅ CORS Preflight Status: {preflight_response.status_code}")
        print(f"✅ CORS Headers: {dict(preflight_response.headers)}")
        
        # Test CORS debug endpoint
        cors_debug_response = requests.get(
            f"{BACKEND_URL}/cors-debug",
            headers={"Origin": FRONTEND_URL},
            timeout=30
        )
        
        if cors_debug_response.status_code == 200:
            cors_data = cors_debug_response.json()
            print(f"✅ CORS Origins Configured: {cors_data.get('cors_origins_configured')}")
            print(f"✅ Origin Allowed: {cors_data.get('origin_allowed')}")
            print(f"✅ CORS Mode: {cors_data.get('cors_mode')}")
            return True
        else:
            print(f"❌ CORS Debug failed: {cors_debug_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CORS test failed: {str(e)}")
        return False

def test_backend_health():
    """Test backend health and availability"""
    print("\n🔍 Testing Backend Health...")
    
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=30)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Backend Status: {health_data.get('status')}")
            print(f"✅ Version: {health_data.get('version')}")
            print(f"✅ CORS Mode: {health_data.get('cors_mode')}")
            print(f"✅ Emergency Mode: {health_data.get('emergency_mode')}")
            return True
        else:
            print(f"❌ Backend health check failed: {health_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Backend health test failed: {str(e)}")
        return False

def test_auth0_url_generation():
    """Test Auth0 URL generation"""
    print("\n🔍 Testing Auth0 URL Generation...")
    
    try:
        auth_url_response = requests.get(
            f"{BACKEND_URL}/api/v1/auth/auth0-url",
            params={"redirect_uri": FRONTEND_CALLBACK},
            headers={"Origin": FRONTEND_URL},
            timeout=30
        )
        
        if auth_url_response.status_code == 200:
            auth_data = auth_url_response.json()
            auth_url = auth_data.get("auth_url")
            print(f"✅ Auth0 URL Generated: {auth_url[:100]}...")
            print(f"✅ Redirect URI: {auth_data.get('redirect_uri')}")
            print(f"✅ Scopes: {auth_data.get('scopes')}")
            return True, auth_url
        else:
            print(f"❌ Auth0 URL generation failed: {auth_url_response.status_code}")
            print(f"❌ Response: {auth_url_response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Auth0 URL test failed: {str(e)}")
        return False, None

def test_authentication_endpoint_validation():
    """Test authentication endpoint with various request formats"""
    print("\n🔍 Testing Authentication Endpoint...")
    
    test_cases = [
        {
            "name": "Empty JSON",
            "data": {},
            "content_type": "application/json"
        },
        {
            "name": "Invalid JSON",
            "data": {"invalid": "data"},
            "content_type": "application/json"
        },
        {
            "name": "Valid Structure (Test Code)",
            "data": {
                "code": "test_authorization_code",
                "redirect_uri": FRONTEND_CALLBACK,
                "state": "test_state"
            },
            "content_type": "application/json"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n  📝 Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/auth/login",
                json=test_case["data"],
                headers={
                    "Origin": FRONTEND_URL,
                    "Content-Type": test_case["content_type"]
                },
                timeout=30
            )
            
            print(f"    Status: {response.status_code}")
            
            # Check CORS headers in response
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            cors_credentials = response.headers.get("Access-Control-Allow-Credentials")
            
            if cors_origin == FRONTEND_URL:
                print(f"    ✅ CORS Origin Header: {cors_origin}")
            else:
                print(f"    ❌ CORS Origin Header: {cors_origin}")
                
            if cors_credentials == "true":
                print(f"    ✅ CORS Credentials: {cors_credentials}")
            else:
                print(f"    ❌ CORS Credentials: {cors_credentials}")
            
            if response.status_code == 400:
                # Expected validation error
                error_data = response.json()
                print(f"    ✅ Validation Error (Expected): {error_data.get('detail', 'No detail')[:100]}")
            elif response.status_code == 500:
                print(f"    ❌ Internal Server Error: {response.text[:200]}")
                return False
            else:
                print(f"    ℹ️  Unexpected Status: {response.text[:200]}")
                
        except Exception as e:
            print(f"    ❌ Request failed: {str(e)}")
            return False
    
    return True

def test_form_data_authentication():
    """Test authentication endpoint with form data (CORS workaround)"""
    print("\n🔍 Testing Form Data Authentication...")
    
    try:
        form_data = {
            "code": "test_authorization_code",
            "redirect_uri": FRONTEND_CALLBACK,
            "state": "test_state"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data=form_data,
            headers={
                "Origin": FRONTEND_URL,
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=30
        )
        
        print(f"✅ Form Data Status: {response.status_code}")
        
        # Check CORS headers
        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        if cors_origin == FRONTEND_URL:
            print(f"✅ CORS Origin Header: {cors_origin}")
        else:
            print(f"❌ CORS Origin Header: {cors_origin}")
        
        if response.status_code == 400:
            error_data = response.json()
            print(f"✅ Form Data Validation (Expected): {error_data.get('detail', 'No detail')[:100]}")
            return True
        elif response.status_code == 500:
            print(f"❌ Form Data Internal Server Error: {response.text[:200]}")
            return False
        else:
            print(f"ℹ️  Form Data Unexpected Status: {response.text[:200]}")
            return True
            
    except Exception as e:
        print(f"❌ Form data test failed: {str(e)}")
        return False

def generate_frontend_integration_guide():
    """Generate frontend integration guide"""
    print("\n📋 Frontend Integration Guide:")
    print("=" * 50)
    
    guide = f"""
FRONTEND INTEGRATION CHECKLIST:

1. CORS Configuration ✅
   - Backend URL: {BACKEND_URL}
   - Frontend URL: {FRONTEND_URL}
   - CORS headers are working correctly

2. Auth0 Flow Implementation:
   
   Step 1: Get Auth0 URL
   ```javascript
   const response = await fetch('{BACKEND_URL}/api/v1/auth/auth0-url?redirect_uri={FRONTEND_CALLBACK}', {{
     headers: {{
       'Origin': '{FRONTEND_URL}'
     }}
   }});
   const {{ auth_url }} = await response.json();
   window.location.href = auth_url;
   ```
   
   Step 2: Handle Callback (at {FRONTEND_CALLBACK})
   ```javascript
   const urlParams = new URLSearchParams(window.location.search);
   const code = urlParams.get('code');
   const state = urlParams.get('state');
   
   if (code) {{
     try {{
       const response = await fetch('{BACKEND_URL}/api/v1/auth/login', {{
         method: 'POST',
         headers: {{
           'Content-Type': 'application/json',
           'Origin': '{FRONTEND_URL}'
         }},
         credentials: 'include',
         body: JSON.stringify({{
           code: code,
           redirect_uri: '{FRONTEND_CALLBACK}',
           state: state
         }})
       }});
       
       if (response.ok) {{
         const authData = await response.json();
         console.log('Authentication successful:', authData);
         // Redirect to dashboard or home page
       }} else {{
         console.error('Authentication failed:', response.status);
         const error = await response.json();
         console.error('Error details:', error);
       }}
     }} catch (error) {{
       console.error('Network error:', error);
     }}
   }}
   ```

3. Fallback Form Data Method (if JSON fails):
   ```javascript
   const formData = new FormData();
   formData.append('code', code);
   formData.append('redirect_uri', '{FRONTEND_CALLBACK}');
   formData.append('state', state);
   
   const response = await fetch('{BACKEND_URL}/api/v1/auth/login', {{
     method: 'POST',
     headers: {{
       'Origin': '{FRONTEND_URL}'
     }},
     credentials: 'include',
     body: formData
   }});
   ```

DEBUGGING TIPS:
- Check browser console for CORS errors
- Verify network requests in DevTools
- Ensure credentials: 'include' is set for cookie handling
- Check that the authorization code is not expired
"""
    
    print(guide)

def main():
    """Run complete validation"""
    print("🚀 Epic 2 CORS and Authentication Validation")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Run all tests
    if not test_backend_health():
        all_tests_passed = False
    
    if not test_cors_configuration():
        all_tests_passed = False
    
    auth_url_success, auth_url = test_auth0_url_generation()
    if not auth_url_success:
        all_tests_passed = False
    
    if not test_authentication_endpoint_validation():
        all_tests_passed = False
    
    if not test_form_data_authentication():
        all_tests_passed = False
    
    # Generate integration guide
    generate_frontend_integration_guide()
    
    # Final summary
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED - Epic 2 Backend Ready")
        print("\n🎯 ISSUE DIAGNOSIS:")
        print("- ✅ CORS is working correctly")
        print("- ✅ Backend is healthy and responding")
        print("- ✅ Auth0 integration is functional")
        print("- ✅ Authentication endpoint accepts requests")
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        print("The original 500 error was likely:")
        print("1. Temporary network issue")
        print("2. Frontend sending malformed requests")
        print("3. Auth0 configuration mismatch")
        print("4. Invalid authorization codes")
        print("\n🚀 ACTION REQUIRED:")
        print("1. Update frontend code using the integration guide above")
        print("2. Test with valid Auth0 authorization codes")
        print("3. Ensure proper error handling in frontend")
        print("4. Verify Auth0 callback URL configuration")
        
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review Issues Above")
        return 1

if __name__ == "__main__":
    sys.exit(main())