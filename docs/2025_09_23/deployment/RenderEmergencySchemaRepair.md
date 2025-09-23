# Emergency Schema Repair for Render Production

**CRITICAL DEPLOYMENT**: Fix massive schema drift blocking £925K Zebra Associates opportunity

## Problem Summary

**Status**: 🚨 CRITICAL - Production schema drift blocking business opportunity

**Issues Identified**:
- 9 missing tables (competitive_factor_templates, module_configurations, industry_templates, module_usage_logs, sector_modules, organization_template_applications, hierarchy_role_assignments, feature_flag_usage, admin_actions)
- 48 missing columns across existing tables
- Migration 003 (Phase 3 enhancements) never properly applied to production
- API router correctly blocking deployment until schema is fixed

**Business Impact**:
- £925K Zebra Associates opportunity blocked
- Admin endpoints non-functional
- Feature flags management unavailable
- Module management system offline

## Solution Overview

**Comprehensive Schema Repair System** for Render PostgreSQL:

1. **Emergency Repair Script** (`render_emergency_schema_repair.py`)
   - Creates all 9 missing tables with proper relationships
   - Adds all 48 missing columns with appropriate data types
   - Updates alembic version to prevent future conflicts
   - Applies performance indexes
   - Full transaction safety with rollback capability

2. **Deployment Script** (`deploy_emergency_repair_to_render.sh`)
   - Render-specific deployment automation
   - Environment validation
   - Dependency installation
   - Execution and verification

3. **SQL Generator** (`generate_render_schema_repair_sql.py`)
   - Generates standalone SQL for manual application
   - Comprehensive repair statements
   - Verification queries included

## Deployment Options

### Option 1: Automated Deployment (Recommended)

1. **Upload files to Render service**:
   ```bash
   # Upload these files to your Render service:
   render_emergency_schema_repair.py
   deploy_emergency_repair_to_render.sh
   ```

2. **Execute deployment**:
   ```bash
   ./deploy_emergency_repair_to_render.sh
   ```

3. **Monitor output** for success confirmation

### Option 2: Manual SQL Application

1. **Generate SQL**:
   ```bash
   python3 generate_render_schema_repair_sql.py
   ```

2. **Apply to Render PostgreSQL**:
   ```bash
   psql $DATABASE_URL -f render_production_schema_repair_TIMESTAMP.sql
   ```

### Option 3: Render Console

1. Copy SQL from generated file
2. Paste into Render PostgreSQL console
3. Execute in sections for safety

## Safety Features

### Transaction Safety
- All operations wrapped in BEGIN/COMMIT transactions
- Automatic rollback on critical errors
- Non-destructive IF NOT EXISTS patterns

### Error Handling
- Comprehensive error logging
- Graceful handling of existing components
- Detailed success/failure reporting

### Verification
- Post-repair schema validation
- Table and column existence checks
- Alembic version verification

## Expected Results

### Tables Created (9)
- `competitive_factor_templates` - Industry-specific competitive analysis templates
- `module_configurations` - Organization-specific module settings
- `industry_templates` - Pre-built industry dashboard templates
- `module_usage_logs` - Analytics module usage tracking
- `sector_modules` - SIC code to module mappings
- `organization_template_applications` - Applied template tracking
- `hierarchy_role_assignments` - Advanced role-based permissions
- `feature_flag_usage` - Feature flag evaluation logging
- `admin_actions` - Administrative action audit trail

### Columns Added (48)
- **sic_codes**: title, description, is_supported, competitive_factors, default_metrics, analytics_config, created_at, updated_at
- **analytics_modules**: tags, ai_enhanced, created_at, updated_at
- **organisation_modules**: All columns (table creation)
- **feature_flags**: status, conditions, metadata, created_by, updated_by, created_at, updated_at
- **feature_flag_overrides**: created_by, reason, expires_at, created_at, updated_at
- **audit_logs**: tenant_id, user_id, action, resource_type, resource_id, changes, ip_address, user_agent, created_at

### Performance Improvements
- Indexes on frequently queried columns
- Optimized foreign key relationships
- JSONB columns for flexible data storage

## Verification Steps

### 1. Table Verification
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'competitive_factor_templates',
    'module_configurations',
    'industry_templates',
    'module_usage_logs',
    'sector_modules',
    'organization_template_applications',
    'hierarchy_role_assignments',
    'feature_flag_usage',
    'admin_actions'
);
```

### 2. Column Verification
```sql
SELECT table_name, column_name FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'feature_flags'
AND column_name = 'status';
```

### 3. Endpoint Verification
```bash
# Test admin endpoints
curl -H "Authorization: Bearer JWT_TOKEN" \
  https://marketedge-platform.onrender.com/api/v1/admin/feature-flags

curl -H "Authorization: Bearer JWT_TOKEN" \
  https://marketedge-platform.onrender.com/api/v1/module-management/modules
```

## Rollback Plan

### If Critical Error Occurs
1. **Automatic Rollback**: Script uses transactions for automatic rollback
2. **Manual Rollback**: Restore from pre-repair database backup
3. **Selective Rollback**: Drop specific tables if needed

### Emergency Contacts
- **DevOps**: Immediate Render console access
- **Database**: PostgreSQL connection via DATABASE_URL
- **Monitoring**: Check application logs for errors

## Success Criteria

### Technical Success
- [ ] All 9 missing tables created
- [ ] All 48 missing columns added
- [ ] Alembic version updated
- [ ] No critical errors in logs
- [ ] Schema validation passes

### Business Success
- [ ] Admin endpoints return 200 OK
- [ ] Feature flags management functional
- [ ] Module management accessible
- [ ] Matt.Lindop@zebra.associates can access admin console
- [ ] £925K opportunity unblocked

## Post-Deployment Actions

### Immediate (0-15 minutes)
1. Verify admin endpoints respond correctly
2. Test feature flags management
3. Confirm module management functionality
4. Notify stakeholders of completion

### Short-term (15-60 minutes)
1. Monitor application logs for errors
2. Test user authentication and authorization
3. Verify data integrity
4. Document any issues encountered

### Medium-term (1-24 hours)
1. Performance monitoring
2. Database query optimization
3. User acceptance testing
4. Business process validation

## Risk Assessment

### Low Risk
- Schema changes use IF NOT EXISTS patterns
- Transaction safety prevents partial failures
- Existing data remains untouched

### Medium Risk
- Large number of schema changes in single operation
- Potential for foreign key constraint issues
- Performance impact during deployment

### Mitigation
- Comprehensive testing in staging
- Rollback procedures documented
- Monitoring during and after deployment

## Communication Plan

### Pre-Deployment
- [ ] Notify stakeholders of maintenance window
- [ ] Confirm business readiness
- [ ] Prepare rollback communication

### During Deployment
- [ ] Live status updates
- [ ] Error escalation procedures
- [ ] Progress monitoring

### Post-Deployment
- [ ] Success confirmation
- [ ] Performance report
- [ ] Business validation results

---

**CRITICAL**: This deployment fixes the schema drift that has been blocking the £925K Zebra Associates opportunity. Execute immediately to restore full platform functionality.

**Contact**: DevOps team for deployment support and monitoring