# Grant super_admin Role to matt.lindop@zebra.associates - Staging Environment

**Date**: 2025-10-07
**Environment**: Staging
**Database**: marketedge-staging-db (marketedge_staging)
**Target User**: matt.lindop@zebra.associates
**Desired Role**: super_admin

---

## Overview

This guide provides multiple methods to grant the `super_admin` role to the specified user on the staging database hosted on Render.

---

## Method 1: Render CLI (Recommended)

### Prerequisites
- Render CLI installed (`brew install render`)
- Render account access with permissions to staging database

### Steps

#### 1. Login to Render CLI
```bash
render login
```
Follow the authentication prompts in your browser.

#### 2. List services to confirm database name
```bash
render services list -o json | grep -i "staging-db"
```

#### 3. Connect to staging database
```bash
render psql marketedge-staging-db
```

This opens a PostgreSQL shell connected to the staging database.

#### 4. Execute SQL commands
Once connected, run the following SQL:

```sql
-- Check current user role
SELECT email, role, is_active FROM users WHERE email = 'matt.lindop@zebra.associates';

-- Update to super_admin
UPDATE users
SET role = 'super_admin',
    is_active = true,
    updated_at = NOW()
WHERE email = 'matt.lindop@zebra.associates';

-- Verify update
SELECT email, role, is_active, updated_at FROM users WHERE email = 'matt.lindop@zebra.associates';

-- Exit
\q
```

#### Expected Output
```
 email                           | role        | is_active | updated_at
---------------------------------+-------------+-----------+----------------------------
 matt.lindop@zebra.associates    | super_admin | t         | 2025-10-07 10:30:00.123456
```

---

## Method 2: Render Dashboard SQL Shell

### Steps

1. **Navigate to Render Dashboard**
   - Go to: https://dashboard.render.com
   - Login with your Render account

2. **Select Staging Database**
   - Click on "Services" in left sidebar
   - Find and click on `marketedge-staging-db`

3. **Open Shell/Connect Tab**
   - Click on "Shell" or "Connect" tab
   - This opens a web-based PostgreSQL console

4. **Execute SQL Script**
   - Copy the contents of `/database/admin/grant_super_admin_staging.sql`
   - Paste into the SQL console
   - Execute the script

5. **Verify Results**
   - Check the query output to confirm role update
   - Look for `UPDATE 1` confirmation

---

## Method 3: Execute SQL Script via File

### If you have the SQL script file

```bash
# Connect and execute the script file
render psql marketedge-staging-db < /Users/matt/Sites/MarketEdge/database/admin/grant_super_admin_staging.sql
```

---

## Method 4: Backend Admin API (If Available)

### Prerequisites
- Access to staging backend: https://marketedge-platform-staging.onrender.com
- Existing admin user access token

### Steps

#### 1. Get User ID
```bash
# Login to staging and get access token
# Then fetch user details
curl -X GET "https://marketedge-platform-staging.onrender.com/api/v1/admin/users?email=matt.lindop@zebra.associates" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

#### 2. Update User Role
```bash
# Use the user ID from step 1
curl -X PATCH "https://marketedge-platform-staging.onrender.com/api/v1/admin/users/{USER_ID}" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "super_admin"}'
```

**Note**: This method requires an existing admin endpoint for user role updates, which may not be available.

---

## Post-Update Verification

### 1. Clear User Session

**Browser Actions** (on staging.zebra.associates):
```javascript
// Open browser console (F12) and run:
localStorage.clear();
sessionStorage.clear();
document.cookie.split(";").forEach(function(c) {
    document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
});

// Then refresh the page
location.reload();
```

### 2. Fresh Login

1. Navigate to: https://staging.zebra.associates/login
2. Complete Auth0 authentication with matt.lindop@zebra.associates
3. New JWT token will include `super_admin` role

### 3. Verify Admin Panel Access

**Check Access**:
- Navigate to: https://staging.zebra.associates/admin
- Should load successfully without 403 errors
- User management features should be accessible

**Verify Token Claims**:
```javascript
// In browser console after login
const user = JSON.parse(localStorage.getItem('current_user'));
console.log('User role:', user.role);
// Should output: super_admin
```

### 4. Test Admin Features

- User Management: Create/edit users
- Feature Flags: View/edit feature flags
- Organization Management: Access org settings
- Dashboard Stats: View admin dashboard statistics

---

## Database Verification Queries

Run these queries to confirm successful update and check related data:

### 1. User Role Verification
```sql
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
```

### 2. Application Access Check
```sql
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
```

### 3. Organization Details
```sql
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
```

### 4. Recent Admin Activity (if audit logging exists)
```sql
SELECT
    al.action,
    al.resource_type,
    al.created_at,
    u.email
