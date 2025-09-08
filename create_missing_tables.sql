-- SQL Script to Create Missing Feature Flags and Modules Tables
-- Generated for Zebra Associates £925K opportunity investigation
-- Use this if alembic migrations are not available

-- WARNING: These are simplified table definitions based on SQLAlchemy models
-- It's recommended to use: alembic upgrade head
-- Only use this script if alembic is not available

-- =============================================================================
-- FEATURE FLAGS TABLES
-- =============================================================================

-- Core feature flags table
CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    rollout_percentage INTEGER DEFAULT 0 NOT NULL CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),
    scope VARCHAR(20) DEFAULT 'global' CHECK (scope IN ('global', 'organisation', 'sector', 'user')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated')),
    config JSONB DEFAULT '{}' NOT NULL,
    allowed_sectors JSONB DEFAULT '[]' NOT NULL,
    blocked_sectors JSONB DEFAULT '[]' NOT NULL,
    module_id VARCHAR(255),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for feature_flags
CREATE INDEX IF NOT EXISTS idx_feature_flags_flag_key ON feature_flags(flag_key);
CREATE INDEX IF NOT EXISTS idx_feature_flags_module_id ON feature_flags(module_id);
CREATE INDEX IF NOT EXISTS idx_feature_flags_scope ON feature_flags(scope);
CREATE INDEX IF NOT EXISTS idx_feature_flags_enabled ON feature_flags(is_enabled);

-- Feature flag overrides table
CREATE TABLE IF NOT EXISTS feature_flag_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_flag_id UUID NOT NULL REFERENCES feature_flags(id) ON DELETE CASCADE,
    organisation_id UUID REFERENCES organisations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    is_enabled BOOLEAN NOT NULL,
    reason TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT feature_flag_overrides_target_check CHECK (
        (organisation_id IS NOT NULL AND user_id IS NULL) OR 
        (organisation_id IS NULL AND user_id IS NOT NULL)
    )
);

-- Indexes for feature_flag_overrides
CREATE INDEX IF NOT EXISTS idx_feature_flag_overrides_flag_id ON feature_flag_overrides(feature_flag_id);
CREATE INDEX IF NOT EXISTS idx_feature_flag_overrides_org_id ON feature_flag_overrides(organisation_id);
CREATE INDEX IF NOT EXISTS idx_feature_flag_overrides_user_id ON feature_flag_overrides(user_id);

-- Feature flag usage tracking table
CREATE TABLE IF NOT EXISTS feature_flag_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_flag_id UUID NOT NULL REFERENCES feature_flags(id) ON DELETE CASCADE,
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    was_enabled BOOLEAN NOT NULL,
    evaluation_context JSONB DEFAULT '{}' NOT NULL,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for feature_flag_usage
CREATE INDEX IF NOT EXISTS idx_feature_flag_usage_flag_id ON feature_flag_usage(feature_flag_id);
CREATE INDEX IF NOT EXISTS idx_feature_flag_usage_org_id ON feature_flag_usage(organisation_id);
CREATE INDEX IF NOT EXISTS idx_feature_flag_usage_user_id ON feature_flag_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_flag_usage_accessed_at ON feature_flag_usage(accessed_at);

-- =============================================================================
-- ANALYTICS MODULES TABLES
-- =============================================================================

-- Core analytics modules registry
CREATE TABLE IF NOT EXISTS analytics_modules (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    version VARCHAR(50) DEFAULT '1.0.0' NOT NULL,
    module_type VARCHAR(20) NOT NULL CHECK (module_type IN ('core', 'analytics', 'integration', 'visualization', 'reporting', 'ai_ml')),
    status VARCHAR(20) DEFAULT 'development' CHECK (status IN ('development', 'testing', 'active', 'deprecated', 'retired')),
    is_core BOOLEAN DEFAULT FALSE NOT NULL,
    requires_license BOOLEAN DEFAULT FALSE NOT NULL,
    entry_point VARCHAR(500) NOT NULL,
    config_schema JSONB DEFAULT '{}' NOT NULL,
    default_config JSONB DEFAULT '{}' NOT NULL,
    dependencies JSONB DEFAULT '[]' NOT NULL,
    api_endpoints JSONB DEFAULT '[]' NOT NULL,
    frontend_components JSONB DEFAULT '[]' NOT NULL,
    min_data_requirements JSONB DEFAULT '{}' NOT NULL,
    documentation_url VARCHAR(500),
    help_text TEXT,
    pricing_tier VARCHAR(50),
    license_requirements JSONB DEFAULT '{}' NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for analytics_modules
CREATE INDEX IF NOT EXISTS idx_analytics_modules_type ON analytics_modules(module_type);
CREATE INDEX IF NOT EXISTS idx_analytics_modules_status ON analytics_modules(status);
CREATE INDEX IF NOT EXISTS idx_analytics_modules_is_core ON analytics_modules(is_core);

-- Organisation modules (which modules are enabled per organisation)
CREATE TABLE IF NOT EXISTS organisation_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    module_id VARCHAR(255) NOT NULL REFERENCES analytics_modules(id) ON DELETE CASCADE,
    is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    configuration JSONB DEFAULT '{}' NOT NULL,
    enabled_for_users JSONB DEFAULT '[]' NOT NULL,
    disabled_for_users JSONB DEFAULT '[]' NOT NULL,
    first_enabled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0 NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(organisation_id, module_id)
);

