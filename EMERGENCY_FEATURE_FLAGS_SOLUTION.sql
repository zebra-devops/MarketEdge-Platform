-- EMERGENCY FEATURE FLAGS TABLE CREATION FOR £925K ZEBRA ASSOCIATES
-- Critical fix for: relation "feature_flags" does not exist
-- Date: 2025-09-08
-- User: matt.lindop@zebra.associates accessing admin dashboard

-- 1. Create feature_flags table (CRITICAL - this is the missing table)
CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT false,
    default_value BOOLEAN DEFAULT false,
    environment VARCHAR(50) DEFAULT 'production',
    rollout_percentage INTEGER DEFAULT 0 CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),
    conditions JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID
);

-- 2. Create feature_flag_overrides table
CREATE TABLE IF NOT EXISTS feature_flag_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_flag_id UUID NOT NULL REFERENCES feature_flags(id) ON DELETE CASCADE,
    organisation_id UUID,
    user_id UUID,
    enabled BOOLEAN NOT NULL,
    override_value BOOLEAN NOT NULL,
    reason TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    UNIQUE(feature_flag_id, organisation_id, user_id)
);

-- 3. Create feature_flag_usage table for analytics
CREATE TABLE IF NOT EXISTS feature_flag_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_flag_id UUID NOT NULL REFERENCES feature_flags(id) ON DELETE CASCADE,
    user_id UUID,
    organisation_id UUID,
    evaluated_value BOOLEAN NOT NULL,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. INSERT CRITICAL FEATURE FLAGS (the exact one causing the error)
INSERT INTO feature_flags (flag_key, name, description, enabled, default_value, rollout_percentage)
VALUES 
    ('admin.advanced_controls', 'Admin Advanced Controls', 'Enable advanced admin dashboard controls for Zebra Associates', true, true, 100),
    ('admin.feature_flags', 'Admin Feature Flag Management', 'Enable feature flag management in admin panel', true, true, 100),
    ('admin.module_management', 'Admin Module Management', 'Enable module management features', true, true, 100),
    ('admin.user_management', 'Admin User Management', 'Enable user management features', true, true, 100),
    ('admin.analytics', 'Admin Analytics Dashboard', 'Enable analytics dashboard for admins', true, true, 100),
    ('module.pricing_intelligence', 'Pricing Intelligence Module', 'Enable pricing analytics module', true, true, 100),
    ('module.market_trends', 'Market Trends Module', 'Enable market trends analysis', true, true, 100),
    ('module.competitive_analysis', 'Competitive Analysis', 'Enable competitor analysis features', true, true, 100),
    ('module.cinema_analytics', 'Cinema Analytics', 'Zebra Associates specialized cinema analytics', true, true, 100),
    ('system.lazy_loading', 'System Lazy Loading', 'Enable lazy loading optimizations', true, true, 100)
ON CONFLICT (flag_key) DO UPDATE SET 
    enabled = EXCLUDED.enabled,
    default_value = EXCLUDED.default_value,
    rollout_percentage = EXCLUDED.rollout_percentage;

-- 5. Create indices for performance
CREATE INDEX IF NOT EXISTS idx_feature_flags_key ON feature_flags(flag_key);
CREATE INDEX IF NOT EXISTS idx_feature_flags_enabled ON feature_flags(enabled);
CREATE INDEX IF NOT EXISTS idx_feature_flag_overrides_flag ON feature_flag_overrides(feature_flag_id);
CREATE INDEX IF NOT EXISTS idx_feature_flag_overrides_org ON feature_flag_overrides(organisation_id);
CREATE INDEX IF NOT EXISTS idx_feature_flag_usage_flag ON feature_flag_usage(feature_flag_id);

-- 6. VERIFICATION QUERIES (critical for confirming fix)
SELECT 'VERIFICATION: Feature flags table exists' as status, COUNT(*) as count FROM feature_flags;
SELECT 'VERIFICATION: admin.advanced_controls flag exists' as status, enabled, default_value 
FROM feature_flags WHERE flag_key = 'admin.advanced_controls';
SELECT 'VERIFICATION: Total enabled flags' as status, COUNT(*) as count 
FROM feature_flags WHERE enabled = true;

-- 7. Test the exact query that was failing
-- This should now work instead of throwing "relation does not exist"
SELECT id, flag_key, name, enabled, default_value 
FROM feature_flags 
WHERE flag_key = 'admin.advanced_controls'
LIMIT 1;