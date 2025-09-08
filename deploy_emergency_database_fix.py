#!/usr/bin/env python3
"""
EMERGENCY DATABASE SCHEMA FIX DEPLOYMENT SCRIPT
===============================================

For £925K Zebra Associates opportunity - Critical production fix
Fixes: relation "feature_flags" does not exist errors

This script safely deploys the database schema fix to production.
"""

import os
import sys
import psycopg2
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'emergency_db_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not found")
        sys.exit(1)
    return db_url

def test_database_connection(db_url):
    """Test database connection before proceeding"""
    try:
        logger.info("🔍 Testing database connection...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version(), current_database(), current_user")
        version, database, user = cursor.fetchone()
        logger.info(f"✅ Connected to database: {database} as {user}")
        logger.info(f"📊 PostgreSQL version: {version}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def check_table_exists(db_url, table_name):
    """Check if a table exists in the database"""
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            )
        """, (table_name,))
        exists = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        logger.error(f"Error checking table {table_name}: {e}")
        return False

def get_alembic_version(db_url):
    """Get current Alembic version"""
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return version
    except Exception as e:
        logger.warning(f"Could not get Alembic version: {e}")
        return None

def execute_sql_file(db_url, sql_file_path):
    """Execute SQL file with error handling and transaction control"""
    try:
        logger.info(f"📂 Loading SQL file: {sql_file_path}")
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        logger.info("🚀 Executing database schema fix...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = False  # Use transaction
        cursor = conn.cursor()
        
        try:
            # Execute the SQL
            cursor.execute(sql_content)
            
            # Commit the transaction
            conn.commit()
            logger.info("✅ Database schema fix executed successfully")
            
            # Fetch and log verification results
            cursor.execute("""
                SELECT COUNT(*) FROM feature_flags 
                WHERE flag_key IN ('admin.advanced_controls', 'market_edge.enhanced_ui')
            """)
            flag_count = cursor.fetchone()[0]
            logger.info(f"✅ Verification: {flag_count} critical feature flags created")
            
        except Exception as e:
            logger.error(f"❌ Error during SQL execution: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to execute SQL file: {e}")
        return False

def verify_fix(db_url):
    """Verify the fix was applied correctly"""
    logger.info("🔍 Verifying database fix...")
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Check feature_flags table exists
        if not check_table_exists(db_url, 'feature_flags'):
            logger.error("❌ feature_flags table still doesn't exist!")
            return False
        
        # Check specific flags exist
        cursor.execute("""
            SELECT flag_key, is_enabled FROM feature_flags 
            WHERE flag_key IN ('admin.advanced_controls', 'market_edge.enhanced_ui')
            ORDER BY flag_key
        """)
        flags = cursor.fetchall()
        
        logger.info("✅ Critical feature flags status:")
        for flag_key, is_enabled in flags:
            status = "ENABLED" if is_enabled else "DISABLED"
            logger.info(f"   • {flag_key}: {status}")
        
        if len(flags) < 2:
            logger.error("❌ Not all critical feature flags were created!")
            return False
        
        # Test the exact query that was failing
        cursor.execute("""
            SELECT id, flag_key, name, is_enabled 
            FROM feature_flags 
            WHERE flag_key = 'admin.advanced_controls'
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        if result:
            logger.info(f"✅ Query test passed: admin.advanced_controls found (ID: {result[0]})")
        else:
            logger.error("❌ Query test failed: admin.advanced_controls not found")
            return False
        
        cursor.close()
        conn.close()
        
        logger.info("🎯 ALL VERIFICATIONS PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def create_backup_info(db_url):
    """Create a backup info file with current state"""
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        backup_info = {
            'timestamp': datetime.now().isoformat(),
            'alembic_version': get_alembic_version(db_url),
            'tables_before_fix': []
        }
        
        # Get list of existing tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        backup_info['tables_before_fix'] = tables
        
        cursor.close()
        conn.close()
        
        # Write backup info
        backup_file = f"backup_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(backup_file, 'w') as f:
            f.write(f"Database state before emergency fix\n")
            f.write(f"Timestamp: {backup_info['timestamp']}\n")
            f.write(f"Alembic version: {backup_info['alembic_version']}\n")
            f.write(f"Tables present: {len(backup_info['tables_before_fix'])}\n")
            f.write(f"Tables list:\n")
            for table in backup_info['tables_before_fix']:
                f.write(f"  - {table}\n")
        
        logger.info(f"📄 Backup info saved to: {backup_file}")
        
    except Exception as e:
        logger.warning(f"Could not create backup info: {e}")

def main():
    """Main execution function"""
    logger.info("=" * 80)
    logger.info("🚨 EMERGENCY DATABASE SCHEMA FIX DEPLOYMENT")
    logger.info("💰 FOR £925K ZEBRA ASSOCIATES OPPORTUNITY")
    logger.info("🎯 FIXING: relation 'feature_flags' does not exist")
    logger.info("=" * 80)
    
    # Get database URL
    db_url = get_database_url()
    logger.info(f"🔗 Using database: {db_url.split('@')[1] if '@' in db_url else 'hidden'}")
    
    # Test connection
    if not test_database_connection(db_url):
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Create backup info
    create_backup_info(db_url)
    
    # Check current state
    logger.info("🔍 Checking current database state...")
    feature_flags_exists = check_table_exists(db_url, 'feature_flags')
    alembic_version = get_alembic_version(db_url)
    
    logger.info(f"📊 Current state:")
    logger.info(f"   • feature_flags table exists: {feature_flags_exists}")
    logger.info(f"   • Alembic version: {alembic_version}")
    
    if feature_flags_exists:
        logger.warning("⚠️  feature_flags table already exists!")
        logger.info("🔍 This might indicate the issue is elsewhere...")
        
        # Still proceed to verify and potentially insert missing flags
        logger.info("🔄 Proceeding with flag verification/creation...")
    
    # Locate SQL file
    sql_file = Path(__file__).parent / "EMERGENCY_DATABASE_SCHEMA_FIX.sql"
    if not sql_file.exists():
        logger.error(f"❌ SQL file not found: {sql_file}")
        sys.exit(1)
    
    # Execute the fix
    logger.info("🚀 DEPLOYING EMERGENCY FIX...")
    if execute_sql_file(db_url, sql_file):
        logger.info("✅ SQL execution completed")
    else:
        logger.error("❌ SQL execution failed")
        sys.exit(1)
    
    # Verify the fix
    if verify_fix(db_url):
        logger.info("🎉 EMERGENCY FIX DEPLOYED SUCCESSFULLY!")
        logger.info("💼 matt.lindop@zebra.associates should now be able to access admin dashboard")
        logger.info("🎯 £925K Zebra Associates opportunity is UNBLOCKED!")
    else:
        logger.error("❌ Fix verification failed")
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("✅ DEPLOYMENT COMPLETE - SYSTEM READY FOR PRODUCTION USE")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()