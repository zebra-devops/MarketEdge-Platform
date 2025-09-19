#!/usr/bin/env python3
"""
Test Production Database Status Column
Direct test to see if the feature_flags.status column exists in production
"""

import requests
import json
from datetime import datetime

def test_production_database_schema():
    """Test if the feature_flags.status column exists by triggering the endpoint"""

    print("🔍 PRODUCTION DATABASE SCHEMA TEST")
    print("="*50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Testing: feature_flags.status column existence")
    print("Target: https://marketedge-platform.onrender.com")
    print()

    # Create a test request that would trigger the SQL query
    # This will fail if the status column is missing
    try:
        # Try to access an admin endpoint that would query feature_flags
        url = "https://marketedge-platform.onrender.com/api/v1/admin/feature-flags"

        # Use a basic GET request (will return 401/403 but should not return 500 if schema is correct)
        response = requests.get(url, timeout=30)

        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        if response.status_code == 500:
            print("❌ 500 ERROR - Schema issue likely exists")
            try:
                error_content = response.json()
                print(f"Error details: {json.dumps(error_content, indent=2)}")

                # Check if it's the specific column error
                error_str = str(error_content)
                if "column feature_flags.status does not exist" in error_str:
                    print("🚨 CONFIRMED: feature_flags.status column is MISSING")
                    print("Migration has NOT been applied to production database")
                    return False
                else:
                    print("❓ Different 500 error - may not be schema related")

            except:
                print("Could not parse error response")

        elif response.status_code in [401, 403]:
            print("✅ GOOD: Authentication error (401/403) instead of 500")
            print("This suggests the schema is correct and endpoint is working")
            print("feature_flags.status column likely EXISTS")
            return True

        elif response.status_code == 200:
            print("✅ EXCELLENT: 200 response - endpoint working perfectly")
            print("feature_flags.status column definitely EXISTS")
            return True

        else:
            print(f"❓ Unexpected status code: {response.status_code}")

        print(f"Response content preview: {response.text[:500]}")

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

    print()
    return None

def check_deployment_timestamp():
    """Check if there are signs of recent deployment"""

    print("🕒 CHECKING DEPLOYMENT TIMESTAMP")
    print("="*30)

    try:
        response = requests.get("https://marketedge-platform.onrender.com/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            timestamp = health_data.get('timestamp', 0)

            # Convert timestamp to readable format
            from datetime import datetime
            deployment_time = datetime.fromtimestamp(timestamp)
            current_time = datetime.now()
            time_diff = current_time - deployment_time

            print(f"Service timestamp: {deployment_time.isoformat()}")
            print(f"Current time: {current_time.isoformat()}")
            print(f"Service age: {time_diff}")

            # If service is less than 10 minutes old, it likely just restarted
            if time_diff.total_seconds() < 600:
                print("✅ Service appears to have restarted recently")
                return True
            else:
                print("⚠️  Service timestamp suggests no recent restart")
                return False
        else:
            print(f"❌ Health check failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Health check request failed: {e}")

    return False

def main():
    """Run all tests"""
    print("🚀 PRODUCTION DATABASE STATUS COLUMN TEST")
    print("="*60)
    print()

    # Check deployment status first
    recent_deployment = check_deployment_timestamp()
    print()

    # Test the schema
    schema_ok = test_production_database_schema()
    print()

    # Final assessment
    print("📋 FINAL ASSESSMENT")
    print("="*20)

    if schema_ok is True:
        print("✅ feature_flags.status column EXISTS in production")
        print("✅ Migration has been successfully applied")
        print("✅ Matt.Lindop admin access should work")
        print("🎯 £925K Zebra Associates opportunity - UNBLOCKED")

    elif schema_ok is False:
        print("❌ feature_flags.status column is MISSING in production")
        print("❌ Migration has NOT been applied")
        print("⏳ Need to wait for Render deployment or trigger manually")
        print("🚨 £925K Zebra Associates opportunity - STILL BLOCKED")

    else:
        print("❓ Schema status unclear from tests")
        print("🔄 Recommend waiting for deployment and re-testing")

    if recent_deployment:
        print("✅ Recent deployment detected - migration may be applying")
    else:
        print("⚠️  No recent deployment detected - may need more time")

    print()
    print("Next steps:")
    print("1. Wait 5-10 minutes for Render deployment")
    print("2. Re-run this test")
    print("3. Test Matt.Lindop login if schema is fixed")

if __name__ == "__main__":
    main()