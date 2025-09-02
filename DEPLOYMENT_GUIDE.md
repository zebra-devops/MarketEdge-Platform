# Database Schema Fix Deployment Guide

## Critical Issue: Missing Base Columns Causing 500 Authentication Errors

The MarketEdge Platform is experiencing authentication failures due to missing `created_at`/`updated_at` columns in 9 database tables. This is blocking the £925K Zebra Associates opportunity.

## Affected Tables

1. `feature_flag_overrides` - missing `updated_at`
2. `feature_flag_usage` - missing `created_at`, `updated_at` 
3. `module_usage_logs` - missing `created_at`, `updated_at`
4. `admin_actions` - missing `updated_at`
5. `audit_logs` - missing `created_at`, `updated_at`
6. `competitive_insights` - missing `updated_at`
7. `competitors` - missing `updated_at`
8. `market_alerts` - missing `updated_at`
9. `market_analytics` - missing `updated_at`
10. `pricing_data` - missing `updated_at`

## Deployment Options

### Option 1: Shell Script (Recommended for Render)

1. **Upload to Render**: Copy `render_db_fix.sh` to your Render service
2. **Run as one-off job**:
   ```bash
   bash render_db_fix.sh
   ```

### Option 2: Python Script (More robust)

1. **Install dependencies**: 
   ```bash
   pip install psycopg2-binary
   ```

2. **Dry run first** (safe):
   ```bash
   python3 fix_missing_base_columns.py --dry-run
   ```

3. **Execute fixes**:
   ```bash
   python3 fix_missing_base_columns.py --execute
   ```

4. **Verify fixes**:
   ```bash
   python3 fix_missing_base_columns.py --verify
   ```

### Option 3: Direct SQL (Manual)

Connect to the production database and run the SQL commands from `manual_db_fix.sql`.

## Environment Setup

The scripts automatically detect the database URL from environment variables:
- `DATABASE_URL` (primary)
- `POSTGRES_URL` 
- `DB_URL`

For Render deployment, `DATABASE_URL` should already be set.

## Safety Features

1. **Transaction-based**: All changes in a single transaction (rollback on failure)
2. **Verification**: Scripts verify changes were applied correctly
3. **Backup creation**: Python script creates table backups before changes
4. **Dry-run mode**: Test what would be changed without making changes
5. **Existence checks**: Only adds columns that don't already exist

## Render Deployment Steps

### Method 1: Shell Environment (Quick Fix)

1. Go to your Render dashboard
2. Navigate to your MarketEdge service
3. Go to "Shell" tab
4. Run these commands:

```bash
# Download the fix script
curl -o db_fix.sh https://raw.githubusercontent.com/YOUR-REPO/main/render_db_fix.sh

# Make executable
chmod +x db_fix.sh

# Run the fix
./db_fix.sh
```

### Method 2: One-off Job (Recommended)

1. In Render dashboard, create a new "Background Worker"
2. Set the build command to: `echo "Database fix job"`
3. Set the start command to: `bash render_db_fix.sh`
4. Deploy the job - it will run once and fix the database

### Method 3: Add to Existing Service

1. Add the script files to your repository
2. Modify your deployment process to run the fix script
3. Deploy normally - the script will run as part of deployment

## Verification Commands

After running the fix, verify with:

```sql
-- Check all tables have required columns
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name IN (
    'feature_flag_overrides', 'feature_flag_usage', 'module_usage_logs',
    'admin_actions', 'audit_logs', 'competitive_insights', 'competitors',
    'market_alerts', 'market_analytics', 'pricing_data'
  )
  AND column_name IN ('created_at', 'updated_at')
ORDER BY table_name, column_name;
```

## Expected Results

After successful deployment:
- ✅ All 9 tables will have proper `created_at`/`updated_at` columns
- ✅ Authentication will work without 500 errors
- ✅ £925K Zebra Associates opportunity unblocked
- ✅ Platform ready for production traffic

## Rollback Plan

If issues occur:
1. The scripts create backups before making changes
2. Use standard PostgreSQL rollback procedures
3. Contact DevOps team for assistance

## Timeline

- **Critical Priority**: Execute within 2 hours
- **Expected Duration**: 5-10 minutes to run
- **Downtime**: Minimal (< 30 seconds during column addition)

## Support

Contact the DevOps team if:
- Scripts fail with errors
- Authentication still fails after fixes
- Performance issues observed post-deployment