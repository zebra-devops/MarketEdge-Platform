#!/usr/bin/env python3
"""
Production Database Fix Script: Add Missing Base Columns
========================================================

This script adds missing created_at/updated_at columns to database tables
that are causing 500 "Database error during authentication" errors.

Critical for £925K Zebra Associates opportunity - fixes authentication blocking issue.

Tables requiring fixes:
- feature_flag_overrides - missing updated_at
- feature_flag_usage - missing created_at, updated_at 
- module_usage_logs - missing created_at, updated_at
- admin_actions - missing updated_at
- audit_logs - missing created_at, updated_at
- competitive_insights - missing updated_at
- competitors - missing updated_at
- market_alerts - missing updated_at
- market_analytics - missing updated_at
- pricing_data - missing updated_at

Usage:
    python fix_missing_base_columns.py --dry-run          # Test mode
    python fix_missing_base_columns.py --execute          # Apply fixes
    python fix_missing_base_columns.py --verify           # Verify schema
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import DictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'db_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseFixer:
    """Production-safe database schema fixer"""
    
    # Tables and their missing columns
    MISSING_COLUMNS = {
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
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection = None
        
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            logger.info("Connecting to database...")
            self.connection = psycopg2.connect(
                self.database_url,
                cursor_factory=DictCursor,
                connect_timeout=30,
                application_name="schema_fixer"
            )
            self.connection.autocommit = False
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table_name,))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error checking table existence for {table_name}: {e}")
            return False
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if column exists in table"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = %s 
                        AND column_name = %s
                    );
                """, (table_name, column_name))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error checking column existence for {table_name}.{column_name}: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Dict:
        """Get comprehensive table information"""
        try:
            with self.connection.cursor() as cursor:
                # Get table structure
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                columns = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                row_count = cursor.fetchone()[0]
                
                return {
                    'exists': len(columns) > 0,
                    'columns': {col['column_name']: {
                        'type': col['data_type'],
                        'nullable': col['is_nullable'],
                        'default': col['column_default']
                    } for col in columns},
                    'row_count': row_count
                }
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return {'exists': False, 'columns': {}, 'row_count': 0}
    
    def analyze_schema(self) -> Dict[str, Dict]:
        """Analyze current schema state"""
        logger.info("Analyzing current database schema...")
        analysis = {}
        
        for table_name, missing_cols in self.MISSING_COLUMNS.items():
            table_info = self.get_table_info(table_name)
            analysis[table_name] = {
                'exists': table_info['exists'],
                'row_count': table_info['row_count'],
                'missing_columns': [],
                'existing_columns': table_info['columns']
            }
            
            if table_info['exists']:
                for col in missing_cols:
                    if col not in table_info['columns']:
                        analysis[table_name]['missing_columns'].append(col)
                        
        return analysis
    
    def create_backup_statement(self, table_name: str) -> str:
        """Generate backup statement for table"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"CREATE TABLE {table_name}_backup_{timestamp} AS SELECT * FROM {table_name};"
    
    def generate_add_column_sql(self, table_name: str, column_name: str) -> str:
        """Generate SQL to add missing column"""
        if column_name == 'created_at':
            return f"""
            ALTER TABLE {table_name} 
            ADD COLUMN {column_name} TIMESTAMP WITH TIME ZONE 
            DEFAULT CURRENT_TIMESTAMP NOT NULL;
            """
        elif column_name == 'updated_at':
            return f"""
            ALTER TABLE {table_name} 
            ADD COLUMN {column_name} TIMESTAMP WITH TIME ZONE 
            DEFAULT CURRENT_TIMESTAMP;
            """
        else:
            raise ValueError(f"Unknown column type: {column_name}")
    
    def dry_run(self) -> bool:
        """Perform dry run analysis"""
        logger.info("=== DRY RUN MODE ===")
        logger.info("Analyzing what changes would be made...")
        
        analysis = self.analyze_schema()
        changes_needed = False
        
        for table_name, info in analysis.items():
            if not info['exists']:
                logger.warning(f"❌ Table {table_name} does not exist")
                continue
                
            if info['missing_columns']:
                changes_needed = True
                logger.info(f"📊 Table: {table_name} (rows: {info['row_count']:,})")
                
                for col in info['missing_columns']:
                    logger.info(f"  ➕ Would add column: {col}")
                    sql = self.generate_add_column_sql(table_name, col)
                    logger.debug(f"     SQL: {sql.strip()}")
            else:
                logger.info(f"✅ Table: {table_name} - all columns present")
        
        if not changes_needed:
            logger.info("🎉 No changes needed - all columns are present!")
        else:
            logger.info(f"📋 Summary: {sum(len(info['missing_columns']) for info in analysis.values())} columns need to be added")
        
        return True
    
    def execute_fixes(self) -> bool:
        """Execute the database fixes"""
        logger.info("=== EXECUTING DATABASE FIXES ===")
        
        analysis = self.analyze_schema()
        total_changes = sum(len(info['missing_columns']) for info in analysis.values())
        
        if total_changes == 0:
            logger.info("🎉 No changes needed - all columns are present!")
            return True
        
        logger.info(f"📋 Planning to add {total_changes} missing columns")
        
        try:
            # Start transaction
            logger.info("🔄 Starting transaction...")
            
            for table_name, info in analysis.items():
                if not info['exists'] or not info['missing_columns']:
                    continue
                
                logger.info(f"🔧 Fixing table: {table_name}")
                
                # Create backup first
                backup_sql = self.create_backup_statement(table_name)
                logger.info(f"💾 Creating backup: {table_name}_backup_*")
                
                with self.connection.cursor() as cursor:
                    cursor.execute(backup_sql)
                
                # Add missing columns
                for col in info['missing_columns']:
                    logger.info(f"  ➕ Adding column: {col}")
                    sql = self.generate_add_column_sql(table_name, col)
                    
                    with self.connection.cursor() as cursor:
                        cursor.execute(sql)
                    
                    logger.info(f"  ✅ Column {col} added successfully")
            
            # Commit transaction
            logger.info("💾 Committing changes...")
            self.connection.commit()
            logger.info("✅ All changes committed successfully!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during execution: {e}")
            logger.info("🔄 Rolling back changes...")
            self.connection.rollback()
            return False
    
    def verify_fixes(self) -> bool:
        """Verify that all fixes were applied correctly"""
        logger.info("=== VERIFYING FIXES ===")
        
        analysis = self.analyze_schema()
        all_good = True
        
        for table_name, info in analysis.items():
            if not info['exists']:
                logger.warning(f"❌ Table {table_name} does not exist")
                all_good = False
                continue
            
            if info['missing_columns']:
                logger.error(f"❌ Table {table_name} still missing columns: {info['missing_columns']}")
                all_good = False
            else:
                logger.info(f"✅ Table {table_name} - all columns present")
        
        if all_good:
            logger.info("🎉 All fixes verified successfully!")
        else:
            logger.error("❌ Some issues remain - fixes may need to be re-run")
        
        return all_good


def get_database_url() -> str:
    """Get database URL from environment"""
    # Try various environment variable names
    url_vars = ['DATABASE_URL', 'POSTGRES_URL', 'DB_URL']
    
    for var in url_vars:
        if url := os.getenv(var):
            return url
    
    # Default for local development
    return "postgresql://localhost:5432/marketedge_production"


def main():
    parser = argparse.ArgumentParser(description='Fix missing database base columns')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Analyze what changes would be made (safe mode)')
    parser.add_argument('--execute', action='store_true',
                       help='Execute the database fixes')
    parser.add_argument('--verify', action='store_true',
                       help='Verify that fixes were applied correctly')
    parser.add_argument('--database-url', type=str,
                       help='Database URL (overrides environment variables)')
    
    args = parser.parse_args()
    
    if not any([args.dry_run, args.execute, args.verify]):
        parser.error("Must specify one of: --dry-run, --execute, --verify")
    
    # Get database URL
    database_url = args.database_url or get_database_url()
    if not database_url:
        logger.error("❌ No database URL provided. Set DATABASE_URL environment variable or use --database-url")
        return 1
    
    # Redact password for logging
    safe_url = database_url.split('@')[1] if '@' in database_url else database_url
    logger.info(f"🗃️  Database: ...@{safe_url}")
    
    # Initialize fixer
    fixer = DatabaseFixer(database_url)
    
    try:
        if not fixer.connect():
            return 1
        
        success = False
        if args.dry_run:
            success = fixer.dry_run()
        elif args.execute:
            success = fixer.execute_fixes()
        elif args.verify:
            success = fixer.verify_fixes()
        
        return 0 if success else 1
        
    finally:
        fixer.disconnect()


if __name__ == "__main__":
    sys.exit(main())