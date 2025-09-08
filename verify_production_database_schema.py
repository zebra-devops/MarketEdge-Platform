#!/usr/bin/env python3
"""
Production Database Schema Verification Tool

Connects to the production database on Render and verifies the current schema state
for the 9 tables that should have been fixed by the emergency endpoint.

This script will:
1. Connect to production database
2. Check if tables exist
3. Verify which Base columns (created_at, updated_at) exist
4. Compare with expected schema
5. Test authentication flow components

Usage:
    python verify_production_database_schema.py
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import asyncio

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from sqlalchemy import create_engine, text, inspect
    from sqlalchemy.engine import Engine
    from sqlalchemy.exc import SQLAlchemyError
    import psycopg2
    from psycopg2 import sql
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

class DatabaseSchemaVerifier:
    """Verifies production database schema state"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine: Optional[Engine] = None
        self.expected_tables_columns = {
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
        
    def connect_to_database(self) -> bool:
        """Establish connection to production database"""
        try:
            logger.info("🔌 Connecting to production database...")
            logger.info(f"   Host: {self.database_url.split('@')[1].split(':')[0] if '@' in self.database_url else 'unknown'}")
            
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    "connect_timeout": 30,
                    "application_name": "schema_verifier"
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
    
    def get_table_info(self, table_name: str) -> Dict:
        """Get detailed information about a table"""
        try:
            with self.engine.connect() as conn:
                inspector = inspect(conn)
                
                # Check if table exists
                if not inspector.has_table(table_name):
                    return {"exists": False, "columns": [], "error": "Table does not exist"}
                
                # Get column information
                columns = inspector.get_columns(table_name)
                column_names = [col['name'] for col in columns]
                
                # Get table row count (with limit for safety)
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = result.fetchone()[0]
                except Exception as count_error:
                    row_count = f"Error: {count_error}"
                
                return {
                    "exists": True,
                    "columns": column_names,
                    "column_details": columns,
                    "row_count": row_count,
                    "error": None
                }
                
        except Exception as e:
            return {"exists": False, "columns": [], "error": str(e)}
    
    def verify_base_columns(self, table_name: str, expected_columns: List[str]) -> Dict:
        """Verify that Base columns exist in a table"""
        table_info = self.get_table_info(table_name)
        
        if not table_info["exists"]:
            return {
                "table_exists": False,
                "missing_columns": expected_columns,
                "existing_columns": [],
                "status": "TABLE_MISSING",
                "error": table_info.get("error")
            }
        
        existing_columns = table_info["columns"]
        missing_columns = [col for col in expected_columns if col not in existing_columns]
        found_columns = [col for col in expected_columns if col in existing_columns]
        
        if missing_columns:
            status = "MISSING_COLUMNS"
        else:
            status = "COMPLETE"
            
        return {
            "table_exists": True,
            "missing_columns": missing_columns,
            "existing_columns": found_columns,
            "all_columns": existing_columns,
            "row_count": table_info["row_count"],
            "status": status,
            "error": None
        }
    
    def verify_all_tables(self) -> Dict:
        """Verify all expected tables and their Base columns"""
        logger.info("🔍 Verifying database schema for all tables...")
        
        results = {}
        summary = {
            "total_tables": len(self.expected_tables_columns),
            "tables_exist": 0,
            "tables_complete": 0,
            "tables_missing": 0,
            "tables_incomplete": 0,
            "total_missing_columns": 0
        }
        
        for table_name, expected_columns in self.expected_tables_columns.items():
            logger.info(f"   Checking {table_name}...")
            
            verification = self.verify_base_columns(table_name, expected_columns)
            results[table_name] = verification
            
            # Update summary
            if verification["table_exists"]:
                summary["tables_exist"] += 1
                if verification["status"] == "COMPLETE":
                    summary["tables_complete"] += 1
                    logger.info(f"   ✅ {table_name}: All columns present")
                else:
                    summary["tables_incomplete"] += 1
                    missing = ", ".join(verification["missing_columns"])
                    logger.warning(f"   ⚠️  {table_name}: Missing columns: {missing}")
                    summary["total_missing_columns"] += len(verification["missing_columns"])
            else:
                summary["tables_missing"] += 1
                logger.error(f"   ❌ {table_name}: Table does not exist")
        
        return {"results": results, "summary": summary}
    
    def check_authentication_components(self) -> Dict:
        """Check critical authentication-related tables and components"""
        logger.info("🔐 Checking authentication components...")
        
        auth_results = {}
        
        # Check core authentication tables
        core_tables = ['users', 'organisations', 'user_sessions']
        for table in core_tables:
            table_info = self.get_table_info(table)
            auth_results[table] = table_info
            
            if table_info["exists"]:
                logger.info(f"   ✅ {table}: EXISTS ({table_info['row_count']} rows)")
            else:
                logger.error(f"   ❌ {table}: MISSING - {table_info['error']}")
        
        # Test basic authentication query
        try:
            with self.engine.connect() as conn:
                # Test a basic user lookup query (similar to auth flow)
                result = conn.execute(text("SELECT id, email, role FROM users LIMIT 1"))
                user_sample = result.fetchone()
                
                if user_sample:
                    auth_results["sample_user_query"] = {
                        "success": True,
                        "has_users": True,
                        "sample_id": str(user_sample[0]),
                        "sample_email": user_sample[1][:20] + "..." if len(user_sample[1]) > 20 else user_sample[1],
                        "role": str(user_sample[2])
                    }
                    logger.info("   ✅ User authentication query: SUCCESS")
                else:
                    auth_results["sample_user_query"] = {
                        "success": True,
                        "has_users": False,
                        "message": "No users found in database"
                    }
                    logger.warning("   ⚠️  User authentication query: SUCCESS but no users found")
                    
        except Exception as e:
            auth_results["sample_user_query"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"   ❌ User authentication query failed: {e}")
        
        return auth_results
    
    def generate_report(self, verification_results: Dict, auth_results: Dict) -> str:
        """Generate a comprehensive verification report"""
        report = []
        report.append("=" * 80)
        report.append("PRODUCTION DATABASE SCHEMA VERIFICATION REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append(f"Database: {self.database_url.split('@')[1] if '@' in self.database_url else 'Unknown'}")
        report.append("")
        
        # Summary
        summary = verification_results["summary"]
        report.append("SCHEMA VERIFICATION SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Tables Checked: {summary['total_tables']}")
        report.append(f"Tables Exist: {summary['tables_exist']}")
        report.append(f"Tables Complete (All Base columns): {summary['tables_complete']}")
        report.append(f"Tables Missing: {summary['tables_missing']}")
        report.append(f"Tables Incomplete: {summary['tables_incomplete']}")
        report.append(f"Total Missing Columns: {summary['total_missing_columns']}")
        report.append("")
        
        # Status assessment
        if summary['total_missing_columns'] == 0 and summary['tables_missing'] == 0:
            report.append("🎯 STATUS: SCHEMA FIX APPEARS SUCCESSFUL")
            report.append("   All expected tables exist with required Base columns")
        elif summary['total_missing_columns'] > 0:
            report.append("⚠️  STATUS: SCHEMA FIX INCOMPLETE OR NOT APPLIED")
            report.append(f"   {summary['total_missing_columns']} Base columns are still missing")
        else:
            report.append("❌ STATUS: SCHEMA ISSUES DETECTED")
            report.append(f"   {summary['tables_missing']} tables are missing entirely")
        report.append("")
        
        # Detailed table results
        report.append("DETAILED TABLE VERIFICATION")
        report.append("-" * 40)
        
        for table_name, result in verification_results["results"].items():
            report.append(f"Table: {table_name}")
            
            if result["table_exists"]:
                report.append(f"  Status: EXISTS ({result['row_count']} rows)")
                if result["existing_columns"]:
                    report.append(f"  Base Columns Present: {', '.join(result['existing_columns'])}")
                if result["missing_columns"]:
                    report.append(f"  Missing Base Columns: {', '.join(result['missing_columns'])}")
                    report.append(f"  🔧 NEEDS REPAIR: Add missing columns")
            else:
                report.append(f"  Status: MISSING")
                report.append(f"  Error: {result['error']}")
                report.append(f"  🚨 CRITICAL: Table does not exist")
            report.append("")
        
        # Authentication check results
        report.append("AUTHENTICATION COMPONENTS CHECK")
        report.append("-" * 40)
        
        for component, result in auth_results.items():
            if component == "sample_user_query":
                if result["success"]:
                    if result.get("has_users"):
                        report.append("✅ User Query Test: PASSED")
                        report.append(f"   Sample User: {result['sample_email']} (Role: {result['role']})")
                    else:
                        report.append("⚠️  User Query Test: PASSED but no users found")
                else:
                    report.append("❌ User Query Test: FAILED")
                    report.append(f"   Error: {result['error']}")
            else:
                if result["exists"]:
                    report.append(f"✅ Table {component}: EXISTS ({result['row_count']} rows)")
                else:
                    report.append(f"❌ Table {component}: MISSING")
                    report.append(f"   Error: {result['error']}")
        
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)
        
        if summary['total_missing_columns'] > 0:
            report.append("1. 🔧 IMMEDIATE ACTION REQUIRED:")
            report.append("   - The emergency database fix did not complete successfully")
            report.append("   - Missing Base columns will cause 500 errors during authentication")
            report.append("   - Re-run the emergency fix or apply manual SQL fixes")
            report.append("")
            
            report.append("2. 💾 Manual Fix SQL Commands:")
            for table_name, result in verification_results["results"].items():
                if result["missing_columns"]:
                    for column in result["missing_columns"]:
                        report.append(f"   ALTER TABLE {table_name} ADD COLUMN {column} TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;")
            report.append("")
        
        if summary['tables_missing'] > 0:
            report.append("3. 🚨 CRITICAL DATABASE ISSUE:")
            report.append("   - Some expected tables are completely missing")
            report.append("   - Run database migrations: alembic upgrade head")
            report.append("")
        
        if summary['total_missing_columns'] == 0 and summary['tables_missing'] == 0:
            report.append("✅ NO ACTION REQUIRED:")
            report.append("   - All database schema fixes appear to be applied correctly")
            report.append("   - Authentication should work properly")
            report.append("   - The 500 error should be resolved")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main verification function"""
    print("🚀 MarketEdge Production Database Schema Verifier")
    print("=" * 60)
    
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
            print("   Set DATABASE_URL environment variable or ensure settings are configured")
            sys.exit(1)
    else:
        print("✅ Database URL loaded from environment")
    
    # Mask sensitive parts of URL for logging
    masked_url = database_url
    if '@' in masked_url:
        parts = masked_url.split('@')
        user_part = parts[0].split('://')
        if len(user_part) > 1:
            user_creds = user_part[1].split(':')
            if len(user_creds) > 1:
                masked_url = f"{user_part[0]}://{user_creds[0]}:***@{parts[1]}"
    
    print(f"🎯 Target Database: {masked_url}")
    print("")
    
    # Initialize verifier
    verifier = DatabaseSchemaVerifier(database_url)
    
    # Connect to database
    if not verifier.connect_to_database():
        print("❌ Failed to connect to production database")
        print("   Check your DATABASE_URL and network connectivity")
        sys.exit(1)
    
    print("")
    
    # Verify schema
    verification_results = verifier.verify_all_tables()
    print("")
    
    # Check authentication components
    auth_results = verifier.check_authentication_components()
    print("")
    
    # Generate and display report
    report = verifier.generate_report(verification_results, auth_results)
    print(report)
    
    # Save report to file
    report_filename = f"production_schema_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to: {report_filename}")
    except Exception as e:
        print(f"⚠️  Could not save report to file: {e}")
    
    print("")
    
    # Exit with appropriate code
    summary = verification_results["summary"]
    if summary['total_missing_columns'] > 0 or summary['tables_missing'] > 0:
        print("❌ VERIFICATION FAILED: Database schema issues detected")
        sys.exit(1)
    else:
        print("✅ VERIFICATION PASSED: Database schema is correct")
        sys.exit(0)


if __name__ == "__main__":
    main()