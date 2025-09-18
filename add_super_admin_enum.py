#!/usr/bin/env python3
"""
Database Enum Update Script - Add super_admin Role
Part of £925K Zebra Associates opportunity resolution

This script adds 'super_admin' to the PostgreSQL enum type 'userrole'
Required before promoting Matt Lindop to super_admin role.

Usage: python add_super_admin_enum.py
"""

import sys
import os
import logging
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
    from sqlalchemy.exc import SQLAlchemyError
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("   Run: pip install sqlalchemy psycopg2-binary")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseEnumUpdater:
    """Updates PostgreSQL enum types for role system"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine: Engine = None
        
    def connect_to_database(self) -> bool:
        """Connect to production database"""
        try:
            logger.info("🔌 Connecting to production database...")
            
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    "connect_timeout": 30,
                    "application_name": "enum_updater"
                }
            )
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                
            if test_value == 1:
                logger.info("✅ Database connection successful")
                return True
            else:
                logger.error("❌ Database connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False
    
    def check_current_enum_values(self) -> list:
        """Check current values in userrole enum"""
        logger.info("📋 Checking current enum values...")
        
        try:
            with self.engine.connect() as conn:
                # Query enum values
                query = text("""
                    SELECT enumlabel 
                    FROM pg_enum 
                    WHERE enumtypid = (
                        SELECT oid 
                        FROM pg_type 
                        WHERE typname = 'userrole'
                    )
                    ORDER BY enumsortorder;
                """)
                
                result = conn.execute(query)
                enum_values = [row[0] for row in result.fetchall()]
                
                logger.info(f"   Current enum values: {enum_values}")
                
                if 'super_admin' in enum_values:
                    logger.info("   ✅ super_admin already exists in enum")
                    return enum_values
                else:
                    logger.info("   📝 super_admin needs to be added")
                    return enum_values
                    
        except Exception as e:
            logger.error(f"❌ Failed to check enum values: {e}")
            return []
    
    def add_super_admin_to_enum(self) -> bool:
        """Add super_admin to the userrole enum"""
        logger.info("🚀 Adding super_admin to userrole enum...")
        
        try:
            with self.engine.begin() as conn:
                # Check if super_admin already exists
                check_query = text("""
                    SELECT COUNT(*) 
                    FROM pg_enum 
                    WHERE enumtypid = (
                        SELECT oid 
                        FROM pg_type 
                        WHERE typname = 'userrole'
                    )
                    AND enumlabel = 'super_admin';
                """)
                
                result = conn.execute(check_query)
                count = result.fetchone()[0]
                
                if count > 0:
                    logger.info("   ✅ super_admin already exists in enum - no action needed")
                    return True
                
                # Add super_admin to enum (at the beginning for highest privilege)
                alter_query = text("""
                    ALTER TYPE userrole ADD VALUE 'super_admin' BEFORE 'admin';
                """)
                
                conn.execute(alter_query)
                
                logger.info("   ✅ super_admin added to enum successfully")
                
                # Verify the addition
                verify_query = text("""
                    SELECT enumlabel 
                    FROM pg_enum 
                    WHERE enumtypid = (
                        SELECT oid 
                        FROM pg_type 
                        WHERE typname = 'userrole'
                    )
                    ORDER BY enumsortorder;
                """)
                
                result = conn.execute(verify_query)
                updated_values = [row[0] for row in result.fetchall()]
                
                logger.info(f"   📋 Updated enum values: {updated_values}")
                
                if 'super_admin' in updated_values:
                    logger.info("   ✅ Verification passed - super_admin is now available")
                    return True
                else:
                    logger.error("   ❌ Verification failed - super_admin not found after addition")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to add super_admin to enum: {e}")
            return False

def main():
    """Main enum update execution"""
    print("=" * 80)
    print("DATABASE ENUM UPDATE SCRIPT")
    print("Adding super_admin role to PostgreSQL enum")
    print("=" * 80)
    print("🎯 Target enum: userrole")
    print("➕ Adding value: super_admin")
    print("🔗 Required for: /api/v1/admin/users endpoint access")
    print("💰 Business context: £925K Zebra Associates opportunity")
    print("")
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Try to load from settings
        try:
            from app.core.config import settings
            database_url = settings.DATABASE_URL
            print("✅ Database URL loaded from settings")
        except Exception as e:
            print(f"❌ Could not load database URL: {e}")
            print("   Set DATABASE_URL environment variable")
            sys.exit(1)
    else:
        print("✅ Database URL loaded from environment")
    
    print("")
    
    # Initialize updater
    updater = DatabaseEnumUpdater(database_url)
    
    # Step 1: Connect
    if not updater.connect_to_database():
        print("❌ Failed to connect to database")
        sys.exit(1)
    
    print("")
    
    # Step 2: Check current enum values
    current_values = updater.check_current_enum_values()
    if not current_values:
        print("❌ Failed to check current enum values")
        sys.exit(1)
    
    print("")
    
    # Step 3: Add super_admin
    if updater.add_super_admin_to_enum():
        print("")
        print("=" * 80)
        print("🎉 ENUM UPDATE COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("✅ super_admin added to userrole enum")
        print("✅ Database ready for user role promotion")
        print("📋 Next step: Run promote_matt_to_super_admin.py")
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ Failed to update enum")
        sys.exit(1)

if __name__ == "__main__":
    main()