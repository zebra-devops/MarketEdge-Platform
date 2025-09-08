# Zebra Associates £925K Opportunity - Database Fix Guide

**URGENT:** This guide resolves 404 errors for user matt.lindop@zebra.associates

## Problem Summary

The 404 errors experienced by the Zebra Associates user are caused by **missing or empty feature flags and module management tables** in the production database. The backend authentication works (returns 401/403), but the frontend interprets empty API responses as 404 errors.

## Solution Overview

1. **Verify database schema** - Check if tables exist
2. **Create missing tables** - If needed
3. **Seed demo data** - Essential feature flags and modules
4. **Configure user access** - For matt.lindop@zebra.associates
5. **Test and validate** - Ensure 404 errors are resolved

## Step-by-Step Fix

### Step 1: Database Schema Verification

```bash
cd /Users/matt/Sites/MarketEdge
python3 verify_feature_flags_modules_production.py
```

**Expected outcomes:**
- ✅ **If all tables exist with data**: Skip to Step 4 (User Access)
- ⚠️ **If tables exist but empty**: Go to Step 3 (Seed Data) 
- ❌ **If tables missing**: Go to Step 2 (Create Tables)

### Step 2: Create Missing Tables (if needed)

**Option A: Preferred - Use Alembic Migrations**
```bash
cd /Users/matt/Sites/MarketEdge
alembic upgrade head
```

**Option B: Manual SQL (if Alembic unavailable)**
```bash
# Connect to production database and run:
psql $DATABASE_URL -f create_missing_tables.sql
```

### Step 3: Seed Essential Demo Data

**First, get user and organisation IDs:**
```sql
-- Find existing user ID for created_by fields
SELECT id, email FROM users LIMIT 1;

-- Find organisation ID (likely where Zebra Associates user belongs)
SELECT id, name FROM organisations LIMIT 1;

-- Find Zebra Associates user ID
SELECT id, email FROM users WHERE email = 'matt.lindop@zebra.associates';
```

**Edit the demo data SQL file:**
```bash
# Replace placeholders in demo_data_feature_flags_modules.sql:
# {USER_ID} -> actual user ID from above query
# {ORG_ID} -> actual organisation ID from above query  
# {ZEBRA_USER_ID} -> matt.lindop@zebra.associates user ID
```

**Execute the demo data:**
```bash
psql $DATABASE_URL -f demo_data_feature_flags_modules.sql
```

### Step 4: Configure Zebra Associates User Access

**If matt.lindop@zebra.associates doesn't exist, create the user:**
```sql
-- This may already exist - check first
SELECT id, email FROM users WHERE email = 'matt.lindop@zebra.associates';
```

**If user exists, verify their organisation assignment and application access is granted by the demo data script.**

### Step 5: Verification and Testing

**Database verification:**
```sql
-- 1. Check feature flags exist
SELECT flag_key, name, is_enabled FROM feature_flags ORDER BY flag_key;

-- 2. Check analytics modules exist  
SELECT id, name, status FROM analytics_modules ORDER BY name;

-- 3. Check organisation has modules enabled
SELECT om.module_id, am.name, om.is_enabled 
FROM organisation_modules om 
JOIN analytics_modules am ON om.module_id = am.id 
WHERE om.organisation_id = '{ORG_ID}';

-- 4. Check user has application access
SELECT application, has_access 
FROM user_application_access 
WHERE user_id = '{ZEBRA_USER_ID}';
```

**API endpoint testing:**
```bash
# Test module discovery API (should return modules now)
curl -X GET "https://your-production-url.onrender.com/api/v1/module-management/modules"

# Test feature flags API (should return flags)
curl -X GET "https://your-production-url.onrender.com/api/v1/admin/feature-flags"
```

**Frontend testing:**
1. **Login as matt.lindop@zebra.associates**
2. **Navigate to module/dashboard sections**
3. **Verify 404 errors are resolved**
4. **Confirm module discovery works**

### Step 6: Cleanup (if needed)

**If you need to remove demo data:**
```sql
-- WARNING: This removes all demo data - use carefully
DELETE FROM feature_flag_overrides;
DELETE FROM feature_flag_usage;  
DELETE FROM feature_flags WHERE flag_key LIKE '%zebra%' OR flag_key LIKE '%demo%';
DELETE FROM organisation_modules WHERE module_id IN ('pricing_intelligence', 'market_trends', 'competitor_analysis', 'zebra_cinema_analytics');
DELETE FROM analytics_modules WHERE id IN ('pricing_intelligence', 'market_trends', 'competitor_analysis', 'zebra_cinema_analytics');
DELETE FROM user_application_access WHERE user_id = '{ZEBRA_USER_ID}';
```

## Expected Results After Fix

### Before Fix (Current State)
- ❌ User gets 404 errors when accessing modules
- ❌ Module discovery returns empty results  
- ❌ Feature flags system non-functional
- ❌ Frontend routing fails due to empty API responses

### After Fix (Target State)
- ✅ User can access all platform modules
- ✅ Module discovery returns available modules
- ✅ Feature flags system fully operational  
- ✅ Frontend routing works properly
- ✅ Demo ready for £925K Zebra Associates opportunity

## Troubleshooting

### Issue: "Database connection failed"
**Solution:** Check DATABASE_URL environment variable and network connectivity to Render

### Issue: "Table already exists" errors  
**Solution:** Tables exist, skip Step 2 and go to Step 3 (Seed Data)

### Issue: "User matt.lindop@zebra.associates not found"
**Solution:** Create user first or check if email is different

### Issue: Still getting 404 errors after fix
**Solution:** 
1. Check browser cache and reload
2. Verify API endpoints return data
3. Check frontend logs for routing issues
4. Ensure organisation_modules has entries for user's org

## Files Generated

1. **`verify_feature_flags_modules_production.py`** - Database verification script
2. **`create_missing_tables.sql`** - Table creation script  
3. **`demo_data_feature_flags_modules.sql`** - Essential demo data
4. **`feature_flags_modules_analysis_report.md`** - Detailed analysis
5. **`ZEBRA_ASSOCIATES_FIX_GUIDE.md`** - This guide

## Time Estimates

- **Database verification:** 10 minutes
- **Table creation (if needed):** 15 minutes  
- **Demo data seeding:** 20 minutes
- **User access configuration:** 10 minutes
- **Testing and validation:** 30 minutes

**Total:** 1-2 hours maximum

## Success Criteria

- ✅ Database has all required tables with demo data
- ✅ matt.lindop@zebra.associates can login and access modules
- ✅ No more 404 errors in frontend
- ✅ Module discovery API returns modules
- ✅ Feature flags API returns flags  
- ✅ Platform ready for Zebra Associates demo

---

**Priority:** CRITICAL - £925K opportunity  
**Timeline:** Execute immediately  
**Business Impact:** High - Platform functionality for key client