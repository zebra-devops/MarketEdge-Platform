#!/usr/bin/env python3
"""
EMERGENCY DATABASE FIX for MarketEdge Platform
Fixes missing created_at/updated_at columns causing authentication 500 errors
Runs directly on Render service with available DATABASE_URL
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, MetaData, inspect
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main execution function for database column fixes"""
    
    logger.info("🚀 EMERGENCY DATABASE FIX: Starting Base columns repair for authentication")
    logger.info("🎯 CRITICAL: Fixing 500 authentication errors for £925K opportunity")
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not found")
        sys.exit(1)
    
    logger.info(f"✅ Database URL found: {database_url[:50]}...")
    
    try:
        # Create engine with production-safe settings
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False  # Disable SQL logging in production
        )
        
        logger.info("✅ Database engine created successfully")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            logger.info(f"✅ Connected to database: {db_name}")
            
        # Define the missing columns for each table
        tables_to_fix = {
            'feature_flag_overrides': ['updated_at'],
            'feature_flag_usage': ['created_at', 'updated_at'],
            'module_usage_logs': ['created_at', 'updated_at'],
            'admin_actions': ['updated_at'],
            'audit_logs': ['created_at', 'updated_at'],
            'competitive_insights': ['updated_at'],
            'competitors': ['updated_at'],
            'market_alerts': ['updated_at'],
            'market_analytics': ['updated_at'],
            'pricing_data': ['updated_at']
        }
        
        logger.info(f"🔧 Fixing {len(tables_to_fix)} tables with missing Base columns")
        
        # Fix each table
        with engine.begin() as conn:  # Use transaction for safety
            for table_name, missing_columns in tables_to_fix.items():
                logger.info(f"🛠️  Fixing table: {table_name}")
                
                # Check if table exists first
                inspector = inspect(engine)
                if table_name not in inspector.get_table_names():
                    logger.warning(f"⚠️  Table {table_name} does not exist - skipping")
                    continue
                
                # Get existing columns
                existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
                
                for column in missing_columns:
                    if column not in existing_columns:
                        logger.info(f"   Adding {column} to {table_name}")
                        
                        # Add the missing column with proper default
                        if column == 'created_at':
                            conn.execute(text(f"""
                                ALTER TABLE {table_name} 
                                ADD COLUMN {column} TIMESTAMP WITH TIME ZONE 
                                DEFAULT CURRENT_TIMESTAMP NOT NULL
                            """))
                        elif column == 'updated_at':
                            conn.execute(text(f"""
                                ALTER TABLE {table_name} 
                                ADD COLUMN {column} TIMESTAMP WITH TIME ZONE 
                                DEFAULT CURRENT_TIMESTAMP NOT NULL
                            """))
                        
                        logger.info(f"   ✅ Added {column} to {table_name}")
                    else:
                        logger.info(f"   ✓ {column} already exists in {table_name}")
                
                logger.info(f"✅ Table {table_name} fixed successfully")
        
        logger.info("🎉 ALL DATABASE FIXES COMPLETED SUCCESSFULLY")
        logger.info("✅ Authentication 500 errors should now be resolved")
        logger.info("🚀 Service ready for £925K opportunity")
        
        # Final verification
        logger.info("🔍 Running final verification...")
        with engine.connect() as conn:
            for table_name in tables_to_fix.keys():
                try:
                    result = conn.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
                    logger.info(f"✅ Table {table_name} accessible")
                except Exception as e:
                    logger.warning(f"⚠️  Table {table_name} verification: {e}")
        
        logger.info("🎯 DATABASE FIX COMPLETE - AUTHENTICATION READY")
        
    except Exception as e:
        logger.error(f"❌ Database fix failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()