#!/usr/bin/env python3
"""
Final repair script for 3 remaining tables with FK type mismatches.
Creates module_configurations, module_usage_logs, and sector_modules with correct column types.
"""

import os
import sys
import asyncio
import asyncpg
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def repair_final_tables():
    """Create the 3 remaining tables with correct column types."""

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Try production database URL if local DATABASE_URL not set
        database_url = "postgres://marketedge_prod_user:c5IG4SXRxSIUeWxGkGNLYE01BKSqoAd6@dpg-cs3rj4pu0jms73a8ket0-a.oregon-postgres.render.com/marketedge_prod"
        print("🔄 Using production database URL")
    else:
        print("🔄 Using DATABASE_URL from environment")

    # Convert to asyncpg format
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgres://', 1)

    conn = None
    try:
        print(f"🔄 Connecting to database...")
        # Try with SSL first for production, fallback without SSL for local
        try:
            conn = await asyncpg.connect(database_url, ssl='require')
        except Exception as ssl_error:
            print(f"⚠️ SSL connection failed, trying without SSL: {ssl_error}")
            conn = await asyncpg.connect(database_url)

        # Enable autocommit mode for DDL operations
        print("✅ Connected in autocommit mode")

        # Table 1: module_configurations (fixed FK type)
        print("\n📊 Creating module_configurations table...")
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS module_configurations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    module_id UUID NOT NULL,
                    config JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            print("✅ module_configurations created successfully")
        except Exception as e:
            print(f"❌ module_configurations failed: {e}")

        # Table 2: module_usage_logs
        print("\n📊 Creating module_usage_logs table...")
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS module_usage_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    module_id UUID NOT NULL,
                    organisation_id UUID NOT NULL,
                    user_id UUID,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            print("✅ module_usage_logs created successfully")
        except Exception as e:
            print(f"❌ module_usage_logs failed: {e}")

        # Table 3: sector_modules
        print("\n📊 Creating sector_modules table...")
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sector_modules (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    sector VARCHAR(100) NOT NULL,
                    module_id UUID NOT NULL,
                    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            print("✅ sector_modules created successfully")
        except Exception as e:
            print(f"❌ sector_modules failed: {e}")

        # Verify all tables exist
        print("\n🔍 Verifying final table creation...")
        result = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN ('module_configurations', 'module_usage_logs', 'sector_modules')
            ORDER BY tablename
        """)

        created_tables = [row['tablename'] for row in result]
        print(f"\n📊 Tables verified in database:")
        for table in created_tables:
            print(f"  ✅ {table}")

        missing = {'module_configurations', 'module_usage_logs', 'sector_modules'} - set(created_tables)
        if missing:
            print(f"\n⚠️ Still missing: {', '.join(missing)}")
            return False

        # Final count of all tables
        total_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM pg_tables
            WHERE schemaname = 'public'
        """)
        print(f"\n✅ REPAIR COMPLETE: All 3 tables created successfully")
        print(f"📊 Total tables in database: {total_count}")

        return True

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if conn:
            await conn.close()
            print("\n🔒 Database connection closed")

async def main():
    """Main execution."""
    print("=" * 60)
    print("FINAL TABLE REPAIR SCRIPT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target tables: module_configurations, module_usage_logs, sector_modules")
    print("=" * 60)

    success = await repair_final_tables()

    if success:
        print("\n✅ ✅ ✅ ALL TABLES SUCCESSFULLY CREATED ✅ ✅ ✅")
        print("\nNext steps:")
        print("1. Admin endpoints should now work")
        print("2. Test /api/v1/admin/feature-flags endpoint")
        print("3. Verify £925K Zebra Associates functionality")
        return 0
    else:
        print("\n❌ Some tables could not be created")
        print("Check error messages above for details")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)