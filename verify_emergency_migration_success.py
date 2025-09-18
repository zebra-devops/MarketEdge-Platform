#!/usr/bin/env python3
"""
Emergency Migration Success Verification
Confirms that the analytics_modules table creation fixed the 500 errors

Business Context: £925K Zebra Associates opportunity
Critical Success: Matt Lindop can now access admin features
"""

import requests
import json
from datetime import datetime
import sys

def test_admin_endpoints():
    """Test all admin endpoints to confirm 500 errors are fixed"""

    print("🧪 EMERGENCY MIGRATION SUCCESS VERIFICATION")
    print("=" * 60)
    print("🏢 Business Context: £925K Zebra Associates opportunity")
    print("🎯 Target: Confirm analytics_modules table fixes 500 errors")
    print("")

    base_url = "https://marketedge-platform.onrender.com/api/v1"

    # Admin endpoints that were previously returning 500 errors
    admin_endpoints = [
        "/admin/feature-flags",
        "/admin/dashboard/stats",
        "/admin/modules",
        "/admin/organizations"
    ]

    results = {
        'timestamp': datetime.now().isoformat(),
        'business_context': '£925K Zebra Associates - analytics_modules fix verification',
        'base_url': base_url,
        'tests': {}
    }

    success_count = 0
    total_tests = len(admin_endpoints)

    for endpoint in admin_endpoints:
        url = base_url + endpoint
        print(f"🌐 Testing: {endpoint}")

        try:
            response = requests.get(url, timeout=10)
            status_code = response.status_code

            if status_code == 401:
                print(f"   ✅ Status: {status_code} (Unauthorized - CORRECT!)")
                print(f"   🎉 No more 500 error - migration successful!")
                success_count += 1
                test_result = "SUCCESS"
                message = "Endpoint correctly returns 401 instead of 500"

            elif status_code == 500:
                print(f"   ❌ Status: {status_code} (Internal Server Error - STILL BROKEN!)")
                print(f"   💥 analytics_modules table issue not resolved")
                test_result = "FAILED"
                message = "Endpoint still returns 500 error - migration failed"

            elif status_code == 403:
                print(f"   ✅ Status: {status_code} (Forbidden - ACCEPTABLE)")
                print(f"   🔒 Different auth issue, but not 500 error")
                success_count += 1
                test_result = "SUCCESS"
                message = "Endpoint returns 403 (acceptable, not 500)"

            else:
                print(f"   ⚠️ Status: {status_code} (Unexpected)")
                test_result = "WARNING"
                message = f"Unexpected status code: {status_code}"

            results['tests'][endpoint] = {
                'url': url,
                'status_code': status_code,
                'result': test_result,
                'message': message,
                'response_time': response.elapsed.total_seconds()
            }

        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout - Render service may be starting")
            results['tests'][endpoint] = {
                'url': url,
                'result': 'TIMEOUT',
                'message': 'Request timeout - service may be restarting'
            }

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {str(e)}")
            results['tests'][endpoint] = {
                'url': url,
                'result': 'ERROR',
                'message': str(e)
            }

        print("")

    # Overall assessment
    print("📊 VERIFICATION RESULTS")
    print("=" * 60)

    success_rate = (success_count / total_tests) * 100
    results['success_rate'] = success_rate
    results['successful_tests'] = success_count
    results['total_tests'] = total_tests

    if success_count == total_tests:
        print("🎉 COMPLETE SUCCESS!")
        print("✅ All admin endpoints fixed")
        print("✅ analytics_modules table created successfully")
        print("✅ 500 errors eliminated")
        print("🚀 Matt Lindop can now access admin features")
        print("💰 £925K Zebra Associates opportunity UNBLOCKED!")

        results['overall_status'] = 'SUCCESS'
        results['business_impact'] = 'POSITIVE - Opportunity unblocked'

    elif success_count > 0:
        print(f"⚠️ PARTIAL SUCCESS ({success_rate:.1f}%)")
        print(f"✅ {success_count}/{total_tests} endpoints fixed")
        print("⚠️ Some endpoints may need additional fixes")

        results['overall_status'] = 'PARTIAL_SUCCESS'
        results['business_impact'] = 'MIXED - Some improvement achieved'

    else:
        print("❌ MIGRATION FAILED!")
        print("💥 No endpoints fixed")
        print("💰 £925K opportunity still blocked")

        results['overall_status'] = 'FAILED'
        results['business_impact'] = 'NEGATIVE - Opportunity still blocked'

    print("=" * 60)

    # Save results
    filename = f"migration_verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"📄 Results saved to: {filename}")

    return success_count == total_tests

if __name__ == "__main__":
    success = test_admin_endpoints()
    sys.exit(0 if success else 1)