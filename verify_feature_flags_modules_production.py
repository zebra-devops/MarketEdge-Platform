#!/usr/bin/env python3
"""
Production Feature Flags & Modules Database Verification Tool

Specifically checks for the feature flags and module tables that are suspected
to be missing and causing 404 errors for Zebra Associates £925K opportunity.

This script will:
1. Connect to production database on Render
2. Check for all feature flags and module-related tables
3. Verify table structure and data presence
4. Provide demo data seeding recommendations
5. Generate actionable SQL scripts for missing tables/data

Tables to verify:
- feature_flags
- feature_flag_overrides  
- feature_flag_usage
- analytics_modules
- organisation_modules
- module_configurations
- module_usage_logs
- user_application_access
- module_feature_flags (if exists)

Usage:
    python verify_feature_flags_modules_production.py
"""

import sys
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
import uuid

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

class FeatureFlagsModulesVerifier:
    """Verifies feature flags and modules tables in production database"""
    
    def __init__(self):
        # Production database URL from the verification script
        self.database_url = os.getenv('DATABASE_URL') or "postgresql://marketedge_user@dpg-d2gch62dbo4c73b0kl80-a.render.com:5432/marketedge_production"
        self.engine: Optional[Engine] = None
        
        # Define expected tables with their critical columns
        self.expected_tables = {
            'feature_flags': {
                'critical_columns': ['id', 'flag_key', 'name', 'is_enabled', 'scope', 'status', 'created_at', 'updated_at'],
                'description': 'Core feature flags table for controlling feature rollouts',
                'sample_data_needed': True
            },
            'feature_flag_overrides': {
                'critical_columns': ['id', 'feature_flag_id', 'organisation_id', 'user_id', 'is_enabled', 'created_at', 'updated_at'],
                'description': 'Organisation/user-specific feature flag overrides',
                'sample_data_needed': False
            },
            'feature_flag_usage': {
                'critical_columns': ['id', 'feature_flag_id', 'organisation_id', 'user_id', 'was_enabled', 'accessed_at'],
                'description': 'Feature flag usage analytics and tracking',
                'sample_data_needed': False
            },
            'analytics_modules': {
                'critical_columns': ['id', 'name', 'description', 'module_type', 'status', 'is_core', 'entry_point', 'created_at', 'updated_at'],
                'description': 'Registry of available analytics modules in the platform',
                'sample_data_needed': True
            },
            'organisation_modules': {
                'critical_columns': ['id', 'organisation_id', 'module_id', 'is_enabled', 'configuration', 'created_at', 'updated_at'],
                'description': 'Track which modules are enabled for each organisation',
                'sample_data_needed': True
            },
            'module_configurations': {
                'critical_columns': ['id', 'module_id', 'organisation_id', 'config_key', 'config_value', 'created_at', 'updated_at'],
                'description': 'Module-specific configuration storage',
                'sample_data_needed': False
            },
            'module_usage_logs': {
                'critical_columns': ['id', 'module_id', 'organisation_id', 'user_id', 'action', 'success', 'timestamp'],
                'description': 'Module usage tracking for analytics and billing',
                'sample_data_needed': False
            },
            'user_application_access': {
                'critical_columns': ['user_id', 'application', 'has_access', 'granted_by', 'granted_at'],
                'description': 'Per-user application access permissions',
                'sample_data_needed': True
            }
        }
    
    def connect_to_database(self) -> bool:
        """Establish connection to production database"""
        try:
            logger.info("🔌 Connecting to production database...")
            
            # Parse database URL to show connection info
            if '@' in self.database_url:
                host_part = self.database_url.split('@')[1].split('/')[0]
                db_name = self.database_url.split('/')[-1]
                logger.info(f"   Host: {host_part}")
                logger.info(f"   Database: {db_name}")
            
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    "connect_timeout": 30,
                    "application_name": "feature_flags_modules_verifier"
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
                
                # Get table row count
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = result.fetchone()[0]
                except Exception as count_error:
                    row_count = f"Error: {count_error}"
                
                # Get sample data (first 3 rows)
                sample_data = []
                try:
                    # Limit columns to avoid too much data
                    limited_columns = column_names[:5]  # First 5 columns only
                    columns_str = ", ".join(limited_columns)
                    result = conn.execute(text(f"SELECT {columns_str} FROM {table_name} LIMIT 3"))
                    sample_data = result.fetchall()
                except Exception:
                    sample_data = []
                
                return {
                    "exists": True,
                    "columns": column_names,
                    "column_details": columns,
                    "row_count": row_count,
                    "sample_data": sample_data,
                    "limited_columns": limited_columns if 'limited_columns' in locals() else column_names[:5],
                    "error": None
                }
                
        except Exception as e:
            return {"exists": False, "columns": [], "error": str(e)}
    
    def verify_table_structure(self, table_name: str, expected_info: Dict) -> Dict:
        """Verify table exists and has expected structure"""
        table_info = self.get_table_info(table_name)
        
        if not table_info["exists"]:
            return {
                "table_exists": False,
                "missing_columns": expected_info['critical_columns'],
                "existing_columns": [],
                "row_count": 0,
                "has_data": False,
                "status": "TABLE_MISSING",
                "error": table_info.get("error"),
                "description": expected_info['description']
            }
        
        existing_columns = table_info["columns"]
        critical_columns = expected_info['critical_columns']
        missing_columns = [col for col in critical_columns if col not in existing_columns]
        found_columns = [col for col in critical_columns if col in existing_columns]
        
        row_count = table_info["row_count"]
        has_data = isinstance(row_count, int) and row_count > 0
        
        if missing_columns:
            status = "MISSING_COLUMNS"
        elif not has_data and expected_info['sample_data_needed']:
            status = "EMPTY_TABLE"
        else:
            status = "COMPLETE"
            
        return {
            "table_exists": True,
            "missing_columns": missing_columns,
            "existing_columns": found_columns,
            "all_columns": existing_columns,
            "row_count": row_count,
            "has_data": has_data,
            "sample_data": table_info.get("sample_data", []),
            "limited_columns": table_info.get("limited_columns", []),
            "status": status,
            "error": None,
            "description": expected_info['description']
        }
    
    def verify_all_tables(self) -> Dict:
        """Verify all expected feature flags and module tables"""
        logger.info("🔍 Verifying feature flags and modules database schema...")
        
        results = {}
        summary = {
            "total_tables": len(self.expected_tables),
            "tables_exist": 0,
            "tables_complete": 0,
            "tables_missing": 0,
            "tables_empty": 0,
            "tables_incomplete": 0,
            "needs_demo_data": 0
        }
        
        for table_name, expected_info in self.expected_tables.items():
            logger.info(f"   Checking {table_name}...")
            
            verification = self.verify_table_structure(table_name, expected_info)
            results[table_name] = verification
            
            # Update summary
            if verification["table_exists"]:
                summary["tables_exist"] += 1
                if verification["status"] == "COMPLETE":
                    summary["tables_complete"] += 1
                    logger.info(f"   ✅ {table_name}: Complete ({verification['row_count']} rows)")
                elif verification["status"] == "EMPTY_TABLE":
                    summary["tables_empty"] += 1
                    if expected_info['sample_data_needed']:
                        summary["needs_demo_data"] += 1
                    logger.warning(f"   ⚠️  {table_name}: Exists but empty (needs demo data)")
                else:
                    summary["tables_incomplete"] += 1
                    missing = ", ".join(verification["missing_columns"])
                    logger.warning(f"   ⚠️  {table_name}: Missing columns: {missing}")
            else:
                summary["tables_missing"] += 1
                logger.error(f"   ❌ {table_name}: Table missing")
        
        return {"results": results, "summary": summary}
    
    def check_user_organisation_data(self) -> Dict:
        """Check if we have users and organisations for demo data"""
        logger.info("👥 Checking existing users and organisations...")
        
        users_info = self.get_table_info("users")
        orgs_info = self.get_table_info("organisations")
        
        return {
            "users": {
                "exists": users_info["exists"],
                "count": users_info.get("row_count", 0),
                "sample": users_info.get("sample_data", [])[:2],  # First 2 users
                "columns": users_info.get("limited_columns", [])
            },
            "organisations": {
                "exists": orgs_info["exists"],
                "count": orgs_info.get("row_count", 0),
                "sample": orgs_info.get("sample_data", [])[:2],  # First 2 orgs
                "columns": orgs_info.get("limited_columns", [])
            }
        }
    
    def generate_demo_data_sql(self, verification_results: Dict, user_org_data: Dict) -> List[str]:
        """Generate SQL scripts for demo data seeding"""
        sql_scripts = []
        results = verification_results["results"]
        
        # Get sample user and org IDs if they exist
        sample_user_id = None
        sample_org_id = None
        
        if user_org_data["users"]["sample"]:
            sample_user_id = str(user_org_data["users"]["sample"][0][0])
        
        if user_org_data["organisations"]["sample"]:
            sample_org_id = str(user_org_data["organisations"]["sample"][0][0])
        
        if not sample_user_id or not sample_org_id:
            sql_scripts.append("-- WARNING: No users or organisations found. Create them first!")
            sql_scripts.append("-- You may need to run the initial_data.py seeding script first")
            sample_user_id = "'{USER_ID}'"  # Placeholder
            sample_org_id = "'{ORG_ID}'"    # Placeholder
        
        sql_scripts.append("-- Demo data for Feature Flags and Modules tables")
        sql_scripts.append("-- Generated for Zebra Associates £925K opportunity")
        sql_scripts.append(f"-- Timestamp: {datetime.now().isoformat()}")
        sql_scripts.append("")
        
        # Feature flags demo data
        if results.get("feature_flags", {}).get("table_exists") and not results["feature_flags"]["has_data"]:
            sql_scripts.append("-- Essential feature flags for module system")
            feature_flags = [
                ("'module_discovery_enabled'", "'Module Discovery'", "'Enable module discovery and routing'", "true", "'global'", "'active'"),
                ("'pricing_intelligence_module'", "'Pricing Intelligence Module'", "'Enable pricing intelligence analytics'", "true", "'organisation'", "'active'"),
                ("'market_trends_module'", "'Market Trends Module'", "'Enable market trends analysis'", "true", "'organisation'", "'active'"),
                ("'competitor_analysis_module'", "'Competitor Analysis Module'", "'Enable competitor analysis features'", "true", "'organisation'", "'active'"),
                ("'zebra_associates_features'", "'Zebra Associates Features'", "'Special features for £925K opportunity'", "true", "'organisation'", "'active'")
            ]
            
            for flag_key, name, desc, enabled, scope, status in feature_flags:
                flag_id = f"'{uuid.uuid4()}'"
                sql_scripts.append(f"""INSERT INTO feature_flags (id, flag_key, name, description, is_enabled, scope, status, rollout_percentage, config, allowed_sectors, blocked_sectors, created_by, created_at, updated_at) VALUES 
({flag_id}, {flag_key}, {name}, {desc}, {enabled}, {scope}, {status}, 100, '{{}}', '[]', '[]', {sample_user_id}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);""")
            sql_scripts.append("")
        
        # Analytics modules demo data
        if results.get("analytics_modules", {}).get("table_exists") and not results["analytics_modules"]["has_data"]:
            sql_scripts.append("-- Core analytics modules for the platform")
            modules = [
                ("'pricing_intelligence'", "'Pricing Intelligence'", "'Advanced pricing analysis and competitive intelligence'", "'analytics'", "'active'", "true", "'app.modules.pricing_intelligence'"),
                ("'market_trends'", "'Market Trends'", "'Market trend analysis and forecasting'", "'analytics'", "'active'", "false", "'app.modules.market_trends'"),
                ("'competitor_analysis'", "'Competitor Analysis'", "'Competitive landscape analysis and monitoring'", "'analytics'", "'active'", "false", "'app.modules.competitor_analysis'"),
                ("'zebra_cinema_analytics'", "'Cinema Analytics'", "'Specialized analytics for cinema industry (Zebra Associates)'", "'analytics'", "'active'", "false", "'app.modules.cinema_analytics'"),
                ("'module_registry'", "'Module Registry'", "'Core module discovery and routing system'", "'core'", "'active'", "true", "'app.core.module_registry'")
            ]
            
            for mod_id, name, desc, mod_type, status, is_core, entry_point in modules:
                sql_scripts.append(f"""INSERT INTO analytics_modules (id, name, description, version, module_type, status, is_core, requires_license, entry_point, config_schema, default_config, dependencies, api_endpoints, frontend_components, min_data_requirements, documentation_url, help_text, pricing_tier, license_requirements, created_by, created_at, updated_at) VALUES 
({mod_id}, {name}, {desc}, '1.0.0', {mod_type}, {status}, {is_core}, false, {entry_point}, '{{}}', '{{}}', '[]', '[]', '[]', '{{}}', NULL, NULL, NULL, '{{}}', {sample_user_id}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);""")
            sql_scripts.append("")
        
        # Organisation modules demo data - enable modules for sample organisation
        if results.get("organisation_modules", {}).get("table_exists") and not results["organisation_modules"]["has_data"] and sample_org_id != "'{ORG_ID}'":
            sql_scripts.append("-- Enable modules for sample organisation")
            org_modules = [
                ("'pricing_intelligence'", "true", "'{\"advanced_features\": true, \"demo_mode\": false}'"),
                ("'market_trends'", "true", "'{\"forecast_horizon\": 12, \"trend_sensitivity\": \"medium\"}'"),
                ("'competitor_analysis'", "true", "'{\"monitoring_frequency\": \"daily\", \"alert_threshold\": 0.1}'"),
                ("'zebra_cinema_analytics'", "true", "'{\"industry_focus\": \"cinema\", \"client\": \"zebra_associates\"}'"),
                ("'module_registry'", "true", "'{\"auto_discovery\": true, \"routing_enabled\": true}'")
            ]
            
            for mod_id, enabled, config in org_modules:
                om_id = f"'{uuid.uuid4()}'"
                sql_scripts.append(f"""INSERT INTO organisation_modules (id, organisation_id, module_id, is_enabled, configuration, enabled_for_users, disabled_for_users, first_enabled_at, access_count, created_by, created_at, updated_at) VALUES 
({om_id}, {sample_org_id}, {mod_id}, {enabled}, {config}, '[]', '[]', CURRENT_TIMESTAMP, 0, {sample_user_id}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);""")
            sql_scripts.append("")
        
        # User application access demo data
        if results.get("user_application_access", {}).get("table_exists") and not results["user_application_access"]["has_data"] and sample_user_id != "'{USER_ID}'":
            sql_scripts.append("-- Grant application access to sample user")
            applications = ["'market_edge'", "'causal_edge'", "'value_edge'"]
            
            for app in applications:
                sql_scripts.append(f"""INSERT INTO user_application_access (user_id, application, has_access, granted_by, granted_at) VALUES 
({sample_user_id}, {app}, true, {sample_user_id}, CURRENT_TIMESTAMP);""")
            sql_scripts.append("")
        
        return sql_scripts
    
    def generate_missing_tables_sql(self, verification_results: Dict) -> List[str]:
        """Generate SQL scripts for creating missing tables"""
        sql_scripts = []
        results = verification_results["results"]
        
        missing_tables = [table for table, info in results.items() if not info["table_exists"]]
        
        if not missing_tables:
            return ["-- All tables exist, no CREATE TABLE scripts needed"]
        
        sql_scripts.append("-- SQL scripts to create missing Feature Flags and Modules tables")
        sql_scripts.append("-- WARNING: These are approximations based on the SQLAlchemy models")
        sql_scripts.append("-- You should prefer running: alembic upgrade head")
        sql_scripts.append("")
        
        # Define table creation scripts (simplified versions)
        table_creation_scripts = {
            "feature_flags": """
CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    rollout_percentage INTEGER DEFAULT 0 NOT NULL,
    scope VARCHAR(20) DEFAULT 'global',
    status VARCHAR(20) DEFAULT 'active',
    config JSONB DEFAULT '{}',
    allowed_sectors JSONB DEFAULT '[]',
    blocked_sectors JSONB DEFAULT '[]',
    module_id VARCHAR(255),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_feature_flags_flag_key ON feature_flags(flag_key);
CREATE INDEX idx_feature_flags_module_id ON feature_flags(module_id);""",

            "feature_flag_overrides": """
CREATE TABLE feature_flag_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_flag_id UUID NOT NULL REFERENCES feature_flags(id),
    organisation_id UUID REFERENCES organisations(id),
    user_id UUID REFERENCES users(id),
    is_enabled BOOLEAN NOT NULL,
    reason TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);""",

            "analytics_modules": """
CREATE TABLE analytics_modules (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    version VARCHAR(50) DEFAULT '1.0.0' NOT NULL,
    module_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'development',
    is_core BOOLEAN DEFAULT FALSE NOT NULL,
    requires_license BOOLEAN DEFAULT FALSE NOT NULL,
    entry_point VARCHAR(500) NOT NULL,
    config_schema JSONB DEFAULT '{}',
    default_config JSONB DEFAULT '{}',
    dependencies JSONB DEFAULT '[]',
    api_endpoints JSONB DEFAULT '[]',
    frontend_components JSONB DEFAULT '[]',
    min_data_requirements JSONB DEFAULT '{}',
    documentation_url VARCHAR(500),
    help_text TEXT,
    pricing_tier VARCHAR(50),
    license_requirements JSONB DEFAULT '{}',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);""",

            "organisation_modules": """
CREATE TABLE organisation_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    module_id VARCHAR(255) NOT NULL REFERENCES analytics_modules(id),
    is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    configuration JSONB DEFAULT '{}',
    enabled_for_users JSONB DEFAULT '[]',
    disabled_for_users JSONB DEFAULT '[]',
    first_enabled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0 NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);""",

            "user_application_access": """
CREATE TABLE user_application_access (
    user_id UUID NOT NULL REFERENCES users(id),
    application VARCHAR(50) NOT NULL,
    has_access BOOLEAN DEFAULT FALSE NOT NULL,
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, application)
);"""
        }
        
        for table_name in missing_tables:
            if table_name in table_creation_scripts:
                sql_scripts.append(f"-- Create {table_name} table")
                sql_scripts.append(table_creation_scripts[table_name])
                sql_scripts.append("")
        
        return sql_scripts
    
    def generate_report(self, verification_results: Dict, user_org_data: Dict, demo_data_sql: List[str], missing_tables_sql: List[str]) -> str:
        """Generate comprehensive verification report"""
        report = []
        report.append("=" * 90)
        report.append("PRODUCTION FEATURE FLAGS & MODULES DATABASE VERIFICATION REPORT")
        report.append("=" * 90)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append(f"Investigation: £925K Zebra Associates opportunity - Module/Feature Flag 404 errors")
        report.append("")
        
        # Executive Summary
        summary = verification_results["summary"]
        report.append("🎯 EXECUTIVE SUMMARY")
        report.append("-" * 50)
        report.append(f"Total Tables Checked: {summary['total_tables']}")
        report.append(f"Tables Exist: {summary['tables_exist']}")
        report.append(f"Tables Complete with Data: {summary['tables_complete']}")
        report.append(f"Tables Missing: {summary['tables_missing']}")
        report.append(f"Tables Empty (Need Demo Data): {summary['tables_empty']}")
        report.append(f"Tables with Missing Columns: {summary['tables_incomplete']}")
        report.append("")
        
        # Root cause analysis
        if summary['tables_missing'] > 0:
            report.append("🚨 ROOT CAUSE IDENTIFIED: MISSING TABLES")
            report.append("   Critical tables do not exist in production database")
            report.append("   This WILL cause 404 errors when frontend tries to access module/feature flag APIs")
            report.append("   Backend returns 401/403 but frontend interprets as 404")
        elif summary['tables_empty'] > 0:
            report.append("⚠️  ROOT CAUSE IDENTIFIED: EMPTY TABLES")
            report.append("   Tables exist but contain no data")
            report.append("   Module discovery will return empty results → 404 errors")
            report.append("   Feature flag checks will fail → authentication issues")
        elif summary['tables_incomplete'] > 0:
            report.append("⚠️  PARTIAL ISSUE: INCOMPLETE TABLES")
            report.append("   Tables exist but missing some columns")
            report.append("   May cause intermittent errors or feature degradation")
        else:
            report.append("✅ SCHEMA STATUS: APPEARS HEALTHY")
            report.append("   All expected tables exist with data")
            report.append("   404 errors may be caused by application logic, not database")
        report.append("")
        
        # Detailed table analysis
        report.append("📊 DETAILED TABLE ANALYSIS")
        report.append("-" * 50)
        
        for table_name, result in verification_results["results"].items():
            report.append(f"🗂️  {table_name.upper()}")
            report.append(f"   Purpose: {result['description']}")
            
            if result["table_exists"]:
                report.append(f"   ✅ Status: EXISTS ({result['row_count']} rows)")
                
                if result["missing_columns"]:
                    report.append(f"   ⚠️  Missing Columns: {', '.join(result['missing_columns'])}")
                
                if result["has_data"]:
                    report.append(f"   ✅ Data: HAS {result['row_count']} RECORDS")
                    if result.get("sample_data") and result.get("limited_columns"):
                        report.append(f"   📄 Sample Data (columns: {', '.join(result['limited_columns'])}):")
                        for i, row in enumerate(result["sample_data"][:2], 1):
                            row_str = " | ".join(str(val)[:30] + "..." if len(str(val)) > 30 else str(val) for val in row)
                            report.append(f"      {i}. {row_str}")
                else:
                    report.append(f"   ❌ Data: EMPTY TABLE")
                    if self.expected_tables[table_name]['sample_data_needed']:
                        report.append(f"   🚨 CRITICAL: This table needs demo data to function properly")
            else:
                report.append(f"   ❌ Status: TABLE DOES NOT EXIST")
                report.append(f"   🚨 CRITICAL: Will cause API endpoint failures")
                report.append(f"   Error: {result['error']}")
            
            report.append("")
        
        # User/Organisation context
        report.append("👥 SUPPORTING DATA ANALYSIS")
        report.append("-" * 50)
        
        if user_org_data["users"]["exists"]:
            report.append(f"✅ Users table: {user_org_data['users']['count']} users")
            if user_org_data["users"]["sample"]:
                user_sample = user_org_data["users"]["sample"][0]
                cols = user_org_data["users"]["columns"]
                sample_info = " | ".join(f"{cols[i]}: {user_sample[i]}" for i in range(min(len(cols), len(user_sample), 3)))
                report.append(f"   Sample: {sample_info}")
        else:
            report.append("❌ Users table: NOT FOUND")
        
        if user_org_data["organisations"]["exists"]:
            report.append(f"✅ Organisations table: {user_org_data['organisations']['count']} organisations")
            if user_org_data["organisations"]["sample"]:
                org_sample = user_org_data["organisations"]["sample"][0]
                cols = user_org_data["organisations"]["columns"]
                sample_info = " | ".join(f"{cols[i]}: {org_sample[i]}" for i in range(min(len(cols), len(org_sample), 3)))
                report.append(f"   Sample: {sample_info}")
        else:
            report.append("❌ Organisations table: NOT FOUND")
        
        report.append("")
        
        # Impact Assessment
        report.append("💥 BUSINESS IMPACT ASSESSMENT")
        report.append("-" * 50)
        
        if summary['tables_missing'] > 0 or summary['tables_empty'] >= 2:
            report.append("🚨 SEVERITY: CRITICAL - £925K OPPORTUNITY AT RISK")
            report.append("   • Module discovery completely broken")
            report.append("   • Feature flags system non-functional")
            report.append("   • User matt.lindop@zebra.associates cannot access platform")
            report.append("   • Demo/evaluation impossible for Zebra Associates")
            report.append("   • Immediate intervention required")
        elif summary['tables_empty'] == 1:
            report.append("⚠️  SEVERITY: HIGH - PLATFORM PARTIALLY FUNCTIONAL")
            report.append("   • Some module functionality may work")
            report.append("   • Feature flags may have limited functionality")
            report.append("   • User experience significantly degraded")
            report.append("   • Demo quality compromised")
        else:
            report.append("✅ SEVERITY: LOW - PLATFORM SHOULD BE FUNCTIONAL")
            report.append("   • Database schema appears complete")
            report.append("   • 404 errors likely caused by application logic")
            report.append("   • Investigate API routing and authentication")
        
        report.append("")
        
        # Recommendations
        report.append("🔧 IMMEDIATE ACTION PLAN")
        report.append("-" * 50)
        
        if summary['tables_missing'] > 0:
            report.append("1. 🚨 CREATE MISSING TABLES (CRITICAL)")
            report.append("   Execute: alembic upgrade head")
            report.append("   Or run the generated SQL scripts below")
            report.append("")
        
        if summary['tables_empty'] > 0:
            report.append("2. 📊 SEED DEMO DATA (HIGH PRIORITY)")
            report.append("   Execute the generated demo data SQL scripts below")
            report.append("   Or run: python database/seeds/initial_data.py")
            report.append("")
        
        report.append("3. 🧪 TEST ZEBRA ASSOCIATES USER ACCESS")
        report.append("   • Verify user matt.lindop@zebra.associates exists")
        report.append("   • Ensure user has proper organisation assignment")
        report.append("   • Test module discovery API endpoints")
        report.append("   • Validate feature flag evaluation")
        report.append("")
        
        report.append("4. 📈 MONITOR & VALIDATE")
        report.append("   • Test frontend module loading")
        report.append("   • Check API endpoint responses")
        report.append("   • Verify 404 errors are resolved")
        report.append("   • Schedule follow-up verification")
        report.append("")
        
        # SQL Scripts section
        if missing_tables_sql and len(missing_tables_sql) > 1:
            report.append("🗂️  SQL SCRIPTS FOR MISSING TABLES")
            report.append("-" * 50)
            report.append("-- EXECUTE THESE IF ALEMBIC IS NOT AVAILABLE")
            report.extend(missing_tables_sql)
            report.append("")
        
        if demo_data_sql and len(demo_data_sql) > 5:
            report.append("📊 DEMO DATA SQL SCRIPTS")
            report.append("-" * 50)
            report.extend(demo_data_sql)
            report.append("")
        
        report.append("=" * 90)
        
        return "\n".join(report)


