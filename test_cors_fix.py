#!/usr/bin/env python3
"""
Test CORS Fix for Frontend Feature Flag Authentication

Tests the CORS configuration fix to ensure Vercel frontend domain
can properly communicate with the backend for feature flag endpoints.
"""

import requests
import json
from datetime import datetime

def test_cors_fix():
    """Test the CORS fix for Vercel frontend domain"""
    print("🔍 TESTING CORS FIX FOR FRONTEND FEATURE FLAG AUTHENTICATION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Production backend URL
    backend_url = "https://marketedge-platform.onrender.com"

    # Matt's frontend domain
    frontend_domain = "https://frontend-36gas2bky-zebraassociates-projects.vercel.app"

    print("📊 TESTING CORS WITH VERCEL FRONTEND DOMAIN")
    print("-" * 50)
    print(f"Frontend: {frontend_domain}")
    print(f"Backend:  {backend_url}")
    print()

    # Test CORS preflight for feature flags endpoint
    print("1. Testing CORS preflight for admin feature flags...")
    try:
        headers = {
            'Origin': frontend_domain,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'authorization,content-type',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.options(
            f"{backend_url}/api/v1/admin/feature-flags",
            headers=headers,
            timeout=15
        )

        print(f"   Status: {response.status_code}")

        # Check CORS headers
        cors_origin = response.headers.get('Access-Control-Allow-Origin', 'MISSING')
        cors_methods = response.headers.get('Access-Control-Allow-Methods', 'MISSING')
        cors_headers = response.headers.get('Access-Control-Allow-Headers', 'MISSING')
        cors_credentials = response.headers.get('Access-Control-Allow-Credentials', 'MISSING')

        print(f"   Allow-Origin: {cors_origin}")
        print(f"   Allow-Methods: {cors_methods}")
        print(f"   Allow-Headers: {cors_headers}")
        print(f"   Allow-Credentials: {cors_credentials}")

        # Verify the fix
        if cors_origin == frontend_domain:
            print("   ✅ CORS ORIGIN FIX WORKING: Frontend domain allowed")
        elif cors_origin == "https://app.zebra.associates":
            print("   ⚠️  CORS FALLBACK: Using zebra.associates default")
        else:
            print(f"   ❌ CORS ISSUE: Unexpected origin response: {cors_origin}")

        if cors_credentials.lower() == 'true':
            print("   ✅ CORS CREDENTIALS: Enabled for authentication")
        else:
            print(f"   ❌ CORS CREDENTIALS: {cors_credentials} - should be 'true'")

    except Exception as e:
        print(f"   ❌ CORS preflight test failed: {e}")

    print("\n2. Testing actual GET request to feature flags (without auth)...")
    try:
        headers = {
            'Origin': frontend_domain,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(
            f"{backend_url}/api/v1/admin/feature-flags",
            headers=headers,
            timeout=15
        )

        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

        # Check CORS headers on actual response
        cors_origin = response.headers.get('Access-Control-Allow-Origin', 'MISSING')
        print(f"   Response CORS Origin: {cors_origin}")

        if response.status_code == 401:
            print("   ✅ CORRECT: Authentication required (401)")
            if cors_origin != 'MISSING':
                print("   ✅ CORS HEADERS: Present on error response")
            else:
                print("   ❌ CORS HEADERS: Missing on error response")
        else:
            print(f"   ⚠️  UNEXPECTED: Status should be 401, got {response.status_code}")

    except Exception as e:
        print(f"   ❌ GET request test failed: {e}")

    print("\n" + "=" * 70)
    print("🎯 CORS FIX VERIFICATION SUMMARY")
    print("=" * 70)

    print("\nWhat should happen next:")
    print("1. Matt.Lindop logs into frontend at:")
    print(f"   {frontend_domain}")
    print("2. Backend receives cookies with proper CORS headers")
    print("3. Feature flag admin panel loads successfully")
    print("4. Authentication works cross-domain")
    print()
    print("If CORS fix is working:")
    print("- Preflight requests return frontend domain in Allow-Origin")
    print("- Credentials are allowed (true)")
    print("- All admin API calls include proper CORS headers")
    print()
    print("If still not working, additional debugging needed:")
    print("- Check cookie domain configuration")
    print("- Verify SameSite=None with Secure=True")
    print("- Test with browser developer tools")

if __name__ == "__main__":
    test_cors_fix()