-- Indexes for organisation_modules
CREATE INDEX IF NOT EXISTS idx_organisation_modules_org_id ON organisation_modules(organisation_id);
CREATE INDEX IF NOT EXISTS idx_organisation_modules_module_id ON organisation_modules(module_id);
CREATE INDEX IF NOT EXISTS idx_organisation_modules_enabled ON organisation_modules(is_enabled);

-- Module configurations (module-specific settings)
CREATE TABLE IF NOT EXISTS module_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(255) NOT NULL REFERENCES analytics_modules(id) ON DELETE CASCADE,
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    config_key VARCHAR(255) NOT NULL,
    config_value JSONB NOT NULL,
    schema_version VARCHAR(50) DEFAULT '1.0.0' NOT NULL,
    is_encrypted BOOLEAN DEFAULT FALSE NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(module_id, organisation_id, config_key)
);

-- Indexes for module_configurations
CREATE INDEX IF NOT EXISTS idx_module_configurations_module_id ON module_configurations(module_id);
CREATE INDEX IF NOT EXISTS idx_module_configurations_org_id ON module_configurations(organisation_id);

-- Module usage logs (for analytics and billing)
CREATE TABLE IF NOT EXISTS module_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(255) NOT NULL REFERENCES analytics_modules(id) ON DELETE CASCADE,
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    endpoint VARCHAR(500),
    duration_ms INTEGER CHECK (duration_ms >= 0),
    context JSONB DEFAULT '{}' NOT NULL,
    success BOOLEAN DEFAULT TRUE NOT NULL,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for module_usage_logs  
CREATE INDEX IF NOT EXISTS idx_module_usage_logs_module_id ON module_usage_logs(module_id);
CREATE INDEX IF NOT EXISTS idx_module_usage_logs_org_id ON module_usage_logs(organisation_id);
CREATE INDEX IF NOT EXISTS idx_module_usage_logs_user_id ON module_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_module_usage_logs_timestamp ON module_usage_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_module_usage_logs_success ON module_usage_logs(success);

-- =============================================================================
-- USER APPLICATION ACCESS TABLE
-- =============================================================================

-- User application access (which applications each user can access)
CREATE TABLE IF NOT EXISTS user_application_access (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    application VARCHAR(50) NOT NULL CHECK (application IN ('market_edge', 'causal_edge', 'value_edge')),
    has_access BOOLEAN DEFAULT FALSE NOT NULL,
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, application)
);

-- Indexes for user_application_access
CREATE INDEX IF NOT EXISTS idx_user_application_access_user_id ON user_application_access(user_id);
CREATE INDEX IF NOT EXISTS idx_user_application_access_application ON user_application_access(application);
CREATE INDEX IF NOT EXISTS idx_user_application_access_has_access ON user_application_access(has_access);

-- =============================================================================
-- USER INVITATIONS TABLE (if not exists)
-- =============================================================================

-- User invitations for invitation workflow
CREATE TABLE IF NOT EXISTS user_invitations (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invitation_token VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired')),
    invited_by UUID NOT NULL REFERENCES users(id),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (user_id)
);

-- Indexes for user_invitations
CREATE INDEX IF NOT EXISTS idx_user_invitations_token ON user_invitations(invitation_token);
CREATE INDEX IF NOT EXISTS idx_user_invitations_status ON user_invitations(status);

-- =============================================================================
-- UPDATE TRIGGERS (Optional - for automatic updated_at timestamps)
-- =============================================================================

-- Function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for tables with updated_at columns
CREATE TRIGGER update_feature_flags_updated_at 
    BEFORE UPDATE ON feature_flags 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feature_flag_overrides_updated_at 
    BEFORE UPDATE ON feature_flag_overrides 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analytics_modules_updated_at 
    BEFORE UPDATE ON analytics_modules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organisation_modules_updated_at 
    BEFORE UPDATE ON organisation_modules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_module_configurations_updated_at 
    BEFORE UPDATE ON module_configurations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Run these to verify tables were created successfully:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%feature%' OR table_name LIKE '%module%';

-- Check constraints:
-- SELECT constraint_name, table_name FROM information_schema.table_constraints WHERE table_schema = 'public' AND (table_name LIKE '%feature%' OR table_name LIKE '%module%');

-- =============================================================================
-- NOTES
-- =============================================================================

-- 1. This script assumes users and organisations tables already exist
-- 2. UUIDs use gen_random_uuid() which requires PostgreSQL 13+ or pgcrypto extension
-- 3. For older PostgreSQL versions, replace gen_random_uuid() with uuid_generate_v4()
-- 4. All foreign key constraints include appropriate ON DELETE CASCADE/RESTRICT
-- 5. Includes proper indexing for query performance
-- 6. JSON columns use JSONB for better performance in PostgreSQL

-- =============================================================================
-- END OF TABLE CREATION SCRIPT
-- =============================================================================