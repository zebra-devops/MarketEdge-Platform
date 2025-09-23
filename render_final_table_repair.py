#!/usr/bin/env python3
"""
EMERGENCY: Create final 3 missing database tables directly on Render
"""
import os
import sys
import logging
import psycopg2
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_final_tables():
    """Create the 3 missing tables with correct FK types"""

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL not configured")
        return False

    try:
        logger.info("🚨 EMERGENCY: Creating final 3 missing tables...")

        # Connect with autocommit for DDL
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()

        # Define the 3 missing tables with correct types
        tables = [
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

        created_count = 0

        for table_name, create_sql in tables:
            try:
                logger.info(f"📊 Creating {table_name}...")
                cursor.execute(create_sql)
                created_count += 1
                logger.info(f"✅ {table_name} created successfully")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"🔄 {table_name} already exists - skipping")
                    created_count += 1
                else:
                    logger.error(f"❌ {table_name} failed: {e}")

        # Verify tables exist
        verification_count = 0
        for table_name, _ in tables:
            try:
                cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                verification_count += 1
                logger.info(f"✅ Verified: {table_name}")
            except Exception as e:
                logger.warning(f"⚠️  Verification failed for {table_name}: {e}")

        cursor.close()
        conn.close()

        logger.info(f"📊 Final Results:")
        logger.info(f"   - Tables processed: {created_count}/3")
        logger.info(f"   - Tables verified: {verification_count}/3")

        if verification_count == 3:
            logger.info("🎉 SUCCESS: All 3 tables now exist!")
            logger.info("🎯 Schema repair complete - admin endpoints should work")
            logger.info("💰 £925K Zebra Associates opportunity: UNBLOCKED")
            return True
        else:
            logger.warning("⚠️  Partial success - some tables still missing")
            return False

    except Exception as e:
        logger.error(f"🚨 EMERGENCY REPAIR FAILED: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚨 STARTING EMERGENCY TABLE REPAIR")
    success = create_final_tables()
    exit_code = 0 if success else 1
    logger.info(f"🏁 Emergency repair finished with exit code: {exit_code}")
    sys.exit(exit_code)