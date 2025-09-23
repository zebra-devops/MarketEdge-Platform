#!/usr/bin/env python3
"""
MANUAL EMERGENCY EXECUTION: Create missing tables directly
Use this if startup script still has issues - bypasses all logic
"""
import os
import sys
import logging
import psycopg2

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - MANUAL - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def manual_create_tables():
    """Direct table creation - no checks, no validation, just create"""

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL not configured")
        print("Set DATABASE_URL environment variable and run again")
        return False

    logger.info("🚨 MANUAL EMERGENCY: Creating 3 missing tables directly...")
    logger.info(f"🔗 Target: {database_url.split('@')[1] if '@' in database_url else 'database'}")

    try:
        # Direct connection with autocommit
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()

        # Drop and recreate to ensure clean state
        tables_to_create = [
            ("module_configurations", """
                DROP TABLE IF EXISTS module_configurations CASCADE;
                CREATE TABLE module_configurations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    module_id UUID NOT NULL,
                    config JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """),
            ("module_usage_logs", """
                DROP TABLE IF EXISTS module_usage_logs CASCADE;
                CREATE TABLE module_usage_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    module_id UUID NOT NULL,
                    organisation_id UUID NOT NULL,
                    user_id UUID,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """),
            ("sector_modules", """
                DROP TABLE IF EXISTS sector_modules CASCADE;
                CREATE TABLE sector_modules (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    sector VARCHAR(100) NOT NULL,
                    module_id UUID NOT NULL,
                    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
        ]

        success_count = 0

        for table_name, sql in tables_to_create:
            try:
                logger.info(f"🔧 Creating {table_name}...")
                cursor.execute(sql)
                logger.info(f"✅ {table_name} created successfully")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ {table_name} failed: {e}")

        # Verify all tables exist
        verification_sql = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('module_configurations', 'module_usage_logs', 'sector_modules')
        ORDER BY table_name;
        """

        cursor.execute(verification_sql)
        existing_tables = [row[0] for row in cursor.fetchall()]

        logger.info(f"📊 Results:")
        logger.info(f"   Created: {success_count}/3 tables")
        logger.info(f"   Verified: {existing_tables}")

        if len(existing_tables) == 3:
            logger.info("🎉 SUCCESS: All 3 tables now exist!")
            logger.info("🎯 Import errors should be resolved")
            logger.info("💰 £925K Zebra Associates opportunity: UNBLOCKED")

            # Test basic table access
            for table in existing_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    logger.info(f"   {table}: {count} rows")
                except Exception as e:
                    logger.warning(f"   {table}: access issue - {e}")

            return True
        else:
            missing = set(['module_configurations', 'module_usage_logs', 'sector_modules']) - set(existing_tables)
            logger.error(f"❌ Still missing tables: {missing}")
            return False

    except Exception as e:
        logger.error(f"🚨 MANUAL CREATION FAILED: {e}")
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

if __name__ == "__main__":
    print("🚨 MANUAL EMERGENCY TABLE CREATION")
    print("="*50)
    print("This bypasses all startup logic and creates tables directly")
    print("Use only if normal deployment process fails")
    print("="*50)

    success = manual_create_tables()

    if success:
        print("\n🎉 MANUAL REPAIR COMPLETE")
        print("✅ All 3 tables created successfully")
        print("🚀 Deploy should now work normally")
        sys.exit(0)
    else:
        print("\n❌ MANUAL REPAIR FAILED")
        print("🛑 Check logs above for specific errors")
        print("📞 Contact dev team for assistance")
        sys.exit(1)