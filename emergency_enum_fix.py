#!/usr/bin/env python3
"""
Emergency Database Enum Fix Script

This script investigates and fixes the enum mismatch issue causing 500 errors.
The issue: Existing database records have lowercase 'default' values but the enum expects uppercase 'DEFAULT'.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    return database_url

def investigate_enum_issue(engine):
    """Investigate the enum mismatch issue"""
    logger.info("=== INVESTIGATING ENUM ISSUE ===")
    
    try:
        with engine.connect() as conn:
            # Check current enum definition
            result = conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = 'industry'
                )
                ORDER BY enumlabel;
            """))
            
            enum_values = [row[0] for row in result.fetchall()]
            logger.info(f"Current enum values in database: {enum_values}")
            
            # Check organisations table for problematic records
            result = conn.execute(text("""
                SELECT id, name, industry, industry_type 
                FROM organisations 
                WHERE name = 'Default'
                LIMIT 5;
            """))
            
            default_orgs = result.fetchall()
            logger.info(f"Found {len(default_orgs)} organisations with name='Default':")
            for org in default_orgs:
                logger.info(f"  ID: {org[0]}, Name: {org[1]}, Industry: {org[2]}, Industry_Type: {org[3]}")
            
            # Check for any records with lowercase enum values
            result = conn.execute(text("""
                SELECT id, name, industry_type::text
                FROM organisations 
                WHERE industry_type::text = 'default'
                LIMIT 10;
            """))
            
            lowercase_records = result.fetchall()
            logger.info(f"Found {len(lowercase_records)} records with lowercase 'default' enum:")
            for record in lowercase_records:
                logger.info(f"  ID: {record[0]}, Name: {record[1]}, Industry_Type: {record[2]}")
            
            # Check all distinct enum values currently in use
            result = conn.execute(text("""
                SELECT DISTINCT industry_type::text as industry_value, COUNT(*) as count
                FROM organisations 
                GROUP BY industry_type::text
                ORDER BY industry_value;
            """))
            
            enum_usage = result.fetchall()
            logger.info("Current enum usage in organisations table:")
            for usage in enum_usage:
                logger.info(f"  '{usage[0]}': {usage[1]} records")
                
    except SQLAlchemyError as e:
        logger.error(f"Database error during investigation: {e}")
        return False
    
    return True

def fix_enum_values(engine, dry_run=True):
    """Fix the enum mismatch by updating lowercase values to uppercase"""
    logger.info("=== FIXING ENUM VALUES ===")
    
    try:
        with engine.connect() as conn:
            if not dry_run:
                # Start a transaction
                trans = conn.begin()
            
            # First, check what needs to be fixed
            result = conn.execute(text("""
                SELECT id, name, industry_type::text
                FROM organisations 
                WHERE industry_type::text = 'default';
            """))
            
            records_to_fix = result.fetchall()
            logger.info(f"Found {len(records_to_fix)} records with lowercase 'default' that need fixing")
            
            if len(records_to_fix) == 0:
                logger.info("No records need fixing - enum values are already correct")
                return True
            
            if dry_run:
                logger.info("DRY RUN MODE - The following records would be updated:")
                for record in records_to_fix:
                    logger.info(f"  ID: {record[0]}, Name: {record[1]}, Current: '{record[2]}' -> New: 'DEFAULT'")
                return True
            
            # Apply the fix - update lowercase 'default' to uppercase 'DEFAULT'
            update_sql = """
                UPDATE organisations 
                SET industry_type = 'DEFAULT'::industry
                WHERE industry_type::text = 'default';
            """
            
            result = conn.execute(text(update_sql))
            updated_count = result.rowcount
            
            logger.info(f"Successfully updated {updated_count} records from 'default' to 'DEFAULT'")
            
            # Verify the fix
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM organisations 
                WHERE industry_type::text = 'default';
            """))
            
            remaining_lowercase = result.fetchone()[0]
            
            if remaining_lowercase == 0:
                logger.info("✅ Fix successful - no lowercase 'default' values remain")
                if not dry_run:
                    trans.commit()
            else:
                logger.error(f"❌ Fix incomplete - {remaining_lowercase} lowercase values still remain")
                if not dry_run:
                    trans.rollback()
                return False
                
    except SQLAlchemyError as e:
        logger.error(f"Database error during fix: {e}")
        if not dry_run:
            trans.rollback()
        return False
    
    return True

def test_auth_endpoint_compatibility(engine):
    """Test if the auth endpoint query will work after the fix"""
    logger.info("=== TESTING AUTH ENDPOINT COMPATIBILITY ===")
    
    try:
        with engine.connect() as conn:
            # Simulate the exact query from auth.py line 255
            result = conn.execute(text("""
                SELECT id, name, industry_type 
                FROM organisations 
                WHERE name = 'Default'
                LIMIT 1;
            """))
            
            default_org = result.fetchone()
            
            if default_org:
                logger.info(f"✅ Default organisation found:")
                logger.info(f"  ID: {default_org[0]}")
                logger.info(f"  Name: {default_org[1]}")
                logger.info(f"  Industry_Type: {default_org[2]}")
                logger.info("✅ Auth endpoint query should work correctly")
                return True
            else:
                logger.warning("❌ No default organisation found - this could cause issues")
                return False
                
    except SQLAlchemyError as e:
        logger.error(f"❌ Auth endpoint test failed: {e}")
        return False

def main():
    """Main execution function"""
    logger.info("Starting Emergency Enum Fix Script")
    
    # Get database connection
    database_url = get_database_url()
    engine = create_engine(database_url, echo=False)
    
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
        
        # Step 1: Investigate the issue
        if not investigate_enum_issue(engine):
            logger.error("Investigation failed")
            sys.exit(1)
        
        # Step 2: Run dry-run fix
        logger.info("\n" + "="*50)
        if not fix_enum_values(engine, dry_run=True):
            logger.error("Dry run failed")
            sys.exit(1)
        
        # Step 3: Test compatibility
        logger.info("\n" + "="*50)
        if not test_auth_endpoint_compatibility(engine):
            logger.warning("Auth endpoint compatibility test failed")
        
        # Step 4: Ask for confirmation to apply the fix
        logger.info("\n" + "="*50)
        logger.info("READY TO APPLY FIX")
        logger.info("This will update lowercase 'default' enum values to uppercase 'DEFAULT'")
        
        if len(sys.argv) > 1 and sys.argv[1] == '--apply':
            logger.info("APPLYING FIX (--apply flag detected)")
            if fix_enum_values(engine, dry_run=False):
                logger.info("✅ Fix applied successfully!")
                
                # Final verification
                logger.info("\n" + "="*50)
                test_auth_endpoint_compatibility(engine)
            else:
                logger.error("❌ Fix failed!")
                sys.exit(1)
        else:
            logger.info("Run with --apply flag to actually apply the fix")
            logger.info("Example: python emergency_enum_fix.py --apply")
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)
    finally:
        engine.dispose()
    
    logger.info("Emergency Enum Fix Script completed")

if __name__ == "__main__":
    main()