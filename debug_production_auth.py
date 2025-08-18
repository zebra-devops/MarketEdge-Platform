#!/usr/bin/env python3
"""
Production Authentication Debugging Tool

This script helps diagnose authentication issues by testing various scenarios
that might be causing 500 errors in the production environment.
"""

import requests
import json
import time
from urllib.parse import urlencode

# Configuration
PRODUCTION_URL = "https://marketedge-platform.onrender.com"
FRONTEND_ORIGIN = "https://app.zebra.associates"

def test_auth_endpoint(test_name, data, headers=None):
    """Test the auth endpoint with specific data and headers"""
    print(f"\n=== {test_name} ===")
    
    default_headers = {
        "Content-Type": "application/json",
        "Origin": FRONTEND_ORIGIN,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        response = requests.post(
            f"{PRODUCTION_URL}/api/v1/auth/login",
            json=data,
            headers=default_headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Raw Response Body: {response.text}")
            
        return response.status_code, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None, str(e)

def main():
    """Run comprehensive auth endpoint testing"""
    print("🔍 Production Authentication Debugging Tool")
    print("=" * 60)
    
    # Test 1: Empty request
    test_auth_endpoint("Empty Request", {})
    
    # Test 2: Missing fields
    test_auth_endpoint("Missing Code", {"redirect_uri": "https://app.zebra.associates/callback"})
    
    # Test 3: Invalid code length
    test_auth_endpoint("Short Code", {"code": "short", "redirect_uri": "https://app.zebra.associates/callback"})
    
    # Test 4: Valid format but fake code
    test_auth_endpoint("Fake Valid Code", {
        "code": "fake_auth_code_12345678901234567890", 
        "redirect_uri": "https://app.zebra.associates/callback"
    })
    
    # Test 5: Form data instead of JSON (old frontend format)
    print("\n=== Form Data Test ===")
    try:
        response = requests.post(
            f"{PRODUCTION_URL}/api/v1/auth/login",
            data=urlencode({
                "code": "form_data_code_12345678901234567890",
                "redirect_uri": "https://app.zebra.associates/callback"
            }),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": FRONTEND_ORIGIN
            },
            timeout=30
        )
        print(f"Form Data Status: {response.status_code}")
        print(f"Form Data Response: {response.text}")
    except Exception as e:
        print(f"❌ Form data test failed: {e}")
    
    # Test 6: Health check
    print("\n=== Health Check ===")
    try:
        response = requests.get(f"{PRODUCTION_URL}/health", timeout=10)
        print(f"Health Status: {response.status_code}")
        health_data = response.json()
        print(f"Health Response: {json.dumps(health_data, indent=2)}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 DEBUGGING COMPLETE")
    print("\nIf all tests return 400/422 errors (not 500), the backend is working correctly.")
    print("If any test returns 500 'internal_error', that indicates the specific issue.")
    print("\nNext steps:")
    print("1. Compare these results with frontend console errors")
    print("2. Check if user has browser cache issues")
    print("3. Test with a fresh Auth0 authorization code")

if __name__ == "__main__":
    main()