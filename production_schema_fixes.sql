-- Production Schema Repair Script
-- Generated: 2025-09-23T11:14:40.955829
-- CRITICAL: Review before applying to production

-- Add missing columns to analytics_modules
ALTER TABLE analytics_modules ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE analytics_modules ADD COLUMN IF NOT EXISTS ai_enhanced BOOLEAN NOT NULL DEFAULT FALSE;

-- Add missing columns to organisation_modules
ALTER TABLE organisation_modules ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE organisation_modules ADD COLUMN IF NOT EXISTS last_used TIMESTAMP WITH TIME ZONE;
ALTER TABLE organisation_modules ADD COLUMN IF NOT EXISTS usage_count INTEGER NOT NULL DEFAULT 0;

-- Add missing columns to feature_flags
ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS conditions JSONB;
ALTER TABLE feature_flags ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Add missing columns to audit_logs
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES organisations(id);

