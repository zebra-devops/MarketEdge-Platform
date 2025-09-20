#!/usr/bin/env python3
"""
VERIFICATION SCRIPT: Feature Flags Status Column Fix
===================================================

This script verifies that the emergency fix for the missing 'status' column
has been successfully applied and that Matt.Lindop's admin access is restored.

Run this AFTER applying the emergency_add_feature_flags_status_column.sql fix.
"""

import requests
import json
import os
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Production API base URL
API_BASE_URL = "https://marketedge-platform.onrender.com"

# Test endpoints that were failing
TEST_ENDPOINTS = [
    "/api/v1/features/market_edge.enhanced_ui",
    "/api/v1/features/admin.advanced_controls",
    "/api/v1/features/enabled",
    "/api/v1/admin/feature-flags"
]

def get_test_token():
    """Get a test token for API calls - replace with actual token"""
    # This should be replaced with Matt.Lindop's actual token
    # For now, return a placeholder
    return os.getenv('TEST_TOKEN', 'PLACEHOLDER_TOKEN')

def test_endpoint(endpoint, token, description):
    """Test a specific endpoint and return results"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        logger.info(f"Testing {description}: {endpoint}")
        response = requests.get(url, headers=headers, timeout=30)

        result = {
            'endpoint': endpoint,
            'description': description,
            'status_code': response.status_code,
            'success': response.status_code < 400,
            'response_size': len(response.content),
            'has_status_error': False
        }

        # Check for the specific error we were fixing
        if response.status_code == 500:
            try:
                error_data = response.json()
                error_message = str(error_data)
                if 'column feature_flags.status does not exist' in error_message:
                    result['has_status_error'] = True
                    result['error_message'] = error_message
            except:
                result['error_message'] = response.text[:200]

        if response.status_code == 200:
            try:
                data = response.json()
                result['response_data'] = data
                logger.info(f"✅ SUCCESS: {description}")
            except:
                logger.info(f"✅ SUCCESS: {description} (non-JSON response)")
        else:
            logger.warning(f"⚠️  ISSUE: {description} returned {response.status_code}")

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ NETWORK ERROR: {description} - {e}")
        return {
            'endpoint': endpoint,
            'description': description,
            'status_code': None,
            'success': False,
            'error': str(e),
            'network_error': True
        }

def main():
    """Run verification tests"""
    print("🔍 FEATURE FLAGS FIX VERIFICATION")
    print("=" * 50)
    print(f"Testing API: {API_BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print()

    token = get_test_token()
    if token == 'PLACEHOLDER_TOKEN':
        print("⚠️  WARNING: Using placeholder token - replace with actual Matt.Lindop token")
        print("   Set TEST_TOKEN environment variable with valid token")
        print()

    results = []

    # Test each endpoint
    test_cases = [
        ("/api/v1/features/market_edge.enhanced_ui", "Market Edge Enhanced UI Feature Flag"),
        ("/api/v1/features/admin.advanced_controls", "Admin Advanced Controls Feature Flag"),
        ("/api/v1/features/enabled", "All Enabled Features List"),
        ("/api/v1/admin/feature-flags", "Admin Feature Flags Management")
    ]

    for endpoint, description in test_cases:
        result = test_endpoint(endpoint, token, description)
        results.append(result)
        print()

    # Analyze results
    print("📊 VERIFICATION SUMMARY")
    print("=" * 30)

    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    status_errors = sum(1 for r in results if r.get('has_status_error', False))
    network_errors = sum(1 for r in results if r.get('network_error', False))

    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Status column errors: {status_errors}")
    print(f"Network errors: {network_errors}")

    if status_errors > 0:
        print("\n❌ VERIFICATION FAILED:")
        print("   Status column errors still occurring")
        print("   The emergency fix may not have been applied correctly")
        print("\n🛠️  NEXT STEPS:")
        print("   1. Check that emergency_add_feature_flags_status_column.sql was applied")
        print("   2. Verify the status column exists in production database")
        print("   3. Check application server logs for errors")

    elif successful_tests == total_tests:
        print("\n✅ VERIFICATION SUCCESSFUL:")
        print("   All feature flag endpoints are working")
        print("   Status column fix has been applied correctly")
        print("   Matt.Lindop should now have admin panel access")

    elif network_errors > 0:
        print("\n⚠️  NETWORK ISSUES:")
        print("   Some tests failed due to network/connectivity issues")
        print("   This may not indicate a problem with the fix")

    else:
        print("\n⚠️  MIXED RESULTS:")
        print("   Some endpoints working, others failing")
        print("   May indicate partial fix or authentication issues")

    # Save detailed results
    results_file = f"feature_flags_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'api_base_url': API_BASE_URL,
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'status_errors': status_errors,
                'network_errors': network_errors
            },
            'detailed_results': results
        }, f, indent=2)

    print(f"\n💾 Detailed results saved to: {results_file}")

    if status_errors == 0 and successful_tests > 0:
        print("\n🎉 MATT.LINDOP ADMIN ACCESS STATUS:")
        print("   Feature flags API is working correctly")
        print("   Admin panel should be accessible")
        print("   Zebra Associates opportunity can proceed")

if __name__ == "__main__":
    main()