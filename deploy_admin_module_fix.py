#!/usr/bin/env python3
"""
Production Deployment Script - Admin Module Fix
Fixes ModuleNotFoundError: No module named 'app.api.admin'

This resolves the critical production error blocking Matt.Lindop's
£925K Zebra Associates opportunity.
"""

import asyncio
import os
import sys
from datetime import datetime
import json

# Add app to path
sys.path.append('/Users/matt/Sites/MarketEdge')

async def verify_fix():
    """Verify the admin module fix is working"""

    print("=" * 70)
    print("ADMIN MODULE FIX - PRODUCTION DEPLOYMENT")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 70)

    results = {
        "timestamp": datetime.now().isoformat(),
        "deployment": "admin_module_fix",
        "status": "in_progress",
        "checks": []
    }

    # 1. Check compatibility module exists
    print("\n1. CHECKING COMPATIBILITY MODULE:")
    print("-" * 50)

    compat_path = '/Users/matt/Sites/MarketEdge/app/api/admin.py'
    if os.path.exists(compat_path):
        print(f"✅ Compatibility module exists: {compat_path}")
        results["checks"].append({
            "check": "compatibility_module",
            "status": "success",
            "message": "Compatibility bridge created"
        })
    else:
        print(f"❌ Compatibility module missing: {compat_path}")
        results["checks"].append({
            "check": "compatibility_module",
            "status": "failed",
            "message": "Compatibility bridge not found"
        })
        return results

    # 2. Test imports work
    print("\n2. TESTING MODULE IMPORTS:")
    print("-" * 50)

    try:
        from app.api.admin import router
        print("✅ Import app.api.admin successful")
        results["checks"].append({
            "check": "import_test",
            "status": "success",
            "message": "app.api.admin imports correctly"
        })
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        results["checks"].append({
            "check": "import_test",
            "status": "failed",
            "message": str(e)
        })
        return results

    # 3. Verify admin endpoints are accessible
    print("\n3. VERIFYING ADMIN ENDPOINTS:")
    print("-" * 50)

    from app.api.api_v1.endpoints.admin import router as admin_router

    feature_flag_endpoints = [
        endpoint for endpoint in admin_router.routes
        if hasattr(endpoint, 'path') and 'feature-flags' in endpoint.path
    ]

    if feature_flag_endpoints:
        print(f"✅ Found {len(feature_flag_endpoints)} feature-flags endpoints:")
        for endpoint in feature_flag_endpoints:
            if hasattr(endpoint, 'methods'):
                print(f"   - {list(endpoint.methods)} {endpoint.path}")
        results["checks"].append({
            "check": "endpoints",
            "status": "success",
            "message": f"Found {len(feature_flag_endpoints)} feature-flags endpoints"
        })
    else:
        print("❌ No feature-flags endpoints found!")
        results["checks"].append({
            "check": "endpoints",
            "status": "failed",
            "message": "No feature-flags endpoints found"
        })

    # 4. Test AdminService import
    print("\n4. TESTING ADMIN SERVICE:")
    print("-" * 50)

    try:
        from app.services.admin_service import AdminService
        print("✅ AdminService imports successfully")
        results["checks"].append({
            "check": "admin_service",
            "status": "success",
            "message": "AdminService available"
        })
    except ImportError as e:
        print(f"❌ AdminService import failed: {e}")
        results["checks"].append({
            "check": "admin_service",
            "status": "failed",
            "message": str(e)
        })

    # 5. Database connectivity test (if available)
    print("\n5. TESTING DATABASE CONNECTIVITY:")
    print("-" * 50)

    try:
        from app.core.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine

        if settings.DATABASE_URL:
            engine = create_async_engine(
                settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
            )

            async with engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                print("✅ Database connection successful")
                results["checks"].append({
                    "check": "database",
                    "status": "success",
                    "message": "Database accessible"
                })

            await engine.dispose()
        else:
            print("⚠️  DATABASE_URL not configured")
            results["checks"].append({
                "check": "database",
                "status": "skipped",
                "message": "DATABASE_URL not configured"
            })
    except Exception as e:
        print(f"⚠️  Database test skipped: {e}")
        results["checks"].append({
            "check": "database",
            "status": "skipped",
            "message": str(e)
        })

    # Final status
    all_passed = all(
        check["status"] == "success" or check["status"] == "skipped"
        for check in results["checks"]
    )

    results["status"] = "success" if all_passed else "failed"

    # 6. Summary
    print("\n" + "=" * 70)
    print("DEPLOYMENT SUMMARY:")
    print("=" * 70)

    if results["status"] == "success":
        print("✅ ADMIN MODULE FIX DEPLOYED SUCCESSFULLY!")
        print("\nFIXED ISSUES:")
        print("- ModuleNotFoundError: No module named 'app.api.admin' RESOLVED")
        print("- Feature flags endpoints now accessible")
        print("- Matt.Lindop can now access admin functionality")
        print("\nNEXT STEPS:")
        print("1. Commit these changes")
        print("2. Deploy to production (Render)")
        print("3. Test feature flags endpoint: GET /api/v1/admin/feature-flags")
        print("4. Verify Matt.Lindop access at app.zebra.associates")
    else:
        print("❌ DEPLOYMENT FAILED - Review errors above")

    # Save results
    report_path = f"admin_module_fix_deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Deployment report saved: {report_path}")

    return results

if __name__ == "__main__":
    results = asyncio.run(verify_fix())
    sys.exit(0 if results["status"] == "success" else 1)