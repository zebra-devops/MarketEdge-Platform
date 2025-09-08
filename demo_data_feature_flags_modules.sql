-- Demo Data for Feature Flags and Modules System
-- Generated for Zebra Associates £925K opportunity
-- Fixes 404 errors by providing essential demo data
-- Target user: matt.lindop@zebra.associates

-- =============================================================================
-- ESSENTIAL FEATURE FLAGS FOR MODULE SYSTEM
-- =============================================================================

-- NOTE: Replace {USER_ID} with an actual user ID from your users table
-- You can find a user ID by running: SELECT id, email FROM users LIMIT 1;

-- Core module system feature flags
INSERT INTO feature_flags (
    id, 
    flag_key, 
    name, 
    description, 
    is_enabled, 
    rollout_percentage, 
    scope, 
    status, 
    config, 
    allowed_sectors, 
    blocked_sectors, 
    module_id,
    created_by, 
    created_at, 
    updated_at
) VALUES 

-- Essential system flags
(gen_random_uuid(), 'module_discovery_enabled', 'Module Discovery System', 'Enable module discovery and routing functionality', true, 100, 'global', 'active', '{}', '[]', '[]', null, '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

(gen_random_uuid(), 'module_registry_enabled', 'Module Registry', 'Enable core module registry system', true, 100, 'global', 'active', '{}', '[]', '[]', 'module_registry', '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Analytics module flags
(gen_random_uuid(), 'pricing_intelligence_module', 'Pricing Intelligence Module', 'Enable pricing intelligence analytics module', true, 100, 'organisation', 'active', '{"advanced_features": true}', '[]', '[]', 'pricing_intelligence', '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

(gen_random_uuid(), 'market_trends_module', 'Market Trends Module', 'Enable market trends analysis module', true, 100, 'organisation', 'active', '{"forecast_horizon": 12}', '[]', '[]', 'market_trends', '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

(gen_random_uuid(), 'competitor_analysis_module', 'Competitor Analysis Module', 'Enable competitor analysis and monitoring', true, 100, 'organisation', 'active', '{"monitoring_enabled": true}', '[]', '[]', 'competitor_analysis', '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Special flag for Zebra Associates opportunity
(gen_random_uuid(), 'zebra_associates_features', 'Zebra Associates Demo Features', 'Special features enabled for £925K Zebra Associates opportunity', true, 100, 'organisation', 'active', '{"demo_mode": true, "cinema_analytics": true, "priority_support": true}', '[]', '[]', 'zebra_cinema_analytics', '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Cinema industry specific module
(gen_random_uuid(), 'zebra_cinema_analytics', 'Cinema Analytics Module', 'Specialized analytics for cinema industry clients', true, 100, 'organisation', 'active', '{"industry": "cinema", "client": "zebra_associates"}', '[]', '[]', 'zebra_cinema_analytics', '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- =============================================================================
-- ANALYTICS MODULES REGISTRY
-- =============================================================================

-- Core analytics modules for the platform
INSERT INTO analytics_modules (
    id,
    name,
    description,
    version,
    module_type,
    status,
    is_core,
    requires_license,
    entry_point,
    config_schema,
    default_config,
    dependencies,
    api_endpoints,
    frontend_components,
    min_data_requirements,
    documentation_url,
    help_text,
    pricing_tier,
    license_requirements,
    created_by,
    created_at,
    updated_at
) VALUES

-- Core system module
('module_registry', 'Module Registry', 'Core module discovery and routing system', '1.0.0', 'core', 'active', true, false, 'app.core.module_registry', '{}', '{"auto_discovery": true}', '[]', '["/api/v1/modules", "/api/v1/module-management"]', '["ModuleDiscovery", "ModuleStatus"]', '{}', null, 'Core system module for managing other modules', null, '{}', '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Analytics modules
('pricing_intelligence', 'Pricing Intelligence', 'Advanced pricing analysis and competitive intelligence', '1.0.0', 'analytics', 'active', false, false, 'app.modules.pricing_intelligence', '{"features": ["competitor_tracking", "price_monitoring", "market_analysis"]}', '{"update_frequency": "daily", "analysis_depth": "comprehensive"}', '["module_registry"]', '["/api/v1/pricing", "/api/v1/competitor-analysis"]', '["PricingDashboard", "CompetitorTable"]', '{"min_competitors": 3, "historical_data_months": 6}', null, 'Analyze competitor pricing and market trends', 'premium', '{}', '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('market_trends', 'Market Trends', 'Market trend analysis and forecasting', '1.0.0', 'analytics', 'active', false, false, 'app.modules.market_trends', '{"forecast_types": ["linear", "seasonal", "ml_based"]}', '{"forecast_horizon": 12, "confidence_interval": 0.95}', '["module_registry"]', '["/api/v1/market-trends", "/api/v1/forecasting"]', '["TrendChart", "ForecastingDashboard"]', '{"historical_data_months": 12}', null, 'Analyze market trends and generate forecasts', 'professional', '{}', '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('competitor_analysis', 'Competitor Analysis', 'Competitive landscape analysis and monitoring', '1.0.0', 'analytics', 'active', false, false, 'app.modules.competitor_analysis', '{"monitoring": ["pricing", "features", "marketing", "financial"]}', '{"alert_threshold": 0.1, "update_frequency": "hourly"}', '["module_registry", "pricing_intelligence"]', '["/api/v1/competitors", "/api/v1/competitive-intelligence"]', '["CompetitorMatrix", "CompetitiveAlerts"]', '{"min_competitors": 5}', null, 'Monitor and analyze competitive landscape', 'professional', '{}', '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Special module for Zebra Associates
('zebra_cinema_analytics', 'Cinema Analytics', 'Specialized analytics for cinema industry (Zebra Associates)', '1.0.0', 'analytics', 'active', false, false, 'app.modules.cinema_analytics', '{"cinema_metrics": ["box_office", "attendance", "concessions", "customer_satisfaction"]}', '{"industry": "cinema", "demo_mode": true, "zebra_features": true}', '["module_registry", "market_trends", "pricing_intelligence"]', '["/api/v1/cinema-analytics", "/api/v1/box-office-analysis"]', '["CinemaDashboard", "BoxOfficeAnalytics", "AttendanceMetrics"]', '{"cinema_locations": 1, "historical_months": 6}', null, 'Comprehensive cinema industry analytics and insights', 'enterprise', '{"client": "zebra_associates"}', '{USER_ID}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- =============================================================================
-- ORGANISATION MODULE ACCESS
-- =============================================================================

-- NOTE: Replace {ORG_ID} with actual organisation ID
-- You can find organisation ID by running: SELECT id, name FROM organisations LIMIT 1;

-- Enable modules for sample organisation (likely where matt.lindop@zebra.associates belongs)
INSERT INTO organisation_modules (
    id,
    organisation_id,
    module_id,
    is_enabled,
    configuration,
    enabled_for_users,
    disabled_for_users,
    first_enabled_at,
    last_accessed_at,
    access_count,
    created_by,
    updated_by,
    created_at,
    updated_at
) VALUES

-- Core module registry (always enabled)
(gen_random_uuid(), '{ORG_ID}', 'module_registry', true, '{"auto_discovery": true, "routing_enabled": true}', '[]', '[]', CURRENT_TIMESTAMP, null, 0, '{USER_ID}', null, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Analytics modules
(gen_random_uuid(), '{ORG_ID}', 'pricing_intelligence', true, '{"advanced_features": true, "demo_mode": false, "competitor_limit": 20}', '[]', '[]', CURRENT_TIMESTAMP, null, 0, '{USER_ID}', null, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

(gen_random_uuid(), '{ORG_ID}', 'market_trends', true, '{"forecast_horizon": 12, "trend_sensitivity": "medium", "auto_alerts": true}', '[]', '[]', CURRENT_TIMESTAMP, null, 0, '{USER_ID}', null, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

(gen_random_uuid(), '{ORG_ID}', 'competitor_analysis', true, '{"monitoring_frequency": "daily", "alert_threshold": 0.1, "comprehensive_reports": true}', '[]', '[]', CURRENT_TIMESTAMP, null, 0, '{USER_ID}', null, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Special Zebra Associates cinema module  
(gen_random_uuid(), '{ORG_ID}', 'zebra_cinema_analytics', true, '{"industry_focus": "cinema", "client": "zebra_associates", "demo_mode": true, "advanced_cinema_metrics": true, "priority_support": true}', '[]', '[]', CURRENT_TIMESTAMP, null, 0, '{USER_ID}', null, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- =============================================================================
-- USER APPLICATION ACCESS 
-- =============================================================================

-- NOTE: Replace {USER_EMAIL} with matt.lindop@zebra.associates user ID
-- Find the user ID: SELECT id FROM users WHERE email = 'matt.lindop@zebra.associates';

-- Grant access to all applications for Zebra Associates user
INSERT INTO user_application_access (
    user_id,
    application,
    has_access,
    granted_by,
    granted_at
) VALUES
('{ZEBRA_USER_ID}', 'market_edge', true, '{USER_ID}', CURRENT_TIMESTAMP),
('{ZEBRA_USER_ID}', 'causal_edge', true, '{USER_ID}', CURRENT_TIMESTAMP), 
('{ZEBRA_USER_ID}', 'value_edge', true, '{USER_ID}', CURRENT_TIMESTAMP);

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Run these queries after inserting the data to verify everything worked:

-- 1. Check feature flags
-- SELECT flag_key, name, is_enabled, scope FROM feature_flags ORDER BY flag_key;

-- 2. Check analytics modules  
-- SELECT id, name, status, is_core, module_type FROM analytics_modules ORDER BY name;

-- 3. Check organisation modules (replace {ORG_ID})
-- SELECT om.module_id, am.name, om.is_enabled 
-- FROM organisation_modules om 
-- JOIN analytics_modules am ON om.module_id = am.id 
-- WHERE om.organisation_id = '{ORG_ID}';

-- 4. Check user application access (replace {ZEBRA_USER_ID})
-- SELECT application, has_access FROM user_application_access 
-- WHERE user_id = '{ZEBRA_USER_ID}';

-- =============================================================================
-- CLEANUP INSTRUCTIONS (if needed)
-- =============================================================================

-- To remove all demo data (use with caution):
-- DELETE FROM feature_flag_overrides;
-- DELETE FROM feature_flag_usage;  
-- DELETE FROM feature_flags WHERE created_by = '{USER_ID}';
-- DELETE FROM organisation_modules WHERE created_by = '{USER_ID}';
-- DELETE FROM analytics_modules WHERE created_by = '{USER_ID}';
-- DELETE FROM user_application_access WHERE granted_by = '{USER_ID}';

-- =============================================================================
-- END OF DEMO DATA SCRIPT
-- =============================================================================