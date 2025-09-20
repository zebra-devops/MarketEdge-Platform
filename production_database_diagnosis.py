#!/usr/bin/env python3
"""
Production Database Diagnosis Script
Checks the current state of the feature_flags table in production
"""

import asyncio
import sys
import os
import httpx
import json
from datetime import datetime

async def check_production_health():
    """Check production backend health and feature flags endpoints"""
    base_url = "https://marketedge-platform.onrender.com"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Check health endpoint
            print("🔍 Checking production health...")
            health_response = await client.get(f"{base_url}/health")
            print(f"Health status: {health_response.status_code}")
            if health_response.status_code == 200:
                print("✅ Production backend is running")
            else:
                print("❌ Production backend health check failed")
                return False

            # Try to access feature flags endpoint (this should fail with the column error)
            print("\n🔍 Testing feature flags endpoint...")

            # First try without authentication to see the error
            ff_response = await client.get(f"{base_url}/api/v1/admin/feature-flags")
            print(f"Feature flags status (no auth): {ff_response.status_code}")

            if ff_response.status_code == 500:
                error_text = ff_response.text
                print(f"❌ 500 Error response: {error_text}")

                if "column" in error_text.lower() and "status" in error_text.lower():
                    print("🎯 CONFIRMED: Missing 'status' column in feature_flags table")
                    return True
                else:
                    print("❌ Different 500 error than expected")

            elif ff_response.status_code == 401:
                print("✅ Got 401 (auth required) - endpoint is working, no column error")
                return False
            else:
                print(f"❓ Unexpected status code: {ff_response.status_code}")

        except Exception as e:
            print(f"❌ Error checking production: {e}")
            return False

    return False

async def check_alembic_migrations():
    """Check what migrations should be applied"""
    print("\n🔍 Checking local migration status...")

    # Read current migration from alembic
    try:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "alembic", "current"],
            capture_output=True,
            text=True,
            cwd="/Users/matt/Sites/MarketEdge",
            env={**os.environ, "DATABASE_URL": "postgresql://matt@localhost:5432/platform_wrapper"}
        )

        if result.returncode == 0:
            current = result.stdout.strip()
            print(f"Local migration status: {current}")
        else:
            print(f"❌ Error checking migrations: {result.stderr}")

    except Exception as e:
        print(f"❌ Error running alembic: {e}")

def analyze_migration_003():
    """Analyze the migration that should contain the status column"""
    migration_file = "/Users/matt/Sites/MarketEdge/database/migrations/versions/003_add_phase3_enhancements.py"

    print(f"\n🔍 Analyzing migration 003...")
    try:
        with open(migration_file, 'r') as f:
            content = f.read()

        # Check if status column is in the migration
        if "'status'" in content and "featureflagstatus" in content:
            print("✅ Migration 003 DOES contain the status column definition")
            print("   Line: sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'DEPRECATED', name='featureflagstatus'), nullable=False)")
        else:
            print("❌ Migration 003 does NOT contain the status column")

    except Exception as e:
        print(f"❌ Error reading migration file: {e}")

async def main():
    """Main diagnosis function"""
    print("🚨 PRODUCTION DATABASE DIAGNOSIS")
    print("="*50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Issue: Matt.Lindop cannot access feature flags - 'status column does not exist'")
    print()

    # Check production endpoint
    has_column_error = await check_production_health()

    # Check local migrations
    await check_alembic_migrations()

    # Analyze migration 003
    analyze_migration_003()

    print("\n" + "="*50)
    print("📋 DIAGNOSIS SUMMARY:")

    if has_column_error:
        print("❌ CONFIRMED: Production database is missing the 'status' column in feature_flags table")
        print("🔧 SOLUTION NEEDED: Apply migration to add missing column")
        print("\nNext Steps:")
        print("1. Create Alembic migration to add status column")
        print("2. Apply migration to production database")
        print("3. Verify feature flags functionality")
    else:
        print("❓ Could not confirm the column error - may need different approach")

    return has_column_error

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)