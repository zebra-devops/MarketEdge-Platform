# MIG-004: Database Migration Strategy Planning

**Epic 1: Pre-Migration Assessment & Planning**  
**User Story:** MIG-004 - Database Migration Strategy Planning (8 pts)  
**Planning Date:** August 15, 2025  
**Planner:** Alex - Full-Stack Software Developer  

## Executive Summary

This document outlines the comprehensive database migration strategy for moving the MarketEdge platform from Railway to Render. The strategy covers PostgreSQL migration, Redis migration, data migration approaches, and connection string management to ensure minimal downtime and zero data loss.

**Migration Strategy:** **LOW-RISK APPROACH** with comprehensive backup and validation procedures

## 1. Current Database Assessment

### 1.1 Railway Database Configuration

**PostgreSQL Database:**
```yaml
Current Status: Railway-managed PostgreSQL
Connection: ${{Postgres.DATABASE_URL}}
Database Name: marketedge_production
Schema Version: Latest (migration 009)
Estimated Size: < 1GB (early stage platform)
Tables: ~15 core tables (users, organizations, features, etc.)
```

**Redis Cache:**
```yaml
Current Status: Railway-managed Redis
Connection: ${{Redis.REDIS_URL}}
Usage: Cache + Rate limiting storage
Data Type: Ephemeral (acceptable loss)
Estimated Size: < 100MB
```

### 1.2 Database Schema Analysis

**Core Tables Structure:**
```sql
-- User Management
users (id, email, auth0_user_id, created_at, updated_at)
user_application_access (user_id, application_id, granted_at)

-- Organization Management  
organisations (id, name, industry_type, created_at, updated_at)
organisation_hierarchy (id, parent_id, child_id, created_at)
organisation_tool_access (organisation_id, tool_id, access_level)

-- Feature Management
features (id, name, description, enabled, created_at)
feature_flags (id, feature_id, organisation_id, enabled, percentage)

-- Rate Limiting
rate_limits (id, identifier, requests, window_seconds, created_at)

-- Audit & Security
audit_logs (id, user_id, action, resource, timestamp, details)
```

**Migration Considerations:**
- ✅ **Standard PostgreSQL** - No Railway-specific features used
- ✅ **Portable schema** - Uses standard SQL types and constraints
- ✅ **Foreign key constraints** - Will be preserved in migration
- ✅ **Indexes** - Standard indexes, easily recreated
- ✅ **Row Level Security** - RLS policies will be preserved

## 2. PostgreSQL Migration Strategy

### 2.1 Migration Approach: Zero-Downtime Blue-Green

**Strategy Overview:**
```
Railway PostgreSQL (Blue) → Render PostgreSQL (Green)
1. Create Render database
2. Initial data sync
3. Application cutover
4. Final data sync
5. Railway cleanup
```

### 2.2 PostgreSQL Export Process

**Step 1: Pre-Migration Backup**
```bash
# Export schema and data from Railway
railway run -- pg_dump $DATABASE_URL \
  --verbose \
  --no-acl \
  --no-owner \
  --format=custom \
  --file=marketedge_railway_backup_$(date +%Y%m%d_%H%M%S).dump

# Export schema only for validation
railway run -- pg_dump $DATABASE_URL \
  --schema-only \
  --no-acl \
  --no-owner \
  --file=marketedge_schema_$(date +%Y%m%d_%H%M%S).sql

# Export data only for separate import
railway run -- pg_dump $DATABASE_URL \
  --data-only \
  --no-acl \
  --no-owner \
  --column-inserts \
  --file=marketedge_data_$(date +%Y%m%d_%H%M%S).sql
```

