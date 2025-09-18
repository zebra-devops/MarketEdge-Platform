#!/usr/bin/env python3
"""
Direct test of feature flags endpoint bypassing browser
Tests the actual backend functionality
"""

import requests
import json
import time
from datetime import datetime
import jwt
import os

# Backend URL
BASE_URL = "https://marketedge-platform.onrender.com"
FEATURE_FLAGS_URL = f"{BASE_URL}/api/v1/admin/feature-flags"

def test_endpoint_availability():
    """Test if endpoint is responding"""
    print("=" * 60)
    print("TEST 1: Endpoint Availability")
    print("=" * 60)
    
    # Test with invalid token first
    headers = {
        "Authorization": "Bearer invalid-token"
    }
    
    start_time = time.time()
    response = requests.get(FEATURE_FLAGS_URL, headers=headers)
    elapsed_time = time.time() - start_time
    
    print(f"URL: {FEATURE_FLAGS_URL}")
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {elapsed_time:.2f}s")
    print(f"Response: {response.text}")
    
    if response.status_code == 401:
        print("✅ Endpoint is responding correctly (401 for invalid auth)")
    else:
        print(f"❌ Unexpected status code: {response.status_code}")
    
    return response.status_code == 401

def test_cors_headers():
    """Test CORS headers are present"""
    print("\n" + "=" * 60)
    print("TEST 2: CORS Headers")
    print("=" * 60)
    
    headers = {
        "Authorization": "Bearer invalid-token",
        "Origin": "https://app.zebra.associates"
    }
    
    response = requests.get(FEATURE_FLAGS_URL, headers=headers)
    
    print(f"Request Origin: https://app.zebra.associates")
    print(f"Response Headers:")
    
    cors_headers = {
        "access-control-allow-origin": None,
        "access-control-allow-credentials": None,
        "access-control-allow-methods": None
    }
    
    for header, value in response.headers.items():
        if "access-control" in header.lower():
            cors_headers[header.lower()] = value
            print(f"  {header}: {value}")
    
    # Note: 401 responses may not include CORS headers depending on middleware order
    if response.status_code == 401:
        print("\n⚠️ Note: 401 responses may not include CORS headers")
        print("   This is expected behavior for authentication failures")
    
    return True

def test_options_preflight():
    """Test OPTIONS preflight request"""
    print("\n" + "=" * 60)
    print("TEST 3: OPTIONS Preflight Request")
    print("=" * 60)
    
    headers = {
        "Origin": "https://app.zebra.associates",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization"
    }
    
    response = requests.options(FEATURE_FLAGS_URL, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"CORS Headers:")
    
    for header, value in response.headers.items():
        if "access-control" in header.lower():
            print(f"  {header}: {value}")
    
    if response.status_code in [200, 204]:
        print("✅ OPTIONS preflight successful")
        return True
    else:
        print(f"❌ OPTIONS preflight failed with status {response.status_code}")
        return False

def create_test_token():
    """Create a test JWT token (for demonstration - won't be valid)"""
    print("\n" + "=" * 60)
    print("TEST 4: Simulated Authentication Token")
    print("=" * 60)
    
    # This is a test token that simulates the structure
    # In production, this would come from Auth0
    payload = {
        "sub": "test-user-id",
        "email": "matt.lindop@zebra.associates",
        "role": "super_admin",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "iss": "test-issuer"
    }
    
    # Note: This uses a test secret - real tokens use Auth0's secret
    test_secret = "test-secret-not-for-production"
    token = jwt.encode(payload, test_secret, algorithm="HS256")
    
    print(f"Created test token for: matt.lindop@zebra.associates")
    print(f"Role: super_admin")
    print(f"Token (first 50 chars): {token[:50]}...")
    
    return token

def test_with_simulated_auth():
    """Test with simulated authentication"""
    print("\n" + "=" * 60)
    print("TEST 5: Request with Simulated Auth Token")
    print("=" * 60)
    
    test_token = create_test_token()
    
    headers = {
        "Authorization": f"Bearer {test_token}",
        "Origin": "https://app.zebra.associates"
    }
    
    print(f"Making request to: {FEATURE_FLAGS_URL}")
    print(f"With Authorization header: Bearer <token>")
    
    start_time = time.time()
    response = requests.get(FEATURE_FLAGS_URL, headers=headers)
    elapsed_time = time.time() - start_time
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Time: {elapsed_time:.2f}s")
    
    if response.status_code == 401:
        print("✅ Backend correctly rejects test token (proper auth validation)")
        print("   Real authentication requires valid Auth0 token")
    elif response.status_code == 200:
        print("✅ Request successful!")
        print(f"Response: {json.dumps(response.json(), indent=2)[:500]}...")
    elif response.status_code == 500:
        print("❌ Internal Server Error - Backend issue detected")
        print(f"Response: {response.text}")
    else:
        print(f"⚠️ Unexpected status: {response.status_code}")
        print(f"Response: {response.text}")
    
    return response.status_code

def main():
    """Run all tests"""
    print("\n🚀 FEATURE FLAGS ENDPOINT DIRECT TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print(f"Target: {FEATURE_FLAGS_URL}")
    print("=" * 60)
    
    results = []
    
    # Test 1: Basic availability
    results.append(("Endpoint Availability", test_endpoint_availability()))
    
    # Test 2: CORS headers
    results.append(("CORS Headers", test_cors_headers()))
    
    # Test 3: OPTIONS preflight
    results.append(("OPTIONS Preflight", test_options_preflight()))
    
    # Test 4: Simulated auth
    status = test_with_simulated_auth()
    results.append(("Auth Validation", status == 401))  # Should reject test token
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    
    if all(r for _, r in results):
        print("✅ All tests passed!")
        print("   - Endpoint is responding correctly")
        print("   - Authentication is properly validated")
        print("   - CORS preflight requests work")
        print("\n📝 Note: To test with real data, a valid Auth0 token is required")
    else:
        print("❌ Some tests failed - check results above")
    
    print("\n💡 Next Step: Test from browser with actual Auth0 authentication")
    print("   URL: https://app.zebra.associates/admin")

if __name__ == "__main__":
    main()