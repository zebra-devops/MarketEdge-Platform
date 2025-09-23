#!/usr/bin/env python3
"""
Deploy final table repair to production using Render API or direct database connection.
"""

import os
import sys
import asyncio
import asyncpg
from datetime import datetime

async def deploy_final_repair():
    """Execute the final repair script on production database."""

    # Production database URL
    production_db_url = "postgres://marketedge_prod_user:c5IG4SXRxSIUeWxGkGNLYE01BKSqoAd6@dpg-cs3rj4pu0jms73a8ket0-a.oregon-postgres.render.com/marketedge_prod"

    conn = None
    try:
        print(f"🔄 Connecting to production database...")
        conn = await asyncpg.connect(production_db_url, ssl='require')
        print("✅ Connected to production database")

        # Create the 3 remaining tables with correct column types
        tables_to_create = [
            ("module_configurations", """
                CREATE TABLE IF NOT EXISTS module_configurations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    module_id UUID NOT NULL,
                    config JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """),
            ("module_usage_logs", """
                CREATE TABLE IF NOT EXISTS module_usage_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    module_id UUID NOT NULL,
                    organisation_id UUID NOT NULL,
                    user_id UUID,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """),
            ("sector_modules", """
                CREATE TABLE IF NOT EXISTS sector_modules (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    sector VARCHAR(100) NOT NULL,
                    module_id UUID NOT NULL,
                    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
        ]

        success_count = 0
        for table_name, create_sql in tables_to_create:
            print(f"\n📊 Creating {table_name}...")
            try:
                await conn.execute(create_sql)
                print(f"✅ {table_name} created successfully")
                success_count += 1
            except Exception as e:
                print(f"❌ {table_name} failed: {e}")

        # Verify all tables exist
        print("\n🔍 Verifying production table creation...")
        result = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN ('module_configurations', 'module_usage_logs', 'sector_modules')
            ORDER BY tablename
        """)

        created_tables = [row['tablename'] for row in result]
        print(f"\n📊 Tables verified in production:")
        for table in created_tables:
            print(f"  ✅ {table}")

        # Get total table count
        total_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM pg_tables
            WHERE schemaname = 'public'
        """)

        print(f"\n✅ PRODUCTION REPAIR COMPLETE")
        print(f"📊 Created: {success_count}/3 tables")
        print(f"📊 Total tables in production: {total_count}")

        return success_count == 3

    except Exception as e:
        print(f"\n❌ Production repair failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if conn:
            await conn.close()
            print("\n🔒 Production database connection closed")

async def main():
    """Main execution."""
    print("=" * 60)
    print("PRODUCTION FINAL TABLE REPAIR")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target: Production database on Render")
    print("=" * 60)

    success = await deploy_final_repair()

    if success:
        print("\n🎉 🎉 🎉 PRODUCTION REPAIR SUCCESSFUL 🎉 🎉 🎉")
        print("\n✅ All missing tables created in production")
        print("✅ Admin endpoints should now work")
        print("✅ £925K Zebra Associates opportunity enabled")
        print("\n🔗 Test endpoint: https://marketedge-platform.onrender.com/api/v1/admin/feature-flags")
        return 0
    else:
        print("\n❌ Production repair failed")
        print("Check error messages above for details")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)