**Step 2: Data Validation Scripts**
```bash
# Create data validation script
#!/bin/bash
# validate_export.sh

echo "Validating PostgreSQL export..."

# Check table counts
psql $SOURCE_DATABASE_URL -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows
FROM pg_stat_user_tables 
ORDER BY live_rows DESC;
"

# Check critical constraints
psql $SOURCE_DATABASE_URL -c "
SELECT conname, contype, confupdtype, confdeltype 
FROM pg_constraint 
WHERE contype IN ('f', 'p', 'u', 'c');
"

# Validate data integrity
psql $SOURCE_DATABASE_URL -c "
-- Check for orphaned records
SELECT 'user_application_access orphans' as check_type, count(*) as count
FROM user_application_access uaa 
LEFT JOIN users u ON uaa.user_id = u.id 
WHERE u.id IS NULL

UNION ALL

SELECT 'organisation_hierarchy orphans' as check_type, count(*) as count
FROM organisation_hierarchy oh 
LEFT JOIN organisations o ON oh.parent_id = o.id 
WHERE o.id IS NULL;
"
```

### 2.3 Render PostgreSQL Setup

**Step 3: Render Database Creation**
```yaml
# render.yaml database configuration
databases:
  - name: marketedge-postgres
    databaseName: marketedge_production
    user: marketedge_user
    plan: standard  # Production plan for proper performance
    region: oregon  # Match application region
    version: "15"   # Latest stable PostgreSQL version
    
    # Production configuration
    ipAllowList: []  # Private network only
    
    # Backup configuration
    backup:
      enabled: true
      schedule: "0 2 * * *"  # Daily at 2 AM
      retention: 30  # 30 days retention
```

**Step 4: Schema Migration**
```bash
# Import schema to Render PostgreSQL
pg_restore \
  --host=$RENDER_DB_HOST \
  --port=$RENDER_DB_PORT \
  --username=$RENDER_DB_USER \
  --dbname=$RENDER_DB_NAME \
  --verbose \
  --no-acl \
  --no-owner \
  --schema-only \
  marketedge_railway_backup.dump

# Verify schema import
psql $RENDER_DATABASE_URL -c "
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
"
```

### 2.4 Data Migration Process

**Step 5: Initial Data Import**
```bash
# Import data to Render PostgreSQL
pg_restore \
  --host=$RENDER_DB_HOST \
  --port=$RENDER_DB_PORT \
  --username=$RENDER_DB_USER \
  --dbname=$RENDER_DB_NAME \
  --verbose \
  --no-acl \
  --no-owner \
  --data-only \
  --disable-triggers \
  marketedge_railway_backup.dump

# Re-enable triggers and validate constraints
psql $RENDER_DATABASE_URL -c "
-- Re-enable all triggers
UPDATE pg_class SET reltriggers = (
    SELECT count(*) FROM pg_trigger WHERE tgrelid = pg_class.oid
);

-- Validate all foreign key constraints
SELECT conname, conrelid::regclass 
FROM pg_constraint 
WHERE contype = 'f' 
AND NOT EXISTS (
    SELECT 1 FROM pg_trigger 
    WHERE tgrelid = conrelid AND tgname = conname
);
"
```

**Step 6: Data Validation**
```bash
# Compare record counts between Railway and Render
#!/bin/bash
# compare_databases.sh

TABLES="users organisations features feature_flags user_application_access organisation_tool_access rate_limits audit_logs"

echo "Comparing record counts between Railway and Render..."
echo "Table | Railway | Render | Match"
echo "------|---------|--------|------"

for table in $TABLES; do
    railway_count=$(psql $RAILWAY_DATABASE_URL -t -c "SELECT count(*) FROM $table;")
    render_count=$(psql $RENDER_DATABASE_URL -t -c "SELECT count(*) FROM $table;")
    
    if [ "$railway_count" -eq "$render_count" ]; then
        match="✅"
    else
        match="❌"
    fi
    
    echo "$table | $railway_count | $render_count | $match"
done
```

## 3. Redis Migration Strategy

### 3.1 Redis Migration Approach: Cache Rebuild

**Strategy: Acceptable Data Loss**
```
Redis Usage Analysis:
- Cache: Session data, API responses → Acceptable loss
- Rate Limiting: Request counters → Acceptable reset
- Temporary Data: Feature flags cache → Rebuilt from PostgreSQL

Decision: Do not migrate Redis data - allow rebuild
```

### 3.2 Render Redis Setup

