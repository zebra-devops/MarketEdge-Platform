# Environment Configuration Guide - Staging Gate Implementation

**Document Version:** 1.0
**Date:** 2025-10-02
**Prepared By:** Maya (DevOps Engineer)

---

## Quick Reference

### Environment Variable Configuration Locations

| Environment | Backend Config | Frontend Config | Database Config |
|-------------|---------------|-----------------|-----------------|
| **Development** | `.env` file | `.env.local` | Local PostgreSQL |
| **PR Preview** | **render.yaml (NEW)** | Vercel auto-config | Render preview DB |
| **Staging** | **render.yaml + Dashboard secrets** | Vercel Dashboard | **render.yaml (auto-provision)** |
| **Production** | **render.yaml + Dashboard secrets** | Vercel Dashboard | Render production DB |

**IMPORTANT (2025-10-02):** Infrastructure now managed via `/render.yaml` blueprint:
- All environment variables defined in render.yaml (version-controlled)
- Secrets (sync: false) still managed in Render Dashboard for security
- Database resources automatically provisioned from render.yaml
- See: `/docs/deployment/RENDER_YAML_MIGRATION.md` for migration guide

---

## Staging Backend Environment Variables (Render)

### Critical Variables (MUST Configure)

```bash
# Auth0 Configuration
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6
AUTH0_CLIENT_SECRET=<from-secrets-vault>
AUTH0_ACTION_SECRET=<from-secrets-vault>
AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/  # CRITICAL!

# Database & Redis
DATABASE_URL=<staging-database-internal-url>
REDIS_URL=<staging-redis-url>

# JWT Configuration
JWT_SECRET_KEY=<staging-specific-secret-different-from-production>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=staging
DEBUG=true
LOG_LEVEL=DEBUG

# CORS Configuration
CORS_ORIGINS=https://staging.zebra.associates,https://*.vercel.app,http://localhost:3000

# Security
CSRF_ENABLED=false
CADDY_PROXY_MODE=false

# Feature Flags
ENABLE_DEBUG_LOGGING=true
RUN_MIGRATIONS=true

# Monitoring
SENTRY_DSN=<empty-or-staging-sentry-dsn>
```

### Configuration Steps (Render Dashboard)

1. Navigate to: https://dashboard.render.com
2. Select: `marketedge-platform-staging` service
3. Go to: **Environment** tab
4. Click: **Add Environment Variable** for each variable above
5. Click: **Save Changes**
6. Service will automatically redeploy

---

## Staging Frontend Environment Variables (Vercel)

### Configuration for Preview Environment

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=https://marketedge-platform-staging.onrender.com
NEXT_PUBLIC_ENVIRONMENT=staging

# Auth0 Configuration
NEXT_PUBLIC_AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr

# Feature Flags
NEXT_PUBLIC_EPIC_1_ENABLED=true
NEXT_PUBLIC_EPIC_2_ENABLED=true
NEXT_PUBLIC_DEBUG_MODE=true
NEXT_PUBLIC_ENABLE_DEV_TOOLS=true

# Analytics
NEXT_PUBLIC_ANALYTICS_ENV=staging
NEXT_PUBLIC_SENTRY_ENVIRONMENT=staging

# Performance
NEXT_PUBLIC_API_TIMEOUT=60000
NEXT_PUBLIC_MAX_RETRIES=5
```

### Configuration Steps (Vercel Dashboard)

1. Navigate to: https://vercel.com/dashboard
2. Select: Your MarketEdge project
3. Go to: **Settings** → **Environment Variables**
4. For each variable:
   - Add **Name** and **Value**
   - Select environments: **Preview** (for staging branch)
5. Click: **Save**
6. Redeploy staging branch

---

## Production Backend Environment Variables (Render)

### Critical Variables

```bash
# Auth0 Configuration
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6
AUTH0_CLIENT_SECRET=<from-secrets-vault>
AUTH0_ACTION_SECRET=<from-secrets-vault>
AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/  # CRITICAL!

# Database & Redis
DATABASE_URL=<production-database-url>
REDIS_URL=<production-redis-url>

# JWT Configuration
JWT_SECRET_KEY=<production-secret-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# CORS Configuration
CORS_ORIGINS=https://app.zebra.associates,https://platform.marketedge.co.uk,https://staging.zebra.associates,https://*.vercel.app

# Security
CSRF_ENABLED=false  # Enable after 5-min smoke test
CADDY_PROXY_MODE=true

# Feature Flags
ENABLE_DEBUG_LOGGING=false
RUN_MIGRATIONS=true

# Monitoring
SENTRY_DSN=<production-sentry-dsn>
```

---

## Production Frontend Environment Variables (Vercel)

### Configuration for Production Environment

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=https://marketedge-platform.onrender.com
NEXT_PUBLIC_ENVIRONMENT=production

# Auth0 Configuration
NEXT_PUBLIC_AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr

# Feature Flags
NEXT_PUBLIC_EPIC_1_ENABLED=true
NEXT_PUBLIC_EPIC_2_ENABLED=true
NEXT_PUBLIC_DEBUG_MODE=false
NEXT_PUBLIC_ENABLE_DEV_TOOLS=false

# Analytics
NEXT_PUBLIC_ANALYTICS_ENV=production
NEXT_PUBLIC_SENTRY_ENVIRONMENT=production

# Performance
NEXT_PUBLIC_API_TIMEOUT=30000
NEXT_PUBLIC_MAX_RETRIES=3
```

