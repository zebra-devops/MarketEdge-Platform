#!/usr/bin/env python3
"""
Monitor the API router fix deployment
Track when the broken_endpoint import error is resolved
"""

import requests
import time
import json
from datetime import datetime

def check_deployment_status():
    """Check if the API router fix has been deployed"""
    try:
        response = requests.get("https://marketedge-platform.onrender.com/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            api_router_included = data.get('api_router_included', False)
            api_router_error = data.get('api_router_error', '')

            print(f"[{datetime.now().strftime('%H:%M:%S')}] API Router Status:")
            print(f"  - Included: {api_router_included}")
            print(f"  - Error: {api_router_error}")

            if api_router_included:
                print("✅ API ROUTER FIX DEPLOYED SUCCESSFULLY!")
                return True
            elif "broken_endpoint" not in api_router_error:
                print("⚠️  Different error - fix may be partially deployed")
                return False
            else:
                print("⏳ Still waiting for deployment...")
                return False
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_api_endpoints():
    """Test if API endpoints are now accessible"""
    endpoints_to_test = [
        "/api/v1/admin/feature-flags",
        "/api/v1/admin/modules",
        "/api/v1/features/enabled"
    ]

    print("\nTesting API endpoints:")
    for endpoint in endpoints_to_test:
        try:
            url = f"https://marketedge-platform.onrender.com{endpoint}"
            response = requests.get(url, timeout=10)

            if response.status_code == 404:
                status = "❌ 404 (endpoint missing)"
            elif response.status_code in [401, 403]:
                status = "✅ Available (auth required)"
            elif response.status_code == 500:
                status = "⚠️  500 (server error)"
            else:
                status = f"? HTTP {response.status_code}"

            print(f"  {endpoint}: {status}")

        except Exception as e:
            print(f"  {endpoint}: ❌ Error - {e}")

def main():
    print("=" * 60)
    print("MONITORING API ROUTER FIX DEPLOYMENT")
    print("=" * 60)
    print("Watching for broken_endpoint import fix to deploy...")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)

    check_count = 0
    max_checks = 20  # Monitor for ~10 minutes (30s intervals)

    try:
        while check_count < max_checks:
            check_count += 1
            print(f"\n--- Check {check_count}/{max_checks} ---")

            if check_deployment_status():
                # Success! Test the endpoints
                test_api_endpoints()
                print("\n🎉 DEPLOYMENT MONITORING COMPLETE!")
                print("API router fix has been successfully deployed.")
                break

            if check_count < max_checks:
                print("Waiting 30 seconds for next check...")
                time.sleep(30)
        else:
            print(f"\n⏰ Monitoring timeout after {max_checks} checks")
            print("Deployment may still be in progress or there may be an issue.")
            print("Check Render dashboard for deployment status.")

    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")

if __name__ == "__main__":
    main()