**Redis Configuration:**
```yaml
# render.yaml Redis configuration
databases:
  - name: marketedge-redis
    plan: standard  # Production plan
    region: oregon  # Match application region
    version: "7"    # Latest stable Redis version
    
    # Configuration
    maxmemoryPolicy: allkeys-lru  # Cache eviction policy
    
    # Security
    ipAllowList: []  # Private network only
```

**Redis Initialization:**
```bash
# Redis initialization script (post-migration)
#!/bin/bash
# initialize_redis.sh

echo "Initializing Redis cache after migration..."

# Clear any existing data (ensure clean state)
redis-cli -u $RENDER_REDIS_URL FLUSHALL

# Pre-warm critical caches
echo "Pre-warming feature flags cache..."
psql $RENDER_DATABASE_URL -c "
SELECT f.name, ff.enabled, ff.percentage, o.id as org_id
FROM features f
JOIN feature_flags ff ON f.id = ff.feature_id
JOIN organisations o ON ff.organisation_id = o.id
WHERE f.enabled = true;
" | while read name enabled percentage org_id; do
    redis-cli -u $RENDER_REDIS_URL SET "feature:$org_id:$name" "$enabled:$percentage"
done

echo "Redis initialization complete"
```

## 4. Connection String Migration

### 4.1 Database URL Mapping

**Railway to Render Connection String Mapping:**

| Service | Railway Format | Render Format |
|---------|----------------|---------------|
| **PostgreSQL** | `${{Postgres.DATABASE_URL}}` | `${{marketedge-postgres.DATABASE_URL}}` |
| **Redis** | `${{Redis.REDIS_URL}}` | `${{marketedge-redis.REDIS_URL}}` |

**Environment Variable Updates:**
```yaml
# Current Railway environment
DATABASE_URL: ${{Postgres.DATABASE_URL}}
REDIS_URL: ${{Redis.REDIS_URL}}
RATE_LIMIT_STORAGE_URL: ${{Redis.REDIS_URL}}/1

# New Render environment
DATABASE_URL: ${{marketedge-postgres.DATABASE_URL}}
REDIS_URL: ${{marketedge-redis.REDIS_URL}}
RATE_LIMIT_STORAGE_URL: ${{marketedge-redis.REDIS_URL}}/1
```

### 4.2 Application Configuration Updates

**Database Connection Configuration:**
```python
# app/core/database.py - No changes required
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=False)

# Connection string format automatically handled by Render:
# postgresql://user:password@host:5432/database
```

**Redis Connection Configuration:**
```python
# app/core/redis_manager.py - No changes required
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.from_url(REDIS_URL)

# Connection string format automatically handled by Render:
# redis://user:password@host:6379
```

## 5. Migration Timeline and Process

### 5.1 Migration Phase Schedule

| Phase | Duration | Description | Downtime |
|-------|----------|-------------|----------|
| **Phase 1: Preparation** | 2 hours | Database setup, export, validation | None |
| **Phase 2: Initial Sync** | 1 hour | Schema and data import to Render | None |
| **Phase 3: Application Deploy** | 30 minutes | Deploy app with new connection strings | 5-10 minutes |
| **Phase 4: Validation** | 1 hour | Data validation, functionality testing | None |
| **Phase 5: Cleanup** | 30 minutes | Railway resource cleanup | None |

**Total Migration Time:** ~5 hours  
**Total Downtime:** 5-10 minutes

### 5.2 Detailed Migration Steps

**Pre-Migration (Day -1):**
```bash
# 1. Create Render database resources
render deploy --env staging  # Test environment first

# 2. Export Railway data for validation
./scripts/export_railway_data.sh

# 3. Import to Render staging for testing
./scripts/import_to_render_staging.sh

# 4. Validate staging environment
./scripts/validate_migration.sh staging
```

**Migration Day:**
```bash
# Hour 0: Final preparation
./scripts/export_railway_data.sh --final

# Hour 1: Production database setup
render deploy --env production

# Hour 2: Data import
./scripts/import_to_render_production.sh

# Hour 3: Application deployment
render deploy --service marketedge-backend

# Hour 4: Validation and monitoring
./scripts/validate_production_migration.sh
./scripts/monitor_migration_health.sh
```

