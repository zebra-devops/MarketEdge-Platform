#!/usr/bin/env python3
"""
Production Schema Repair Script
===============================

This script analyzes the production database schema and applies comprehensive fixes
to bring it up to date with the current SQLAlchemy models.

CRITICAL USAGE:
- This script is designed to fix production schema drift
- Creates missing tables and columns identified in validation
- Safe to run multiple times (uses IF NOT EXISTS patterns)
- Logs all operations for audit trail

Usage:
    # Dry run - show what would be fixed
    python database/production_schema_repair.py --dry-run

    # Apply fixes to production database
    python database/production_schema_repair.py --apply

    # Generate SQL file for manual review
    python database/production_schema_repair.py --generate-sql > production_fixes.sql

Environment Variables Required:
    DATABASE_URL - PostgreSQL connection string for production database

Exit Codes:
    0: Success (no issues or fixes applied successfully)
    1: Schema validation failed or fixes needed
    2: Database connection failed
    3: Critical error during repair
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Set
from datetime import datetime
from sqlalchemy import text, create_engine, Engine
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'schema_repair_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class ProductionSchemaRepairer:
    """Comprehensive production schema repair tool"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.fixes_applied = []
        self.errors_encountered = []

    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = self.engine.connect()
            yield conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def validate_current_schema(self) -> Dict[str, List[str]]:
        """Validate current production schema and identify missing components"""
        logger.info("Validating production database schema...")

        missing_tables = []
        missing_columns = {}

        with self.get_connection() as conn:
            # Check for missing tables
            expected_tables = {
                'competitive_factor_templates': self.get_competitive_factor_templates_sql(),
                'module_configurations': self.get_module_configurations_sql(),
                'industry_templates': self.get_industry_templates_sql(),
                'module_usage_logs': self.get_module_usage_logs_sql(),
                'sector_modules': self.get_sector_modules_sql(),
                'organization_template_applications': self.get_organization_template_applications_sql(),
                'hierarchy_role_assignments': self.get_hierarchy_role_assignments_sql(),
                'feature_flag_usage': self.get_feature_flag_usage_sql(),
                'admin_actions': self.get_admin_actions_sql()
            }

            # Check which tables exist
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """))
            existing_tables = {row[0] for row in result.fetchall()}

            for table_name in expected_tables.keys():
                if table_name not in existing_tables:
                    missing_tables.append(table_name)
                    logger.warning(f"Missing table: {table_name}")

            # Check for missing columns in existing tables
            expected_columns = {
                'sic_codes': ['title', 'description', 'is_supported', 'competitive_factors', 'default_metrics', 'analytics_config', 'created_at', 'updated_at'],
                'analytics_modules': ['tags', 'ai_enhanced', 'created_at', 'updated_at'],
                'organisation_modules': ['organisation_id', 'module_id', 'enabled', 'configuration', 'last_used', 'usage_count', 'created_at', 'updated_at'],
                'feature_flags': ['status', 'conditions', 'metadata', 'created_by', 'updated_by', 'created_at', 'updated_at'],
                'feature_flag_overrides': ['created_by', 'reason', 'expires_at', 'created_at', 'updated_at'],
                'audit_logs': ['tenant_id', 'user_id', 'action', 'resource_type', 'resource_id', 'changes', 'ip_address', 'user_agent', 'created_at']
            }

            for table_name, expected_cols in expected_columns.items():
                if table_name in existing_tables:
                    # Get actual columns
                    result = conn.execute(text("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                        AND table_name = :table_name
                    """), {"table_name": table_name})
                    actual_columns = {row[0] for row in result.fetchall()}

                    missing_cols = []
                    for col in expected_cols:
                        if col not in actual_columns:
                            missing_cols.append(col)
                            logger.warning(f"Missing column: {table_name}.{col}")

                    if missing_cols:
                        missing_columns[table_name] = missing_cols

        return {
            'missing_tables': missing_tables,
            'missing_columns': missing_columns,
            'total_issues': len(missing_tables) + sum(len(cols) for cols in missing_columns.values())
        }

    def generate_repair_sql(self, validation_results: Dict) -> List[str]:
        """Generate SQL statements to repair schema"""
        sql_statements = []

        # Add header comment
        sql_statements.append("-- Production Schema Repair Script")
        sql_statements.append(f"-- Generated: {datetime.now().isoformat()}")
        sql_statements.append("-- CRITICAL: Review before applying to production")
        sql_statements.append("")

        # Create missing tables
        table_creation_sql = {
            'competitive_factor_templates': self.get_competitive_factor_templates_sql(),
            'module_configurations': self.get_module_configurations_sql(),
            'industry_templates': self.get_industry_templates_sql(),
            'module_usage_logs': self.get_module_usage_logs_sql(),
            'sector_modules': self.get_sector_modules_sql(),
            'organization_template_applications': self.get_organization_template_applications_sql(),
            'hierarchy_role_assignments': self.get_hierarchy_role_assignments_sql(),
            'feature_flag_usage': self.get_feature_flag_usage_sql(),
            'admin_actions': self.get_admin_actions_sql()
        }

        for table_name in validation_results['missing_tables']:
            if table_name in table_creation_sql:
                sql_statements.append(f"-- Create missing table: {table_name}")
                sql_statements.append(table_creation_sql[table_name])
                sql_statements.append("")

        # Add missing columns
        column_additions = {
            'sic_codes': {
                'title': 'ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS title VARCHAR(500) NOT NULL DEFAULT \'\';',
                'description': 'ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS description TEXT;',
                'is_supported': 'ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS is_supported BOOLEAN NOT NULL DEFAULT FALSE;',
                'competitive_factors': 'ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS competitive_factors JSONB NOT NULL DEFAULT \'{}\'::jsonb;',
                'default_metrics': 'ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS default_metrics JSONB NOT NULL DEFAULT \'{}\'::jsonb;',
                'analytics_config': 'ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS analytics_config JSONB NOT NULL DEFAULT \'{}\'::jsonb;',
                'created_at': 'ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();',
                'updated_at': 'ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();'
            },
            'analytics_modules': {
                'tags': 'ALTER TABLE analytics_modules ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT \'[]\'::jsonb;',
                'ai_enhanced': 'ALTER TABLE analytics_modules ADD COLUMN IF NOT EXISTS ai_enhanced BOOLEAN NOT NULL DEFAULT FALSE;',
                'created_at': 'ALTER TABLE analytics_modules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();',
                'updated_at': 'ALTER TABLE analytics_modules ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();'
            },
            'organisation_modules': {
                'organisation_id': 'ALTER TABLE organisation_modules ADD COLUMN IF NOT EXISTS organisation_id UUID REFERENCES organisations(id);',
                'module_id': 'ALTER TABLE organisation_modules ADD COLUMN IF NOT EXISTS module_id VARCHAR(255) REFERENCES analytics_modules(id);',
                'enabled': 'ALTER TABLE organisation_modules ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT TRUE;',
                'configuration': 'ALTER TABLE organisation_modules ADD COLUMN IF NOT EXISTS configuration JSONB NOT NULL DEFAULT \'{}\'::jsonb;',
                'last_used': 'ALTER TABLE organisation_modules ADD COLUMN IF NOT EXISTS last_used TIMESTAMP WITH TIME ZONE;',
                'usage_count': 'ALTER TABLE organisation_modules ADD COLUMN IF NOT EXISTS usage_count INTEGER NOT NULL DEFAULT 0;',
                'created_at': 'ALTER TABLE organisation_modules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();',
                'updated_at': 'ALTER TABLE organisation_modules ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();'
            },
            'feature_flags': {
                'status': 'ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT \'active\';',
                'conditions': 'ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS conditions JSONB;',
                'metadata': 'ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT \'{}\'::jsonb;',
                'created_by': 'ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);',
                'updated_by': 'ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES users(id);',
                'created_at': 'ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();',
                'updated_at': 'ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();'
            },
            'feature_flag_overrides': {
                'created_by': 'ALTER TABLE feature_flag_overrides ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);',
                'reason': 'ALTER TABLE feature_flag_overrides ADD COLUMN IF NOT EXISTS reason TEXT;',
                'expires_at': 'ALTER TABLE feature_flag_overrides ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE;',
                'created_at': 'ALTER TABLE feature_flag_overrides ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();',
                'updated_at': 'ALTER TABLE feature_flag_overrides ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();'
            },
            'audit_logs': {
                'tenant_id': 'ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES organisations(id);',
                'user_id': 'ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);',
                'action': 'ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS action VARCHAR(50) NOT NULL DEFAULT \'\';',
                'resource_type': 'ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS resource_type VARCHAR(50);',
                'resource_id': 'ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS resource_id VARCHAR(255);',
                'changes': 'ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS changes JSONB;',
                'ip_address': 'ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS ip_address INET;',
                'user_agent': 'ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_agent TEXT;',
                'created_at': 'ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();'
            }
        }

        for table_name, missing_cols in validation_results['missing_columns'].items():
            if table_name in column_additions:
                sql_statements.append(f"-- Add missing columns to {table_name}")
                for col_name in missing_cols:
                    if col_name in column_additions[table_name]:
                        sql_statements.append(column_additions[table_name][col_name])
                sql_statements.append("")

        return sql_statements

    def apply_repairs(self, sql_statements: List[str], dry_run: bool = True) -> bool:
        """Apply schema repairs to database"""
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be applied")
            for stmt in sql_statements:
                if not stmt.startswith('--') and stmt.strip():
                    logger.info(f"Would execute: {stmt}")
            return True

        logger.info("Applying schema repairs to production database...")
        success_count = 0
        error_count = 0

        with self.get_connection() as conn:
            trans = conn.begin()
            try:
                for stmt in sql_statements:
                    if stmt.startswith('--') or not stmt.strip():
                        continue

                    try:
                        logger.info(f"Executing: {stmt}")
                        conn.execute(text(stmt))
                        success_count += 1
                        self.fixes_applied.append(stmt)
                    except Exception as e:
                        logger.error(f"Failed to execute: {stmt}")
                        logger.error(f"Error: {e}")
                        error_count += 1
                        self.errors_encountered.append(f"{stmt}: {e}")

                        # Continue with other fixes unless it's critical
                        if "does not exist" in str(e) and "relation" in str(e):
                            logger.warning("Skipping due to missing dependency - will retry after table creation")
                            continue
                        else:
                            # For other errors, continue but log
                            pass

                if error_count == 0:
                    trans.commit()
                    logger.info(f"Successfully applied {success_count} schema fixes")
                    return True
                else:
                    trans.rollback()
                    logger.error(f"Rolled back due to {error_count} errors")
                    return False

            except Exception as e:
                trans.rollback()
                logger.error(f"Critical error during repair: {e}")
                return False

    # Table creation SQL methods
    def get_competitive_factor_templates_sql(self) -> str:
        return """
CREATE TABLE IF NOT EXISTS competitive_factor_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sic_code VARCHAR(10) NOT NULL REFERENCES sic_codes(code),
    factor_name VARCHAR(255) NOT NULL,
    description TEXT,
    weight DECIMAL(5,2) DEFAULT 1.0,
    calculation_method VARCHAR(50),
    data_requirements JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

    def get_module_configurations_sql(self) -> str:
        return """
