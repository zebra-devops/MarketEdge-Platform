#!/usr/bin/env python3
"""
CRITICAL: Feature Flag Authentication Transmission Diagnostic

This script diagnoses why authentication headers aren't reaching the backend
for the /admin/feature-flags endpoint while other admin endpoints work.

For the £925K Zebra Associates opportunity - Matt.Lindop needs feature flag access.
"""

import requests
import os
import json
from datetime import datetime
import sys

# Configuration
API_BASE = "https://marketedge-platform.onrender.com/api/v1"
FEATURE_FLAGS_ENDPOINT = f"{API_BASE}/admin/feature-flags"
OTHER_ADMIN_ENDPOINT = f"{API_BASE}/admin/dashboard/stats"

def get_test_token():
    """Get a test token from environment or prompt user"""
    token = os.getenv('TEST_ACCESS_TOKEN')
    if not token:
        print("❌ No TEST_ACCESS_TOKEN environment variable found")
        print("Please set TEST_ACCESS_TOKEN with Matt.Lindop's access token")
        print("or provide it when prompted.")
        token = input("Enter access token: ").strip()
    return token

def test_cors_preflight(url, token):
    """Test CORS preflight for the endpoint"""
    print(f"\n🔍 Testing CORS preflight for: {url}")

    headers = {
        'Origin': 'https://app.zebra.associates',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'authorization,content-type'
    }

    try:
        response = requests.options(url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")

        # Check CORS headers
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        cors_methods = response.headers.get('Access-Control-Allow-Methods')
        cors_headers = response.headers.get('Access-Control-Allow-Headers')

        print(f"   CORS Origin: {cors_origin}")
        print(f"   CORS Methods: {cors_methods}")
        print(f"   CORS Headers: {cors_headers}")

        if 'authorization' not in (cors_headers or '').lower():
            print("   ❌ Authorization header not in CORS allowed headers!")
            return False
        else:
            print("   ✅ Authorization header allowed by CORS")
            return True

    except Exception as e:
        print(f"   ❌ CORS preflight failed: {e}")
        return False

def test_direct_request(url, token, endpoint_name):
    """Test direct GET request to endpoint"""
    print(f"\n🔍 Testing direct {endpoint_name} request: {url}")

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Origin': 'https://app.zebra.associates'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            print(f"   ✅ {endpoint_name} request successful")
            return True
        elif response.status_code == 401:
            print(f"   ❌ {endpoint_name} authentication failed")
            print(f"   Response: {response.text[:200]}")
            return False
        elif response.status_code == 403:
            print(f"   ❌ {endpoint_name} access denied")
            print(f"   Response: {response.text[:200]}")
            return False
        else:
            print(f"   ❌ {endpoint_name} unexpected status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ {endpoint_name} request failed: {e}")
        return False

def test_header_transmission(url, token, endpoint_name):
    """Test if Authorization header is being transmitted"""
    print(f"\n🔍 Testing header transmission for {endpoint_name}")

    # Test with detailed headers to see what gets through
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Origin': 'https://app.zebra.associates',
        'Referer': 'https://app.zebra.associates/admin',
        'User-Agent': 'MarketEdge-Debug/1.0'
    }

    print(f"   Sending headers: {list(headers.keys())}")
    print(f"   Token preview: {token[:20]}...")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   Response status: {response.status_code}")

        # Look for specific backend authentication messages
        response_text = response.text
        if "No credentials provided" in response_text:
            print("   ❌ Backend reports 'No credentials provided'")
            print("   🔍 This means Authorization header didn't reach the backend")
            return False
        elif "Could not validate credentials" in response_text:
            print("   ⚠️  Backend received Authorization header but token validation failed")
            print("   🔍 Header transmission is working, token issue")
            return True
        elif response.status_code == 200:
            print("   ✅ Full success - header transmitted and token validated")
            return True
        else:
            print(f"   ❓ Unexpected response: {response_text[:200]}")
            return None

    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

def main():
    print("🔍 FEATURE FLAG AUTHENTICATION TRANSMISSION DIAGNOSTIC")
    print("=" * 60)
    print(f"Diagnostic Time: {datetime.now().isoformat()}")
    print(f"Target: {FEATURE_FLAGS_ENDPOINT}")
    print()

    # Get test token
    token = get_test_token()
    if not token:
        print("❌ Cannot proceed without access token")
        sys.exit(1)

    print(f"✅ Using token: {token[:20]}...")

    # Test results
    results = {}

    # 1. Test CORS preflight for feature flags
    results['feature_flags_cors'] = test_cors_preflight(FEATURE_FLAGS_ENDPOINT, token)

    # 2. Test CORS preflight for other admin endpoint
    results['other_admin_cors'] = test_cors_preflight(OTHER_ADMIN_ENDPOINT, token)

    # 3. Test direct feature flags request
    results['feature_flags_direct'] = test_direct_request(FEATURE_FLAGS_ENDPOINT, token, "Feature Flags")

    # 4. Test direct other admin request
    results['other_admin_direct'] = test_direct_request(OTHER_ADMIN_ENDPOINT, token, "Admin Stats")

    # 5. Test header transmission for feature flags
    results['feature_flags_headers'] = test_header_transmission(FEATURE_FLAGS_ENDPOINT, token, "Feature Flags")

    # 6. Test header transmission for other admin endpoint
    results['other_admin_headers'] = test_header_transmission(OTHER_ADMIN_ENDPOINT, token, "Admin Stats")

    # Analysis
    print("\n📊 DIAGNOSTIC RESULTS")
    print("=" * 40)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL" if result is False else "❓ UNKNOWN"
        print(f"{test_name}: {status}")

    print("\n🎯 ANALYSIS")
    print("=" * 20)

    if results['feature_flags_headers'] is False and results['other_admin_headers'] is True:
        print("❌ CRITICAL: Feature flags endpoint not receiving Authorization headers")
        print("✅ Other admin endpoints receiving headers correctly")
        print("🔍 ROOT CAUSE: Endpoint-specific header transmission issue")
        print()
        print("📋 RECOMMENDED ACTIONS:")
        print("1. Check backend middleware order for /admin/feature-flags route")
        print("2. Verify CORS configuration allows Authorization header")
        print("3. Check for endpoint-specific middleware that strips headers")
        print("4. Compare working admin endpoint middleware vs feature flags")

    elif results['feature_flags_headers'] is True and results['feature_flags_direct'] is False:
        print("✅ Headers reaching backend correctly")
        print("❌ Token validation failing")
        print("🔍 ROOT CAUSE: Token validation issue, not header transmission")
        print()
        print("📋 RECOMMENDED ACTIONS:")
        print("1. Check Matt.Lindop's token format (internal JWT vs Auth0)")
        print("2. Verify Auth0 token verification is working")
        print("3. Check user role and permissions")

    elif not any(results.values()):
        print("❌ CRITICAL: Complete authentication failure")
        print("🔍 ROOT CAUSE: Systemic authentication issue")
        print()
        print("📋 RECOMMENDED ACTIONS:")
        print("1. Check backend service status")
        print("2. Verify token is valid and not expired")
        print("3. Check network connectivity")

    else:
        print("✅ Mixed results - need manual analysis")
        print("🔍 Check individual test results above")

    print(f"\n🏁 Diagnostic completed at {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()