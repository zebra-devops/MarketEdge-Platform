# Epic 2: Railway to Render Environment Variable Mapping Guide

## Migration Date: 2025-08-16
## Version: 1.0.0

---

## Executive Summary

This document provides a complete mapping of environment variables from Railway to Render platform, ensuring zero-downtime migration for the MarketEdge Platform supporting the £925K Odeon opportunity.

---

## Environment Variable Categories

### 1. Core Application Settings

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `PORT` | 80 | 80 | Caddy proxy port |
| `FASTAPI_PORT` | 8000 | 8000 | FastAPI backend port |
| `ENVIRONMENT` | production | production | No change |
| `DEBUG` | false | false | Keep disabled for production |
| `LOG_LEVEL` | INFO | INFO | Adjust as needed |
| `PROJECT_NAME` | Platform Wrapper | Platform Wrapper | No change |
| `PROJECT_VERSION` | 1.0.0 | 2.0.0 | Updated for migration |
| `API_V1_STR` | /api/v1 | /api/v1 | No change |

### 2. Database Configuration

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `DATABASE_URL` | postgresql://... | Auto-generated | Render auto-populates from database service |
| `DATABASE_URL_TEST` | postgresql://...test | Not needed | Test databases handled separately |

**Render Configuration:**
```yaml
- key: DATABASE_URL
  fromDatabase:
    name: marketedge-postgres
    property: connectionString
```

### 3. Redis Configuration

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `REDIS_URL` | redis://localhost:6379 | Auto-generated | Render auto-populates from Redis service |

**Render Configuration:**
```yaml
- key: REDIS_URL
  fromDatabase:
    name: marketedge-redis
    property: connectionString
```

### 4. Auth0 Configuration ⚠️ SENSITIVE

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `AUTH0_DOMAIN` | dev-g8trhgbfdq2sk2m8.us.auth0.com | Same | Public value |
| `AUTH0_CLIENT_ID` | mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr | Same | Set manually in Render |
| `AUTH0_CLIENT_SECRET` | [REDACTED] | [REDACTED] | **MUST set manually in Render dashboard** |
| `AUTH0_CALLBACK_URL` | https://...vercel.app/callback | https://marketedge-platform.onrender.com/callback | Update to Render domain |

### 5. JWT and Security Configuration

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `JWT_SECRET_KEY` | [REDACTED] | Auto-generated | Render generates secure value |
| `JWT_ALGORITHM` | HS256 | HS256 | No change |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | 30 | No change |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | 7 | No change |

**Render Configuration:**
```yaml
- key: JWT_SECRET_KEY
  generateValue: true  # Render generates secure random value
```

### 6. CORS Configuration

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `CORS_ORIGINS` | JSON array | JSON array | Updated with Render domains |
| `CORS_ALLOWED_ORIGINS` | Comma-separated | Comma-separated | Updated with Render domains |

**Railway Values:**
```
["http://localhost:3000","http://localhost:3001","https://app.zebra.associates","https://frontend-jitpuqzpd-zebraassociates-projects.vercel.app"]
```

**Render Values:**
```
["https://app.zebra.associates","https://marketedge-frontend.onrender.com","http://localhost:3000","http://localhost:3001"]
```

### 7. Rate Limiting Configuration

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `RATE_LIMIT_ENABLED` | true | true | No change |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | 60 | 60 | No change |
| `RATE_LIMIT_BURST_SIZE` | Not set | 10 | New addition for better control |

### 8. Data Layer Configuration (Optional)

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `DATA_LAYER_ENABLED` | false | false | Keep disabled unless needed |
| `DATA_LAYER_SUPABASE__URL` | [If enabled] | [If enabled] | Set manually if enabling |
| `DATA_LAYER_SUPABASE__KEY` | [If enabled] | [If enabled] | Set manually if enabling |

### 9. Caddy Proxy Configuration

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `CADDY_PROXY_MODE` | true | true | Required for multi-service |
| `CADDY_AUTO_HTTPS` | Not set | off | Render handles SSL |

### 10. Multi-tenant Configuration

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `MULTI_TENANT_ENABLED` | Not set | true | Explicitly enabled |
| `DEFAULT_TENANT_ID` | Not set | default | Default tenant identifier |

### 11. Feature Flags

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `FEATURE_USER_MANAGEMENT` | Not set | true | Explicitly enabled |
| `FEATURE_ADMIN_PANEL` | Not set | true | Explicitly enabled |
| `FEATURE_MARKET_EDGE` | Not set | true | Explicitly enabled |
| `FEATURE_CAUSAL_EDGE` | Not set | true | Explicitly enabled |
| `FEATURE_VALUE_EDGE` | Not set | true | Explicitly enabled |

### 12. Monitoring and Performance (New)

