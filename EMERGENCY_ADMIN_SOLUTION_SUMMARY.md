# EMERGENCY ADMIN SOLUTION - £925K OPPORTUNITY

## CRITICAL STATUS
- **User**: matt.lindop@zebra.associates
- **Problem**: Epic endpoints returning 403 (admin privileges required)
- **Business Impact**: £925K opportunity blocked
- **Solution**: Grant admin role and application access

## CURRENT SITUATION
✅ **Database**: Accessible (2 users, 1 organisation)  
✅ **User Exists**: matt.lindop@zebra.associates found in database  
❌ **Epic 1**: GET /api/v1/module-management/modules → 403 Forbidden  
❌ **Epic 2**: GET /api/v1/admin/feature-flags → 403 Forbidden  
❌ **API Endpoint**: Enum conversion issues in production

## IMMEDIATE SOLUTION: DATABASE CONSOLE

### Step 1: Access Render Database Console
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select **marketedge-postgres** database
3. Click **Connect** → **Console**

### Step 2: Execute These SQL Commands

```sql
-- 1. Verify user exists and check current role
SELECT id, email, role, is_active 
FROM users 
WHERE email = 'matt.lindop@zebra.associates';

-- 2. Grant admin role
UPDATE users 
SET role = 'admin' 
WHERE email = 'matt.lindop@zebra.associates';

-- 3. Grant access to all applications
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

-- 4. Update existing records to ensure access
UPDATE user_application_access 
SET has_access = TRUE, granted_at = NOW()
FROM users u
WHERE user_application_access.user_id = u.id
AND u.email = 'matt.lindop@zebra.associates'
AND user_application_access.has_access = FALSE;

-- 5. Verify the changes
SELECT 
    u.email,
    u.role,
    CASE WHEN u.role = 'admin' THEN '✅ ADMIN' ELSE '❌ NOT ADMIN' END as admin_status
FROM users u
WHERE u.email = 'matt.lindop@zebra.associates';

-- 6. Verify application access
SELECT 
    u.email,
    uaa.application,
    uaa.has_access,
    CASE WHEN uaa.has_access THEN '✅ GRANTED' ELSE '❌ DENIED' END as access_status
FROM users u
LEFT JOIN user_application_access uaa ON u.id = uaa.user_id
WHERE u.email = 'matt.lindop@zebra.associates'
ORDER BY uaa.application;
```

### Step 3: Verification
Expected results:
- User role = 'admin' ✅
- All 3 applications (market_edge, causal_edge, value_edge) = has_access TRUE ✅

## CRITICAL NEXT STEP
**matt.lindop@zebra.associates MUST:**
1. **Log out** completely from the application
2. **Log back in** via Auth0
3. This generates new JWT token with admin role
4. **Test Epic endpoints** - should return 200 instead of 403

## VERIFICATION ENDPOINTS
After re-authentication, test these:
- Epic 1: `GET https://marketedge-platform.onrender.com/api/v1/module-management/modules`
- Epic 2: `GET https://marketedge-platform.onrender.com/api/v1/admin/feature-flags`

## AUTHENTICATION FLOW
1. **Current Token**: Contains old role (viewer/analyst)
2. **Database**: Now contains admin role ✅
3. **Re-authenticate**: Generates new token with admin role
4. **Epic Access**: 200 OK instead of 403 Forbidden ✅

## BUSINESS IMPACT
- ❌ **Current**: £925K opportunity blocked
- ✅ **After fix**: Epic functionality demonstrable
- 🎯 **Timeline**: 5 minutes to implement + re-authentication

## ALTERNATIVE: API ENDPOINT (if SQL console not available)
The emergency admin endpoint has enum issues, but user can try:
```bash
curl -X POST "https://marketedge-platform.onrender.com/api/v1/database/emergency-admin-setup"
```

## FILES CREATED
- `/Users/matt/Sites/MarketEdge/emergency_admin_setup.sql` - Complete SQL script
- `/Users/matt/Sites/MarketEdge/emergency_admin_status_check.py` - Status checker
- Emergency admin endpoint deployed to production

## SUCCESS CRITERIA
✅ User role = 'admin'  
✅ Application access granted for all 3 apps  
✅ Epic 1 endpoint returns 200 (not 403)  
✅ Epic 2 endpoint returns 200 (not 403)  
✅ £925K opportunity unblocked  

---

**URGENT ACTION REQUIRED**: Run SQL commands in Render database console NOW