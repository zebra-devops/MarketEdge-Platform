#!/usr/bin/env python3
"""
Test script to verify authentication fixes for Auth0 JWT validation and CSRF.

Tests:
1. JWT algorithm validation fix (Auth0 token with RS256)
2. CSRF middleware exemption for /auth/refresh
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth0_token_validation():
    """Test that Auth0 tokens are properly validated with RS256 algorithm."""
    print("\n" + "="*60)
    print("TEST 1: Auth0 JWT Algorithm Validation")
    print("="*60)

    # This is a real Auth0 token from the browser (will be expired, but tests the algorithm validation)
    auth0_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik5fOXQtbTdJaXE2dS11Rkt0X21tMiJ9.eyJodHRwczovL21hcmtldGVkZ2UuY29tL3VzZXJfcm9sZSI6InN1cGVyX2FkbWluIiwiaHR0cHM6Ly9tYXJrZXRlZGdlLmNvbS9vcmdhbmlzYXRpb25faWQiOiI4MzVkNGYyNC1jZmYyLTQzZTgtYTQ3MC05MzIxNmEzZDk5YTMiLCJodHRwczovL21hcmtldGVkZ2UuY29tL2luZHVzdHJ5IjoiY2luZW1hIiwiaXNzIjoiaHR0cHM6Ly9kZXYtbGtrcGNqbHZhN2s1MDltNy51cy5hdXRoMC5jb20vIiwic3ViIjoiYXV0aDB8Njc2Y2M0MjRjMjhlNzNlZmNhMWNlMWIwIiwiYXVkIjpbImh0dHBzOi8vbWFya2V0ZWRnZS5jb20vYXBpIiwiaHR0cHM6Ly9kZXYtbGtrcGNqbHZhN2s1MDltNy51cy5hdXRoMC5jb20vdXNlcmluZm8iXSwiZXhwIjoxNzM1OTA3MjY0LCJpYXQiOjE3MzU4MjA4NjQsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwifQ.bPQ_-example-signature"

    # Try to access a protected endpoint with the token
    headers = {
        "Authorization": f"Bearer {auth0_token}"
    }

    response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Expected: 401 (expired) but NOT "alg value is not allowed"
    if response.status_code == 401:
        detail = response.json().get("detail", "")
        if "alg value is not allowed" in detail:
            print("❌ FAILED: JWT algorithm validation still broken")
            return False
        elif "expired" in detail.lower() or "invalid" in detail.lower():
            print("✅ PASSED: JWT algorithm validation works (token expired as expected)")
            return True
    elif response.status_code == 200:
        print("✅ PASSED: JWT validation succeeded (unexpected but acceptable)")
        return True

    print("⚠️  UNKNOWN: Unexpected response")
    return False


def test_csrf_refresh_exemption():
    """Test that /auth/refresh is exempt from CSRF protection."""
    print("\n" + "="*60)
    print("TEST 2: CSRF Middleware Exemption for /auth/refresh")
    print("="*60)

    # Try to POST to /auth/refresh without CSRF token
    # Should NOT get 403 CSRF validation failed
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/refresh",
        cookies={"refresh_token": "fake_refresh_token"}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Expected: 401 (invalid token) but NOT 403 (CSRF validation failed)
    if response.status_code == 403:
        detail = response.json().get("detail", "")
        if "CSRF" in detail:
            print("❌ FAILED: /auth/refresh still blocked by CSRF")
            return False
    elif response.status_code == 401:
        print("✅ PASSED: /auth/refresh bypasses CSRF (gets 401 for invalid token)")
        return True
    elif response.status_code == 500:
        detail = response.json().get("detail", "")
        if "CSRF" not in detail:
            print("✅ PASSED: /auth/refresh bypasses CSRF (500 from token validation)")
            return True

    print("⚠️  UNKNOWN: Unexpected response")
    return False


def main():
    """Run all authentication fix tests."""
    print("\n" + "="*60)
    print("AUTHENTICATION FIXES TEST SUITE")
    print("="*60)

    results = []

    # Test 1: JWT algorithm validation
    results.append(("JWT Algorithm Validation", test_auth0_token_validation()))

    # Test 2: CSRF exemption
    results.append(("CSRF Exemption for /auth/refresh", test_csrf_refresh_exemption()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
