#!/usr/bin/env python3
"""
Render Production Database Schema Verification Tool

Connects specifically to the Render production database and verifies schema state.

This script will:
1. Connect to Render production database
2. Check if tables exist
3. Verify which Base columns exist
4. Test authentication flow

Usage:
    python verify_render_production_schema.py
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

try:
    from sqlalchemy import create_engine, text, inspect
    from sqlalchemy.engine import Engine
    import psycopg2
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

class RenderDatabaseVerifier:
    """Verifies Render production database schema state"""
    
    def __init__(self):
        # Use the production database URL from Render
        self.database_url = "postgresql://marketedge_user@dpg-d2gch62dbo4c73b0kl80-a.render.com:5432/marketedge_production"
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
        """Establish connection to Render production database"""
        try:
            logger.info("🔌 Connecting to Render production database...")
            logger.info("   Host: dpg-d2gch62dbo4c73b0kl80-a.render.com")
            logger.info("   Database: marketedge_production")
            
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
                result = conn.execute(text("SELECT 1 as test, current_database() as db_name, version() as version"))
                row = result.fetchone()
                test_value = row[0]
                db_name = row[1]
                pg_version = row[2]
                
            if test_value == 1:
                logger.info("✅ Database connection successful")
                logger.info(f"   Database: {db_name}")
                logger.info(f"   PostgreSQL: {pg_version.split(',')[0]}")
                return True
            else:
                logger.error("❌ Database connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Render database: {e}")
            
            # More specific error handling
            if "connection timed out" in str(e).lower():
                logger.error("   This could be a network connectivity issue")
            elif "password authentication failed" in str(e).lower():
                logger.error("   Database authentication failed - check credentials")
            elif "does not exist" in str(e).lower():
                logger.error("   Database does not exist or incorrect connection details")
            
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
        logger.info("🔍 Verifying Render production database schema...")
        
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
                    logger.info(f"   ✅ {table_name}: All columns present ({verification['row_count']} rows)")
                else:
                    summary["tables_incomplete"] += 1
                    missing = ", ".join(verification["missing_columns"])
                    logger.warning(f"   ⚠️  {table_name}: Missing columns: {missing}")
                    summary["total_missing_columns"] += len(verification["missing_columns"])
            else:
                summary["tables_missing"] += 1
                logger.error(f"   ❌ {table_name}: Table does not exist - {verification['error']}")
        
        return {"results": results, "summary": summary}
    
    def check_authentication_components(self) -> Dict:
        """Check critical authentication-related tables and components"""
        logger.info("🔐 Checking authentication components...")
        
        auth_results = {}
        
        # Check core authentication tables
        core_tables = ['users', 'organisations']
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
    
    def test_emergency_fix_endpoint_impact(self) -> Dict:
        """Test what the emergency fix endpoint would have done"""
        logger.info("🚨 Testing emergency fix endpoint simulation...")
        
        fix_results = {}
        
        try:
            with self.engine.connect() as conn:
                for table_name, expected_columns in self.expected_tables_columns.items():
                    table_results = {
                        "table_exists": False,
                        "columns_checked": [],
                        "columns_missing": [],
                        "would_fix": []
                    }
                    
                    try:
                        # Check if table exists (like the endpoint does)
                        conn.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
                        table_results["table_exists"] = True
                        
                        for column in expected_columns:
                            try:
                                # Try to select the column to see if it exists
                                conn.execute(text(f"SELECT {column} FROM {table_name} LIMIT 1"))
                                table_results["columns_checked"].append(f"{column}: EXISTS")
                            except Exception:
                                # Column doesn't exist
                                table_results["columns_missing"].append(column)
                                table_results["would_fix"].append(f"ADD COLUMN {column}")
                                
                    except Exception:
                        table_results["table_exists"] = False
                    
                    fix_results[table_name] = table_results
                    
        except Exception as e:
            logger.error(f"   ❌ Emergency fix simulation failed: {e}")
            return {"error": str(e)}
        
        return fix_results
    
    def generate_comprehensive_report(self, verification_results: Dict, auth_results: Dict, fix_simulation: Dict) -> str:
        """Generate a comprehensive verification report"""
        report = []
        report.append("=" * 80)
        report.append("RENDER PRODUCTION DATABASE SCHEMA VERIFICATION REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append("Database: dpg-d2gch62dbo4c73b0kl80-a.render.com:5432/marketedge_production")
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
            report.append("🎯 STATUS: PRODUCTION SCHEMA FIX SUCCESSFUL")
            report.append("   ✅ All expected tables exist with required Base columns")
            report.append("   ✅ The authentication 500 error should be RESOLVED")
            report.append("   ✅ The /emergency/fix-database-schema endpoint worked correctly")
        elif summary['total_missing_columns'] > 0:
            report.append("⚠️  STATUS: PRODUCTION SCHEMA FIX INCOMPLETE")
            report.append(f"   ❌ {summary['total_missing_columns']} Base columns are still missing")
            report.append("   ❌ The authentication 500 error will PERSIST")
            report.append("   ❌ The /emergency/fix-database-schema endpoint may not have run properly")
        else:
            report.append("❌ STATUS: CRITICAL PRODUCTION DATABASE ISSUES")
            report.append(f"   ❌ {summary['tables_missing']} tables are missing entirely")
            report.append("   ❌ Database migrations may not have been applied")
        report.append("")
        
        # Detailed table results
        report.append("DETAILED TABLE VERIFICATION")
        report.append("-" * 40)
        
        for table_name, result in verification_results["results"].items():
            report.append(f"🗂️  Table: {table_name}")
            
            if result["table_exists"]:
                report.append(f"   Status: EXISTS ({result['row_count']} rows)")
                if result["existing_columns"]:
                    report.append(f"   ✅ Base Columns Present: {', '.join(result['existing_columns'])}")
                if result["missing_columns"]:
                    report.append(f"   ❌ Missing Base Columns: {', '.join(result['missing_columns'])}")
                    report.append(f"   🔧 NEEDS REPAIR: Emergency fix did not add these columns")
                else:
                    report.append(f"   ✅ ALL REQUIRED COLUMNS PRESENT")
            else:
                report.append(f"   ❌ Status: MISSING")
                report.append(f"   Error: {result['error']}")
                report.append(f"   🚨 CRITICAL: Table does not exist - migrations needed")
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
                        report.append("   ✅ Basic authentication queries work correctly")
                    else:
                        report.append("⚠️  User Query Test: PASSED but no users found")
                        report.append("   ⚠️  Database exists but has no user data")
                else:
                    report.append("❌ User Query Test: FAILED")
                    report.append(f"   Error: {result['error']}")
                    report.append("   ❌ Authentication queries will fail - 500 error cause")
            else:
                if result["exists"]:
                    report.append(f"✅ Table {component}: EXISTS ({result['row_count']} rows)")
                else:
                    report.append(f"❌ Table {component}: MISSING")
                    report.append(f"   Error: {result['error']}")
        
        report.append("")
        
        # Emergency fix simulation results
        if "error" not in fix_simulation:
            report.append("EMERGENCY FIX ENDPOINT SIMULATION")
            report.append("-" * 40)
            
            tables_that_would_be_fixed = []
            tables_already_complete = []
            
            for table_name, fix_result in fix_simulation.items():
                if fix_result["table_exists"]:
                    if fix_result["would_fix"]:
                        tables_that_would_be_fixed.append(table_name)
                        report.append(f"🔧 Table {table_name}: WOULD BE FIXED")
                        report.append(f"   Missing columns: {', '.join(fix_result['columns_missing'])}")
                        report.append(f"   Fix actions: {', '.join(fix_result['would_fix'])}")
                    else:
                        tables_already_complete.append(table_name)
                        report.append(f"✅ Table {table_name}: ALREADY COMPLETE")
                else:
                    report.append(f"❌ Table {table_name}: DOES NOT EXIST (would be skipped)")
            
            report.append("")
            report.append(f"📊 Summary: {len(tables_already_complete)} tables complete, {len(tables_that_would_be_fixed)} would need fixing")
            
            if len(tables_that_would_be_fixed) == 0:
                report.append("🎯 CONCLUSION: All tables already had required columns - emergency fix was not needed")
                report.append("   This explains why the endpoint returned 'fixed_tables: []'")
            else:
                report.append("⚠️  CONCLUSION: Emergency fix should have made changes but didn't")
                report.append("   This suggests the endpoint may not have run properly")
        
        report.append("")
        
        # Final recommendations
        report.append("FINAL RECOMMENDATIONS")
        report.append("-" * 40)
        
        if summary['total_missing_columns'] == 0 and summary['tables_missing'] == 0:
            report.append("✅ PRODUCTION STATUS: HEALTHY")
            report.append("   ✅ All database schema fixes are applied correctly")
            report.append("   ✅ Authentication should work without 500 errors")
            report.append("   ✅ The production application is ready for use")
            report.append("")
            report.append("🎯 Next Steps:")
            report.append("   1. Test the production authentication flow")
            report.append("   2. Verify frontend can connect successfully")
            report.append("   3. Monitor for any remaining 500 errors")
        
        elif summary['total_missing_columns'] > 0:
            report.append("⚠️  PRODUCTION STATUS: SCHEMA ISSUES DETECTED")
            report.append("   ❌ Missing Base columns will cause authentication 500 errors")
            report.append("   🔧 Immediate action required to fix production")
            report.append("")
            report.append("🚨 URGENT Action Plan:")
            report.append("   1. Re-run emergency fix endpoint:")
            report.append("      curl -X POST https://your-production-url.onrender.com/emergency/fix-database-schema")
            report.append("")
            report.append("   2. Or apply manual SQL fixes:")
            for table_name, result in verification_results["results"].items():
                if result["missing_columns"]:
                    for column in result["missing_columns"]:
                        report.append(f"      ALTER TABLE {table_name} ADD COLUMN {column} TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;")
        
        if summary['tables_missing'] > 0:
            report.append("")
            report.append("🚨 CRITICAL: Missing tables detected")
            report.append("   Run database migrations in production:")
            report.append("   alembic upgrade head")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main verification function"""
    print("🚀 MarketEdge Render Production Database Schema Verifier")
    print("=" * 70)
    print("🎯 Target: Render Production Database")
    print("   Host: dpg-d2gch62dbo4c73b0kl80-a.render.com")
    print("   Database: marketedge_production")
    print("")
    
    # Initialize verifier
    verifier = RenderDatabaseVerifier()
    
    # Connect to database
    print("⏳ Attempting to connect to Render production database...")
    if not verifier.connect_to_database():
        print("❌ CRITICAL: Failed to connect to Render production database")
        print("")
        print("🔧 Possible solutions:")
        print("   1. Check if the Render service is running")
        print("   2. Verify the database URL and credentials")
        print("   3. Check network connectivity to render.com")
        print("   4. Ensure the database service is not sleeping")
        sys.exit(1)
    
    print("")
    
    # Verify schema
    print("📊 Verifying production database schema...")
    verification_results = verifier.verify_all_tables()
    print("")
    
    # Check authentication components
    print("🔐 Testing authentication components...")
    auth_results = verifier.check_authentication_components()
    print("")
    
    # Simulate what emergency fix would do
    print("🚨 Simulating emergency fix endpoint behavior...")
    fix_simulation = verifier.test_emergency_fix_endpoint_impact()
    print("")
    
    # Generate and display report
    report = verifier.generate_comprehensive_report(verification_results, auth_results, fix_simulation)
    print(report)
    
    # Save report to file
    report_filename = f"render_production_schema_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"📄 Detailed report saved to: {report_filename}")
    except Exception as e:
        print(f"⚠️  Could not save report to file: {e}")
    
    print("")
    
    # Exit with appropriate code based on results
    summary = verification_results["summary"]
    if summary['total_missing_columns'] > 0 or summary['tables_missing'] > 0:
        print("❌ VERIFICATION FAILED: Production database has schema issues")
        print("🚨 URGENT: Authentication 500 errors will persist until fixed")
        sys.exit(1)
    else:
        print("✅ VERIFICATION PASSED: Production database schema is correct")
        print("🎯 SUCCESS: Authentication should work properly in production")
        sys.exit(0)


if __name__ == "__main__":
    main()