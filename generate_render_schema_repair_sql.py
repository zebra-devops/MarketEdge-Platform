#!/usr/bin/env python3
"""
Generate Schema Repair SQL for Render Production
===============================================

This script generates the complete SQL needed to repair the production
schema on Render without requiring a database connection. Based on the
known schema drift issues identified by production validation.

The generated SQL can be applied directly to the Render PostgreSQL database.
"""

import sys
from datetime import datetime
from pathlib import Path

def generate_comprehensive_schema_repair_sql():
    """Generate complete SQL for all known schema issues"""

    timestamp = datetime.now().isoformat()

    sql_statements = [
        "-- MarketEdge Production Schema Repair SQL",
        f"-- Generated: {timestamp}",
        "-- Target: Render PostgreSQL Database",
        "-- CRITICAL: Review before applying to production",
        "",
        "-- Begin Transaction",
        "BEGIN;",
        "",
        "-- ================================================================",
        "-- PHASE 1: CREATE MISSING TABLES",
        "-- ================================================================",
        "",
        "-- 1. competitive_factor_templates",
        """CREATE TABLE IF NOT EXISTS competitive_factor_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sic_code VARCHAR(10) NOT NULL REFERENCES sic_codes(code),
    factor_name VARCHAR(255) NOT NULL,
    description TEXT,
    weight DECIMAL(5,2) DEFAULT 1.0,
    calculation_method VARCHAR(50),
    data_requirements JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);""",
        "",
        "-- 2. module_configurations",
        """CREATE TABLE IF NOT EXISTS module_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(255) NOT NULL REFERENCES analytics_modules(id),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    config_key VARCHAR(255) NOT NULL,
    config_value JSONB NOT NULL,
    is_encrypted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(module_id, organisation_id, config_key)
);""",
        "",
        "-- 3. industry_templates",
        """CREATE TABLE IF NOT EXISTS industry_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sic_code VARCHAR(10) NOT NULL REFERENCES sic_codes(code),
    template_name VARCHAR(255) NOT NULL,
    template_data JSONB NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);""",
        "",
        "-- 4. module_usage_logs",
        """CREATE TABLE IF NOT EXISTS module_usage_logs (
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
);""",
        "",
        "-- 5. sector_modules",
        """CREATE TABLE IF NOT EXISTS sector_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sic_code VARCHAR(10) NOT NULL REFERENCES sic_codes(code),
    module_id VARCHAR(255) NOT NULL REFERENCES analytics_modules(id),
    is_recommended BOOLEAN NOT NULL DEFAULT FALSE,
    priority_order INTEGER DEFAULT 0,
    configuration_template JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(sic_code, module_id)
);""",
        "",
        "-- 6. organization_template_applications",
        """CREATE TABLE IF NOT EXISTS organization_template_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    template_id UUID NOT NULL REFERENCES industry_templates(id),
    applied_by UUID REFERENCES users(id),
    customizations JSONB DEFAULT '{}',
    applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);""",
        "",
        "-- 7. hierarchy_role_assignments",
        """CREATE TABLE IF NOT EXISTS hierarchy_role_assignments (
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
);""",
        "",
        "-- 8. feature_flag_usage",
        """CREATE TABLE IF NOT EXISTS feature_flag_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_id UUID NOT NULL REFERENCES feature_flags(id),
    organisation_id UUID REFERENCES organisations(id),
    user_id UUID REFERENCES users(id),
    evaluation_result BOOLEAN NOT NULL,
    evaluation_context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);""",
        "",
        "-- 9. admin_actions",
        """CREATE TABLE IF NOT EXISTS admin_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id UUID NOT NULL REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL,
    target_resource VARCHAR(100),
    target_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);""",
        "",
        "-- ================================================================",
        "-- PHASE 2: ADD MISSING COLUMNS TO EXISTING TABLES",
        "-- ================================================================",
        "",
        "-- sic_codes table enhancements",
        "ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS title VARCHAR(500) NOT NULL DEFAULT '';",
        "ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS description TEXT;",
        "ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS is_supported BOOLEAN NOT NULL DEFAULT FALSE;",
        "ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS competitive_factors JSONB NOT NULL DEFAULT '{}'::jsonb;",
        "ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS default_metrics JSONB NOT NULL DEFAULT '{}'::jsonb;",
        "ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS analytics_config JSONB NOT NULL DEFAULT '{}'::jsonb;",
        "ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();",
        "ALTER TABLE sic_codes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();",
        "",
        "-- analytics_modules table enhancements",
        "ALTER TABLE analytics_modules ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb;",
        "ALTER TABLE analytics_modules ADD COLUMN IF NOT EXISTS ai_enhanced BOOLEAN NOT NULL DEFAULT FALSE;",
        "ALTER TABLE analytics_modules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();",
        "ALTER TABLE analytics_modules ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();",
        "",
        "-- organisation_modules table creation (if missing) and enhancements",
        """CREATE TABLE IF NOT EXISTS organisation_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    module_id VARCHAR(255) NOT NULL REFERENCES analytics_modules(id),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_used TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(organisation_id, module_id)
);""",
        "",
        "-- feature_flags table enhancements",
        "ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active';",
        "ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS conditions JSONB;",
        "ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;",
        "ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);",
        "ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES users(id);",
        "ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();",
        "ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();",
        "",
        "-- feature_flag_overrides table enhancements",
        "ALTER TABLE feature_flag_overrides ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);",
        "ALTER TABLE feature_flag_overrides ADD COLUMN IF NOT EXISTS reason TEXT;",
        "ALTER TABLE feature_flag_overrides ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE feature_flag_overrides ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();",
        "ALTER TABLE feature_flag_overrides ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();",
        "",
        "-- audit_logs table enhancements",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES organisations(id);",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS action VARCHAR(50) NOT NULL DEFAULT '';",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS resource_type VARCHAR(50);",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS resource_id VARCHAR(255);",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS changes JSONB;",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS ip_address INET;",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_agent TEXT;",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();",
        "",
        "-- ================================================================",
        "-- PHASE 3: CREATE INDEXES FOR PERFORMANCE",
        "-- ================================================================",
        "",
        "-- Indexes for feature_flags",
        "CREATE INDEX IF NOT EXISTS idx_feature_flags_status ON feature_flags(status);",
        "CREATE INDEX IF NOT EXISTS idx_feature_flags_created_by ON feature_flags(created_by);",
        "",
        "-- Indexes for module usage tracking",
        "CREATE INDEX IF NOT EXISTS idx_module_usage_logs_module_org ON module_usage_logs(module_id, organisation_id);",
        "CREATE INDEX IF NOT EXISTS idx_module_usage_logs_created_at ON module_usage_logs(created_at);",
        "",
        "-- Indexes for admin actions",
        "CREATE INDEX IF NOT EXISTS idx_admin_actions_admin_user ON admin_actions(admin_user_id);",
        "CREATE INDEX IF NOT EXISTS idx_admin_actions_created_at ON admin_actions(created_at);",
        "",
        "-- Indexes for audit logs",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_id ON audit_logs(tenant_id);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);",
        "",
        "-- ================================================================",
        "-- PHASE 4: UPDATE ALEMBIC VERSION (CRITICAL)",
        "-- ================================================================",
        "",
        "-- Update alembic version to reflect that Phase 3 migrations are applied",
        "-- This prevents future migration conflicts",
        "UPDATE alembic_version SET version_num = '003' WHERE version_num IS NOT NULL;",
        "",
        "-- If no version exists, insert it",
        "INSERT INTO alembic_version (version_num) SELECT '003' WHERE NOT EXISTS (SELECT 1 FROM alembic_version);",
        "",
        "-- ================================================================",
        "-- PHASE 5: VERIFY SCHEMA REPAIR",
        "-- ================================================================",
        "",
        "-- Count tables to verify creation",
        "SELECT 'competitive_factor_templates' as table_name, COUNT(*) as exists FROM information_schema.tables WHERE table_name = 'competitive_factor_templates';",
        "SELECT 'module_configurations' as table_name, COUNT(*) as exists FROM information_schema.tables WHERE table_name = 'module_configurations';",
        "SELECT 'industry_templates' as table_name, COUNT(*) as exists FROM information_schema.tables WHERE table_name = 'industry_templates';",
        "SELECT 'module_usage_logs' as table_name, COUNT(*) as exists FROM information_schema.tables WHERE table_name = 'module_usage_logs';",
        "SELECT 'sector_modules' as table_name, COUNT(*) as exists FROM information_schema.tables WHERE table_name = 'sector_modules';",
        "SELECT 'organization_template_applications' as table_name, COUNT(*) as exists FROM information_schema.tables WHERE table_name = 'organization_template_applications';",
        "SELECT 'hierarchy_role_assignments' as table_name, COUNT(*) as exists FROM information_schema.tables WHERE table_name = 'hierarchy_role_assignments';",
        "SELECT 'feature_flag_usage' as table_name, COUNT(*) as exists FROM information_schema.tables WHERE table_name = 'feature_flag_usage';",
        "SELECT 'admin_actions' as table_name, COUNT(*) as exists FROM information_schema.tables WHERE table_name = 'admin_actions';",
        "",
        "-- Verify critical columns exist",
        "SELECT 'feature_flags.status' as column_name, COUNT(*) as exists FROM information_schema.columns WHERE table_name = 'feature_flags' AND column_name = 'status';",
        "SELECT 'sic_codes.title' as column_name, COUNT(*) as exists FROM information_schema.columns WHERE table_name = 'sic_codes' AND column_name = 'title';",
        "SELECT 'analytics_modules.tags' as column_name, COUNT(*) as exists FROM information_schema.columns WHERE table_name = 'analytics_modules' AND column_name = 'tags';",
        "",
        "-- Commit Transaction",
        "COMMIT;",
        "",
        "-- ================================================================",
        "-- REPAIR COMPLETE",
        "-- ================================================================",
        "",
        "SELECT 'Schema repair completed successfully' as status;",
    ]

    return sql_statements

def main():
    """Generate the schema repair SQL file"""
    print("🛠️  Generating schema repair SQL for Render production...")

    # Generate SQL
    sql_statements = generate_comprehensive_schema_repair_sql()

    # Write to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sql_file = Path(f"render_production_schema_repair_{timestamp}.sql")

    with open(sql_file, 'w') as f:
        for statement in sql_statements:
            f.write(statement + '\n')

    print(f"✅ Schema repair SQL generated: {sql_file}")
    print(f"📊 Generated {len([s for s in sql_statements if s.strip() and not s.startswith('--')])} SQL statements")

    print("\n📋 Next steps:")
    print("1. Review the generated SQL file")
    print("2. Apply to Render PostgreSQL database:")
    print(f"   psql $DATABASE_URL -f {sql_file}")
    print("3. Or copy SQL content to Render SQL console")
    print("4. Verify admin endpoints are functional")

    print(f"\n📄 SQL file location: {sql_file.absolute()}")

    return sql_file

if __name__ == "__main__":
    main()