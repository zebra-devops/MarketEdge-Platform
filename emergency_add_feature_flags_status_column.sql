-- EMERGENCY PRODUCTION FIX: Add missing status column to feature_flags table
-- ============================================================================
--
-- ISSUE: Production feature flags API returning 500 errors
-- ERROR: "column feature_flags.status does not exist"
-- IMPACT: Matt.Lindop cannot access admin panel for £925K Zebra Associates opportunity
--
-- ROOT CAUSE: Migration 003 was not properly applied to production database
-- SOLUTION: Add the missing status column with proper ENUM type
--
-- SAFETY: This is a safe additive change that won't break existing functionality
--
-- Before applying:
-- 1. Backup production database
-- 2. Test in staging environment
-- 3. Apply during low-traffic period
-- 4. Verify feature flags endpoints work after application

BEGIN;

-- Step 1: Create the featureflagstatus ENUM type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'featureflagstatus') THEN
        CREATE TYPE featureflagstatus AS ENUM ('ACTIVE', 'INACTIVE', 'DEPRECATED');
        RAISE NOTICE 'Created featureflagstatus ENUM type';
    ELSE
        RAISE NOTICE 'featureflagstatus ENUM type already exists';
    END IF;
END $$;

-- Step 2: Add the status column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'feature_flags' AND column_name = 'status'
    ) THEN
        ALTER TABLE feature_flags
        ADD COLUMN status featureflagstatus DEFAULT 'ACTIVE'::featureflagstatus NOT NULL;
        RAISE NOTICE 'Added status column to feature_flags table';
    ELSE
        RAISE NOTICE 'status column already exists in feature_flags table';
    END IF;
END $$;

-- Step 3: Ensure all existing records have the ACTIVE status
UPDATE feature_flags
SET status = 'ACTIVE'::featureflagstatus
WHERE status IS NULL;

-- Step 4: Create index for performance (matches migration 003)
CREATE INDEX IF NOT EXISTS ix_feature_flags_status ON feature_flags(status);

-- Step 5: Verification queries
DO $$
DECLARE
    total_flags INTEGER;
    active_flags INTEGER;
    column_exists BOOLEAN;
BEGIN
    -- Check if column exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'feature_flags' AND column_name = 'status'
    ) INTO column_exists;

    IF column_exists THEN
        -- Count flags
        SELECT COUNT(*) INTO total_flags FROM feature_flags;
        SELECT COUNT(*) INTO active_flags FROM feature_flags WHERE status = 'ACTIVE';

        RAISE NOTICE 'VERIFICATION SUCCESSFUL:';
        RAISE NOTICE '- status column exists: %', column_exists;
        RAISE NOTICE '- total feature flags: %', total_flags;
        RAISE NOTICE '- active feature flags: %', active_flags;
        RAISE NOTICE 'Feature flags API should now work correctly';
    ELSE
        RAISE EXCEPTION 'VERIFICATION FAILED: status column was not created';
    END IF;
END $$;

COMMIT;

-- Post-application verification
-- Run these queries after applying the fix to confirm everything works:

-- 1. Verify column structure
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'feature_flags' AND column_name = 'status';

-- 2. Test a simple query that was failing
SELECT
    flag_key,
    name,
    is_enabled,
    status,
    rollout_percentage
FROM feature_flags
LIMIT 5;

-- 3. Count by status
SELECT
    status,
    COUNT(*) as count
FROM feature_flags
GROUP BY status;