FROM audit_log al
JOIN users u ON al.user_id = u.id
WHERE u.email = 'matt.lindop@zebra.associates'
ORDER BY al.created_at DESC
LIMIT 10;
```

---

## Troubleshooting

### Issue: User Not Found
**Problem**: SQL returns 0 rows for user query

**Solution**:
1. Check if user exists in database:
   ```sql
   SELECT email FROM users WHERE email ILIKE '%matt.lindop%';
   ```
2. If not found, user may need to login once to staging first (Auth0 user creation on first login)
3. Or check if email is spelled differently in database

### Issue: Update Returns 0 Rows
**Problem**: UPDATE statement returns `UPDATE 0`

**Solution**:
1. Verify user exists first
2. Check exact email spelling (case-sensitive)
3. Try with case-insensitive search:
   ```sql
   UPDATE users SET role = 'super_admin' WHERE email ILIKE 'matt.lindop@zebra.associates';
   ```

### Issue: Role Not Reflected in JWT Token
**Problem**: User still sees old role after update

**Solution**:
1. Clear all browser cache, localStorage, sessionStorage, and cookies
2. Logout completely from Auth0
3. Close all browser tabs for staging site
4. Open fresh browser session and login again
5. Check new JWT token includes `super_admin` in claims

### Issue: Admin Panel 403 Forbidden
**Problem**: User still gets 403 on admin routes

**Solution**:
1. Verify database role is actually `super_admin`:
   ```sql
   SELECT role FROM users WHERE email = 'matt.lindop@zebra.associates';
   ```
2. Check backend logs for authorization errors
3. Verify JWT token includes correct role claim
4. Check if backend has cached user permissions (may require backend restart)

### Issue: Render CLI Authentication Failed
**Problem**: `render login` fails or token expired

**Solution**:
1. Re-run `render login` and complete browser authentication
2. If still failing, try:
   ```bash
   rm ~/.render/config.json
   render login
   ```
3. Use Method 2 (Render Dashboard) as alternative

---

## Rollback Procedure

If you need to revert the role change:

```sql
-- Revert to previous role (adjust role value as needed)
UPDATE users
SET role = 'user',  -- or 'admin', 'analyst' depending on previous role
    updated_at = NOW()
WHERE email = 'matt.lindop@zebra.associates';

-- Verify rollback
SELECT email, role, updated_at FROM users WHERE email = 'matt.lindop@zebra.associates';
```

---

## Security Considerations

1. **super_admin Access**: Grants full administrative access to:
   - All organizations and tenants
   - User management (create, edit, delete)
   - Feature flag management
   - System configuration
   - Admin analytics and monitoring

2. **Audit Trail**: This change should be logged in audit logs (if implemented)

3. **Access Review**: Periodically review users with super_admin role

4. **Production Separation**: This change affects **staging only**, production remains unchanged

---

## Files Created

1. **SQL Script**: `/Users/matt/Sites/MarketEdge/database/admin/grant_super_admin_staging.sql`
   - Executable SQL commands with verification steps

2. **This Guide**: `/Users/matt/Sites/MarketEdge/database/admin/STAGING_SUPER_ADMIN_GRANT_GUIDE.md`
   - Comprehensive execution and verification guide

---

## Expected Outcome

After successful execution:

✅ **Database State**:
- `users.role` = `super_admin` for matt.lindop@zebra.associates
- `users.is_active` = `true`
- `users.updated_at` = current timestamp

✅ **Application Access**:
- User can access https://staging.zebra.associates/admin
- All admin panel features available
- Feature flag management accessible
- User management operations permitted

✅ **JWT Token**:
- New tokens include `"role": "super_admin"` in payload
- Backend authorizes admin endpoints
- Frontend renders admin UI components

---

## Next Steps

1. **Execute Method 1** (Render CLI) or **Method 2** (Render Dashboard)
2. **Verify database update** using verification queries
3. **Clear user session** and login fresh
4. **Test admin panel access** at staging.zebra.associates/admin
5. **Report results** with confirmation of successful role grant

---

## Support

If you encounter any issues:

1. Check Render dashboard for database status
2. Verify database migrations are up to date
3. Check backend logs for authorization errors
4. Ensure Auth0 configuration is correct for staging
5. Verify network connectivity to Render services

---

**End of Guide**
