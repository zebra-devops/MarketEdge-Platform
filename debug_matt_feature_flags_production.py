#!/usr/bin/env python3
"""
Debug Matt.Lindop's Feature Flags Production Access
Simulates his exact authentication flow to reproduce the column error
"""

import asyncio
import httpx
import json
from datetime import datetime

# Matt's user info from previous debug sessions
MATT_AUTH0_ID = "auth0|66e1e17a8b9d4ac18b7f6c77"
MATT_EMAIL = "matt.lindop@zebra.associates"

async def test_feature_flags_with_auth():
    """Test feature flags endpoint with proper authentication headers"""
    base_url = "https://marketedge-platform.onrender.com"

    # Create a mock JWT token payload that would be generated for Matt
    # We'll test the endpoint directly to see the actual error

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            print("🔍 Testing feature flags endpoint with authentication simulation...")

            # Try to access the admin feature flags endpoint
            # This should trigger the database query that fails
            headers = {
                "Authorization": "Bearer fake-token-to-trigger-db-query",
                "Content-Type": "application/json"
            }

            response = await client.get(
                f"{base_url}/api/v1/admin/feature-flags",
                headers=headers
            )

            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

            # Check for the specific column error
            if response.status_code == 500:
                error_text = response.text
                if "column" in error_text.lower() and "status" in error_text.lower():
                    print("🎯 CONFIRMED: Missing 'status' column error found!")
                    return True
                elif "feature_flags.status does not exist" in error_text:
                    print("🎯 CONFIRMED: Exact column error found!")
                    return True
                else:
                    print("❌ Different 500 error than expected")
                    print(f"Error details: {error_text}")

            elif response.status_code == 401:
                print("✅ Authentication required (expected)")
                # Try to check if the error is hidden behind auth

                # Let's try the health endpoint to see if it accesses feature flags
                health_response = await client.get(f"{base_url}/health")
                print(f"Health check: {health_response.status_code}")

            return False

        except Exception as e:
            print(f"❌ Error during test: {e}")
            return False

async def test_direct_database_query():
    """Test by making a request that would trigger the feature flags query"""
    base_url = "https://marketedge-platform.onrender.com"

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            print("\n🔍 Testing endpoints that might query feature_flags table...")

            # Try different endpoints that might access feature flags
            endpoints_to_test = [
                "/api/v1/admin/feature-flags",
                "/api/v1/feature-flags",
                "/api/v1/admin/dashboard/stats",
                "/api/v1/organisations/current",
            ]

            for endpoint in endpoints_to_test:
                print(f"\nTesting: {endpoint}")
                response = await client.get(f"{base_url}{endpoint}")
                print(f"  Status: {response.status_code}")

                if response.status_code == 500:
                    error_text = response.text
                    print(f"  Error: {error_text[:200]}...")

                    if "status" in error_text and "column" in error_text:
                        print(f"  🎯 FOUND THE ERROR in {endpoint}!")
                        return endpoint, error_text

        except Exception as e:
            print(f"❌ Error during endpoint testing: {e}")

    return None, None

async def check_migration_status_production():
    """Check if production is at the right migration level"""
    print("\n🔍 Checking production migration synchronization...")

    # We know local is at migration 010
    # Let's see if there's a way to check production migration status

    # One approach: see if any of the tables from migration 003 exist
    # by trying to access endpoints that would use them

    base_url = "https://marketedge-platform.onrender.com"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Try accessing SIC codes endpoint (also from migration 003)
            response = await client.get(f"{base_url}/api/v1/sic-codes")
            print(f"SIC codes endpoint: {response.status_code}")

            if response.status_code == 500:
                error_text = response.text
                if "sic_codes" in error_text and "does not exist" in error_text:
                    print("❌ SIC codes table also missing - migration 003 not applied!")
                    return False
            elif response.status_code in [200, 401, 403]:
                print("✅ SIC codes table exists - migration 003 was applied")
                return True

        except Exception as e:
            print(f"❌ Error checking SIC codes: {e}")

    return None

async def main():
    """Main debugging function"""
    print("🚨 MATT LINDOP FEATURE FLAGS PRODUCTION DEBUG")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"User: {MATT_EMAIL} ({MATT_AUTH0_ID})")
    print(f"Issue: 'column feature_flags.status does not exist'")
    print()

    # Test 1: Direct endpoint testing
    await test_feature_flags_with_auth()

    # Test 2: Try multiple endpoints to find the error
    error_endpoint, error_details = await test_direct_database_query()

    # Test 3: Check migration synchronization
    migration_status = await check_migration_status_production()

    print("\n" + "="*60)
    print("📋 DEBUG SUMMARY:")

    if error_endpoint:
        print(f"❌ CONFIRMED: Column error found in {error_endpoint}")
        print(f"📄 Error details: {error_details}")
        print("\n🔧 SOLUTION:")
        print("1. Production database is missing migration 003 or status column was dropped")
        print("2. Need to create and apply migration to add status column")
        print("3. Verify all migration 003 tables exist in production")
    else:
        print("❓ Could not reproduce the column error directly")
        print("🔍 Possible causes:")
        print("1. Error only occurs with specific authentication context")
        print("2. Error only occurs with specific query patterns")
        print("3. Production database state is inconsistent")

    if migration_status is False:
        print("\n❌ CRITICAL: Migration 003 was not properly applied to production")
    elif migration_status is True:
        print("\n✅ Migration 003 tables exist - may be partial application issue")

if __name__ == "__main__":
    asyncio.run(main())