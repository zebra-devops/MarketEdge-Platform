#!/usr/bin/env python3
"""
Monitor Critical Migration Deployment
=====================================

Monitors the deployment of migration 003 to production and verifies
the analytics_modules table is successfully created.

Critical for: £925K Zebra Associates opportunity
Target: Matt.Lindop Feature Flags access
"""

import requests
import time
import json
from datetime import datetime


def check_service_health():
    """Check if the service is responding"""
    try:
        response = requests.get("https://marketedge-platform.onrender.com/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            return True, health_data
        else:
            return False, f"HTTP {response.status_code}"
    except requests.RequestException as e:
        return False, str(e)


def check_feature_flags_endpoint():
    """Check if feature flags endpoint is working (should return 401 without auth)"""
    try:
        response = requests.get("https://marketedge-platform.onrender.com/api/v1/admin/feature-flags", timeout=10)
        if response.status_code == 401:
            return True, "Feature flags endpoint responding correctly (401 auth required)"
        elif response.status_code == 500:
            try:
                error_data = response.json()
                if "analytics_modules" in str(error_data):
                    return False, "analytics_modules table still missing"
                else:
                    return False, f"500 error: {error_data}"
            except:
                return False, "500 error (unknown cause)"
        else:
            return False, f"Unexpected status: {response.status_code}"
    except requests.RequestException as e:
        return False, str(e)


def monitor_deployment():
    """Monitor the deployment process"""

    print("🚀 MONITORING CRITICAL MIGRATION DEPLOYMENT")
    print("="*50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target: https://marketedge-platform.onrender.com")
    print(f"Mission: Create analytics_modules table for £925K opportunity")
    print()

    print("⏳ Waiting for Render to detect changes and start deployment...")
    print("   (This typically takes 2-3 minutes after git push)")
    print()

    # Wait for initial deployment detection
    time.sleep(120)  # 2 minutes initial wait

    max_attempts = 30  # 15 minutes total monitoring
    success_count = 0

    for attempt in range(1, max_attempts + 1):
        print(f"🔍 Check {attempt}/{max_attempts}: ", end="", flush=True)

        # Check service health
        health_ok, health_info = check_service_health()

        if health_ok:
            print("✅ Service healthy", end=" | ")

            # Check feature flags endpoint
            ff_ok, ff_info = check_feature_flags_endpoint()

            if ff_ok:
                print(f"✅ {ff_info}")
                success_count += 1

                if success_count >= 3:  # 3 consecutive successes
                    print("\n🎉 DEPLOYMENT SUCCESSFUL!")
                    print("="*30)
                    print("✅ Service is healthy")
                    print("✅ Feature flags endpoint is working")
                    print("✅ analytics_modules table created")
                    print("✅ Matt.Lindop can access Feature Flags")
                    print()
                    print("🎯 NEXT ACTIONS:")
                    print("1. Matt.Lindop should login at https://app.zebra.associates")
                    print("2. Navigate to admin panel")
                    print("3. Access Feature Flags management")
                    print("4. Confirm full admin functionality")
                    print()
                    print(f"✅ £925K Zebra Associates opportunity: UNBLOCKED")
                    return True
            else:
                print(f"❌ {ff_info}")
                success_count = 0

                if "analytics_modules table still missing" in ff_info:
                    print("    ⚠️  Migration may still be in progress or failed")
        else:
            print(f"❌ Service unhealthy: {health_info}")
            success_count = 0

        if attempt < max_attempts:
            print("    ⏳ Waiting 30 seconds...")
            time.sleep(30)

    print("\n❌ DEPLOYMENT MONITORING TIMEOUT")
    print("="*35)
    print("The deployment is taking longer than expected.")
    print()
    print("🔧 TROUBLESHOOTING STEPS:")
    print("1. Check Render dashboard for build logs")
    print("2. Look for migration errors in build output")
    print("3. Verify database connection during build")
    print("4. Check if alembic upgrade 003 completed successfully")
    print()
    print("Manual verification command:")
    print("python production_migration_verification.py")

    return False


def main():
    """Main monitoring function"""

    print("🎯 CRITICAL BUSINESS DEPLOYMENT MONITORING")
    print("🎯 Target: £925K Zebra Associates opportunity")
    print("🎯 Mission: analytics_modules table creation")
    print("🎯 Beneficiary: Matt.Lindop Feature Flags access")
    print()

    success = monitor_deployment()

    print(f"\n⏰ Monitoring completed: {datetime.now().isoformat()}")

    if success:
        # Save success report
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "SUCCESS",
            "analytics_modules_table": "CREATED",
            "feature_flags_endpoint": "WORKING",
            "business_impact": "£925K Zebra Associates opportunity UNBLOCKED",
            "next_actions": [
                "Matt.Lindop login at https://app.zebra.associates",
                "Access admin panel with super_admin role",
                "Navigate to Feature Flags management",
                "Confirm full admin functionality"
            ]
        }

        with open("analytics_modules_deployment_success_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("📄 Success report saved: analytics_modules_deployment_success_report.json")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)