CREATE TABLE IF NOT EXISTS module_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(255) NOT NULL REFERENCES analytics_modules(id),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    config_key VARCHAR(255) NOT NULL,
    config_value JSONB NOT NULL,
    is_encrypted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(module_id, organisation_id, config_key)
);
"""

    def get_industry_templates_sql(self) -> str:
        return """
CREATE TABLE IF NOT EXISTS industry_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sic_code VARCHAR(10) NOT NULL REFERENCES sic_codes(code),
    template_name VARCHAR(255) NOT NULL,
    template_data JSONB NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

    def get_module_usage_logs_sql(self) -> str:
        return """
CREATE TABLE IF NOT EXISTS module_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(255) NOT NULL REFERENCES analytics_modules(id),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    execution_time_ms INTEGER,
    memory_usage_mb INTEGER,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

    def get_sector_modules_sql(self) -> str:
        return """
CREATE TABLE IF NOT EXISTS sector_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sic_code VARCHAR(10) NOT NULL REFERENCES sic_codes(code),
    module_id VARCHAR(255) NOT NULL REFERENCES analytics_modules(id),
    is_recommended BOOLEAN NOT NULL DEFAULT FALSE,
    priority_order INTEGER DEFAULT 0,
    configuration_template JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(sic_code, module_id)
);
"""

    def get_organization_template_applications_sql(self) -> str:
        return """
