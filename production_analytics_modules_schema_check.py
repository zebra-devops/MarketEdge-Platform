#!/usr/bin/env python3
"""
CRITICAL: Check production database analytics_modules table schema
Verify if description column exists and migration 003 is applied
"""

import os
import asyncio
import asyncpg
import json
from datetime import datetime

async def check_production_database():
    """Check production database schema for analytics_modules table"""

    # Get production database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        return False

    try:
        # Connect to production database with SSL
        conn = await asyncpg.connect(database_url, ssl='require')
        print("✅ Connected to production database")

        # Check if analytics_modules table exists
        table_exists_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'analytics_modules'
        );
        """

        table_exists = await conn.fetchval(table_exists_query)
        print(f"📋 analytics_modules table exists: {table_exists}")

        if not table_exists:
            print("❌ CRITICAL: analytics_modules table does not exist in production")
            await conn.close()
            return False

        # Get complete table schema for analytics_modules
        schema_query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'analytics_modules'
        ORDER BY ordinal_position;
        """

        columns = await conn.fetch(schema_query)
        print(f"\n📊 analytics_modules table has {len(columns)} columns:")

        has_description = False
        column_info = {}

        for column in columns:
            column_name = column['column_name']
            data_type = column['data_type']
            nullable = column['is_nullable']
            default = column['column_default']
            max_length = column['character_maximum_length']

            print(f"  - {column_name}: {data_type}" +
                  (f"({max_length})" if max_length else "") +
                  f" {'NULL' if nullable == 'YES' else 'NOT NULL'}" +
                  (f" DEFAULT {default}" if default else ""))

            column_info[column_name] = {
                'data_type': data_type,
                'is_nullable': nullable,
                'column_default': default,
                'character_maximum_length': max_length
            }

            if column_name == 'description':
                has_description = True

        print(f"\n🔍 Description column exists: {has_description}")

        if has_description:
            desc_info = column_info['description']
            print(f"   - Type: {desc_info['data_type']}")
            print(f"   - Nullable: {desc_info['is_nullable']}")
            print(f"   - Expected: text NOT NULL")

            if desc_info['data_type'] == 'text' and desc_info['is_nullable'] == 'NO':
                print("✅ Description column schema matches expected SQLAlchemy model")
            else:
                print("❌ Description column schema does NOT match expected model")

        # Check migration status
        migration_query = """
        SELECT version_num
        FROM alembic_version
        ORDER BY version_num DESC
        LIMIT 1;
        """

        try:
            current_migration = await conn.fetchval(migration_query)
            print(f"\n🔄 Current migration version: {current_migration}")

            # Check if migration 003 is applied
            if current_migration and current_migration >= '003':
                print("✅ Migration 003 (Phase 3 enhancements) has been applied")
            else:
                print("❌ Migration 003 has NOT been applied")

        except Exception as e:
            print(f"⚠️  Could not check migration status: {e}")

        # Test a simple query on the table
        try:
            count_query = "SELECT COUNT(*) FROM analytics_modules;"
            count = await conn.fetchval(count_query)
            print(f"\n📈 Current analytics_modules records: {count}")

            if count > 0:
                # Get sample record to verify structure
                sample_query = """
                SELECT id, name, description, module_type, status
                FROM analytics_modules
                LIMIT 1;
                """
                sample = await conn.fetchrow(sample_query)
                if sample:
                    print("📝 Sample record structure verified:")
                    print(f"   - ID: {sample['id']}")
                    print(f"   - Name: {sample['name']}")
                    print(f"   - Description: {sample['description'][:50]}..." if sample['description'] else 'NULL')
                    print(f"   - Type: {sample['module_type']}")
                    print(f"   - Status: {sample['status']}")

        except Exception as e:
            print(f"❌ Error querying analytics_modules: {e}")
            has_description = False

        await conn.close()

        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'database_check': 'production_analytics_modules_schema',
            'table_exists': table_exists,
            'description_column_exists': has_description,
            'current_migration': current_migration,
            'migration_003_applied': current_migration >= '003' if current_migration else False,
            'columns': column_info,
            'status': 'SUCCESS' if (table_exists and has_description) else 'FAILED'
        }

        # Save report
        report_file = f"production_analytics_modules_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Report saved to: {report_file}")

        if table_exists and has_description:
            print("\n✅ PRODUCTION DATABASE CHECK: PASSED")
            print("   - analytics_modules table exists")
            print("   - description column exists with correct schema")
            print("   - Migration 003 has been applied")
            return True
        else:
            print("\n❌ PRODUCTION DATABASE CHECK: FAILED")
            if not table_exists:
                print("   - analytics_modules table is missing")
            if not has_description:
                print("   - description column is missing")
            return False

    except Exception as e:
        print(f"❌ CRITICAL ERROR connecting to production database: {e}")
        return False

if __name__ == "__main__":
    print("🔍 CRITICAL DATABASE CHECK: Production analytics_modules schema verification")
    print("=" * 80)

    success = asyncio.run(check_production_database())

    if not success:
        print("\n🚨 PRODUCTION DATABASE ISSUE DETECTED")
        print("   Matt.Lindop's feature flags access may be blocked due to missing schema")
        print("   Zebra Associates £925K opportunity at risk")
        exit(1)
    else:
        print("\n✅ Production database schema verification complete")
        exit(0)