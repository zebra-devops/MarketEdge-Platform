# Staging Environment Testing Procedures

**Document Version**: 1.0
**Created**: September 21, 2025
**Purpose**: Comprehensive testing procedures for staging environments

## 🧪 Testing Overview

This document provides step-by-step testing procedures for validating staging environments before production deployment.

## 🚀 Pre-Deployment Testing

### 1. Environment Creation Validation

```bash
# Verify environment variables are set correctly
curl https://pr-{N}-marketedge-backend.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "environment": "staging",
  "timestamp": "2025-09-21T...",
  "version": "1.2.0"
}
```

### 2. Database Migration Testing

```bash
# Connect to staging database
psql $STAGING_DATABASE_URL

# Verify all tables exist
\dt

# Expected tables:
# - organizations
# - users
# - feature_flags
# - analytics_modules
# - user_roles
# - alembic_version

# Check migration status
SELECT * FROM alembic_version;
```

### 3. Auth0 Integration Testing

```bash
# Test Auth0 configuration
curl https://pr-{N}-marketedge-backend.onrender.com/api/v1/auth/auth0-url

# Should return staging Auth0 authorization URL
# Domain should be: dev-zebra-marketedge.uk.auth0.com
```

## 🔐 Authentication Testing

### 1. Login Flow Testing

```bash
# Navigate to API docs
open https://pr-{N}-marketedge-backend.onrender.com/api/v1/docs

# Click "Authorize" button
# Login with staging Auth0 credentials
# Verify JWT token is issued correctly
```

### 2. Role-Based Access Testing

```bash
# Test admin endpoints (requires super_admin role)
curl -H "Authorization: Bearer $TOKEN" \
  https://pr-{N}-marketedge-backend.onrender.com/api/v1/admin/dashboard/stats

# Expected: 200 response with dashboard data
```

### 3. Token Validation Testing

```python
# Test JWT token structure
import jwt
import json

token = "your-jwt-token-here"
decoded = jwt.decode(token, options={"verify_signature": False})

# Verify token contains:
# - user_id
# - organisation_id
# - role (should be super_admin for Matt.Lindop)
# - industry_type
# - sic_code
print(json.dumps(decoded, indent=2))
```

## 📊 Database Testing

### 1. Test Data Validation

```sql
-- Connect to staging database
-- Verify test organizations exist

SELECT name, domain, industry, sic_code
FROM organizations
WHERE domain LIKE '%.staging'
   OR domain = 'zebra.associates'
   OR domain = 'odeon.co.uk';

-- Expected results:
-- Zebra Associates (Staging) | zebra.associates | B2B | 70221
-- ODEON Cinemas (Staging) | odeon.co.uk | Cinema | 59140
-- Test Hotel Group | testhotel.staging | Hotel | 55100
```

### 2. Multi-Tenant Isolation Testing

```sql
-- Test Row Level Security (RLS) policies
SET app.current_organisation_id = 'test-org-id';

-- Should only return data for the set organization
SELECT * FROM users;
SELECT * FROM feature_flags;
```

### 3. Feature Flags Testing

```sql
-- Verify feature flags are seeded correctly
SELECT key, name, is_enabled, percentage_rollout
FROM feature_flags
ORDER BY key;

-- Test organization-specific overrides
SELECT ff.key, ffo.is_enabled, ffo.organization_id
FROM feature_flags ff
LEFT JOIN feature_flag_overrides ffo ON ff.id = ffo.feature_flag_id;
```

## 🛠️ API Endpoint Testing

### 1. Health and Readiness Checks

```bash
# Basic health check
curl https://pr-{N}-marketedge-backend.onrender.com/health
# Expected: {"status": "healthy", "environment": "staging"}

# Readiness check (includes database/Redis connectivity)
curl https://pr-{N}-marketedge-backend.onrender.com/ready
# Expected: {"status": "ready", "checks": {...}}
```

### 2. Core API Endpoints

```bash
# Set your authorization token
TOKEN="your-jwt-token"
BASE_URL="https://pr-{N}-marketedge-backend.onrender.com/api/v1"

# Test user endpoints
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/auth/me"
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/users"

# Test organization endpoints
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/organisations/current"

# Test tools endpoints
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/tools"
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/tools/access"
```

### 3. Admin Endpoints (Super Admin Required)

```bash
# Test admin dashboard
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/admin/dashboard/stats"

# Test feature flag management
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/admin/feature-flags"

# Test analytics modules
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/admin/modules"

# Test SIC codes
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/admin/sic-codes"
```

## 🎯 Feature-Specific Testing

### 1. Feature Flag System

```bash
# Test feature flag evaluation
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/features/enabled"

# Test specific feature flag
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/features/analytics_dashboard"

# Test admin feature flag management
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key":"test_flag","name":"Test Flag","description":"Test","is_enabled":true}' \
  "$BASE_URL/admin/feature-flags"
```

### 2. Analytics Modules

```bash
# Test module listing
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/admin/modules"

# Test module enablement
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/admin/modules/{module_id}/enable"

# Test module analytics
curl -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/admin/modules/{module_id}/analytics"
```

## 🔍 Performance Testing

### 1. Response Time Testing

```bash
# Test response times for key endpoints
time curl -s https://pr-{N}-marketedge-backend.onrender.com/health

# Expected: < 500ms for health checks
# Expected: < 2s for authenticated endpoints
```

