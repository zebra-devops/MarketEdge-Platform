#!/usr/bin/env python3
"""
Test the emergency CORS middleware locally
"""
import requests
import time

def test_cors_fix():
    base_url = "https://marketedge-backend-production.up.railway.app"
    custom_origin = "https://app.zebra.associates"
    
    print(f"Testing CORS fix for {custom_origin}")
    print(f"Backend URL: {base_url}")
    print("=" * 50)
    
    # Test 1: Health endpoint with Origin header
    print("Test 1: GET /health with Origin header")
    try:
        response = requests.get(
            f"{base_url}/health",
            headers={"Origin": custom_origin},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Check for Access-Control-Allow-Origin
        if "Access-Control-Allow-Origin" in response.headers:
            print(f"✅ Access-Control-Allow-Origin: {response.headers['Access-Control-Allow-Origin']}")
        else:
            print("❌ Access-Control-Allow-Origin header MISSING")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    
    # Test 2: OPTIONS preflight request
    print("Test 2: OPTIONS /health (preflight)")
    try:
        response = requests.options(
            f"{base_url}/health",
            headers={
                "Origin": custom_origin,
                "Access-Control-Request-Method": "GET"
            },
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Check for Access-Control-Allow-Origin
        if "Access-Control-Allow-Origin" in response.headers:
            print(f"✅ Access-Control-Allow-Origin: {response.headers['Access-Control-Allow-Origin']}")
        else:
            print("❌ Access-Control-Allow-Origin header MISSING")
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print("\n" + "=" * 50)
    
    # Test 3: Check if debug endpoint is available
    print("Test 3: GET /cors-debug")
    try:
        response = requests.get(
            f"{base_url}/cors-debug",
            headers={"Origin": custom_origin},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Debug info: {response.json()}")
        else:
            print(f"Debug endpoint not available: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_cors_fix()