---

## Auth0 Configuration

### Callback URL Configuration

**Navigate to:** https://manage.auth0.com → Applications → MarketEdge Platform → Settings

**Allowed Callback URLs:**
```
http://localhost:3000/callback,
https://app.zebra.associates/callback,
https://platform.marketedge.co.uk/callback,
https://staging.zebra.associates/callback,
https://*.vercel.app/callback,
https://*.onrender.com/callback
```

**Allowed Logout URLs:**
```
http://localhost:3000,
https://app.zebra.associates,
https://platform.marketedge.co.uk,
https://staging.zebra.associates,
https://*.vercel.app,
https://*.onrender.com
```

**Allowed Web Origins:**
```
http://localhost:3000,
https://app.zebra.associates,
https://platform.marketedge.co.uk,
https://staging.zebra.associates,
https://*.vercel.app,
https://*.onrender.com
```

---

## GitHub Secrets Configuration

### Required GitHub Secrets

**Navigate to:** GitHub Repository → Settings → Secrets and variables → Actions

```bash
# Auth0
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6
AUTH0_CLIENT_SECRET=<secret>
AUTH0_ACTION_SECRET=<secret>
AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/

# Test Credentials
ZEBRA_TEST_EMAIL=matt.lindop@zebra.associates
ZEBRA_TEST_PASSWORD=<secret>

# JWT
JWT_SECRET_KEY=<secret>

# Optional: Render API (for automated deployments)
RENDER_API_KEY=<secret>

# Optional: Vercel Token (for automated deployments)
VERCEL_TOKEN=<secret>
```

---

## DNS Configuration

### Custom Domain Setup

#### Staging Backend: staging-api.zebra.associates

**DNS Provider Configuration:**
```
Type: CNAME
Name: staging-api
Value: marketedge-platform-staging.onrender.com
TTL: 300 (5 minutes)
```

**Render Configuration:**
1. Render Dashboard → Staging Service → Settings → Custom Domain
2. Add domain: `staging-api.zebra.associates`
3. Wait for SSL certificate (automatic)

#### Staging Frontend: staging.zebra.associates

**DNS Provider Configuration:**
```
Type: CNAME
Name: staging
Value: cname.vercel-dns.com
TTL: 300 (5 minutes)
```

**Vercel Configuration:**
1. Vercel Dashboard → Project → Settings → Domains
2. Add domain: `staging.zebra.associates`
3. Assign to branch: `staging`
4. Wait for SSL certificate (automatic)

---

## Environment Variables Security Best Practices

### DO NOT

- ❌ Commit secrets to git
- ❌ Use production secrets in staging
- ❌ Share secrets via email/Slack
- ❌ Use weak JWT secret keys

### DO

- ✅ Use secrets vault (1Password, AWS Secrets Manager)
- ✅ Rotate secrets regularly
- ✅ Use different secrets per environment
- ✅ Document secret locations securely
- ✅ Use GitHub Secrets for CI/CD

---

## Verification Checklist

### After Staging Configuration

- [ ] All environment variables set in Render
- [ ] All environment variables set in Vercel
- [ ] Auth0 callback URLs updated
- [ ] DNS records configured
- [ ] SSL certificates provisioned
- [ ] Health endpoint returns 200 OK
- [ ] Authentication flow works end-to-end
- [ ] Database connection successful
- [ ] Redis connection successful
- [ ] CORS headers present in responses

### After Production Configuration

- [ ] All environment variables set in Render
- [ ] All environment variables set in Vercel
- [ ] Production Auth0 callback URLs verified
- [ ] Production DNS records verified
- [ ] Production SSL certificates valid
- [ ] Production health endpoint returns 200 OK
- [ ] Zebra Associates user can login
- [ ] Super admin panel accessible
- [ ] No errors in production logs
- [ ] Monitoring and alerting configured

---

## Troubleshooting

### Issue: AUTH0_AUDIENCE not set

**Symptoms:**
- Auth0 returns opaque tokens
- JWT verification fails
- "Invalid token" errors

**Solution:**
```bash
# Set in Render Dashboard
AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/

# Verify in Auth0 URL response
curl "https://backend-url/api/v1/auth/auth0-url?redirect_uri=..."
# Should include: &audience=https%3A%2F%2F...
```

### Issue: CORS errors

**Symptoms:**
- Browser shows "No 'Access-Control-Allow-Origin'"
- API requests blocked

**Solution:**
```bash
# Update CORS_ORIGINS in Render
CORS_ORIGINS=https://frontend-domain,https://*.vercel.app

# Verify CORS headers
curl -H "Origin: https://frontend-domain" -I https://backend-url/health
```

### Issue: Database connection failed

**Symptoms:**
- "Connection refused" errors
- Application won't start

**Solution:**
```bash
# Verify DATABASE_URL format
postgresql://user:password@host:5432/database

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-02
**Status:** ✅ Complete
