#!/usr/bin/env python3
"""
Production Database Analytics Modules Diagnostic
Diagnoses the missing analytics_modules table issue causing 500 errors.

This script:
1. Connects to production database
2. Checks current migration status
3. Verifies if analytics_modules table exists
4. Identifies the root cause of the missing table
5. Provides remediation steps
"""

import os
import asyncio
import asyncpg
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Production database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

# If DATABASE_URL not found, prompt for it or use default
if not DATABASE_URL:
    print("DATABASE_URL environment variable not found.")
    print("Please set the production DATABASE_URL:")
    print("export DATABASE_URL='postgresql://[username]:[password]@[host]:[port]/[database]'")
    print("\nFor Render.com production database, find this in:")
    print("1. Render Dashboard > PostgreSQL service > Connect tab")
    print("2. Copy the 'External Database URL'")
    print("\nAlternatively, run this script on the production server where DATABASE_URL is set.")
    exit(1)

async def check_database_status():
    """Check production database migration status and table existence"""
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "database_connection": False,
        "alembic_version_table_exists": False,
        "current_migration": None,
        "analytics_modules_exists": False,
        "feature_flags_exists": False,
        "migration_history": [],
        "table_count": 0,
        "error_details": None,
        "recommended_actions": []
    }
    
    try:
        # Connect to database
        logger.info("Connecting to production database...")
        conn = await asyncpg.connect(DATABASE_URL)
        results["database_connection"] = True
        logger.info("✅ Database connection successful")
        
        # Check if alembic_version table exists
        alembic_check = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            );
        """)
        results["alembic_version_table_exists"] = alembic_check
        
        if alembic_check:
            # Get current migration version
            current_version = await conn.fetchval("SELECT version_num FROM alembic_version")
            results["current_migration"] = current_version
            logger.info(f"📋 Current migration: {current_version}")
        else:
            logger.warning("⚠️ alembic_version table does not exist")
            results["recommended_actions"].append("Initialize Alembic migration tracking")
        
        # Check if analytics_modules table exists
        analytics_modules_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'analytics_modules'
            );
        """)
        results["analytics_modules_exists"] = analytics_modules_exists
        
        if analytics_modules_exists:
            logger.info("✅ analytics_modules table exists")
        else:
            logger.error("❌ analytics_modules table MISSING - This is the root cause!")
            results["recommended_actions"].append("Run migration 003_add_phase3_enhancements.py to create analytics_modules table")
        
        # Check if feature_flags table exists
        feature_flags_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'feature_flags'
            );
        """)
        results["feature_flags_exists"] = feature_flags_exists
        
        if feature_flags_exists:
            logger.info("✅ feature_flags table exists")
        else:
            logger.error("❌ feature_flags table MISSING")
            results["recommended_actions"].append("Run migration 003_add_phase3_enhancements.py to create feature_flags table")
        
        # Get total table count
        table_count = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        results["table_count"] = table_count
        logger.info(f"📊 Total tables in public schema: {table_count}")
        
        # List all tables for debugging
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        table_names = [row['table_name'] for row in tables]
        logger.info(f"📝 Tables present: {', '.join(table_names)}")
        
        # Check for specific critical tables from migration 003
        critical_tables = ['analytics_modules', 'feature_flags', 'sic_codes', 'audit_logs']
        missing_tables = []
        
        for table in critical_tables:
            exists = table in table_names
            if not exists:
                missing_tables.append(table)
                logger.error(f"❌ Critical table missing: {table}")
        
        if missing_tables:
            results["recommended_actions"].append(f"Missing critical tables: {', '.join(missing_tables)}")
            results["recommended_actions"].append("Run 'python3 -m alembic upgrade head' to apply all pending migrations")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ Database diagnostic failed: {str(e)}")
        results["error_details"] = str(e)
        results["recommended_actions"].append("Check database connection and credentials")
    
    return results

async def main():
    """Main execution function"""
    logger.info("🔍 Starting Production Database Analytics Modules Diagnostic")
    logger.info("=" * 60)
    
    # Run database status check
    results = await check_database_status()
    
    # Generate summary report
    logger.info("\n" + "=" * 60)
    logger.info("📋 DIAGNOSTIC SUMMARY")
    logger.info("=" * 60)
    
    print(f"Database Connection: {'✅' if results['database_connection'] else '❌'}")
    print(f"Current Migration: {results['current_migration'] or 'Not found'}")
    print(f"Analytics Modules Table: {'✅' if results['analytics_modules_exists'] else '❌ MISSING'}")
    print(f"Feature Flags Table: {'✅' if results['feature_flags_exists'] else '❌ MISSING'}")
    print(f"Total Tables: {results['table_count']}")
    
    if results["recommended_actions"]:
        print("\n🔧 RECOMMENDED ACTIONS:")
        for i, action in enumerate(results["recommended_actions"], 1):
            print(f"  {i}. {action}")
    
    # Root cause analysis
    print("\n🎯 ROOT CAUSE ANALYSIS:")
    if not results["analytics_modules_exists"]:
        print("❌ The analytics_modules table is missing from production database")
        print("❌ This causes SQLAlchemy 'relation does not exist' errors")
        print("❌ Matt.Lindop's Feature Flags access fails with 500 Internal Server Error")
        print("❌ Migration 003_add_phase3_enhancements.py was not applied to production")
    else:
        print("✅ analytics_modules table exists - issue may be elsewhere")
    
    # Save results to file
    import json
    output_file = f"production_analytics_modules_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📄 Diagnostic results saved to: {output_file}")
    
    if not results["analytics_modules_exists"]:
        logger.info("\n🚨 CRITICAL: Missing analytics_modules table confirmed")
        logger.info("🔧 NEXT STEPS: Run database migrations to create missing tables")
        logger.info("📋 Command: python3 -m alembic upgrade head")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())