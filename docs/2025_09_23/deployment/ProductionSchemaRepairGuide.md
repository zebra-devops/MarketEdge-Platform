# Production Schema Repair Guide

**Date**: September 23, 2025
**Author**: Maya (DevOps Agent)
**Status**: CRITICAL - Production schema drift detected
**Priority**: HIGH - Blocks £925K Zebra Associates opportunity

## Executive Summary

Production database schema is significantly out of sync with application models, causing:
- 9 missing tables
- 48 missing columns across existing tables
- Failed API endpoints
- Migration inconsistencies

**Impact**: Critical business functionality blocked, including admin features required for Zebra Associates.

## Schema Drift Analysis

### Missing Tables (Production)
1. `competitive_factor_templates` - SIC code competitive analysis
2. `module_configurations` - Organization-specific module settings
3. `industry_templates` - Industry-specific dashboard templates
4. `module_usage_logs` - Analytics module usage tracking
5. `sector_modules` - SIC-to-module mappings
6. `organization_template_applications` - Applied template tracking
7. `hierarchy_role_assignments` - Advanced role management
8. `feature_flag_usage` - Feature flag evaluation logs
9. `admin_actions` - Admin action audit trail

### Missing Columns (Production)
- **sic_codes**: title, description, is_supported, competitive_factors, default_metrics, analytics_config, created_at, updated_at
- **analytics_modules**: tags, ai_enhanced, created_at, updated_at
- **organisation_modules**: organisation_id, module_id, enabled, configuration, last_used, usage_count, created_at, updated_at
- **feature_flags**: status, conditions, metadata, created_by, updated_by, created_at, updated_at
- **feature_flag_overrides**: created_by, reason, expires_at, created_at, updated_at
- **audit_logs**: tenant_id, user_id, action, resource_type, resource_id, changes, ip_address, user_agent, created_at

### Root Cause
Migration 003 (Phase 3 enhancements) appears to have partially failed or never been applied to production, leaving the database at an earlier schema version.

## Recovery Strategy

### Option 1: Automated Schema Repair (RECOMMENDED)

**Tools**: `database/production_schema_repair.py`

**Advantages**:
- Safe `IF NOT EXISTS` patterns
- Comprehensive validation
- Detailed logging
- Rollback capability

**Steps**:
```bash
# 1. Dry run validation
python3 database/production_schema_repair.py --dry-run

# 2. Generate SQL for review
python3 database/production_schema_repair.py --generate-sql > fixes.sql

# 3. Apply fixes
python3 database/production_schema_repair.py --apply
```

### Option 2: Manual Migration Reset

**Use when**: Automated repair fails

**Steps**:
```bash
# 1. Check current Alembic version
alembic current

# 2. Generate baseline migration
python3 database/generate_baseline.py

# 3. Stamp to head
alembic stamp head
```

## Pre-Deployment Checklist

### Environment Validation
- [ ] Production database connection verified
- [ ] DATABASE_URL environment variable set correctly
- [ ] Backup strategy confirmed
- [ ] Maintenance window scheduled
- [ ] Rollback plan documented

### Schema Validation
- [ ] Current production schema documented
- [ ] Missing components identified
- [ ] Repair script tested in staging
- [ ] SQL review completed
- [ ] Foreign key dependencies verified

### Application Readiness
- [ ] Latest code deployed to production
- [ ] Import errors resolved (broken_endpoint fix)
- [ ] Critical endpoints functional
- [ ] Auth0 configuration verified

## Deployment Procedure

### Phase 1: Pre-Deployment (15 minutes)
```bash
# Create database backup
pg_dump $DATABASE_URL > production_backup_$(date +%Y%m%d_%H%M%S).sql

# Validate current state
python3 validate_production_schema_via_api.py

# Generate repair script
python3 database/production_schema_repair.py --generate-sql > production_fixes.sql
```

### Phase 2: Schema Repair (20 minutes)
```bash
# Apply schema fixes
DATABASE_URL=$PRODUCTION_DATABASE_URL python3 database/production_schema_repair.py --apply

# Verify repair success
python3 database/validate_schema.py --check
```

### Phase 3: Application Verification (10 minutes)
```bash
# Test critical endpoints
curl https://marketedge-platform.onrender.com/health
curl https://marketedge-platform.onrender.com/api/v1/admin/feature-flags -H "Authorization: Bearer $TOKEN"

# Verify admin functionality
python3 test_admin_endpoints.py
```

### Phase 4: Post-Deployment Validation (15 minutes)
```bash
# Check migration state
alembic current

# Test multi-tenant isolation
python3 test_tenant_isolation.py

# Monitor for errors
tail -f production.log
```

## Risk Assessment

### High Risk Items
1. **Foreign Key Dependencies**: New columns reference existing tables
2. **Data Integrity**: Default values for NOT NULL columns
3. **Application Compatibility**: Code expects new schema

### Risk Mitigation
- Use `IF NOT EXISTS` patterns to prevent conflicts
- Apply DEFAULT values for NOT NULL columns
- Test rollback procedures
- Monitor application after deployment

### Rollback Plan
```bash
# If schema repair fails
psql $DATABASE_URL < production_backup_TIMESTAMP.sql

# If application issues occur
# Revert to previous deployment
# Check application logs for specific errors
```

## Success Criteria

### Schema Validation
- [ ] All expected tables exist in production
- [ ] All expected columns exist with correct types
- [ ] Foreign key relationships intact
- [ ] No orphaned data

### API Functionality
- [ ] `/health` endpoint returns healthy status
- [ ] `/api/v1/admin/feature-flags` returns 401/403 (not 404)
- [ ] `/api/v1/admin/modules` returns 401/403 (not 404)
- [ ] `/api/v1/features/enabled` returns 401/403 (not 404)

### Business Critical Features
- [ ] Zebra Associates super_admin user access
- [ ] Feature flag management interface
- [ ] Multi-tenant organization switching
- [ ] Industry-specific dashboard loading

## Post-Deployment Actions

### Immediate (0-2 hours)
- Monitor application logs for errors
- Test critical user journeys
- Verify admin panel functionality
- Check database connection pools

### Short Term (24 hours)
- Monitor performance metrics
- Verify tenant data isolation
- Test feature flag evaluations
- Validate audit log generation

### Long Term (1 week)
- Review migration process lessons learned
- Update deployment procedures
- Implement schema drift monitoring
- Schedule next maintenance window

## Contact Information

**Primary**: DevOps Team (Maya)
**Secondary**: Development Team
**Emergency**: Production Support On-Call

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-09-23 | Maya | Initial production schema repair guide |

---

**⚠️ CRITICAL**: This guide addresses production schema drift that blocks critical business functionality. Execute during scheduled maintenance window with full backup and rollback procedures ready.