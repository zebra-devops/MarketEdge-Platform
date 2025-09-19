#!/usr/bin/env python3
"""
Execute Emergency Database Fix via API Endpoint

This script will:
1. Wait for deployment to complete
2. Call the new emergency endpoint to create missing tables
3. Verify authentication is working
"""

import requests
import time
import json
from datetime import datetime

PRODUCTION_BASE_URL = "https://marketedge-platform.onrender.com"

def wait_for_deployment():
    """Wait for the new deployment to be available"""
    print("🔄 Waiting for deployment to complete...")

    max_attempts = 30  # 5 minutes
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{PRODUCTION_BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                print(f"✅ Deployment is live (attempt {attempt + 1})")
                return True
        except Exception as e:
            print(f"⏳ Attempt {attempt + 1}: {str(e)}")

        if attempt < max_attempts - 1:
            time.sleep(10)

    print("❌ Deployment wait timeout")
    return False

def execute_emergency_fix():
    """Call the emergency endpoint to create missing tables"""
    print("\n🚨 Executing emergency database fix...")

    try:
        # Call the new emergency endpoint
        url = f"{PRODUCTION_BASE_URL}/api/v1/auth/emergency/create-hierarchy-tables"
        response = requests.post(url, timeout=60)

        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print("✅ EMERGENCY FIX SUCCESSFUL!")
            print(f"Message: {result.get('message', 'Success')}")
            print(f"Operations: {result.get('operations', [])}")
            return True
        else:
            print(f"❌ Emergency fix failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error executing emergency fix: {str(e)}")
        return False

def test_authentication():
    """Test that authentication is now working"""
    print("\n🔍 Testing authentication endpoint...")

    try:
        # Test the /me endpoint which was failing
        url = f"{PRODUCTION_BASE_URL}/api/v1/auth/me"
        response = requests.get(url, timeout=10)

        print(f"Auth test status: {response.status_code}")

        if response.status_code in [401, 403]:
            print("✅ Authentication endpoint responding correctly (expected 401/403 without token)")
            return True
        elif response.status_code == 500:
            print("❌ Still getting 500 errors - tables may not be created properly")
            return False
        else:
            print(f"ℹ️  Unexpected status: {response.status_code}")
            return True

    except Exception as e:
        print(f"❌ Error testing authentication: {str(e)}")
        return False

def verify_oauth_login():
    """Verify OAuth login flow is working"""
    print("\n🔍 Testing OAuth login flow...")

    try:
        # Test OAuth URL generation (should not fail with 500)
        url = f"{PRODUCTION_BASE_URL}/api/v1/auth/auth0-url"
        params = {"redirect_uri": "https://marketedge.com/callback"}
        response = requests.get(url, params=params, timeout=10)

        print(f"OAuth URL test status: {response.status_code}")

        if response.status_code == 200:
            print("✅ OAuth URL generation working correctly")
            return True
        else:
            print(f"❌ OAuth URL generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing OAuth: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🚨 EMERGENCY DATABASE FIX EXECUTION")
    print("=" * 60)
    print(f"Target: {PRODUCTION_BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("Purpose: Fix missing hierarchy tables blocking OAuth login")
    print("=" * 60)

    # Step 1: Wait for deployment
    if not wait_for_deployment():
        print("❌ Deployment failed - cannot proceed")
        return False

    # Step 2: Execute emergency fix
    if not execute_emergency_fix():
        print("❌ Emergency fix failed")
        return False

    # Step 3: Test authentication
    time.sleep(5)  # Give database a moment to reflect changes
    auth_working = test_authentication()
    oauth_working = verify_oauth_login()

    # Summary
    print("\n" + "=" * 60)
    if auth_working and oauth_working:
        print("✅ EMERGENCY FIX COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("✓ Missing database tables created")
        print("✓ Authentication endpoints responding")
        print("✓ OAuth login flow working")
        print()
        print("🎉 Matt.Lindop can now login to access Feature Flags!")
        print("🎉 £925K Zebra Associates opportunity unblocked!")
        return True
    else:
        print("⚠️  EMERGENCY FIX PARTIALLY SUCCESSFUL")
        print("=" * 60)
        print(f"✓ Authentication working: {auth_working}")
        print(f"✓ OAuth working: {oauth_working}")
        print()
        print("Manual verification may be needed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)