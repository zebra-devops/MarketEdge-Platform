#!/usr/bin/env python3
"""
Test direct authentication to bypass CORS preflight issues
"""
import requests

def test_direct_auth():
    backend_url = "https://marketedge-backend-production.up.railway.app"
    custom_origin = "https://app.zebra.associates"
    
    print("Testing direct authentication bypass...")
    
    # Test 1: Get Auth0 URL (this works)
    print("\n1. Testing Auth0 URL endpoint...")
    auth_url_response = requests.get(
        f"{backend_url}/api/v1/auth/auth0-url",
        params={"redirect_uri": f"{custom_origin}/callback"},
        headers={"Origin": custom_origin}
    )
    print(f"Status: {auth_url_response.status_code}")
    print(f"Auth URL working: {auth_url_response.status_code == 200}")
    if auth_url_response.status_code == 200:
        print(f"Auth URL: {auth_url_response.json().get('auth_url', 'N/A')}")
    
    # Test 2: Try POST without preflight
    print("\n2. Testing direct POST (bypassing preflight)...")
    try:
        # Make a simple request that might not trigger preflight
        simple_headers = {
            "Content-Type": "application/x-www-form-urlencoded",  # Simple content type
            "Origin": custom_origin
        }
        
        # Test data for auth
        auth_data = {
            "code": "test_code",
            "redirect_uri": f"{custom_origin}/callback"
        }
        
        auth_response = requests.post(
            f"{backend_url}/api/v1/auth/login",
            data=auth_data,  # Use form data instead of JSON
            headers=simple_headers
        )
        
        print(f"Direct POST Status: {auth_response.status_code}")
        print(f"Response Headers: {dict(auth_response.headers)}")
        
        # Check for CORS headers
        if "Access-Control-Allow-Origin" in auth_response.headers:
            print(f"✅ CORS headers present: {auth_response.headers['Access-Control-Allow-Origin']}")
        else:
            print("❌ CORS headers missing")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Check what browsers actually send
    print("\n3. Testing exact browser preflight simulation...")
    try:
        preflight_response = requests.options(
            f"{backend_url}/api/v1/auth/login",
            headers={
                "Origin": custom_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            }
        )
        
        print(f"Preflight Status: {preflight_response.status_code}")
        print(f"Preflight Headers: {dict(preflight_response.headers)}")
        
        if "Access-Control-Allow-Origin" in preflight_response.headers:
            print(f"✅ Preflight CORS: {preflight_response.headers['Access-Control-Allow-Origin']}")
        else:
            print("❌ Preflight CORS missing")
            
    except Exception as e:
        print(f"Preflight Error: {e}")

if __name__ == "__main__":
    test_direct_auth()