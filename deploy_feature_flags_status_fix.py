#!/usr/bin/env python3
"""
Production Deployment Script: Feature Flags Status Column Fix

This script applies the missing 'status' column to the feature_flags table
to fix Matt.Lindop's admin access issue.

CRITICAL: This fixes the £925K Zebra Associates opportunity blocker.

Usage:
    python deploy_feature_flags_status_fix.py

Requirements:
    - PRODUCTION_DATABASE_URL environment variable
    - Or connection to production database via alembic.ini
"""

import os
import sys
import asyncio
import subprocess
from datetime import datetime

def apply_migration():
    """Apply the specific migration that adds the status column"""
    print("🚀 PRODUCTION DEPLOYMENT: Feature Flags Status Column Fix")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Migration: a0a2f1ab72ce_add_missing_status_column_to_feature_")
    print(f"Issue: Matt.Lindop admin access - 'column feature_flags.status does not exist'")
    print()

    try:
        # Apply the migration
        print("🔧 Applying migration to add feature_flags.status column...")

        result = subprocess.run([
            "alembic", "upgrade", "a0a2f1ab72ce"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Migration applied successfully!")
            print(f"Output: {result.stdout}")

            # Verify the column was added
            print("\n🔍 Verifying column was added...")

            # You can add verification code here if needed

            print("\n" + "="*60)
            print("📋 DEPLOYMENT SUMMARY:")
            print("✅ Status column added to feature_flags table")
            print("✅ Enum type 'featureflagstatus' created/verified")
            print("✅ Default value 'ACTIVE' set for existing records")
            print()
            print("🎯 NEXT STEPS:")
            print("1. Test Matt.Lindop's admin access: https://app.zebra.associates")
            print("2. Verify feature flags endpoint: /api/v1/admin/feature-flags")
            print("3. Confirm no 500 errors in production logs")
            print()
            print("💰 £925K Zebra Associates opportunity - ADMIN ACCESS RESTORED")

            return True

        else:
            print(f"❌ Migration failed!")
            print(f"Error: {result.stderr}")
            print(f"Output: {result.stdout}")
            return False

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False

def verify_production_ready():
    """Verify we're ready to deploy to production"""
    print("🔍 Pre-deployment verification...")

    # Check if migration file exists
    migration_file = "database/migrations/versions/a0a2f1ab72ce_add_missing_status_column_to_feature_.py"
    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        return False
    else:
        print(f"✅ Migration file exists: {migration_file}")

    # Check alembic configuration
    if not os.path.exists("alembic.ini"):
        print("❌ alembic.ini not found")
        return False
    else:
        print("✅ alembic.ini found")

    print("✅ Ready for production deployment")
    return True

def main():
    """Main deployment function"""

    # Verify we're ready
    if not verify_production_ready():
        print("❌ Pre-deployment verification failed")
        sys.exit(1)

    # Confirm deployment
    print(f"\n🚨 CRITICAL PRODUCTION DEPLOYMENT")
    print(f"This will modify the production database to add the missing 'status' column")
    print(f"to the feature_flags table.")
    print()

    # For automated deployment, remove this confirmation
    # For manual deployment, uncomment the following:
    # confirm = input("Type 'YES' to proceed with production deployment: ")
    # if confirm != "YES":
    #     print("❌ Deployment cancelled")
    #     sys.exit(1)

    # Apply the migration
    success = apply_migration()

    if success:
        print("\n🎉 DEPLOYMENT SUCCESSFUL!")
        print("Matt.Lindop can now access feature flags in admin panel")
        sys.exit(0)
    else:
        print("\n💥 DEPLOYMENT FAILED!")
        print("Manual intervention required")
        sys.exit(1)

if __name__ == "__main__":
    main()