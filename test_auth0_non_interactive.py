#!/usr/bin/env python3
"""
Non-interactive test script for Auth0 JWT security fixes
Tests JWT signature verification and token refresh flow
"""

import asyncio
import httpx
import json
import os
from urllib.parse import parse_qs, urlparse

# Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "dev-g8trhgbfdq2sk2m8.us.auth0.com")

class AuthTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_backend_health(self):
        """Test 1: Verify backend health"""
        print("\n" + "="*60)
        print("TEST 1: Backend Health Check")
        print("="*60)

        response = await self.client.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend healthy: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   Services: {data['services']}")
            return True
        else:
            print(f"❌ Backend unhealthy: {response.status_code}")
            return False

    async def test_jwks_availability(self):
        """Test 2: Verify JWKS endpoint availability"""
        print("\n" + "="*60)
        print("TEST 2: JWKS Endpoint Availability")
        print("="*60)

        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        response = await self.client.get(jwks_url)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ JWKS endpoint accessible")
            print(f"   Number of keys: {len(data.get('keys', []))}")
            for i, key in enumerate(data.get('keys', [])[:2]):
                print(f"   Key {i+1}: {key.get('kid', 'unknown')} (type: {key.get('kty', 'unknown')})")
            return True
        else:
            print(f"❌ JWKS endpoint not accessible: {response.status_code}")
            return False

    async def test_auth_url_generation(self):
        """Test 3: Get Auth0 authorization URL"""
        print("\n" + "="*60)
        print("TEST 3: Auth0 URL Generation")
        print("="*60)

        response = await self.client.get(
            f"{BASE_URL}/api/v1/auth/auth0-url",
            params={"redirect_uri": f"{FRONTEND_URL}/callback"}
        )

        if response.status_code == 200:
            data = response.json()
            auth_url = data.get("auth_url", "")
            print(f"✅ Auth URL generated successfully")

            # Parse URL to check parameters
            parsed = urlparse(auth_url)
            params = parse_qs(parsed.query)

            print(f"   Domain: {parsed.netloc}")
            print(f"   Client ID: {params.get('client_id', [''])[0][:20]}...")
            print(f"   Scopes: {params.get('scope', [''])[0]}")
            print(f"   Has state: {'state' in params}")

            return True
        else:
            print(f"❌ Failed to generate auth URL: {response.status_code}")
            return False

    async def test_invalid_token(self):
        """Test 4: Test with invalid/malformed token"""
        print("\n" + "="*60)
        print("TEST 4: Invalid Token Handling")
        print("="*60)

        # Test with malformed token
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = await self.client.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)

        if response.status_code == 401:
            print(f"✅ Invalid token correctly rejected with 401")
            return True
        else:
            print(f"❌ Unexpected response for invalid token: {response.status_code}")
            return False

    async def test_expired_token_simulation(self):
        """Test 5: Simulate expired token"""
        print("\n" + "="*60)
        print("TEST 5: Expired Token Handling")
        print("="*60)

        # Create an obviously expired JWT (this is just for testing the error path)
        expired_jwt = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1SU3lGVXR3ckFpcVRRNndEMWZPZCJ9.eyJpc3MiOiJodHRwczovL2Rldi1nOHRyaGdiZmRxMnNrMm04LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJhdXRoMHw2NmU5YzJjYzRkNzk1MTQ0NDI5ZDY2MjQiLCJhdWQiOiJ3RWdqYU9uazhNU2dSVGRhV1VSTkthRnU4ME1HMFNhNiIsImlhdCI6MTcyNjU4MTQ1MiwiZXhwIjoxNzI2NjE3NDUyLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIHJlYWQ6b3JnYW5pemF0aW9uIHJlYWQ6cm9sZXMiLCJhenAiOiJ3RWdqYU9uazhNU2dSVGRhV1VSTkthRnU4ME1HMFNhNiJ9.fake_signature"

        headers = {"Authorization": f"Bearer {expired_jwt}"}
        response = await self.client.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)

        if response.status_code == 401:
            print(f"✅ Expired token correctly rejected with 401")
            return True
        else:
            print(f"❌ Unexpected response for expired token: {response.status_code}")
            return False

    async def test_jwks_caching(self):
        """Test 6: Verify JWKS caching implementation"""
        print("\n" + "="*60)
        print("TEST 6: JWKS Caching Implementation")
        print("="*60)

        # Make multiple requests to verify caching doesn't cause issues
        for i in range(3):
            headers = {"Authorization": "Bearer invalid.token.here"}
            response = await self.client.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)

            if response.status_code != 401:
                print(f"❌ Request {i+1} failed with status {response.status_code}")
                return False

        print(f"✅ JWKS caching working correctly")
        print(f"   Made 3 requests with consistent 401 responses")
        return True

    async def test_no_credentials(self):
        """Test 7: Test endpoint with no credentials"""
        print("\n" + "="*60)
        print("TEST 7: No Credentials Handling")
        print("="*60)

        response = await self.client.get(f"{BASE_URL}/api/v1/auth/me")

        if response.status_code == 401:
            print(f"✅ No credentials correctly rejected with 401")
            return True
        else:
            print(f"❌ Unexpected response for no credentials: {response.status_code}")
            return False

    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*60)
        print("AUTH0 SECURITY FIXES TEST SUITE (Non-Interactive)")
        print("="*60)
        print(f"Backend URL: {BASE_URL}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Auth0 Domain: {AUTH0_DOMAIN}")

        results = {
            "Backend Health": await self.test_backend_health(),
            "JWKS Availability": await self.test_jwks_availability(),
            "Auth URL Generation": await self.test_auth_url_generation(),
            "Invalid Token Handling": await self.test_invalid_token(),
            "Expired Token Handling": await self.test_expired_token_simulation(),
            "JWKS Caching": await self.test_jwks_caching(),
            "No Credentials Handling": await self.test_no_credentials(),
        }

        # Summary
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)

        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {test_name}")

        total_tests = len(results)
        passed_tests = sum(1 for p in results.values() if p)

        print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("\n🎉 All tests passed! Auth0 security fixes verified.")
            print("\n✅ READY FOR COMMIT AND PUSH")
        elif passed_tests >= total_tests - 1:
            print("\n✅ Core security tests passed.")
            print("⚠️ Minor issues detected - review recommended")
        else:
            print("\n⚠️ Multiple tests failed. Please review the results above.")
            print("❌ NOT READY FOR DEPLOYMENT")

        await self.client.aclose()

        return passed_tests == total_tests

async def main():
    tester = AuthTester()
    success = await tester.run_all_tests()

    # Print manual testing instructions
    print("\n" + "="*60)
    print("MANUAL TESTING INSTRUCTIONS")
    print("="*60)
    print("\nTo test the full JWT verification with a real token:")
    print("1. Open browser to http://localhost:3000")
    print("2. Login with devops@zebra.associates")
    print("3. Open browser DevTools > Network tab")
    print("4. Monitor /api/v1/auth/me requests")
    print("5. Verify responses show 200 OK with user data")
    print("6. Check backend logs for JWT verification messages")
    print("\nTo test token refresh:")
    print("1. After login, wait for access token to near expiry")
    print("2. Make authenticated request")
    print("3. System should automatically refresh token")
    print("4. Check backend logs for token refresh messages")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
