-- ============================================================================
-- Grant super_admin Role to matt.lindop@zebra.associates on Staging
-- ============================================================================
-- Environment: Staging (marketedge-staging-db)
-- Database: marketedge_staging
-- Target User: matt.lindop@zebra.associates
-- Desired Role: super_admin
-- Created: 2025-10-07
-- ============================================================================

-- Step 1: Verify user exists and check current role
SELECT
    id,
    email,
    first_name,
    last_name,
    role,
    is_active,
    organisation_id,
    created_at,
    updated_at
FROM users
WHERE email = 'matt.lindop@zebra.associates';

-- Expected output: User record with current role

-- Step 2: Update user role to super_admin
UPDATE users
SET
    role = 'super_admin',
    is_active = true,
    updated_at = NOW()
WHERE email = 'matt.lindop@zebra.associates';

-- Expected output: UPDATE 1 (if user exists)

-- Step 3: Verify the update was successful
SELECT
    id,
    email,
    first_name,
    last_name,
    role,
    is_active,
    organisation_id,
    created_at,
    updated_at
FROM users
WHERE email = 'matt.lindop@zebra.associates';

-- Expected output: User record with role = 'super_admin'

-- Step 4: Check application access for this user
SELECT
    u.email,
    u.role,
    uaa.application,
    uaa.has_access,
    uaa.created_at
FROM users u
LEFT JOIN user_application_access uaa ON u.id = uaa.user_id
WHERE u.email = 'matt.lindop@zebra.associates'
ORDER BY uaa.application;

-- Expected output: List of applications the user has access to

-- Step 5: Verify user's organization details
SELECT
    u.email,
    u.role,
    o.name as organisation_name,
    o.slug as organisation_slug,
    o.industry_type,
    o.is_active as org_is_active
FROM users u
LEFT JOIN organisations o ON u.organisation_id = o.id
WHERE u.email = 'matt.lindop@zebra.associates';

-- Expected output: User's organization information

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. This script should be executed on the staging database only
-- 2. super_admin role grants full access to admin panel and all features
-- 3. After running this script, the user must:
--    - Clear browser cache and localStorage
--    - Login fresh to staging environment
--    - New JWT token will include super_admin role
-- 4. Verify admin access at: https://staging.zebra.associates/admin
-- ============================================================================

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
-- To revert the change (restore previous role):
-- UPDATE users
-- SET role = 'user'  -- or 'admin', 'analyst' depending on previous role
-- WHERE email = 'matt.lindop@zebra.associates';
-- ============================================================================
