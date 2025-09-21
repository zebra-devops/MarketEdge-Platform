# Preview Environment Validation Checklist

## Pre-Validation Setup

### ✅ Pull Request Created
- [ ] PR created manually at: https://github.com/zebra-devops/MarketEdge-Platform/pull/new/test/preview-environment-auth0-validation
- [ ] PR title: "Test: Preview Environment Auth0 Validation"
- [ ] PR description includes complete test plan
- [ ] Branch: `test/preview-environment-auth0-validation`

### ✅ Render Environment Monitoring
- [ ] Render dashboard shows preview environment creation
- [ ] Preview URL obtained: `https://marketedge-backend-pr-XXX.onrender.com`
- [ ] Build and deployment completed successfully
- [ ] No deployment errors in Render logs

## Environment Configuration Validation

### Test 1: Public Environment Configuration
**Command**:
```bash
curl https://marketedge-backend-pr-XXX.onrender.com/api/v1/system/environment-config
```

**Expected Results**:
- [ ] Status: `200 OK`
- [ ] `environment.ENVIRONMENT`: `"staging"`
- [ ] `environment.is_staging`: `true`
- [ ] `environment.USE_STAGING_AUTH0`: `true`
- [ ] `auth0_config.domain`: Contains "staging" or staging domain
- [ ] `cors_origins`: Includes `"https://*.onrender.com"`
- [ ] `debug_info.preview_environment_detected`: `true`

**Actual Results**:
```
Status: ___
Environment: ___
Auth0 Domain: ___
CORS Origins: ___
```

### Test 2: Staging Health Check
**Command**:
```bash
curl https://marketedge-backend-pr-XXX.onrender.com/api/v1/system/staging-health
```

**Expected Results**:
- [ ] Status: `200 OK`
- [ ] `status`: `"HEALTHY"`
- [ ] `environment`: `"staging"`
- [ ] `staging_mode`: `true`
- [ ] `auth0_environment`: `"staging"`
- [ ] `database_connected`: `true`
- [ ] `redis_connected`: `true`
- [ ] `staging_env_vars` present with correct values

**Actual Results**:
```
Status: ___
Environment: ___
Auth0 Environment: ___
Database Connected: ___
Redis Connected: ___
```

### Test 3: Basic Health Check
**Command**:
```bash
curl https://marketedge-backend-pr-XXX.onrender.com/health
```

**Expected Results**:
- [ ] Status: `200 OK`
- [ ] Response indicates healthy status
- [ ] Environment information present

**Actual Results**:
```
Status: ___
Response: ___
```

## Security Isolation Validation

### Auth0 Configuration Security
- [ ] **Production Auth0 domain NOT exposed** in environment-config
- [ ] **Staging Auth0 domain** correctly configured
- [ ] **Client secrets** properly masked in responses
- [ ] **Environment variables** show staging configuration

### CORS Configuration Validation
- [ ] **Wildcard domains** `*.onrender.com` configured
- [ ] **Preview URL** accessible without CORS errors
- [ ] **Localhost** still included for development
- [ ] **Production domains** not required for preview

### Data Isolation Validation
- [ ] **Separate database** instance for preview
- [ ] **Test data** seeded correctly
- [ ] **No production data** accessible
- [ ] **Migration status** shows staging migrations applied

## Authentication Flow Validation

### Staging Auth0 Authentication (Optional - Requires Staging User)
**Command** (if staging Auth0 user available):
```bash
curl -H "Authorization: Bearer <staging-token>" \
     https://marketedge-backend-pr-XXX.onrender.com/api/v1/system/auth0-validation
```

**Expected Results**:
- [ ] Status: `200 OK`
- [ ] `auth0_details.domain`: Staging Auth0 domain
- [ ] `auth0_details.environment_type`: `"staging"`
- [ ] `auth0_details.staging_mode_active`: `true`
- [ ] User authentication successful

**Actual Results**:
```
Status: ___
Auth0 Domain: ___
Environment Type: ___
Staging Mode: ___
```

## Render Configuration Validation

