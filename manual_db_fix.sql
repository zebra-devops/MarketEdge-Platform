-- MarketEdge Production Database Fix
-- Adds missing created_at/updated_at columns to fix authentication 500 errors
-- Critical for £925K Zebra Associates opportunity
-- Execute on production database: marketedge-postgres

-- Begin transaction for safety
BEGIN;

-- Create log entry
SELECT 'Starting database schema fix for missing Base columns' as status,
       NOW() as timestamp;

-- Fix 1: feature_flag_overrides - Add updated_at
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'feature_flag_overrides' 
          AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE feature_flag_overrides 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'Added updated_at to feature_flag_overrides';
    ELSE
        RAISE NOTICE 'Column updated_at already exists in feature_flag_overrides';
    END IF;
END $$;

-- Fix 2: feature_flag_usage - Add created_at and updated_at
DO $$ 
BEGIN
    -- Add created_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'feature_flag_usage' 
          AND column_name = 'created_at'
    ) THEN
        ALTER TABLE feature_flag_usage 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
        RAISE NOTICE 'Added created_at to feature_flag_usage';
    ELSE
        RAISE NOTICE 'Column created_at already exists in feature_flag_usage';
    END IF;
    
    -- Add updated_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'feature_flag_usage' 
          AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE feature_flag_usage 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'Added updated_at to feature_flag_usage';
    ELSE
        RAISE NOTICE 'Column updated_at already exists in feature_flag_usage';
    END IF;
END $$;

-- Fix 3: module_usage_logs - Add created_at and updated_at
DO $$ 
BEGIN
    -- Add created_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'module_usage_logs' 
          AND column_name = 'created_at'
    ) THEN
        ALTER TABLE module_usage_logs 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
        RAISE NOTICE 'Added created_at to module_usage_logs';
    ELSE
        RAISE NOTICE 'Column created_at already exists in module_usage_logs';
    END IF;
    
    -- Add updated_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'module_usage_logs' 
          AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE module_usage_logs 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'Added updated_at to module_usage_logs';
    ELSE
        RAISE NOTICE 'Column updated_at already exists in module_usage_logs';
    END IF;
END $$;

-- Fix 4: admin_actions - Add updated_at
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'admin_actions' 
          AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE admin_actions 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'Added updated_at to admin_actions';
    ELSE
        RAISE NOTICE 'Column updated_at already exists in admin_actions';
    END IF;
END $$;

-- Fix 5: audit_logs - Add created_at and updated_at
DO $$ 
BEGIN
    -- Add created_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'audit_logs' 
          AND column_name = 'created_at'
    ) THEN
        ALTER TABLE audit_logs 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
        RAISE NOTICE 'Added created_at to audit_logs';
    ELSE
        RAISE NOTICE 'Column created_at already exists in audit_logs';
    END IF;
    
    -- Add updated_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'audit_logs' 
          AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE audit_logs 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'Added updated_at to audit_logs';
    ELSE
        RAISE NOTICE 'Column updated_at already exists in audit_logs';
    END IF;
END $$;

-- Fix 6: competitive_insights - Add updated_at (only if table exists)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_name = 'competitive_insights'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = 'competitive_insights' 
              AND column_name = 'updated_at'
        ) THEN
            ALTER TABLE competitive_insights 
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            RAISE NOTICE 'Added updated_at to competitive_insights';
        ELSE
            RAISE NOTICE 'Column updated_at already exists in competitive_insights';
        END IF;
    ELSE
        RAISE NOTICE 'Table competitive_insights does not exist - skipping';
    END IF;
END $$;

-- Fix 7: competitors - Add updated_at (only if table exists)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_name = 'competitors'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = 'competitors' 
              AND column_name = 'updated_at'
        ) THEN
            ALTER TABLE competitors 
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            RAISE NOTICE 'Added updated_at to competitors';
        ELSE
            RAISE NOTICE 'Column updated_at already exists in competitors';
        END IF;
    ELSE
        RAISE NOTICE 'Table competitors does not exist - skipping';
    END IF;
END $$;

-- Fix 8: market_alerts - Add updated_at (only if table exists)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_name = 'market_alerts'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = 'market_alerts' 
              AND column_name = 'updated_at'
        ) THEN
            ALTER TABLE market_alerts 
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            RAISE NOTICE 'Added updated_at to market_alerts';
        ELSE
            RAISE NOTICE 'Column updated_at already exists in market_alerts';
        END IF;
    ELSE
        RAISE NOTICE 'Table market_alerts does not exist - skipping';
    END IF;
END $$;

-- Fix 9: market_analytics - Add updated_at (only if table exists)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_name = 'market_analytics'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = 'market_analytics' 
              AND column_name = 'updated_at'
        ) THEN
            ALTER TABLE market_analytics 
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            RAISE NOTICE 'Added updated_at to market_analytics';
        ELSE
            RAISE NOTICE 'Column updated_at already exists in market_analytics';
        END IF;
    ELSE
        RAISE NOTICE 'Table market_analytics does not exist - skipping';
    END IF;
END $$;

-- Fix 10: pricing_data - Add updated_at (only if table exists)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_name = 'pricing_data'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = 'pricing_data' 
              AND column_name = 'updated_at'
        ) THEN
            ALTER TABLE pricing_data 
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            RAISE NOTICE 'Added updated_at to pricing_data';
        ELSE
            RAISE NOTICE 'Column updated_at already exists in pricing_data';
        END IF;
    ELSE
        RAISE NOTICE 'Table pricing_data does not exist - skipping';
    END IF;
END $$;

-- Verification: List all tables and their timestamp columns
SELECT 'Verification - checking all timestamp columns' as status;

SELECT 
    table_name,
    column_name,
    data_type,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name IN (
    'feature_flag_overrides', 'feature_flag_usage', 'module_usage_logs',
    'admin_actions', 'audit_logs', 'competitive_insights', 'competitors',
    'market_alerts', 'market_analytics', 'pricing_data'
  )
  AND column_name IN ('created_at', 'updated_at')
ORDER BY table_name, column_name;

-- Final status
SELECT 'Database schema fix completed successfully' as status,
       NOW() as timestamp;

-- Commit all changes
COMMIT;

-- Success message
SELECT '✅ ALL FIXES APPLIED - Authentication should work properly now!' as final_status;