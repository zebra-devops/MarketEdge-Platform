#!/usr/bin/env python3
"""
Quick CORS and Header Transmission Test for Feature Flags

Tests if Authorization headers are being blocked by CORS for feature flags
specifically vs other admin endpoints.
"""

import requests
import json
from datetime import datetime

def test_cors_and_headers():
    """Test CORS configuration and header transmission"""

    base_url = "https://marketedge-platform.onrender.com/api/v1"

    # Test endpoints
    endpoints = {
        "feature_flags": f"{base_url}/admin/feature-flags",
        "admin_stats": f"{base_url}/admin/dashboard/stats"
    }

    # Test token (dummy for CORS testing)
    test_token = "Bearer dummy-token-for-cors-test"

    print("🔍 CORS AND HEADER TRANSMISSION TEST")
    print("=" * 50)
    print(f"Time: {datetime.now().isoformat()}")
    print()

    for name, url in endpoints.items():
        print(f"📍 Testing {name}: {url}")

        # 1. Test CORS preflight
        print("   🔍 CORS Preflight...")
        try:
            cors_response = requests.options(
                url,
                headers={
                    'Origin': 'https://app.zebra.associates',
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'authorization,content-type'
                },
                timeout=10
            )

            print(f"      Status: {cors_response.status_code}")

            cors_origin = cors_response.headers.get('Access-Control-Allow-Origin', 'Not set')
            cors_headers = cors_response.headers.get('Access-Control-Allow-Headers', 'Not set')
            cors_methods = cors_response.headers.get('Access-Control-Allow-Methods', 'Not set')

            print(f"      Allow-Origin: {cors_origin}")
            print(f"      Allow-Headers: {cors_headers}")
            print(f"      Allow-Methods: {cors_methods}")

            if 'authorization' in cors_headers.lower():
                print("      ✅ Authorization header allowed by CORS")
            else:
                print("      ❌ Authorization header NOT allowed by CORS")

        except Exception as e:
            print(f"      ❌ CORS test failed: {e}")

        # 2. Test actual GET request with Authorization
        print("   🔍 GET Request with Authorization...")
        try:
            get_response = requests.get(
                url,
                headers={
                    'Authorization': test_token,
                    'Content-Type': 'application/json',
                    'Origin': 'https://app.zebra.associates'
                },
                timeout=10
            )

            print(f"      Status: {get_response.status_code}")

            response_text = get_response.text
            if "No credentials provided" in response_text:
                print("      ❌ Backend: 'No credentials provided' - Header not transmitted")
            elif "Could not validate credentials" in response_text:
                print("      ✅ Backend: Header received, token validation attempted")
            else:
                print(f"      ❓ Backend response: {response_text[:100]}...")

        except Exception as e:
            print(f"      ❌ GET request failed: {e}")

        print()

if __name__ == "__main__":
    test_cors_and_headers()