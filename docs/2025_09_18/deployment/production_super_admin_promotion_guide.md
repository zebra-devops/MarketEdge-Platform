# Production Super Admin Promotion Guide
## Critical Database Update for £925K Zebra Associates Opportunity

**Date**: 2025-09-18
**Priority**: CRITICAL - Business Blocker
**Impact**: Unblocks £925K opportunity with Zebra Associates

## Executive Summary

Matt Lindop currently has `admin` role in production, which blocks access to Feature Flags (returns 500 error: "Super admin role required"). This guide provides the steps to promote Matt Lindop to `super_admin` role in the production database.

## Current Production Status

- **User ID**: `ebc9567a-bbf8-4ddf-8eee-7635fba62363`
- **Email**: `matt.lindop@zebra.associates` / `matt.lindop@marketedge.com`
- **Current Role**: `admin` (BLOCKING Feature Flags access)
- **Required Role**: `super_admin`
- **Error**: Feature Flags endpoint returns 500 with "Super admin role required"

## Deployment Steps

### Step 1: Access Production Database

#### Option A: Using Render Dashboard (Recommended)
1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Navigate to `marketedge-platform` service
3. Go to **Environment** tab
4. Copy the `DATABASE_URL` value
5. Use the production promotion script

#### Option B: Direct SQL Access
1. Access Render PostgreSQL console
2. Connect to production database
3. Execute SQL commands directly

### Step 2: Execute Production Update

#### Using the Automated Script (Recommended)

```bash
# 1. Set production database URL (if not in environment)
export PRODUCTION_DATABASE_URL="<your-render-database-url>"

# 2. Run the promotion script
python production_super_admin_promotion.py
```

The script will:
- Connect to production database
- Check current role status
- Update role to super_admin
- Verify the update
- Save results with timestamp

#### Using Direct SQL Commands

```sql
-- 1. Check current status
SELECT id, email, role, full_name, organization_id
FROM users
WHERE email IN ('matt.lindop@zebra.associates', 'matt.lindop@marketedge.com');

-- 2. Update to super_admin
UPDATE users
SET role = 'super_admin',
    updated_at = CURRENT_TIMESTAMP
WHERE email IN ('matt.lindop@zebra.associates', 'matt.lindop@marketedge.com')
AND role != 'super_admin'
RETURNING id, email, role;

-- 3. Verify update
SELECT id, email, role, updated_at
FROM users
WHERE email IN ('matt.lindop@zebra.associates', 'matt.lindop@marketedge.com');
```

### Step 3: Verify Production Access

After the database update:

1. **Have Matt Lindop log out and log back in** to refresh JWT token with new role
2. **Test Feature Flags endpoint**:
   ```bash
   curl -X GET https://marketedge-platform.onrender.com/api/v1/admin/feature-flags \
     -H "Authorization: Bearer <matt-lindop-token>"
   ```
   Should return 200 with feature flags data (not 500 error)

3. **Verify Admin Dashboard Access**:
   - Navigate to `/admin/dashboard/stats`
   - Should load without permission errors

## Expected Results

### Before Update
```json
{
  "email": "matt.lindop@zebra.associates",
  "role": "admin",
  "feature_flags_access": false,
  "error": "500 - Super admin role required"
}
```

### After Update
```json
{
  "email": "matt.lindop@zebra.associates",
  "role": "super_admin",
  "feature_flags_access": true,
  "admin_dashboard_access": true
}
```

## Rollback Procedure

If issues occur after promotion:

```sql
-- Rollback to admin role
UPDATE users
SET role = 'admin',
    updated_at = CURRENT_TIMESTAMP
WHERE email IN ('matt.lindop@zebra.associates', 'matt.lindop@marketedge.com');
```

## Business Impact

- **Immediate**: Unblocks £925K Zebra Associates opportunity
- **Feature Access**: Full Feature Flags management capability
- **Admin Functions**: Complete admin dashboard access
- **Multi-tenant Management**: Organization switching and management

## Security Considerations

- `super_admin` role has highest privileges in the system
- Matt Lindop is authorized for this role per business requirements
- Role change is audited in database `updated_at` timestamp
- JWT tokens will reflect new role after re-authentication

## Post-Deployment Checklist

- [ ] Database update executed successfully
- [ ] Role verified as `super_admin` in production
- [ ] Matt Lindop logged out and back in
- [ ] Feature Flags endpoint returns 200 (not 500)
- [ ] Admin dashboard accessible
- [ ] Organization switching functional
- [ ] Business stakeholder notified of completion

## Support Contact

**Issue Type**: Production database role update
**Platform**: Render PostgreSQL
**Service**: marketedge-platform
**Critical Path**: £925K opportunity depends on this update

## Audit Trail

All changes are logged with:
- Timestamp of update
- Previous role value
- New role value
- User performing update
- Business justification (£925K Zebra Associates opportunity)