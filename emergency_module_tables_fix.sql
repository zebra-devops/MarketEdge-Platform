-- EMERGENCY FIX: Create missing module and feature flag tables for £925K Zebra Associates
-- Date: 2025-09-03
-- Purpose: Fix 404 errors by creating missing database tables

-- 1. Create feature_flags table if missing
CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT false,
    module_id VARCHAR(255),
    rollout_percentage INTEGER DEFAULT 0 CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),
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
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    UNIQUE(feature_flag_id, organisation_id, user_id)
);

-- 3. Create analytics_modules table
CREATE TABLE IF NOT EXISTS analytics_modules (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    module_type VARCHAR(50) DEFAULT 'ANALYTICS',
    status VARCHAR(50) DEFAULT 'ACTIVE',
    version VARCHAR(50) DEFAULT '1.0.0',
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID
);

-- 4. Create organisation_modules table
CREATE TABLE IF NOT EXISTS organisation_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL,
    module_id VARCHAR(255) NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    UNIQUE(organisation_id, module_id)
);

-- 5. Create module_feature_flags table
CREATE TABLE IF NOT EXISTS module_feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(255) NOT NULL,
    feature_flag_id UUID NOT NULL REFERENCES feature_flags(id) ON DELETE CASCADE,
    is_required BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(module_id, feature_flag_id)
);

-- 6. Insert core feature flags
INSERT INTO feature_flags (flag_key, name, description, enabled, module_id, rollout_percentage)
VALUES 
    ('module_discovery', 'Module Discovery', 'Enable module discovery system', true, 'core', 100),
    ('pricing_intelligence', 'Pricing Intelligence Module', 'Enable pricing analytics', true, 'pricing_intelligence', 100),
    ('market_trends', 'Market Trends Module', 'Enable market trend analysis', true, 'market_trends', 100),
    ('competitive_analysis', 'Competitive Analysis', 'Enable competitor tracking', true, 'competitive_analysis', 100),
    ('cinema_analytics', 'Cinema Analytics', 'Zebra Associates cinema analytics', true, 'cinema_analytics', 100)
ON CONFLICT (flag_key) DO UPDATE 
SET enabled = true, rollout_percentage = 100;

-- 7. Insert analytics modules
INSERT INTO analytics_modules (id, name, description, module_type, status)
VALUES 
    ('pricing_intelligence', 'Pricing Intelligence', 'Real-time pricing analytics and optimization', 'ANALYTICS', 'ACTIVE'),
    ('market_trends', 'Market Trends Analysis', 'Track and analyze market trends', 'ANALYTICS', 'ACTIVE'),
    ('competitive_analysis', 'Competitive Analysis', 'Monitor competitor activities', 'ANALYTICS', 'ACTIVE'),
    ('cinema_analytics', 'Cinema Analytics', 'Zebra Associates specialized cinema metrics', 'ANALYTICS', 'ACTIVE')
ON CONFLICT (id) DO UPDATE 
SET status = 'ACTIVE';

-- 8. Enable modules for Zebra Associates organisation
INSERT INTO organisation_modules (organisation_id, module_id, is_enabled)
SELECT 
    o.id,
    m.id,
    true
FROM organisations o
CROSS JOIN analytics_modules m
WHERE o.name ILIKE '%zebra%'
ON CONFLICT (organisation_id, module_id) DO UPDATE 
SET is_enabled = true;

-- 9. Grant application access to matt.lindop@zebra.associates
INSERT INTO user_application_access (user_id, application, has_access, granted_by, granted_at)
SELECT 
    u.id,
    'MARKET_EDGE',
    true,
    u.id,
    CURRENT_TIMESTAMP
FROM users u
WHERE u.email = 'matt.lindop@zebra.associates'
ON CONFLICT DO NOTHING;

-- 10. Link feature flags to modules
INSERT INTO module_feature_flags (module_id, feature_flag_id, is_required)
SELECT 
    am.id,
    ff.id,
    true
FROM analytics_modules am
JOIN feature_flags ff ON ff.module_id = am.id
ON CONFLICT DO NOTHING;

-- Verification queries
SELECT 'Feature Flags Created:' as status, COUNT(*) as count FROM feature_flags;
SELECT 'Analytics Modules Created:' as status, COUNT(*) as count FROM analytics_modules;
SELECT 'Organisation Modules Enabled:' as status, COUNT(*) as count FROM organisation_modules;
SELECT 'Module Feature Flags Linked:' as status, COUNT(*) as count FROM module_feature_flags;