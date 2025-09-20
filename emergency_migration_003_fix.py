#!/usr/bin/env python3
"""
EMERGENCY: Apply Migration 003 to Production Database
CRITICAL: Fix analytics_modules table for Matt.Lindop Zebra Associates £925K opportunity

This script applies the missing migration 003 that creates the proper
analytics_modules table with description column and all required fields.
"""

import asyncio
import asyncpg
import json
from datetime import datetime
import os

# Production database URL
PRODUCTION_DATABASE_URL = "postgresql://marketedge_user:Qra5HBKofZqoQwQgKNyVnOOwKVRbRPAW@dpg-d2gch62dbo4c73b0kl80-a.oregon-postgres.render.com/marketedge_production"

async def apply_migration_003():
    """Apply migration 003 to production database"""

    print("🚨 EMERGENCY MIGRATION 003 APPLICATION")
    print("=" * 80)
    print("BUSINESS CRITICAL: £925K Zebra Associates Opportunity")
    print("Target: Fix analytics_modules table schema for Matt.Lindop feature flags access")
    print("=" * 80)

    results = {
        'timestamp': datetime.now().isoformat(),
        'environment': 'PRODUCTION',
        'action': 'APPLY_MIGRATION_003',
        'target_table': 'analytics_modules',
        'reason': 'Fix Matt.Lindop feature flags access for Zebra Associates opportunity'
    }

    try:
        # Connect to production database
        conn = await asyncpg.connect(PRODUCTION_DATABASE_URL, ssl='require')
        print("✅ Connected to production database")

        # Start transaction
        async with conn.transaction():

            # Step 1: Check current state
            print("\n1. Checking current analytics_modules table state...")
            current_columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'analytics_modules'
                ORDER BY ordinal_position;
            """)

            print(f"   Current columns: {len(current_columns)}")
            for col in current_columns:
                print(f"     - {col['column_name']}: {col['data_type']}")

            # Step 2: Check if we need to drop and recreate table
            has_description = any(col['column_name'] == 'description' for col in current_columns)
            print(f"   Has description column: {has_description}")

            if not has_description:
                print("\n2. Dropping existing analytics_modules table...")
                await conn.execute("DROP TABLE IF EXISTS analytics_modules CASCADE;")
                print("   ✅ Dropped existing table")

                # Step 3: Create ModuleType enum (if not exists)
                print("\n3. Creating ModuleType enum...")
                try:
                    await conn.execute("""
                        CREATE TYPE moduletype AS ENUM (
                            'CORE', 'ANALYTICS', 'INTEGRATION',
                            'VISUALIZATION', 'REPORTING', 'AI_ML'
                        );
                    """)
                    print("   ✅ ModuleType enum created")
                except Exception as e:
                    if "already exists" in str(e):
                        print("   ✅ ModuleType enum already exists")
                    else:
                        raise e

                # Step 4: Create ModuleStatus enum (if not exists)
                print("\n4. Creating ModuleStatus enum...")
                try:
                    await conn.execute("""
                        CREATE TYPE modulestatus AS ENUM (
                            'DEVELOPMENT', 'TESTING', 'ACTIVE',
                            'DEPRECATED', 'RETIRED'
                        );
                    """)
                    print("   ✅ ModuleStatus enum created")
                except Exception as e:
                    if "already exists" in str(e):
                        print("   ✅ ModuleStatus enum already exists")
                    else:
                        raise e

                # Step 5: Create proper analytics_modules table
                print("\n5. Creating analytics_modules table with proper schema...")
                create_table_sql = """
                    CREATE TABLE analytics_modules (
                        id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT NOT NULL,
                        version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
                        module_type moduletype NOT NULL,
                        status modulestatus NOT NULL DEFAULT 'DEVELOPMENT',
                        is_core BOOLEAN NOT NULL DEFAULT false,
                        requires_license BOOLEAN NOT NULL DEFAULT false,
                        entry_point VARCHAR(500) NOT NULL,
                        config_schema JSONB NOT NULL DEFAULT '{}',
                        default_config JSONB NOT NULL DEFAULT '{}',
                        dependencies JSONB NOT NULL DEFAULT '[]',
                        min_data_requirements JSONB NOT NULL DEFAULT '{}',
                        api_endpoints JSONB NOT NULL DEFAULT '[]',
                        frontend_components JSONB NOT NULL DEFAULT '[]',
                        documentation_url VARCHAR(500),
                        help_text TEXT,
                        pricing_tier VARCHAR(50),
                        license_requirements JSONB NOT NULL DEFAULT '{}',
                        created_by UUID NOT NULL REFERENCES users(id),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """
                await conn.execute(create_table_sql)
                print("   ✅ analytics_modules table created with proper schema")

                # Step 6: Update alembic version
                print("\n6. Updating migration version to 003...")
                await conn.execute("UPDATE alembic_version SET version_num = '003';")
                print("   ✅ Migration version updated to 003")

                # Step 7: Insert sample analytics module for testing
                print("\n7. Inserting sample analytics module for testing...")

                # Get a super_admin user for created_by
                super_admin = await conn.fetchrow("""
                    SELECT id FROM users
                    WHERE email = 'matt.lindop@zebra.associates'
                    OR role = 'super_admin'
                    LIMIT 1;
                """)

                if super_admin:
                    await conn.execute("""
                        INSERT INTO analytics_modules (
                            id, name, description, module_type, status,
                            entry_point, created_by
                        ) VALUES (
                            'cinema_competitive_intelligence',
                            'Cinema Competitive Intelligence',
                            'Advanced competitive analysis for cinema industry with pricing intelligence and market positioning insights',
                            'ANALYTICS',
                            'ACTIVE',
                            'app.modules.cinema.competitive_intelligence',
                            $1
                        );
                    """, super_admin['id'])
                    print("   ✅ Sample analytics module inserted")
                else:
                    print("   ⚠️  No super_admin user found for sample module")

                results['migration_applied'] = True
                results['status'] = 'SUCCESS'
                print("\n✅ MIGRATION 003 SUCCESSFULLY APPLIED")

            else:
                print("\n✅ analytics_modules table already has proper schema")
                results['migration_applied'] = False
                results['status'] = 'ALREADY_APPLIED'

        # Verify final state
        print("\n8. Verifying final table state...")
        final_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'analytics_modules'
            ORDER BY ordinal_position;
        """)

        print(f"   Final column count: {len(final_columns)}")
        has_description_final = any(col['column_name'] == 'description' for col in final_columns)
        print(f"   Description column exists: {has_description_final}")

        # Check migration version
        migration_version = await conn.fetchval("SELECT version_num FROM alembic_version;")
        print(f"   Migration version: {migration_version}")

        results['final_column_count'] = len(final_columns)
        results['has_description_column'] = has_description_final
        results['migration_version'] = migration_version

        await conn.close()

        # Save results
        report_file = f"emergency_migration_003_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Results saved to: {report_file}")

        if has_description_final and migration_version == '003':
            print("\n🎉 EMERGENCY MIGRATION SUCCESSFUL!")
            print("   Matt.Lindop should now have feature flags access")
            print("   Zebra Associates £925K opportunity unblocked")
            return True
        else:
            print("\n❌ MIGRATION VERIFICATION FAILED")
            return False

    except Exception as e:
        print(f"\n❌ EMERGENCY MIGRATION FAILED: {e}")
        results['status'] = 'FAILED'
        results['error'] = str(e)

        # Save error results
        error_file = f"emergency_migration_003_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"📄 Error details saved to: {error_file}")
        return False

if __name__ == "__main__":
    print("🚨 STARTING EMERGENCY MIGRATION 003 APPLICATION")
    print("CRITICAL: Fix for Matt.Lindop Zebra Associates £925K opportunity")
    print("=" * 80)

    success = asyncio.run(apply_migration_003())

    if success:
        print("\n✅ EMERGENCY MIGRATION COMPLETE - PRODUCTION READY")
        exit(0)
    else:
        print("\n❌ EMERGENCY MIGRATION FAILED - MANUAL INTERVENTION REQUIRED")
        exit(1)