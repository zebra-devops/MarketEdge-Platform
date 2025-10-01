#!/usr/bin/env python3
"""
Debug script to diagnose application access issues
"""

import requests
import json
import sys

def test_auth_and_user_data():
    """Test the authentication and user data flow"""
    base_url = "http://localhost:8000"

    print("🔍 DEBUGGING APPLICATION ACCESS FLOW")
    print("=" * 50)

    # Test 1: Check if backend is responding
    try:
        health_response = requests.get(f"{base_url}/health")
        print(f"✅ Backend Health: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Backend Health: {e}")
        return

    # Test 2: Check auth endpoints
    try:
        auth_url_response = requests.get(f"{base_url}/api/v1/auth/auth0-url?redirect_uri=http://localhost:3000/callback")
        print(f"✅ Auth URL endpoint: {auth_url_response.status_code}")
    except Exception as e:
        print(f"❌ Auth URL endpoint: {e}")

    # Test 3: Check user endpoints (these will fail without auth but should return 401/403)
    try:
        users_response = requests.get(f"{base_url}/api/v1/admin/users")
        print(f"📊 Users endpoint status: {users_response.status_code}")
        print(f"📊 Users response: {users_response.text[:200]}")
    except Exception as e:
        print(f"❌ Users endpoint: {e}")

    # Test 4: Check if any users endpoint works
    endpoints_to_test = [
        "/api/v1/admin/users",
        "/api/v1/users",
        "/api/v1/organisations/users",
        "/api/v1/current-user"
    ]

    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"📊 {endpoint}: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

if __name__ == "__main__":
    test_auth_and_user_data()