| Variable Name | Railway Value | Render Value | Migration Notes |
|--------------|---------------|--------------|-----------------|
| `ENABLE_METRICS` | Not set | true | Enable metrics collection |
| `METRICS_PORT` | Not set | 9090 | Metrics endpoint port |
| `TRACE_ENABLED` | Not set | false | Enable for debugging only |

---

## Migration Steps

### Step 1: Pre-Migration Validation

1. Export current Railway environment variables:
   ```bash
   railway variables export > railway_vars_backup.env
   ```

2. Review sensitive variables that need manual setting:
   - `AUTH0_CLIENT_SECRET`
   - Any API keys not listed in render.yaml

### Step 2: Render Service Creation

1. Create services using render.yaml:
   ```bash
   render blueprint launch
   ```

2. Wait for initial deployment to complete

### Step 3: Manual Variable Configuration

1. Navigate to Render Dashboard > Service > Environment
2. Add the following sensitive variables manually:
   - `AUTH0_CLIENT_SECRET`
   - Any additional API keys

### Step 4: Domain and CORS Updates

1. After Render assigns domain, update:
   - `AUTH0_CALLBACK_URL` with new Render domain
   - `CORS_ORIGINS` and `CORS_ALLOWED_ORIGINS` with Render domains

2. Update Auth0 application settings:
   - Add Render callback URL to allowed callbacks
   - Add Render domain to allowed origins

### Step 5: Validation

1. Check health endpoint:
   ```bash
   curl https://marketedge-platform.onrender.com/health
   ```

2. Test CORS:
   ```javascript
   fetch('https://marketedge-platform.onrender.com/api/v1/health', {
     credentials: 'include',
     headers: { 'Origin': 'https://app.zebra.associates' }
   })
   ```

3. Verify database connectivity in logs
4. Test Auth0 authentication flow

---

## Environment Variable Groups (Render Feature)

Render supports environment variable groups for better organization:

### Group 1: auth0-secrets
```yaml
- name: auth0-secrets
  envVars:
    - key: AUTH0_CLIENT_ID
    - key: AUTH0_CLIENT_SECRET
```

### Group 2: database-secrets
```yaml
- name: database-secrets
  envVars:
    - key: DATABASE_PASSWORD
    - key: REDIS_PASSWORD
```

### Group 3: external-services
```yaml
- name: external-services
  envVars:
    - key: SENTRY_DSN
    - key: DATADOG_API_KEY
    - key: SLACK_WEBHOOK_URL
```

---

## Security Considerations

### Sensitive Variables Handling

1. **Never commit secrets to render.yaml**
   - Use `sync: false` for sensitive variables
   - Set manually in Render dashboard

2. **Use Render's secret generation**
   - JWT_SECRET_KEY auto-generated
   - Database passwords auto-generated

3. **Audit variable access**
   - Review team member permissions
   - Use environment-specific variables

### Variable Rotation Strategy

1. **Regular rotation schedule:**
   - JWT_SECRET_KEY: Every 90 days
   - Auth0 credentials: Every 180 days
   - API keys: Based on provider requirements

2. **Rotation procedure:**
   - Update in Render dashboard
   - Trigger redeployment
   - Verify service health
   - Update documentation

---

## Rollback Plan

If migration issues occur:

1. **Keep Railway running** until Render is fully validated
2. **DNS cutover** only after complete validation
3. **Environment variable backup** maintained for 30 days
4. **Quick rollback procedure:**
   ```bash
   # Point DNS back to Railway
   # Restore Railway environment if modified
   railway up
   ```

---

## Validation Checklist

- [ ] All core application variables mapped
- [ ] Database URLs auto-configured
- [ ] Redis URL auto-configured
- [ ] Auth0 secrets manually set
- [ ] JWT secret generated by Render
- [ ] CORS origins updated with Render domains
- [ ] Feature flags explicitly set
- [ ] Rate limiting configured
- [ ] Health endpoint responding
- [ ] Authentication flow working
- [ ] Database queries successful
- [ ] Redis caching operational

---

## Support and Troubleshooting

### Common Issues and Solutions

1. **Database connection errors**
   - Verify DATABASE_URL is auto-populated
   - Check database service is running
   - Review connection pool settings

2. **CORS errors**
   - Ensure Render domain added to CORS_ALLOWED_ORIGINS
   - Verify Caddy configuration is correct
   - Check preflight request handling

3. **Auth0 callback errors**
   - Update AUTH0_CALLBACK_URL with Render domain
   - Add Render URL to Auth0 allowed callbacks
   - Clear browser cookies and retry

### Contact Information

- **Render Support:** https://render.com/support
- **Render Status:** https://status.render.com
- **Documentation:** https://render.com/docs

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-08-16 | DevOps Team | Initial mapping document |

---

**Document Status:** ACTIVE
**Review Date:** 2025-08-16
**Next Review:** 2025-09-16