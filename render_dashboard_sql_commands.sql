
-- Execute these SQL commands in Render Dashboard Query Interface

-- 1. Create Zebra Associates organization (if it doesn't exist)
INSERT INTO organisations (id, name, created_at, updated_at)
SELECT gen_random_uuid(), 'Zebra Associates', NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM organisations WHERE name = 'Zebra Associates'
);

-- 2. Create Matt Lindop super admin user
INSERT INTO users (id, email, auth0_id, name, role, is_active, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'matt.lindop@zebra.associates',
    'auth0|placeholder-will-be-updated-on-first-login',
    'Matt Lindop',
    'SUPER_ADMIN',
    true,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'matt.lindop@zebra.associates'
);

-- 3. Link user to organization
INSERT INTO user_hierarchy_assignments (id, user_id, organization_id, created_at)
SELECT 
    gen_random_uuid(),
    u.id,
    o.id,
    NOW()
FROM users u, organisations o
WHERE u.email = 'matt.lindop@zebra.associates'
  AND o.name = 'Zebra Associates'
  AND NOT EXISTS (
      SELECT 1 FROM user_hierarchy_assignments uha 
      WHERE uha.user_id = u.id AND uha.organization_id = o.id
  );

-- 4. Verify creation
SELECT 
    u.id,
    u.email,
    u.name,
    u.role,
    u.is_active,
    o.name as organization
FROM users u
LEFT JOIN user_hierarchy_assignments uha ON u.id = uha.user_id
LEFT JOIN organisations o ON uha.organization_id = o.id
WHERE u.email = 'matt.lindop@zebra.associates';