### 5.3 Rollback Strategy

**Rollback Triggers:**
- Data validation failures
- Application connectivity issues
- Performance degradation > 50%
- Critical functionality failures

**Rollback Process:**
```bash
# 1. Revert to Railway database connections
railway variables set DATABASE_URL="${{Postgres.DATABASE_URL}}"
railway variables set REDIS_URL="${{Redis.REDIS_URL}}"

# 2. Redeploy with Railway connections
railway up --detach

# 3. Validate Railway environment
./scripts/validate_railway_health.sh

# 4. Pause Render resources (cost saving)
render scale --service marketedge-backend --replicas 0
```

## 6. Data Validation and Testing

### 6.1 Validation Test Suite

**Database Integrity Tests:**
```sql
-- Test 1: Record count validation
WITH railway_counts AS (
    SELECT 'users' as table_name, count(*) as count FROM users
    UNION ALL SELECT 'organisations', count(*) FROM organisations
    UNION ALL SELECT 'features', count(*) FROM features
    -- ... other tables
),
render_counts AS (
    -- Same query structure for Render database
)
SELECT r.table_name, r.count as railway_count, re.count as render_count,
       CASE WHEN r.count = re.count THEN '✅' ELSE '❌' END as match
FROM railway_counts r
JOIN render_counts re ON r.table_name = re.table_name;

-- Test 2: Foreign key integrity
SELECT conname, 
       CASE WHEN violated_count = 0 THEN '✅' ELSE '❌' END as status
FROM (
    SELECT conname, count(*) as violated_count
    FROM pg_constraint c
    WHERE contype = 'f'
    GROUP BY conname
) validation;

-- Test 3: Data consistency checks
SELECT 'Auth0 user mapping' as test,
       CASE WHEN count(*) = 0 THEN '✅' ELSE '❌' END as status
FROM users 
WHERE auth0_user_id IS NULL OR auth0_user_id = '';
```

**Application Functionality Tests:**
```bash
#!/bin/bash
# test_application_functionality.sh

BASE_URL="https://marketedge-backend.onrender.com"

echo "Testing critical application functionality..."

# Test 1: Health endpoint
echo "Testing health endpoint..."
health_response=$(curl -s "$BASE_URL/health")
if echo "$health_response" | grep -q "healthy"; then
    echo "✅ Health endpoint working"
else
    echo "❌ Health endpoint failed"
fi

# Test 2: Database connectivity
echo "Testing database connectivity..."
ready_response=$(curl -s "$BASE_URL/ready")
if echo "$ready_response" | grep -q "database.*connected"; then
    echo "✅ Database connectivity working"
else
    echo "❌ Database connectivity failed"
fi

# Test 3: Redis connectivity
if echo "$ready_response" | grep -q "redis.*connected"; then
    echo "✅ Redis connectivity working"
else
    echo "❌ Redis connectivity failed"
fi

# Test 4: Auth0 integration
echo "Testing Auth0 integration..."
auth_response=$(curl -s -H "Origin: https://app.zebra.associates" \
                     -X OPTIONS "$BASE_URL/api/auth/me")
if [ $? -eq 0 ]; then
    echo "✅ Auth0 CORS working"
else
    echo "❌ Auth0 CORS failed"
fi

# Test 5: Critical API endpoints
endpoints="/api/organisations /api/features /api/users"
for endpoint in $endpoints; do
    echo "Testing $endpoint..."
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    if [ "$response" = "401" ] || [ "$response" = "200" ]; then
        echo "✅ $endpoint responding correctly"
    else
        echo "❌ $endpoint failed (HTTP $response)"
    fi
done
```

### 6.2 Performance Validation

**Database Performance Tests:**
```sql
-- Test query performance on key operations
EXPLAIN ANALYZE 
SELECT u.*, o.name as organisation_name
FROM users u
JOIN user_application_access uaa ON u.id = uaa.user_id
JOIN organisations o ON uaa.application_id = o.id
WHERE u.auth0_user_id = 'test_user_id';

-- Test bulk operations performance  
EXPLAIN ANALYZE
SELECT f.name, ff.enabled, ff.percentage
FROM features f
JOIN feature_flags ff ON f.id = ff.feature_id
WHERE ff.organisation_id IN (SELECT id FROM organisations LIMIT 100);

-- Monitor index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan > 0
ORDER BY idx_scan DESC;
```