### 2. Database Performance

```sql
-- Test query performance
EXPLAIN ANALYZE SELECT * FROM organizations WHERE domain = 'zebra.associates';

-- Should use index on domain column
-- Should complete in < 10ms
```

### 3. Concurrent Request Testing

```bash
# Test concurrent requests (simple load test)
for i in {1..10}; do
  curl -s https://pr-{N}-marketedge-backend.onrender.com/health &
done
wait

# All requests should complete successfully
```

## 🛡️ Security Testing

### 1. Authentication Security

```bash
# Test unauthorized access (should fail)
curl -w "%{http_code}" https://pr-{N}-marketedge-backend.onrender.com/api/v1/admin/dashboard/stats
# Expected: 401 or 403

# Test with invalid token
curl -H "Authorization: Bearer invalid-token" \
  https://pr-{N}-marketedge-backend.onrender.com/api/v1/auth/me
# Expected: 401
```

### 2. CORS Testing

```bash
# Test CORS headers (staging should allow all origins)
curl -H "Origin: https://test.example.com" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS \
  https://pr-{N}-marketedge-backend.onrender.com/api/v1/health

# Should include: Access-Control-Allow-Origin: *
```

### 3. Input Validation Testing

```bash
# Test SQL injection protection
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test\"); DROP TABLE users; --"}' \
  "$BASE_URL/admin/feature-flags"

# Should return validation error, not execute SQL
```

## 📋 Matt.Lindop Specific Testing

### 1. Super Admin Access Validation

```bash
# Verify Matt.Lindop has super_admin role
# Login with Matt's credentials in staging
# Check JWT token role claim

# Test super admin endpoints
curl -H "Authorization: Bearer $MATT_TOKEN" \
  "$BASE_URL/admin/dashboard/stats"

# Should return comprehensive platform statistics
```

### 2. Feature Flag Management

```bash
# Test feature flag creation
curl -X POST -H "Authorization: Bearer $MATT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "zebra_premium_features",
    "name": "Zebra Premium Features",
    "description": "Premium features for Zebra Associates",
    "is_enabled": true,
    "percentage_rollout": 100
  }' \
  "$BASE_URL/admin/feature-flags"

# Test organization override creation
curl -X POST -H "Authorization: Bearer $MATT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "zebra-org-id",
    "is_enabled": true
  }' \
  "$BASE_URL/admin/feature-flags/{flag_id}/overrides"
```

### 3. Organization Management

```bash
# Test current organization access
curl -H "Authorization: Bearer $MATT_TOKEN" \
  "$BASE_URL/organisations/current"

# Should return Zebra Associates organization details
# Verify industry_type: "B2B"
# Verify sic_code: "70221"
```

## 📊 Test Results Documentation

### Test Execution Template

```markdown
## Staging Environment Test Report

**Environment**: pr-{N}-marketedge-backend.onrender.com
**Test Date**: YYYY-MM-DD
**Tester**: [Name]

### Test Results Summary
- ✅ Environment Creation: PASS
- ✅ Database Migration: PASS
- ✅ Auth0 Integration: PASS
- ✅ API Endpoints: PASS
- ✅ Admin Access: PASS
- ✅ Security: PASS
- ✅ Performance: PASS

### Detailed Results
1. **Health Check**: Response time 150ms ✅
2. **Database**: All 15 tables present ✅
3. **Auth0**: Login successful ✅
4. **Admin Dashboard**: Stats loaded ✅
5. **Feature Flags**: CRUD operations working ✅

### Issues Found
- None

### Recommendation
- ✅ APPROVE for production deployment
```

## 🚨 Failure Scenarios

### Common Issues and Solutions

#### 1. Environment Won't Start
```bash
# Check Render logs
render logs --service=marketedge-backend --tail

# Common causes:
# - Invalid render.yaml syntax
# - Missing environment variables
# - Database connection issues
```

#### 2. Auth0 Integration Fails
```bash
# Verify staging Auth0 configuration
# Check callback URLs include preview environment pattern
# Ensure staging secrets are set correctly
```

#### 3. Database Migration Fails
```bash
# Connect to staging database
psql $STAGING_DATABASE_URL

# Check for migration conflicts
SELECT * FROM alembic_version;

# Re-run staging setup if needed
python database/staging_setup.py
```

#### 4. Admin Access Denied
```bash
# Verify JWT token contains super_admin role
# Check organization context in token
# Ensure user exists in staging database
```

## 🎯 Success Criteria

### Deployment Approval Criteria

A staging environment passes testing when:

1. **Infrastructure**: ✅ All services start successfully
2. **Database**: ✅ Migrations applied, test data loaded
3. **Authentication**: ✅ Auth0 login works, JWT tokens valid
4. **API**: ✅ All endpoints respond correctly
5. **Admin Access**: ✅ Super admin functions work
6. **Security**: ✅ Authentication and authorization enforced
7. **Performance**: ✅ Response times within acceptable limits

### Production Deployment Decision

Only deploy to production when:
- All staging tests pass
- Code review approved
- Business stakeholder approval (for significant changes)
- Database backup confirmed (if schema changes)

---

**Staging Environment Testing Complete**

This testing framework ensures comprehensive validation of all staging environments before production deployment, protecting the critical £925K Zebra Associates opportunity while maintaining platform reliability.