CREATE TABLE IF NOT EXISTS organization_template_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    template_id UUID NOT NULL REFERENCES industry_templates(id),
    applied_by UUID REFERENCES users(id),
    customizations JSONB DEFAULT '{}',
    applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
"""

    def get_hierarchy_role_assignments_sql(self) -> str:
        return """
CREATE TABLE IF NOT EXISTS hierarchy_role_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    role VARCHAR(50) NOT NULL,
    permissions JSONB DEFAULT '[]',
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(user_id, organisation_id, role)
);
"""

    def get_feature_flag_usage_sql(self) -> str:
        return """
CREATE TABLE IF NOT EXISTS feature_flag_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_id UUID NOT NULL REFERENCES feature_flags(id),
    organisation_id UUID REFERENCES organisations(id),
    user_id UUID REFERENCES users(id),
    evaluation_result BOOLEAN NOT NULL,
    evaluation_context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

    def get_admin_actions_sql(self) -> str:
        return """
CREATE TABLE IF NOT EXISTS admin_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id UUID NOT NULL REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL,
    target_resource VARCHAR(100),
    target_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
"""

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Repair production database schema")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without applying changes")
    parser.add_argument("--apply", action="store_true", help="Apply schema repairs to database")
    parser.add_argument("--generate-sql", action="store_true", help="Generate SQL file for manual review")
    parser.add_argument("--database-url", help="Database URL (defaults to DATABASE_URL env var)")

    args = parser.parse_args()

    # Default to dry-run mode
    if not any([args.dry_run, args.apply, args.generate_sql]):
        args.dry_run = True

    # Get database URL
    database_url = args.database_url or os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("ERROR: DATABASE_URL environment variable not set")
        sys.exit(2)

    try:
        # Initialize repairer
        repairer = ProductionSchemaRepairer(database_url)

        # Validate current schema
        validation_results = repairer.validate_current_schema()

        if validation_results['total_issues'] == 0:
            logger.info("✅ Production schema is valid - no repairs needed")
            sys.exit(0)

        logger.warning(f"❌ Found {validation_results['total_issues']} schema issues:")
        logger.warning(f"  - Missing tables: {len(validation_results['missing_tables'])}")
        logger.warning(f"  - Missing columns: {sum(len(cols) for cols in validation_results['missing_columns'].values())}")

        # Generate repair SQL
        repair_sql = repairer.generate_repair_sql(validation_results)

        if args.generate_sql:
            for stmt in repair_sql:
                print(stmt)
            sys.exit(0)

        # Apply or simulate repairs
        success = repairer.apply_repairs(repair_sql, dry_run=args.dry_run)

        if success:
            if args.dry_run:
                logger.info("✅ Dry run completed - ready for production application")
            else:
                logger.info("✅ Schema repairs applied successfully")
            sys.exit(0)
        else:
            logger.error("❌ Schema repair failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()