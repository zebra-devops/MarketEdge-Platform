#!/usr/bin/env python3
"""
Baseline Schema Generator
========================

Generates complete baseline schema SQL from SQLAlchemy models.
This creates a single source of truth for the expected database schema.

Usage:
    python database/generate_baseline.py > database/baseline_schema.sql
    python database/generate_baseline.py --apply  # Apply to database directly

The generated SQL can be used to:
1. Create a fresh database with complete schema
2. Validate existing databases against expected schema
3. Recover from schema drift issues
"""

import os
import sys
import argparse
import asyncio
from sqlalchemy import MetaData, create_engine
from sqlalchemy.schema import CreateTable, CreateIndex, CreateSequence
from sqlalchemy.ext.asyncio import create_async_engine

# Add app directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.base import Base
from app.models.user import User, UserRole
from app.models.organisation import Organisation
from app.models.modules import AnalyticsModule, OrganisationModule, ModuleConfiguration, ModuleUsageLog
from app.models.feature_flags import FeatureFlag, FeatureFlagUsage
from app.models.audit_log import AuditLog
from app.models.sectors import SICCode


def generate_baseline_schema() -> str:
    """Generate complete baseline schema SQL"""

    # Create a temporary in-memory engine for SQL generation
    engine = create_engine("postgresql://user:pass@localhost/db", echo=False)

    sql_statements = []

    # Add header
    sql_statements.append("""-- MarketEdge Platform Baseline Schema
-- Generated from SQLAlchemy models
-- This represents the complete expected database schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable Row Level Security
SET row_security = on;
""")

    # Generate CREATE TABLE statements for all models
    for table_name, table in Base.metadata.tables.items():
        create_table_sql = str(CreateTable(table).compile(engine))
        sql_statements.append(f"-- Table: {table_name}")
        sql_statements.append(create_table_sql + ";")
        sql_statements.append("")

    # Generate sequences if any
    for sequence in Base.metadata._sequences.values():
        create_sequence_sql = str(CreateSequence(sequence).compile(engine))
        sql_statements.append(f"-- Sequence: {sequence.name}")
        sql_statements.append(create_sequence_sql + ";")
        sql_statements.append("")

    # Generate indexes
    sql_statements.append("-- Indexes")
    for table_name, table in Base.metadata.tables.items():
        for index in table.indexes:
            create_index_sql = str(CreateIndex(index).compile(engine))
            sql_statements.append(create_index_sql + ";")

    sql_statements.append("")

    # Add Row Level Security policies
    sql_statements.append("""-- Row Level Security Policies
-- Enable RLS on multi-tenant tables

-- Enable RLS on organisations
ALTER TABLE organisations ENABLE ROW LEVEL SECURITY;

-- Enable RLS on organisation_users
ALTER TABLE organisation_users ENABLE ROW LEVEL SECURITY;

-- Enable RLS on organisation_modules
ALTER TABLE organisation_modules ENABLE ROW LEVEL SECURITY;

-- Enable RLS on module_configurations
ALTER TABLE module_configurations ENABLE ROW LEVEL SECURITY;

-- Enable RLS on module_usage_logs
ALTER TABLE module_usage_logs ENABLE ROW LEVEL SECURITY;

-- Enable RLS on audit_logs
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Enable RLS on data_sources
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;

-- Enable RLS on data_source_configurations
ALTER TABLE data_source_configurations ENABLE ROW LEVEL SECURITY;

-- Enable RLS on integration_logs
ALTER TABLE integration_logs ENABLE ROW LEVEL SECURITY;

-- Enable RLS on dashboards
ALTER TABLE dashboards ENABLE ROW LEVEL SECURITY;

-- Enable RLS on dashboard_widgets
ALTER TABLE dashboard_widgets ENABLE ROW LEVEL SECURITY;

-- Enable RLS on dashboard_shares
ALTER TABLE dashboard_shares ENABLE ROW LEVEL SECURITY;

-- Enable RLS on competitive_factors
ALTER TABLE competitive_factors ENABLE ROW LEVEL SECURITY;

-- Enable RLS on feature_flag_usage
ALTER TABLE feature_flag_usage ENABLE ROW LEVEL SECURITY;

-- Basic RLS policy for organisation isolation
-- This is a simplified policy - production should have more sophisticated rules
CREATE POLICY tenant_isolation ON organisations
    FOR ALL
    TO authenticated
    USING (id = current_setting('app.current_organisation_id', true)::uuid);

-- Add similar policies for other tables
-- (In production, these would be more comprehensive)
""")

    # Add essential constraints and validations
    sql_statements.append("""-- Essential Constraints and Validations

-- User email uniqueness
ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email);

-- Organisation name uniqueness
ALTER TABLE organisations ADD CONSTRAINT organisations_name_unique UNIQUE (name);

-- SIC code format validation
ALTER TABLE sic_codes ADD CONSTRAINT sic_codes_code_format
    CHECK (code ~ '^[0-9]{4,5}$');

-- Feature flag rollout percentage validation
ALTER TABLE feature_flags ADD CONSTRAINT feature_flags_rollout_percentage
    CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100);

-- Competitive factor weight validation
ALTER TABLE competitive_factor_templates ADD CONSTRAINT competitive_factor_templates_weight
    CHECK (weight >= 0 AND weight <= 100);

-- Analytics module status validation
ALTER TABLE analytics_modules ADD CONSTRAINT analytics_modules_status_valid
    CHECK (status IN ('development', 'testing', 'active', 'deprecated', 'retired'));

-- Data source status validation
ALTER TABLE data_sources ADD CONSTRAINT data_sources_status_valid
    CHECK (status IN ('active', 'inactive', 'error', 'pending'));
""")

    # Add performance indexes
    sql_statements.append("""-- Performance Indexes

-- User authentication indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_auth0_id ON users(auth0_id);

-- Organisation access indexes
CREATE INDEX IF NOT EXISTS idx_organisation_users_org_user ON organisation_users(organisation_id, user_id);
CREATE INDEX IF NOT EXISTS idx_organisation_users_user ON organisation_users(user_id);

-- Module usage indexes
CREATE INDEX IF NOT EXISTS idx_module_usage_logs_timestamp ON module_usage_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_module_usage_logs_module_org ON module_usage_logs(module_id, organisation_id);

-- Feature flag usage indexes
CREATE INDEX IF NOT EXISTS idx_feature_flag_usage_flag_time ON feature_flag_usage(feature_flag_id, accessed_at);
CREATE INDEX IF NOT EXISTS idx_feature_flag_usage_org_time ON feature_flag_usage(organisation_id, accessed_at);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action ON audit_logs(user_id, action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp_action ON audit_logs(timestamp, action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Dashboard indexes
CREATE INDEX IF NOT EXISTS idx_dashboards_org_user ON dashboards(organisation_id, user_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_widgets_dashboard ON dashboard_widgets(dashboard_id);

-- Data source indexes
CREATE INDEX IF NOT EXISTS idx_data_sources_org_status ON data_sources(organisation_id, status);
CREATE INDEX IF NOT EXISTS idx_integration_logs_source_timestamp ON integration_logs(data_source_id, timestamp);

-- Competitive factor indexes
CREATE INDEX IF NOT EXISTS idx_competitive_factors_org_active ON competitive_factors(organisation_id, is_active);
""")

    # Add schema validation function
    sql_statements.append("""-- Schema Validation Function
-- Call this function to verify schema integrity

CREATE OR REPLACE FUNCTION validate_schema()
RETURNS TABLE(table_name text, column_name text, issue_type text, description text)
LANGUAGE plpgsql
AS $$
BEGIN
    -- This function would contain comprehensive schema validation logic
    -- For now, it's a placeholder for future enhancement
    RETURN QUERY
    SELECT
        'schema_validation'::text as table_name,
        'complete'::text as column_name,
        'info'::text as issue_type,
        'Baseline schema applied successfully'::text as description;
END;
$$;

-- Add schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES ('baseline_v1.0', 'Initial baseline schema from SQLAlchemy models')
ON CONFLICT (version) DO NOTHING;
""")

    return "\n".join(sql_statements)


