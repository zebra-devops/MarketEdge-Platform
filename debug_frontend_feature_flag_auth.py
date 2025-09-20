#!/usr/bin/env python3
"""
Frontend Feature Flag Authentication Debugger

Analyzes the frontend authentication flow for admin feature flag endpoints
to identify why authentication headers are missing in production.
"""

import requests
import json
from datetime import datetime

def test_auth_flow():
    """Test the authentication flow for feature flags"""
    print("🔍 FRONTEND FEATURE FLAG AUTHENTICATION DEBUGGER")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Production backend URL
    backend_url = "https://marketedge-platform.onrender.com"

    print("📊 TESTING AUTHENTICATION ENDPOINTS")
    print("-" * 40)

    # Test 1: Health endpoint (no auth required)
    print("1. Testing health endpoint (no auth)...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        print(f"   ✅ Health: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Health failed: {e}")

    # Test 2: Feature flags endpoint without auth
    print("\n2. Testing feature flags without auth...")
    try:
        response = requests.get(f"{backend_url}/api/v1/admin/feature-flags", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

        if response.status_code == 401:
            print("   ✅ CORRECT: Properly rejecting unauthenticated requests")
        elif response.status_code == 403:
            print("   ✅ CORRECT: Properly rejecting unauthorized requests")
        else:
            print("   ⚠️  UNEXPECTED: Should reject without auth")

    except Exception as e:
        print(f"   ❌ Feature flags test failed: {e}")

    # Test 3: CORS preflight
    print("\n3. Testing CORS preflight...")
    try:
        headers = {
            'Origin': 'https://frontend-36gas2bky-zebraassociates-projects.vercel.app',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'authorization,content-type'
        }
        response = requests.options(f"{backend_url}/api/v1/admin/feature-flags",
                                  headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   CORS Headers: {dict(response.headers)}")

        cors_headers = response.headers.get('Access-Control-Allow-Origin', 'MISSING')
        print(f"   Allow-Origin: {cors_headers}")

    except Exception as e:
        print(f"   ❌ CORS test failed: {e}")

    print("\n" + "=" * 60)
    print("🎯 FRONTEND-SPECIFIC ISSUES TO CHECK")
    print("=" * 60)

    issues = [
        "1. Cookie domain mismatch:",
        "   - Backend: marketedge-platform.onrender.com",
        "   - Frontend: frontend-36gas2bky-zebraassociates-projects.vercel.app",
        "   - Cookies may not be sent cross-domain",
        "",
        "2. Token timing issues:",
        "   - FeatureFlagManager loads before auth completes",
        "   - Temporary token not persisting correctly",
        "   - Session storage backup not working",
        "",
        "3. Production environment detection:",
        "   - detectProductionEnvironment() may be failing",
        "   - Wrong storage strategy being used",
        "",
        "4. httpOnly cookie configuration:",
        "   - Access tokens should be httpOnly: false",
        "   - Backend might be setting httpOnly: true",
        "",
        "5. CORS credentials configuration:",
        "   - withCredentials must be true for cookies",
        "   - CORS allow-credentials must be set"
    ]

    for issue in issues:
        print(issue)

    print("\n" + "=" * 60)
    print("🛠️  RECOMMENDED FIXES")
    print("=" * 60)

    fixes = [
        "1. Add authentication state debugging to FeatureFlagManager",
        "2. Implement retry logic for failed feature flag requests",
        "3. Add cookie domain verification for production",
        "4. Check CORS configuration for credentials",
        "5. Verify backend access token cookie settings",
        "6. Test token persistence across navigation"
    ]

    for fix in fixes:
        print(fix)

    print("\n✅ Diagnostic complete - check authentication configuration")

if __name__ == "__main__":
    test_auth_flow()