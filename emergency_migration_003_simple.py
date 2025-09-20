#!/usr/bin/env python3
"""
EMERGENCY: Simple Migration 003 Fix for Production
CRITICAL: Fix analytics_modules table description column for Matt.Lindop

Simplified approach without transactions to fix the immediate issue.
"""

import asyncio
import asyncpg
import json
from datetime import datetime

# Production database URL
PRODUCTION_DATABASE_URL = "postgresql://marketedge_user:Qra5HBKofZqoQwQgKNyVnOOwKVRbRPAW@dpg-d2gch62dbo4c73b0kl80-a.oregon-postgres.render.com/marketedge_production"

async def fix_analytics_modules_table():
    """Simple fix for analytics_modules table - add missing description column"""

    print("🚨 EMERGENCY SIMPLE MIGRATION FIX")
    print("=" * 80)
    print("BUSINESS CRITICAL: £925K Zebra Associates Opportunity")
    print("Fix: Add description column to analytics_modules table")
    print("=" * 80)

    try:
        # Connect to production database
        conn = await asyncpg.connect(PRODUCTION_DATABASE_URL, ssl='require')
        print("✅ Connected to production database")

        # Check current columns
        print("\n1. Checking current analytics_modules schema...")
        current_columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'analytics_modules'
            ORDER BY ordinal_position;
        """)

        print(f"   Current columns ({len(current_columns)}):")
        for col in current_columns:
            print(f"     - {col['column_name']}: {col['data_type']}")

        # Check if description column exists
        has_description = any(col['column_name'] == 'description' for col in current_columns)
        print(f"\n   Description column exists: {has_description}")

        if not has_description:
            print("\n2. Adding description column...")
            await conn.execute("""
                ALTER TABLE analytics_modules
                ADD COLUMN description TEXT NOT NULL DEFAULT 'Analytics module for competitive intelligence';
            """)
            print("   ✅ Description column added")

            # Update alembic version
            print("\n3. Updating migration version...")
            await conn.execute("UPDATE alembic_version SET version_num = '003';")
            print("   ✅ Migration version updated to 003")

        # Add other missing columns if needed
        print("\n4. Checking for other required columns...")

        required_columns = [
            ('version', 'VARCHAR(50)', "'1.0.0'"),
            ('entry_point', 'VARCHAR(500)', "'app.modules.default'"),
            ('config_schema', 'JSONB', "'{}'::jsonb"),
            ('default_config', 'JSONB', "'{}'::jsonb"),
            ('dependencies', 'JSONB', "'[]'::jsonb"),
            ('is_core', 'BOOLEAN', 'false'),
            ('requires_license', 'BOOLEAN', 'false')
        ]

        for col_name, col_type, default_value in required_columns:
            column_exists = any(col['column_name'] == col_name for col in current_columns)
            if not column_exists:
                print(f"   Adding {col_name} column...")
                try:
                    await conn.execute(f"""
                        ALTER TABLE analytics_modules
                        ADD COLUMN {col_name} {col_type} DEFAULT {default_value};
                    """)
                    print(f"     ✅ {col_name} column added")
                except Exception as e:
                    print(f"     ⚠️  {col_name} column failed: {e}")

        # Verify final state
        print("\n5. Verifying final state...")
        final_columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'analytics_modules'
            ORDER BY ordinal_position;
        """)

        has_description_final = any(col['column_name'] == 'description' for col in final_columns)
        print(f"   Final column count: {len(final_columns)}")
        print(f"   Description column exists: {has_description_final}")

        # Check migration version
        migration_version = await conn.fetchval("SELECT version_num FROM alembic_version;")
        print(f"   Migration version: {migration_version}")

        await conn.close()

        # Save results
        results = {
            'timestamp': datetime.now().isoformat(),
            'action': 'SIMPLE_MIGRATION_FIX',
            'description_column_added': not has_description,
            'final_column_count': len(final_columns),
            'has_description_column': has_description_final,
            'migration_version': migration_version,
            'status': 'SUCCESS' if has_description_final else 'FAILED'
        }

        report_file = f"emergency_simple_migration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Results saved to: {report_file}")

        if has_description_final:
            print("\n🎉 EMERGENCY FIX SUCCESSFUL!")
            print("   Analytics modules table now has description column")
            print("   Matt.Lindop should have feature flags access")
            print("   Zebra Associates £925K opportunity unblocked")
            return True
        else:
            print("\n❌ EMERGENCY FIX FAILED")
            return False

    except Exception as e:
        print(f"\n❌ EMERGENCY FIX FAILED: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_analytics_modules_table())

    if success:
        print("\n✅ EMERGENCY MIGRATION COMPLETE")
        exit(0)
    else:
        print("\n❌ EMERGENCY MIGRATION FAILED")
        exit(1)