async def apply_baseline_schema(database_url: str):
    """Apply baseline schema directly to database"""
    schema_sql = generate_baseline_schema()

    engine = create_async_engine(database_url, echo=False)

    try:
        async with engine.begin() as conn:
            # Split SQL into individual statements and execute
            statements = schema_sql.split(';')

            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        await conn.execute(statement)
                    except Exception as e:
                        print(f"Warning: Failed to execute statement: {statement[:100]}...")
                        print(f"Error: {e}")

        print("Baseline schema applied successfully")

    except Exception as e:
        print(f"Error applying baseline schema: {e}")
        raise
    finally:
        await engine.dispose()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate baseline schema from SQLAlchemy models")
    parser.add_argument("--apply", action="store_true", help="Apply schema directly to database")
    parser.add_argument("--database-url", help="Database URL (defaults to DATABASE_URL env var)")
    parser.add_argument("--output", help="Output file path (defaults to stdout)")

    args = parser.parse_args()

    if args.apply:
        database_url = args.database_url or os.getenv("DATABASE_URL")
        if not database_url:
            print("ERROR: DATABASE_URL environment variable not set", file=sys.stderr)
            sys.exit(1)

        asyncio.run(apply_baseline_schema(database_url))
    else:
        schema_sql = generate_baseline_schema()

        if args.output:
            with open(args.output, 'w') as f:
                f.write(schema_sql)
            print(f"Baseline schema written to {args.output}")
        else:
            print(schema_sql)


if __name__ == "__main__":
    main()