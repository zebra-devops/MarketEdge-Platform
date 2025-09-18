#!/usr/bin/env python
"""
Production Super Admin Access Verification
Tests that Matt Lindop can access Feature Flags after role promotion
"""

import requests
import json
from datetime import datetime
import sys

# Production API endpoints
PRODUCTION_API = "https://marketedge-platform.onrender.com"
FEATURE_FLAGS_ENDPOINT = f"{PRODUCTION_API}/api/v1/admin/feature-flags"
ADMIN_STATS_ENDPOINT = f"{PRODUCTION_API}/api/v1/admin/dashboard/stats"
HEALTH_ENDPOINT = f"{PRODUCTION_API}/health"

def test_health_check():
    """Verify production API is responding"""
    print("\n1️⃣  Testing Production Health Check...")
    print("=" * 60)

    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        if response.status_code == 200:
            print(f"✅ Production API is healthy: {response.json()}")
            return True
        else:
            print(f"⚠️  Health check returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_feature_flags_access(token=None):
    """Test Feature Flags endpoint access"""
    print("\n2️⃣  Testing Feature Flags Access...")
    print("=" * 60)

    if not token:
        print("⚠️  No token provided. To test authenticated access:")
        print("   1. Have Matt Lindop log in to the application")
        print("   2. Get the access token from browser DevTools")
        print("   3. Run: python verify_production_super_admin_access.py <token>")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(FEATURE_FLAGS_ENDPOINT, headers=headers, timeout=10)

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ SUCCESS! Feature Flags accessible with super_admin role")
            data = response.json()
            print(f"   Features returned: {len(data.get('features', []))}")

            # Show sample of features
            if data.get('features'):
                print("\n   Sample features:")
                for feature in data['features'][:3]:
                    print(f"   - {feature.get('name')}: {feature.get('enabled')}")
            return True

        elif response.status_code == 403:
            print("❌ FAILED: 403 Forbidden - Still insufficient permissions")
            print("   Likely cause: Token still has 'admin' role, not 'super_admin'")
            print("   Solution: Have Matt log out and log back in to refresh token")
            return False

        elif response.status_code == 500:
            error_detail = response.json().get('detail', 'Unknown error')
            if "Super admin role required" in error_detail:
                print("❌ FAILED: Super admin role still not applied in production")
                print("   The database update may not have been executed yet")
            else:
                print(f"❌ FAILED: 500 error - {error_detail}")
            return False

        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            print(f"   Body: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("⚠️  Request timed out (Render cold start may be occurring)")
        print("   Try again in 60 seconds")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_admin_dashboard_access(token=None):
    """Test Admin Dashboard Stats access"""
    print("\n3️⃣  Testing Admin Dashboard Access...")
    print("=" * 60)

    if not token:
        print("⚠️  Skipping authenticated test (no token provided)")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(ADMIN_STATS_ENDPOINT, headers=headers, timeout=10)

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ SUCCESS! Admin Dashboard accessible")
            data = response.json()
            if 'total_users' in data:
                print(f"   Total Users: {data['total_users']}")
                print(f"   Total Organizations: {data.get('total_organizations', 'N/A')}")
            return True
        else:
            print(f"❌ Admin Dashboard returned {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def decode_jwt_payload(token):
    """Decode JWT to check role claim"""
    try:
        # JWT is three base64 parts separated by dots
        parts = token.split('.')
        if len(parts) != 3:
            return None

        # Decode the payload (second part)
        import base64
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.b64decode(payload)
        return json.loads(decoded)
    except:
        return None

def main():
    """Main verification flow"""
    print("\n🔍 PRODUCTION SUPER ADMIN ACCESS VERIFICATION")
    print("=" * 80)
    print("Purpose: Verify Matt Lindop can access Feature Flags after promotion")
    print("=" * 80)

    # Get token from command line if provided
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print(f"\n📌 Using provided access token")

        # Try to decode token to check role
        payload = decode_jwt_payload(token)
        if payload:
            print(f"   Token User: {payload.get('email', 'Unknown')}")
            print(f"   Token Role: {payload.get('role', 'Unknown')}")
            if payload.get('role') != 'super_admin':
                print("   ⚠️  Token still has old role - user needs to re-authenticate")

    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': []
    }

    # Test 1: Health check
    health_ok = test_health_check()
    results['tests'].append({
        'name': 'health_check',
        'passed': health_ok
    })

    if not health_ok:
        print("\n❌ Production API not responding. Cannot continue tests.")
        return

    # Test 2: Feature Flags access
    feature_flags_ok = test_feature_flags_access(token)
    results['tests'].append({
        'name': 'feature_flags_access',
        'passed': feature_flags_ok
    })

    # Test 3: Admin Dashboard access
    if token:
        admin_dash_ok = test_admin_dashboard_access(token)
        results['tests'].append({
            'name': 'admin_dashboard_access',
            'passed': admin_dash_ok
        })

    # Summary
    print("\n" + "=" * 80)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 80)

    all_passed = all(test['passed'] for test in results['tests'])

    if all_passed and token:
        print("✅ ALL TESTS PASSED!")
        print("✅ Matt Lindop has full super_admin access in production")
        print("✅ £925K Zebra Associates opportunity is UNBLOCKED")
    elif not token:
        print("⚠️  Limited testing without authentication token")
        print("\nTo complete verification:")
        print("1. Execute: python production_super_admin_promotion.py")
        print("2. Have Matt Lindop log out and log back in")
        print("3. Get the new access token from browser")
        print("4. Run: python verify_production_super_admin_access.py <token>")
    else:
        print("❌ Some tests failed. Please check:")
        print("1. Was the database update executed?")
        print("2. Did Matt log out and back in to get new token?")
        print("3. Is the production API responding correctly?")

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"production_verification_results_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Results saved to: {filename}")

if __name__ == "__main__":
    main()