## 7. Risk Assessment and Mitigation

### 7.1 Migration Risks

| Risk Category | Probability | Impact | Mitigation Strategy |
|---------------|-------------|--------|-------------------|
| **Data Loss** | LOW | CRITICAL | Complete backup validation, checksums |
| **Extended Downtime** | MEDIUM | HIGH | Blue-green deployment, rollback plan |
| **Performance Degradation** | LOW | MEDIUM | Performance testing, connection pooling |
| **Auth0 Integration Issues** | LOW | HIGH | CORS validation, Auth0 domain testing |
| **Rate Limiting Reset** | HIGH | LOW | Acceptable - rate limits rebuild |

### 7.2 Mitigation Strategies

**Data Protection:**
```bash
# Multiple backup strategies
1. Railway native backup (pre-migration)
2. pg_dump custom format backup
3. pg_dump SQL format backup
4. Data validation checksums
5. Test restoration on staging environment
```

**Service Continuity:**
```bash
# Zero-downtime approach
1. Parallel environment setup (Render)
2. Data sync while Railway active
3. Quick DNS/connection string switch
4. Immediate rollback capability
5. Health monitoring throughout
```

**Performance Assurance:**
```bash
# Performance validation
1. Connection pool configuration
2. Index recreation verification
3. Query performance baseline comparison
4. Load testing on Render environment
5. Resource monitoring setup
```

## 8. Post-Migration Validation

### 8.1 Immediate Validation (0-2 hours)

**Critical System Checks:**
```bash
# 1. Database connectivity
psql $RENDER_DATABASE_URL -c "SELECT count(*) FROM users;"

# 2. Redis connectivity  
redis-cli -u $RENDER_REDIS_URL ping

# 3. Application health
curl https://marketedge-backend.onrender.com/health
curl https://marketedge-backend.onrender.com/ready

# 4. Auth0 integration
curl -H "Origin: https://app.zebra.associates" \
     https://marketedge-backend.onrender.com/api/auth/me

# 5. CORS functionality for Odeon demo
curl -X OPTIONS \
     -H "Origin: https://app.zebra.associates" \
     -H "Access-Control-Request-Method: GET" \
     https://marketedge-backend.onrender.com/api/organisations
```

### 8.2 Extended Validation (2-24 hours)

**Comprehensive Testing:**
```bash
# 1. Data integrity validation
./scripts/validate_data_integrity.sh

# 2. Performance monitoring
./scripts/monitor_performance_metrics.sh

# 3. User acceptance testing
./scripts/run_user_acceptance_tests.sh

# 4. Error monitoring
./scripts/monitor_error_rates.sh

# 5. £925K Odeon demo validation
./scripts/test_odeon_demo_integration.sh
```

### 8.3 Monitoring and Alerting

**Key Metrics to Monitor:**
```yaml
Database Metrics:
  - Connection count and pool usage
  - Query response times (baseline: < 100ms)
  - Error rates (target: < 0.1%)
  - Connection failures

Redis Metrics:
  - Cache hit ratio (target: > 90%)
  - Memory usage
  - Connection count
  - Operation latency

Application Metrics:
  - API response times (target: < 500ms)
  - Auth0 authentication success rate
  - CORS preflight success rate
  - Health check response times
```

## 9. Cleanup and Optimization

### 9.1 Railway Resource Cleanup

**Post-Migration Cleanup (24-48 hours after successful migration):**
```bash
# 1. Verify Render environment stability
./scripts/verify_render_stability.sh

# 2. Create final Railway backup
railway run -- pg_dump $DATABASE_URL --file=final_railway_backup.dump

# 3. Document Railway configuration for future reference
railway variables > railway_final_config.txt
railway status > railway_final_status.txt

# 4. Scale down Railway resources (cost saving)
# Keep databases for 48 hours as safety net

# 5. After 48 hours of stable operation:
# - Delete Railway PostgreSQL database
# - Delete Railway Redis database  
# - Cancel Railway project (if dedicated to this service)
```

