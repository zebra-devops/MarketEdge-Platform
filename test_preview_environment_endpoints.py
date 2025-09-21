#!/usr/bin/env python3
"""
Test script for preview environment validation endpoints.
This script validates that the new system endpoints are working correctly.
"""

import requests
import json
import sys
import os
from typing import Dict, Any

def test_endpoint(url: str, endpoint: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Test a specific endpoint and return the response"""
    full_url = f"{url}{endpoint}"
    try:
        response = requests.get(full_url, headers=headers, timeout=30)
        return {
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 300,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "url": full_url
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "success": False,
            "error": str(e),
            "url": full_url
        }

def main():
    """Main test function"""
    # Test against local development server
    base_url = "http://localhost:8000"

    print("🧪 Testing Preview Environment Validation Endpoints")
    print(f"🎯 Base URL: {base_url}")
    print("=" * 60)

    # Test endpoints
    endpoints_to_test = [
        {
            "endpoint": "/api/v1/system/environment-config",
            "name": "Environment Config (Public)",
            "description": "Should show current environment and Auth0 configuration"
        },
        {
            "endpoint": "/api/v1/system/staging-health",
            "name": "Staging Health Check (Public)",
            "description": "Should show health status and staging configuration"
        },
        {
            "endpoint": "/health",
            "name": "Basic Health Check",
            "description": "Should confirm API is running"
        }
    ]

    all_passed = True

    for test_case in endpoints_to_test:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"📝 Description: {test_case['description']}")
        print(f"🔗 Endpoint: {test_case['endpoint']}")

        result = test_endpoint(base_url, test_case['endpoint'])

        if result['success']:
            print(f"✅ SUCCESS - Status: {result['status_code']}")

            # Pretty print JSON response if available
            if isinstance(result['data'], dict):
                print("📊 Response Data:")
                important_fields = ['status', 'environment', 'auth0_config', 'staging_mode', 'auth0_environment']
                for field in important_fields:
                    if field in result['data']:
                        print(f"   {field}: {result['data'][field]}")
            else:
                print(f"📄 Response: {result['data'][:200]}...")
        else:
            print(f"❌ FAILED - Status: {result['status_code']}")
            if 'error' in result:
                print(f"💥 Error: {result['error']}")
            else:
                print(f"📄 Response: {result['data']}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Endpoints ready for preview environment testing")
        print("\n📝 Next Steps:")
        print("1. Commit changes and push to trigger preview environment")
        print("2. Test these same endpoints on the preview URL")
        print("3. Verify staging Auth0 configuration in preview")
    else:
        print("❌ SOME TESTS FAILED - Fix issues before creating pull request")
        sys.exit(1)

if __name__ == "__main__":
    main()