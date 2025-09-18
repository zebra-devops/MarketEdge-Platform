#!/usr/bin/env python3
"""
Apply Analytics Modules Migration to Production
Applies the missing migration 003_add_phase3_enhancements.py to create analytics_modules table.

This script safely applies database migrations to resolve the missing analytics_modules table
that is causing 500 errors for Matt.Lindop's Feature Flags access.

CRITICAL: This must be run on the production server or with production DATABASE_URL set.
"""

import os
import sys
import subprocess
import asyncio
import asyncpg
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Verify we're in the correct environment for migration"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not found")
        logger.error("🔧 Set production DATABASE_URL before running migrations:")
        logger.error("   export DATABASE_URL='postgresql://[user]:[password]@[host]:[port]/[database]'")
        return False
    
    # Basic safety check - avoid running on local development
    if 'localhost' in database_url:
        logger.warning("⚠️  DATABASE_URL appears to be localhost")
        confirmation = input("Are you sure you want to run production migrations on localhost? (yes/no): ")
        if confirmation.lower() != 'yes':
            logger.info("❌ Migration cancelled by user")
            return False
    
    logger.info(f"✅ DATABASE_URL found: {database_url[:50]}...")
    return True

async def verify_database_connection():
    """Verify database connection before migration"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = await asyncpg.connect(database_url)
        
        # Test basic query
        result = await conn.fetchval("SELECT version()")
        logger.info(f"✅ Database connection verified: {result[:50]}...")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False

async def check_current_migration_status():
    """Check current migration status"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = await asyncpg.connect(database_url)
        
        # Check if alembic_version table exists
        alembic_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            );
        """)
        
        if alembic_exists:
            current_version = await conn.fetchval("SELECT version_num FROM alembic_version")
            logger.info(f"📋 Current migration: {current_version}")
        else:
            logger.warning("⚠️  alembic_version table does not exist")
            current_version = None
        
        # Check if analytics_modules exists
        analytics_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'analytics_modules'
            );
        """)
        
        await conn.close()
        
        return {
            'current_version': current_version,
            'alembic_exists': alembic_exists,
            'analytics_modules_exists': analytics_exists
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to check migration status: {str(e)}")
        return None

def run_alembic_migration():
    """Run alembic upgrade to apply pending migrations"""
    try:
        logger.info("🔄 Running alembic upgrade head...")
        
        # Run alembic upgrade command
        result = subprocess.run(
            ['python3', '-m', 'alembic', 'upgrade', 'head'],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("✅ Alembic upgrade completed successfully")
        logger.info(f"📋 Output: {result.stdout}")
        
        if result.stderr:
            logger.warning(f"⚠️  Stderr: {result.stderr}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Alembic upgrade failed with exit code {e.returncode}")
        logger.error(f"❌ Stdout: {e.stdout}")
        logger.error(f"❌ Stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to run alembic upgrade: {str(e)}")
        return False

async def verify_migration_success():
    """Verify that the migration was successful"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = await asyncpg.connect(database_url)
        
        # Check if analytics_modules table now exists
        analytics_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'analytics_modules'
            );
        """)
        
        # Check if feature_flags table exists
        feature_flags_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'feature_flags'
            );
        """)
        
        # Get updated migration version
        current_version = await conn.fetchval("SELECT version_num FROM alembic_version")
        
        await conn.close()
        
        success = analytics_exists and feature_flags_exists
        
        if success:
            logger.info("✅ Migration verification successful!")
            logger.info(f"✅ analytics_modules table: {'EXISTS' if analytics_exists else 'MISSING'}")
            logger.info(f"✅ feature_flags table: {'EXISTS' if feature_flags_exists else 'MISSING'}")
            logger.info(f"✅ Current migration: {current_version}")
        else:
            logger.error("❌ Migration verification failed!")
            logger.error(f"❌ analytics_modules table: {'EXISTS' if analytics_exists else 'MISSING'}")
            logger.error(f"❌ feature_flags table: {'EXISTS' if feature_flags_exists else 'MISSING'}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Failed to verify migration: {str(e)}")
        return False

async def main():
    """Main execution function"""
    logger.info("🚀 Starting Analytics Modules Migration Application")
    logger.info("=" * 60)
    logger.info("🎯 Purpose: Fix missing analytics_modules table causing 500 errors")
    logger.info("🎯 Target: Matt.Lindop Feature Flags access for £925K Zebra Associates")
    logger.info("=" * 60)
    
    # Step 1: Environment check
    if not check_environment():
        return False
    
    # Step 2: Database connection check
    if not await verify_database_connection():
        return False
    
    # Step 3: Check current migration status
    logger.info("\n📋 Checking current migration status...")
    status = await check_current_migration_status()
    if not status:
        return False
    
    if status['analytics_modules_exists']:
        logger.info("✅ analytics_modules table already exists!")
        logger.info("🔍 The 500 error may have a different root cause.")
        return True
    
    logger.info(f"❌ analytics_modules table missing - applying migrations...")
    
    # Step 4: Apply migrations
    logger.info("\n🔄 Applying database migrations...")
    if not run_alembic_migration():
        return False
    
    # Step 5: Verify success
    logger.info("\n🔍 Verifying migration success...")
    if not await verify_migration_success():
        return False
    
    # Step 6: Success summary
    logger.info("\n" + "=" * 60)
    logger.info("🎉 MIGRATION DEPLOYMENT SUCCESSFUL!")
    logger.info("=" * 60)
    logger.info("✅ analytics_modules table created")
    logger.info("✅ feature_flags table verified")
    logger.info("✅ Matt.Lindop's Feature Flags access should now work")
    logger.info("🔧 Next: Test Feature Flags endpoint to confirm fix")
    logger.info("📋 Test URL: https://marketedge-platform.onrender.com/api/v1/admin/feature-flags")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)