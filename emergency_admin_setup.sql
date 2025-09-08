-- ============================================================================
-- EMERGENCY ADMIN SETUP SQL - £925K OPPORTUNITY
-- Direct SQL commands to grant admin privileges to matt.lindop@zebra.associates
-- ============================================================================
-- 
-- INSTRUCTIONS:
-- 1. Go to Render Dashboard → Database → Console
-- 2. Run these commands in order
-- 3. Verify the results
-- 4. Have user re-authenticate via Auth0
-- ============================================================================

-- Step 1: Verify user exists and check current status
SELECT 
    id, 
    email, 
    first_name, 
    last_name, 
    role, 
    is_active,
    organisation_id,
    created_at
FROM users 
WHERE email = 'matt.lindop@zebra.associates';

-- Step 2: Update user role to admin
UPDATE users 
SET role = 'admin' 
WHERE email = 'matt.lindop@zebra.associates';

-- Step 3: Verify role update
SELECT 
    email, 
    role, 
    'Role updated successfully' as status
FROM users 
WHERE email = 'matt.lindop@zebra.associates';

-- Step 4: Check existing application access
SELECT 
    uaa.application,
    uaa.has_access,
    uaa.granted_at
FROM user_application_access uaa
JOIN users u ON u.id = uaa.user_id
WHERE u.email = 'matt.lindop@zebra.associates';

-- Step 5: Grant access to market_edge (if not exists)
INSERT INTO user_application_access (user_id, application, has_access, granted_by, granted_at)
SELECT 
    u.id,
    'market_edge',
    TRUE,
    u.id,
    NOW()
FROM users u
WHERE u.email = 'matt.lindop@zebra.associates'
AND NOT EXISTS (
    SELECT 1 FROM user_application_access uaa 
    WHERE uaa.user_id = u.id AND uaa.application = 'market_edge'
);

-- Step 6: Grant access to causal_edge (if not exists)
INSERT INTO user_application_access (user_id, application, has_access, granted_by, granted_at)
SELECT 
    u.id,
    'causal_edge',
    TRUE,
    u.id,
    NOW()
FROM users u
WHERE u.email = 'matt.lindop@zebra.associates'
AND NOT EXISTS (
    SELECT 1 FROM user_application_access uaa 
    WHERE uaa.user_id = u.id AND uaa.application = 'causal_edge'
);

-- Step 7: Grant access to value_edge (if not exists)
INSERT INTO user_application_access (user_id, application, has_access, granted_by, granted_at)
SELECT 
    u.id,
    'value_edge',
    TRUE,
    u.id,
    NOW()
FROM users u
WHERE u.email = 'matt.lindop@zebra.associates'
AND NOT EXISTS (
    SELECT 1 FROM user_application_access uaa 
    WHERE uaa.user_id = u.id AND uaa.application = 'value_edge'
);

-- Step 8: Update existing application access records to ensure they are enabled
UPDATE user_application_access 
SET 
    has_access = TRUE,
    granted_at = NOW()
FROM users u
WHERE user_application_access.user_id = u.id
AND u.email = 'matt.lindop@zebra.associates'
AND user_application_access.has_access = FALSE;

-- Step 9: Final verification - check all admin privileges
SELECT 
    u.email,
    u.role,
    u.is_active,
    'Admin role: ' || CASE 
        WHEN u.role = 'admin' THEN '✅ YES' 
        ELSE '❌ NO (' || u.role || ')' 
    END as admin_status,
    'Epic Access: ' || CASE 
        WHEN u.role = 'admin' THEN '✅ GRANTED' 
        ELSE '❌ DENIED' 
    END as epic_access
FROM users u
WHERE u.email = 'matt.lindop@zebra.associates';

-- Step 10: Show all application access
SELECT 
    u.email,
    uaa.application,
    uaa.has_access,
    uaa.granted_at,
    CASE 
        WHEN uaa.has_access THEN '✅ GRANTED'
        ELSE '❌ DENIED'
    END as access_status
FROM users u
LEFT JOIN user_application_access uaa ON u.id = uaa.user_id
WHERE u.email = 'matt.lindop@zebra.associates'
ORDER BY uaa.application;

-- ============================================================================
-- SUCCESS VERIFICATION
-- ============================================================================
-- Expected results:
-- 1. User role = 'admin' 
-- 2. User has_access = TRUE for market_edge, causal_edge, value_edge
-- 3. Epic endpoints should work after user re-authenticates
-- ============================================================================

-- Step 11: Summary query
SELECT 
    'ADMIN SETUP COMPLETE' as status,
    u.email,
    u.role,
    COUNT(uaa.application) as applications_granted,
    'User must re-authenticate via Auth0 to get updated JWT' as next_step
FROM users u
LEFT JOIN user_application_access uaa ON u.id = uaa.user_id AND uaa.has_access = TRUE
WHERE u.email = 'matt.lindop@zebra.associates'
GROUP BY u.id, u.email, u.role;