### Environment Variables Check
Verify these environment variables are set in Render preview:
- [ ] `ENVIRONMENT=staging`
- [ ] `USE_STAGING_AUTH0=true`
- [ ] `AUTH0_DOMAIN_STAGING` set to staging tenant
- [ ] `AUTH0_CLIENT_ID_STAGING` set
- [ ] `AUTH0_CLIENT_SECRET_STAGING` set
- [ ] `CORS_ORIGINS` includes `https://*.onrender.com`
- [ ] `ENABLE_DEBUG_LOGGING=true`

### Deployment Process Validation
- [ ] **Automatic deployment** triggered by PR creation
- [ ] **Build process** completed without errors
- [ ] **Database migrations** applied automatically
- [ ] **Test data seeding** completed successfully
- [ ] **Startup script** detected staging mode

## Integration Validation

### API Documentation Access
- [ ] Swagger UI accessible: `https://marketedge-backend-pr-XXX.onrender.com/api/v1/docs`
- [ ] ReDoc accessible: `https://marketedge-backend-pr-XXX.onrender.com/api/v1/redoc`
- [ ] OpenAPI schema: `https://marketedge-backend-pr-XXX.onrender.com/api/v1/openapi.json`

### Cross-Domain Functionality
- [ ] **CORS headers** present in responses
- [ ] **Wildcard domain** support working
- [ ] **Preview URL** accessible from different origins
- [ ] **No CORS errors** in browser console

## Failure Scenarios Testing

### Invalid Requests
- [ ] **404 errors** handled gracefully
- [ ] **500 errors** return proper JSON responses
- [ ] **Authentication errors** show appropriate messages
- [ ] **Rate limiting** working if configured

### Security Boundaries
- [ ] **Production endpoints** not accessible
- [ ] **Admin endpoints** require proper authentication
- [ ] **Sensitive data** not exposed in error messages
- [ ] **Debug information** only in staging mode

## Performance Validation

### Response Times
- [ ] **Environment config**: < 2 seconds
- [ ] **Health checks**: < 5 seconds
- [ ] **API documentation**: < 10 seconds
- [ ] **Database queries**: Reasonable performance

### Resource Usage
- [ ] **Memory usage** within expected limits
- [ ] **CPU usage** reasonable for preview environment
- [ ] **Database connections** properly managed
- [ ] **Redis connections** working efficiently

## Final Validation Summary

### ✅ Critical Success Criteria
- [ ] **Staging Auth0 tenant** in use (not production)
- [ ] **Environment isolation** complete
- [ ] **CORS configuration** supports wildcard domains
- [ ] **Database and Redis** connectivity confirmed
- [ ] **All validation endpoints** responding correctly

### ✅ Business Impact Confirmed
- [ ] **Zebra Associates opportunity protected** - No production exposure
- [ ] **Matt.Lindop testing safety** - Staging environment confirmed
- [ ] **Development workflow** - Preview environments working
- [ ] **"Never debug in production"** - Complete isolation achieved

### ✅ Documentation Complete
- [ ] **Validation results** documented
- [ ] **Any issues** noted and resolved
- [ ] **Process improvements** identified
- [ ] **Team handoff** information prepared

## Next Steps After Validation

### If Validation Successful ✅
1. **Document success** in validation report
2. **Close test PR** after validation complete
3. **Update team processes** with validation workflow
4. **Schedule regular validation** for future PRs

### If Validation Issues Found ❌
1. **Document issues** immediately
2. **Stop further testing** until resolved
3. **Fix configuration** in Render dashboard
4. **Re-run validation** after fixes
5. **Escalate critical issues** to team lead

## Emergency Procedures

### Critical Security Issue Detected
1. **Immediately close PR**
2. **Disable preview environment** in Render
3. **Document issue** with full details
4. **Notify security team** if production exposure risk
5. **Do not proceed** until resolved

### Configuration Issues
1. **Check Render environment variables**
2. **Verify Auth0 staging tenant** configuration
3. **Confirm CORS settings** in render.yaml
4. **Review startup logs** for errors
5. **Test locally** if needed to debug

---

**Validation Date**: ____________
**Validator**: ____________
**Preview URL**: ____________
**Overall Status**: ✅ PASS / ❌ FAIL
**Notes**: ____________