def main():
    """Main verification function"""
    print("🚀 MarketEdge Feature Flags & Modules Production Database Verifier")
    print("🎯 Target: Zebra Associates £925K Opportunity - 404 Error Investigation")
    print("=" * 90)
    
    # Initialize verifier
    verifier = FeatureFlagsModulesVerifier()
    
    # Connect to database
    print("⏳ Connecting to production database...")
    if not verifier.connect_to_database():
        print("❌ CRITICAL: Failed to connect to production database")
        print("")
        print("🔧 Check:")
        print("   1. DATABASE_URL environment variable")
        print("   2. Network connectivity to Render")
        print("   3. Database service status")
        sys.exit(1)
    
    print("")
    
    # Verify tables
    print("📊 Verifying feature flags and module tables...")
    verification_results = verifier.verify_all_tables()
    print("")
    
    # Check supporting data
    print("👥 Checking supporting user/organisation data...")
    user_org_data = verifier.check_user_organisation_data()
    print("")
    
    # Generate SQL scripts
    print("🔧 Generating remediation SQL scripts...")
    demo_data_sql = verifier.generate_demo_data_sql(verification_results, user_org_data)
    missing_tables_sql = verifier.generate_missing_tables_sql(verification_results)
    print("")
    
    # Generate and display report
    report = verifier.generate_report(verification_results, user_org_data, demo_data_sql, missing_tables_sql)
    print(report)
    
    # Save report and SQL scripts
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save main report
    report_filename = f"feature_flags_modules_verification_{timestamp}.txt"
    try:
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to: {report_filename}")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")
    
    # Save demo data SQL
    if demo_data_sql and len(demo_data_sql) > 5:
        demo_sql_filename = f"demo_data_script_{timestamp}.sql"
        try:
            with open(demo_sql_filename, 'w') as f:
                f.write('\n'.join(demo_data_sql))
            print(f"📄 Demo data SQL saved to: {demo_sql_filename}")
        except Exception as e:
            print(f"⚠️  Could not save demo SQL: {e}")
    
    # Save table creation SQL
    if missing_tables_sql and len(missing_tables_sql) > 1:
        tables_sql_filename = f"missing_tables_script_{timestamp}.sql"
        try:
            with open(tables_sql_filename, 'w') as f:
                f.write('\n'.join(missing_tables_sql))
            print(f"📄 Missing tables SQL saved to: {tables_sql_filename}")
        except Exception as e:
            print(f"⚠️  Could not save tables SQL: {e}")
    
    print("")
    
    # Exit with status code
    summary = verification_results["summary"]
    if summary['tables_missing'] > 0 or summary['tables_empty'] >= 2:
        print("❌ CRITICAL ISSUES DETECTED - £925K OPPORTUNITY AT RISK")
        print("🚨 IMMEDIATE ACTION REQUIRED")
        sys.exit(2)  # Critical
    elif summary['tables_empty'] > 0 or summary['tables_incomplete'] > 0:
        print("⚠️  ISSUES DETECTED - PLATFORM FUNCTIONALITY COMPROMISED")
        print("🔧 ACTION RECOMMENDED")
        sys.exit(1)  # Warning
    else:
        print("✅ DATABASE SCHEMA APPEARS HEALTHY")
        print("🔍 INVESTIGATE APPLICATION LOGIC FOR 404 ERRORS")
        sys.exit(0)  # Success


if __name__ == "__main__":
    main()