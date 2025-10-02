#!/usr/bin/env python3
"""
Test script to verify Auth0 refresh token fix
This script tests the authorization URL generation to ensure:
1. offline_access scope is included
2. audience parameter is NOT included
3. All required scopes are present
"""

import asyncio
from app.auth.auth0 import auth0_client
from urllib.parse import urlparse, parse_qs

def test_authorization_url():
    """Test that authorization URL is correctly configured"""
    print("Testing Auth0 Authorization URL Configuration...")
    print("=" * 80)
    
    # Generate auth URL
    auth_url = auth0_client.get_authorization_url(
        redirect_uri='http://localhost:3000/auth/callback'
    )
    
    print(f"\nGenerated URL:\n{auth_url}\n")
    
    # Parse URL
    parsed = urlparse(auth_url)
    params = parse_qs(parsed.query)
    
    # Extract parameters
    scopes = params.get('scope', [''])[0].split()
    audience = params.get('audience', [None])[0]
    
    print("URL Parameters:")
    print("-" * 80)
    print(f"Domain: {parsed.netloc}")
    print(f"Path: {parsed.path}")
    print(f"Scopes: {scopes}")
    print(f"Audience: {audience}")
    print(f"State: {params.get('state', [''])[0][:20]}...")
    print(f"Response Type: {params.get('response_type', [''])[0]}")
    print(f"Client ID: {params.get('client_id', [''])[0]}")
    
    # Validation checks
    print("\n" + "=" * 80)
    print("VALIDATION CHECKS:")
    print("-" * 80)
    
    checks = {
        "✅ openid scope present": 'openid' in scopes,
        "✅ profile scope present": 'profile' in scopes,
        "✅ email scope present": 'email' in scopes,
        "✅ offline_access scope present (CRITICAL FIX)": 'offline_access' in scopes,
        "✅ read:organization scope present": 'read:organization' in scopes,
        "✅ read:roles scope present": 'read:roles' in scopes,
        "✅ audience parameter NOT present (CRITICAL FIX)": audience is None,
        "✅ response_type is 'code'": params.get('response_type', [''])[0] == 'code',
        "✅ state parameter present": bool(params.get('state', [''])[0]),
    }
    
    all_passed = True
    for check, passed in checks.items():
        status = "PASS" if passed else "FAIL ❌"
        print(f"{status:12} {check}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL CHECKS PASSED - Auth0 configuration is correct!")
        print("\nExpected behavior:")
        print("  1. Login will redirect to Auth0 successfully")
        print("  2. After Auth0 authentication, code exchange will succeed")
        print("  3. Access token will work with /userinfo endpoint")
        print("  4. Refresh token will be returned (due to offline_access)")
        print("  5. Login will complete successfully")
    else:
        print("❌ SOME CHECKS FAILED - Review the configuration")
        print("\nPlease verify:")
        print("  1. offline_access scope is added in auth0.py")
        print("  2. audience parameter is removed from authorization URL")
    
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = test_authorization_url()
    exit(0 if success else 1)