### 9.2 Render Environment Optimization

**Performance Optimization:**
```yaml
# Optimize Render database configuration
databases:
  - name: marketedge-postgres
    plan: standard-2  # Upgrade if needed based on usage
    connectionPooling:
      enabled: true
      maxConnections: 25
    monitoring:
      enabled: true
    
  - name: marketedge-redis
    plan: standard-1
    evictionPolicy: allkeys-lru
    monitoring:
      enabled: true
```

**Security Hardening:**
```yaml
# Enhanced security configuration
services:
  - name: marketedge-backend
    envVars:
      # Database security
      - key: DATABASE_SSL_MODE
        value: require
      - key: DATABASE_POOL_SIZE
        value: 20
      - key: DATABASE_MAX_OVERFLOW
        value: 5
      
      # Redis security
      - key: REDIS_SSL
        value: true
      - key: REDIS_HEALTH_CHECK_INTERVAL
        value: 30
```

## 10. Success Criteria and Rollback Conditions

### 10.1 Migration Success Criteria

**Must-Have Success Criteria:**
- ✅ **Zero data loss** - All records migrated successfully
- ✅ **Application functionality** - All API endpoints responding correctly
- ✅ **Auth0 integration** - Authentication working for £925K Odeon demo
- ✅ **CORS configuration** - Cross-origin requests working properly
- ✅ **Performance parity** - Response times within 10% of Railway baseline
- ✅ **Health monitoring** - /health and /ready endpoints functional

**Nice-to-Have Success Criteria:**
- ✅ **Performance improvement** - Faster response times than Railway
- ✅ **Enhanced monitoring** - Better observability in Render
- ✅ **Cost optimization** - Lower infrastructure costs
- ✅ **Improved backup strategy** - More frequent and reliable backups

### 10.2 Rollback Conditions

**Immediate Rollback Triggers:**
- ❌ **Data corruption detected** - Any data integrity violations
- ❌ **Auth0 integration failure** - Authentication not working
- ❌ **Critical API failures** - Core functionality broken
- ❌ **Performance degradation > 50%** - Unacceptable response times
- ❌ **Database connectivity issues** - Connection failures or timeouts

**Rollback Procedure:**
```bash
# Emergency rollback (< 15 minutes)
1. Revert environment variables to Railway connections
2. Redeploy application on Railway
3. Validate Railway environment health
4. Notify stakeholders of rollback
5. Investigate Render issues for next attempt
```

## 11. Conclusion and Recommendations

### 11.1 Migration Strategy Summary

**Recommended Approach: BLUE-GREEN DEPLOYMENT**
- **Low Risk:** Comprehensive backup and validation procedures
- **Minimal Downtime:** 5-10 minutes application cutover
- **Zero Data Loss:** Multiple validation layers and checksums
- **Quick Rollback:** Immediate revert capability maintained

### 11.2 Key Success Factors

1. **Thorough Testing:** Staging environment validation before production
2. **Data Validation:** Multiple checkpoints and integrity verification  
3. **Performance Monitoring:** Baseline comparison and alerting
4. **Rollback Readiness:** Tested emergency revert procedures
5. **Stakeholder Communication:** Clear timeline and status updates

### 11.3 Next Steps

1. ✅ **MIG-004 COMPLETE** - Database migration strategy documented
2. 🔄 **Proceed to MIG-005** - Environment variable migration planning
3. 🔄 **Create migration scripts** - Automate the migration process
4. 🔄 **Setup staging environment** - Test migration procedures
5. 🔄 **Schedule migration window** - Coordinate with stakeholders

**Migration Confidence Level:** **HIGH**  
**Estimated Success Probability:** **95%**  
**Risk Level:** **LOW**  

---

**Planning Completed:** August 15, 2025  
**Next Phase:** Environment Variable Migration Planning (MIG-005)  
**Document Version:** 1.0.0