#!/usr/bin/env python3
"""
EMERGENCY PRODUCTION SCHEMA DIAGNOSTIC: Feature Flags Status Column
==================================================================

This script diagnoses the missing 'status' column in the feature_flags table
that is causing 500 errors for Matt.Lindop's admin access at Zebra Associates.

ROOT CAUSE ANALYSIS:
- Production database is at migration 010 (CSV import tables)
- Migration 003 DOES include the status column in feature_flags table
- BUT migration 80105006e3d3 does NOT recreate the feature_flags table
- The latest migration drops many tables but leaves feature_flags alone
- So if migration 003 was never properly applied, the status column is missing

CRITICAL FINDING:
- Migration 003 line 79: status column is defined with ENUM
- Migration 80105006e3d3: No reference to feature_flags table structure
- Current production error: "column feature_flags.status does not exist"

This indicates migration 003 was never properly applied in production.
"""

import os
import asyncio
import asyncpg
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Production database connection
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable not set")

async def main():
    """Diagnose the production database schema for feature flags"""

    print("🔍 EMERGENCY SCHEMA DIAGNOSTIC: Feature Flags Status Column")
    print("=" * 70)

    conn = None
    try:
        # Connect to production database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to production database")

        # Check current migration version
        print("\n📋 MIGRATION STATUS:")
        try:
            current_version = await conn.fetchval("SELECT version_num FROM alembic_version LIMIT 1")
            print(f"Current migration: {current_version}")
        except Exception as e:
            print(f"❌ Could not read alembic_version: {e}")

        # Check if feature_flags table exists
        print("\n🗂️  FEATURE FLAGS TABLE EXISTENCE:")
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'feature_flags'
            )
        """)
        print(f"feature_flags table exists: {table_exists}")

        if table_exists:
            # Get complete table structure
            print("\n📊 FEATURE FLAGS TABLE STRUCTURE:")
            columns = await conn.fetch("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    udt_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'feature_flags'
                ORDER BY ordinal_position
            """)

            status_column_exists = False
            for col in columns:
                if col['column_name'] == 'status':
                    status_column_exists = True
                    print(f"✅ {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
                else:
                    print(f"   {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")

            print(f"\n🎯 STATUS COLUMN EXISTS: {status_column_exists}")

            if not status_column_exists:
                print("\n❌ CRITICAL ISSUE CONFIRMED:")
                print("   - feature_flags table exists but missing 'status' column")
                print("   - This means migration 003 was not properly applied")
                print("   - The application code expects this column to exist")

                # Check if the ENUM type exists
                print("\n🔍 CHECKING ENUM TYPES:")
                enum_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type
                        WHERE typname = 'featureflagstatus'
                    )
                """)
                print(f"featureflagstatus ENUM exists: {enum_exists}")

                # Show what we need to add
                print("\n🛠️  REQUIRED SCHEMA FIX:")
                print("1. Create ENUM type: featureflagstatus")
                print("2. Add status column to feature_flags table")
                print("3. Set default value to 'ACTIVE'")
                print("4. Update existing records")

            # Count existing feature flags
            flag_count = await conn.fetchval("SELECT COUNT(*) FROM feature_flags")
            print(f"\n📈 Current feature flags count: {flag_count}")

            if flag_count > 0:
                print("\n🚨 EXISTING DATA IMPACT:")
                print("   - Adding status column will require default values")
                print("   - All existing flags should default to 'ACTIVE'")

        else:
            print("❌ feature_flags table does not exist - migration 003 not applied")

        # Check if related tables exist from migration 003
        print("\n🔗 RELATED TABLES FROM MIGRATION 003:")
        related_tables = ['sic_codes', 'analytics_modules', 'feature_flag_overrides', 'feature_flag_usage']
        for table in related_tables:
            exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                )
            """)
            print(f"   {table}: {'✅ exists' if exists else '❌ missing'}")

        # Generate the fix SQL
        print("\n💊 EMERGENCY FIX SQL:")
        print("=" * 50)
        fix_sql = """
-- EMERGENCY FIX: Add missing status column to feature_flags table
-- This should be run in production to fix Matt.Lindop's admin access

BEGIN;

-- 1. Create the ENUM type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'featureflagstatus') THEN
        CREATE TYPE featureflagstatus AS ENUM ('ACTIVE', 'INACTIVE', 'DEPRECATED');
    END IF;
END $$;

-- 2. Add the status column with default value
ALTER TABLE feature_flags
ADD COLUMN IF NOT EXISTS status featureflagstatus DEFAULT 'ACTIVE'::featureflagstatus NOT NULL;

-- 3. Update any existing records to have ACTIVE status
UPDATE feature_flags SET status = 'ACTIVE'::featureflagstatus WHERE status IS NULL;

-- 4. Verify the fix
SELECT
    COUNT(*) as total_flags,
    COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_flags
FROM feature_flags;

COMMIT;
"""
        print(fix_sql)

        # Create emergency fix file
        fix_filename = f"emergency_feature_flags_status_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with open(fix_filename, 'w') as f:
            f.write(fix_sql)
        print(f"\n💾 Fix saved to: {fix_filename}")

        print("\n🚀 NEXT STEPS:")
        print("1. Review the generated SQL fix")
        print("2. Test in staging environment first")
        print("3. Apply to production during maintenance window")
        print("4. Verify Matt.Lindop can access feature flags admin panel")
        print("5. Update migration tracking to prevent future issues")

    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        print(f"\n❌ DIAGNOSTIC ERROR: {e}")
        print("\nThis may indicate:")
        print("- Database connection issues")
        print("- Insufficient permissions")
        print("- Database not accessible")

    finally:
        if conn:
            await conn.close()
            print("\n📤 Database connection closed")

if __name__ == "__main__":
    asyncio.run(main())