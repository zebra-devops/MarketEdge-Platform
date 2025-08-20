#!/usr/bin/env python3
"""
Debug script to test Auth0 callback → cookie storage → API request flow
"""
import requests
import json
import os
from http.cookies import SimpleCookie

# Configuration
BACKEND_URL = "https://marketedge-platform.onrender.com"
FRONTEND_URL = "https://app.zebra.associates"

def test_cookie_settings():
    """Test the /api/v1/auth/login endpoint and examine cookie headers"""
    print("🔍 Testing Auth0 login endpoint cookie settings...")
    
    # Mock login request (this will fail but let us see response headers)
    login_url = f"{BACKEND_URL}/api/v1/auth/login"
    
    # Use form data to avoid CORS preflight
    form_data = {
        'code': 'test_code_12345',
        'redirect_uri': f'{FRONTEND_URL}/callback',
        'state': 'test_state'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': FRONTEND_URL,
        'Referer': f'{FRONTEND_URL}/callback'
    }
    
    try:
        response = requests.post(
            login_url,
            data=form_data,
            headers=headers,
            allow_redirects=False
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers:")
        for key, value in response.headers.items():
            if 'cookie' in key.lower() or 'cors' in key.lower() or 'origin' in key.lower():
                print(f"  {key}: {value}")
        
        # Check if Set-Cookie headers are present
        set_cookie_headers = response.headers.get_list('Set-Cookie') if hasattr(response.headers, 'get_list') else []
        if not set_cookie_headers:
            set_cookie_headers = [v for k, v in response.headers.items() if k.lower() == 'set-cookie']
        
        if set_cookie_headers:
            print(f"🍪 Set-Cookie Headers Found:")
            for cookie_header in set_cookie_headers:
                print(f"  {cookie_header}")
                # Parse cookie attributes
                cookie = SimpleCookie()
                cookie.load(cookie_header)
                for morsel in cookie.values():
                    print(f"    Cookie: {morsel.key}={morsel.value}")
                    print(f"    Attributes: secure={morsel['secure']}, httponly={morsel['httponly']}, samesite={morsel['samesite']}, domain={morsel['domain']}, path={morsel['path']}")
        else:
            print("❌ No Set-Cookie headers found!")
        
        # Check CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        print(f"🌍 CORS Headers:")
        for key, value in cors_headers.items():
            print(f"  {key}: {value}")
        
        # Check if credentials are allowed
        if cors_headers['Access-Control-Allow-Credentials'] != 'true':
            print("❌ WARNING: Access-Control-Allow-Credentials is not 'true' - cookies will be blocked!")
        
        # Show response body (for error details)
        if response.text:
            try:
                error_data = response.json()
                print(f"📋 Response Body: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📋 Response Body: {response.text[:500]}")
    
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_cors_preflight():
    """Test CORS preflight request"""
    print("\n🔍 Testing CORS preflight request...")
    
    login_url = f"{BACKEND_URL}/api/v1/auth/login"
    
    # CORS preflight request
    headers = {
        'Origin': FRONTEND_URL,
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type, Authorization'
    }
    
    try:
        response = requests.options(login_url, headers=headers)
        
        print(f"📊 Preflight Status: {response.status_code}")
        print(f"📊 Preflight Headers:")
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        for key, value in cors_headers.items():
            print(f"  {key}: {value}")
            
        if response.status_code != 200:
            print("❌ CORS preflight failed!")
        
    except Exception as e:
        print(f"❌ Preflight request failed: {e}")

if __name__ == "__main__":
    print("🚀 Cookie Authentication Debug Test")
    print("=" * 50)
    
    test_cors_preflight()
    test_cookie_settings()
    
    print("\n📋 Summary:")
    print("- If Set-Cookie headers are missing, cookies won't be stored")
    print("- If Access-Control-Allow-Credentials is not 'true', cookies will be blocked")
    print("- If cookie secure=true but using HTTP, cookies won't be stored")
    print("- If cookie domain doesn't match, cookies won't be stored")
    print("- If cookie samesite=strict and cross-origin, cookies may be blocked")