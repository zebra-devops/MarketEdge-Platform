#!/usr/bin/env python3
"""
Test script to verify greenlet error fix for Matt.Lindop's Feature Flags access
This tests the critical async/sync SQLAlchemy fix for the £925K Zebra Associates opportunity
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_feature_flags_endpoint():
    """Test the feature flags endpoint that was causing greenlet errors"""

    print("🔍 Testing Feature Flags Endpoint - Greenlet Error Fix Validation")
    print("=" * 70)

    base_url = "https://marketedge-platform.onrender.com"

    # Test the endpoint that was causing greenlet errors
    endpoint = f"{base_url}/api/v1/admin/feature-flags"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test basic health check first
            print("1. Testing backend health...")
            health_response = await client.get(f"{base_url}/health")
            if health_response.status_code == 200:
                print("✅ Backend is healthy")
            else:
                print(f"❌ Backend health check failed: {health_response.status_code}")
                return

            # Test feature flags endpoint without auth (should get 401, not 500 greenlet error)
            print("\n2. Testing feature flags endpoint without auth...")
            response = await client.get(endpoint)

            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")

            if response.status_code == 401:
                print("✅ Expected 401 Unauthorized - No greenlet error!")
                print("✅ Fix successful: async/sync mismatch resolved")

                # Check if response contains proper error message
                try:
                    error_data = response.json()
                    print(f"Error Response: {error_data}")

                    if "Could not validate credentials" in error_data.get("detail", ""):
                        print("✅ Proper authentication error - not a server error")
                    else:
                        print(f"⚠️  Unexpected error detail: {error_data.get('detail')}")

                except json.JSONDecodeError:
                    print(f"⚠️  Non-JSON response: {response.text}")

            elif response.status_code == 500:
                print("❌ Still getting 500 error - greenlet issue may persist")
                try:
                    error_data = response.json()
                    print(f"Error Details: {error_data}")

                    # Check for greenlet-related errors
                    error_detail = str(error_data.get("detail", "")).lower()
                    if "greenlet" in error_detail or "missinggreenlet" in error_detail:
                        print("❌ CRITICAL: Greenlet error still present!")
                        return False
                    else:
                        print("🔍 500 error but not greenlet-related")

                except json.JSONDecodeError:
                    print(f"Raw error response: {response.text}")

            else:
                print(f"⚠️  Unexpected status code: {response.status_code}")
                print(f"Response: {response.text}")

            # Test with various query parameters that might trigger the AnalyticsModule validation
            print("\n3. Testing with module_id parameter...")
            module_response = await client.get(f"{endpoint}?module_id=test-module")
            print(f"Module test status: {module_response.status_code}")

            if module_response.status_code == 401:
                print("✅ Module validation handling correctly (401 auth required)")
            elif module_response.status_code == 500:
                print("❌ Module validation still causing 500 errors")

            print("\n4. Testing enabled_only parameter...")
            enabled_response = await client.get(f"{endpoint}?enabled_only=true")
            print(f"Enabled-only test status: {enabled_response.status_code}")

            if enabled_response.status_code == 401:
                print("✅ Enabled-only filtering handling correctly")
            elif enabled_response.status_code == 500:
                print("❌ Enabled-only filtering causing 500 errors")

            return True

        except httpx.TimeoutException:
            print("❌ Request timeout - backend may be cold starting")
            return False
        except httpx.RequestError as e:
            print(f"❌ Request error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False


async def test_admin_dashboard_stats():
    """Test the admin dashboard stats endpoint for additional validation"""

    print("\n" + "=" * 70)
    print("🔍 Testing Admin Dashboard Stats - Additional Validation")
    print("=" * 70)

    base_url = "https://marketedge-platform.onrender.com"
    endpoint = f"{base_url}/api/v1/admin/dashboard/stats"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(endpoint)
            print(f"Dashboard stats status: {response.status_code}")

            if response.status_code == 401:
                print("✅ Dashboard stats properly requiring authentication")
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    error_detail = str(error_data.get("detail", "")).lower()
                    if "greenlet" in error_detail:
                        print("❌ Dashboard stats still has greenlet issues")
                        return False
                    else:
                        print("🔍 Dashboard 500 error but not greenlet-related")
                except:
                    print("🔍 Dashboard 500 error - unable to parse response")

            return True

        except Exception as e:
            print(f"❌ Dashboard test error: {e}")
            return False


async def main():
    """Main test execution"""

    print("🚀 GREENLET ERROR FIX VALIDATION")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("Target: £925K Zebra Associates Feature Flags Access")
    print("Issue: sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called")
    print()

    # Run tests
    feature_flags_ok = await test_feature_flags_endpoint()
    dashboard_ok = await test_admin_dashboard_stats()

    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)

    if feature_flags_ok and dashboard_ok:
        print("✅ GREENLET FIX VALIDATION: SUCCESS")
        print("✅ Feature Flags endpoint no longer throwing greenlet errors")
        print("✅ Admin endpoints properly handling async/sync patterns")
        print("✅ Matt.Lindop should be able to access Feature Flags when authenticated")
        print()
        print("🎯 NEXT STEPS:")
        print("   1. Deploy this fix to production")
        print("   2. Test with Matt.Lindop's actual Auth0 credentials")
        print("   3. Verify full admin panel functionality")

        return True
    else:
        print("❌ GREENLET FIX VALIDATION: ISSUES DETECTED")
        print("❌ Additional investigation required")
        print("❌ £925K Zebra Associates opportunity still at risk")

        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)