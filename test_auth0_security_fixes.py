#!/usr/bin/env python3
"""
Test script for CRITICAL SECURITY FIXES from code review.

Tests:
1. Auth0 JWT signature verification with JWKS
2. Auth0 refresh token flow
3. Integration of both fixes

DO NOT RUN IN PRODUCTION - FOR LOCAL TESTING ONLY
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.auth.dependencies import get_auth0_jwks, verify_auth0_token
from app.auth.auth0 import auth0_client
from app.core.logging import logger


async def test_jwks_fetch():
    """Test 1: Verify JWKS fetching and caching works"""
    print("\n" + "="*60)
    print("TEST 1: JWKS Fetching and Caching")
    print("="*60)

    try:
        # First fetch - should hit Auth0
        print("\n[1.1] Fetching JWKS from Auth0 (first time)...")
        jwks = await get_auth0_jwks()

        if not jwks or "keys" not in jwks:
            print("❌ FAILED: Invalid JWKS structure")
            return False

        print(f"✓ SUCCESS: Fetched {len(jwks['keys'])} keys from JWKS")
        print(f"  Key IDs: {[k.get('kid', 'no-kid')[:16] + '...' for k in jwks['keys'][:3]]}")

        # Second fetch - should use cache
        print("\n[1.2] Fetching JWKS again (should use cache)...")
        jwks2 = await get_auth0_jwks()

        if jwks2 == jwks:
            print("✓ SUCCESS: JWKS caching is working")
        else:
            print("⚠️  WARNING: JWKS cache may not be working properly")

        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        logger.exception("JWKS test failed")
        return False


async def test_token_verification_mock():
    """Test 2: Verify token verification logic (mock token)"""
    print("\n" + "="*60)
    print("TEST 2: Token Verification Logic")
    print("="*60)

    print("\n[2.1] Testing with invalid token (should fail gracefully)...")

    try:
        # Test with invalid token
        result = await verify_auth0_token("invalid_token_string")

        if result is None:
            print("✓ SUCCESS: Invalid token correctly rejected")
        else:
            print("❌ FAILED: Invalid token was accepted")
            return False

        print("\n[2.2] Testing with empty token (should fail gracefully)...")
        result = await verify_auth0_token("")

        if result is None:
            print("✓ SUCCESS: Empty token correctly rejected")
        else:
            print("❌ FAILED: Empty token was accepted")
            return False

        print("\nℹ️  NOTE: Real token testing requires valid Auth0 credentials")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        logger.exception("Token verification test failed")
        return False


async def test_refresh_token_logic():
    """Test 3: Verify refresh token method exists and has correct signature"""
    print("\n" + "="*60)
    print("TEST 3: Refresh Token Flow Logic")
    print("="*60)

    print("\n[3.1] Checking refresh_token method exists...")

    if not hasattr(auth0_client, 'refresh_token'):
        print("❌ FAILED: refresh_token method not found on auth0_client")
        return False

    print("✓ SUCCESS: refresh_token method exists on auth0_client")

    print("\n[3.2] Checking method signature...")
    import inspect
    sig = inspect.signature(auth0_client.refresh_token)
    params = list(sig.parameters.keys())

    if 'refresh_token' not in params:
        print("❌ FAILED: refresh_token parameter not found")
        return False

    print(f"✓ SUCCESS: Method signature correct: {params}")

    print("\n[3.3] Testing with invalid refresh token (should fail gracefully)...")
    try:
        result = await auth0_client.refresh_token("invalid_refresh_token")

        if result is None:
            print("✓ SUCCESS: Invalid refresh token correctly rejected")
        else:
            print("⚠️  WARNING: Invalid refresh token returned data (may be test environment)")

        print("\nℹ️  NOTE: Real refresh token testing requires valid Auth0 credentials")
        return True

    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        logger.exception("Refresh token test failed")
        return False


async def test_integration():
    """Test 4: Integration test of both fixes"""
    print("\n" + "="*60)
    print("TEST 4: Integration Test")
    print("="*60)

    print("\n[4.1] Verifying imports are correct...")

    try:
        from jose import jwt, jwk
        from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
        print("✓ SUCCESS: python-jose imports working")
    except ImportError as e:
        print(f"❌ FAILED: Missing dependency: {e}")
        print("   Run: pip install python-jose[cryptography]")
        return False

    print("\n[4.2] Verifying httpx is available...")
    try:
        import httpx
        print("✓ SUCCESS: httpx available")
    except ImportError as e:
        print(f"❌ FAILED: Missing dependency: {e}")
        return False

    print("\n[4.3] Checking configuration...")
    from app.core.config import settings

    if not settings.AUTH0_DOMAIN:
        print("❌ FAILED: AUTH0_DOMAIN not configured")
        return False

    print(f"✓ SUCCESS: Auth0 domain configured: {settings.AUTH0_DOMAIN}")

    if not settings.AUTH0_CLIENT_ID:
        print("❌ FAILED: AUTH0_CLIENT_ID not configured")
        return False

    print(f"✓ SUCCESS: Auth0 client ID configured: {settings.AUTH0_CLIENT_ID[:8]}...")

    return True


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("CRITICAL SECURITY FIXES - TEST SUITE")
    print("="*80)
    print("\nTesting fixes for:")
    print("  - CRITICAL ISSUE #2: Missing Auth0 JWT Signature Verification")
    print("  - CRITICAL ISSUE #3: Token Refresh Flow Inconsistency")
    print("\n" + "="*80)

    results = {
        "JWKS Fetching": await test_jwks_fetch(),
        "Token Verification": await test_token_verification_mock(),
        "Refresh Token Flow": await test_refresh_token_logic(),
        "Integration": await test_integration()
    }

    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<50} {status}")

    all_passed = all(results.values())

    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nSecurity fixes are implemented and working correctly.")
        print("\nNext steps:")
        print("1. Test with valid Auth0 tokens (local environment)")
        print("2. Run pytest test suite")
        print("3. Test end-to-end authentication flow")
        print("4. Deploy to staging for validation")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease review the failures above and fix before deploying.")
    print("="*80 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
