# Staging Deployment Runbook: staging.zebra.associates

## Quick Reference

**Objective**: Deploy complete staging environment for MarketEdge Platform
**Domain**: staging.zebra.associates
**Estimated Time**: 45-60 minutes (initial setup)
**Prerequisites**: Render account, Vercel account, Google Domains access

## Pre-Deployment Checklist

- [ ] Render staging service created and configured
- [ ] Vercel project configured for staging deployment
- [ ] Auth0 staging application configured
- [ ] Google Domains access confirmed
- [ ] Backend environment variables ready
- [ ] Frontend environment variables ready
- [ ] Staging database provisioned

## Deployment Sequence

### Phase 1: Backend Deployment (Render)

#### 1.1 Create/Verify Render Service

**Service Configuration**:
```yaml
Service Name: marketedge-platform-staging
Environment: staging
Region: Oregon (US West) or Frankfurt (EU Central)
Plan: Standard or higher (for custom domains)
Branch: staging or main
Root Directory: /
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### 1.2 Configure Environment Variables

**Required Environment Variables**:
```bash
# Database
DATABASE_URL=postgresql://[staging-db-url]
DATABASE_HOST=[staging-db-host]
DATABASE_PORT=5432
DATABASE_NAME=marketedge_staging
DATABASE_USER=[staging-user]
DATABASE_PASSWORD=[staging-password]

# Redis
REDIS_URL=redis://[staging-redis-url]

# Auth0
AUTH0_DOMAIN=marketedge.eu.auth0.com
AUTH0_CLIENT_ID=[staging-client-id]
AUTH0_CLIENT_SECRET=[staging-client-secret]
AUTH0_AUDIENCE=https://api.marketedge.com
AUTH0_API_IDENTIFIER=https://api.marketedge.com
AUTH0_CALLBACK_URL=https://staging.zebra.associates/api/auth/callback
AUTH0_ACTION_SECRET=[staging-action-secret]
AUTH0_JWKS_URL=https://marketedge.eu.auth0.com/.well-known/jwks.json

# Application
ENVIRONMENT=staging
DEBUG=true
LOG_LEVEL=DEBUG
SECRET_KEY=[generate-new-secret]
FRONTEND_URL=https://staging.zebra.associates
BACKEND_URL=https://marketedge-platform-staging.onrender.com

# CORS
CORS_ORIGINS=https://staging.zebra.associates,http://localhost:3000

# Feature Flags
ENABLE_FEATURE_FLAGS=true
ENABLE_ANALYTICS=true
ENABLE_MONITORING=true
```

#### 1.3 Deploy Backend

```bash
# Trigger deployment via Render dashboard or Git push
git checkout staging
git push origin staging

# Monitor deployment logs
# Navigate to: Render Dashboard > Services > marketedge-platform-staging > Logs
```

#### 1.4 Verify Backend Deployment

```bash
# Check health endpoint
curl https://marketedge-platform-staging.onrender.com/health

# Expected response:
# {"status":"healthy","environment":"staging",...}

# Check API documentation
curl https://marketedge-platform-staging.onrender.com/docs
# Should return 200 OK
```

### Phase 2: Frontend Deployment (Vercel)

#### 2.1 Configure Vercel Project

**Project Settings**:
```yaml
Project Name: marketedge-staging
Framework Preset: Next.js
Root Directory: platform-wrapper/frontend
Build Command: npm run build
Output Directory: .next
Install Command: npm install
Node Version: 20.x
```

#### 2.2 Set Environment Variables in Vercel

**Production Environment Variables** (for staging environment):
```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://marketedge-platform-staging.onrender.com
NEXT_PUBLIC_ENVIRONMENT=staging

# Auth0 Configuration
NEXT_PUBLIC_AUTH0_DOMAIN=marketedge.eu.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=[staging-client-id]
NEXT_PUBLIC_AUTH0_REDIRECT_URI=https://staging.zebra.associates/api/auth/callback
NEXT_PUBLIC_AUTH0_AUDIENCE=https://api.marketedge.com

# Backend Auth0 Secrets (for server-side)
AUTH0_CLIENT_SECRET=[staging-client-secret]
AUTH0_SECRET=[generate-new-secret]

# Application
NEXT_PUBLIC_APP_NAME=MarketEdge Platform (Staging)
VERCEL_ENV=production  # Vercel's "production" deployment for staging branch
```

#### 2.3 Deploy Frontend

```bash
# From project root
cd platform-wrapper/frontend

# Deploy to Vercel
vercel --prod --env=staging

# Or configure Git integration:
# Vercel Dashboard > Project > Settings > Git
# Production Branch: staging
```

#### 2.4 Verify Frontend Deployment

```bash
# Check Vercel deployment URL
curl -I https://marketedge-staging.vercel.app

# Should return 200 OK
```

### Phase 3: DNS Configuration (Google Domains)

#### 3.1 Add DNS Record

**Steps**:
1. Log into Google Domains: https://domains.google.com
2. Navigate to: My domains > zebra.associates > DNS
3. Scroll to: Custom resource records
4. Add new record:
   - **Host name**: staging
   - **Type**: CNAME
   - **TTL**: 300 (5 minutes for testing)
   - **Data**: cname.vercel-dns.com

#### 3.2 Verify DNS Record Created

```bash
# Check in Google Domains interface
# Should show: staging.zebra.associates CNAME cname.vercel-dns.com

# Save changes and wait for propagation (5-30 minutes)
```

### Phase 4: Vercel Custom Domain Configuration

#### 4.1 Add Custom Domain in Vercel

**Steps**:
1. Navigate to Vercel Dashboard
2. Select project: marketedge-staging
3. Go to: Settings > Domains
4. Add domain: `staging.zebra.associates`
5. Click "Add"

#### 4.2 Verify Domain Configuration

Vercel will:
- Detect CNAME record automatically
- Provision SSL certificate (Let's Encrypt)
- Configure edge network routing

**Expected Status**: "Valid Configuration" with SSL certificate icon

### Phase 5: Auth0 Configuration Updates

#### 5.1 Update Auth0 Application Settings

**Navigate to**: Auth0 Dashboard > Applications > MarketEdge Platform (Staging)

**Add to Application URIs**:
```
Allowed Callback URLs:
https://staging.zebra.associates/api/auth/callback

Allowed Logout URLs:
https://staging.zebra.associates

Allowed Web Origins:
https://staging.zebra.associates

Allowed Origins (CORS):
https://staging.zebra.associates
```

#### 5.2 Test Auth0 Configuration

```bash
# Test authorization endpoint
curl "https://marketedge.eu.auth0.com/authorize?client_id=[client-id]&redirect_uri=https://staging.zebra.associates/api/auth/callback&response_type=code"

# Should redirect or return HTML (not 404)
```

## Verification Procedures

### DNS Propagation Check

```bash
# Wait 5-30 minutes after DNS configuration
dig staging.zebra.associates +short
# Expected: cname.vercel-dns.com

# Check from Google DNS
dig @8.8.8.8 staging.zebra.associates +short

# Check from Cloudflare DNS
dig @1.1.1.1 staging.zebra.associates +short

# Use online tool for global verification
# https://www.whatsmydns.net/#CNAME/staging.zebra.associates
```

### SSL Certificate Verification

```bash
# Check SSL certificate (after DNS propagation)
curl -vI https://staging.zebra.associates 2>&1 | grep -E "(subject|issuer|expire)"

# Expected issuer: Let's Encrypt
# Expected subject: staging.zebra.associates
```

### Full Stack Health Check

```bash
# 1. Frontend accessibility
curl -I https://staging.zebra.associates
# Expected: 200 OK

# 2. Backend health endpoint (through frontend proxy)
curl https://staging.zebra.associates/api/health
# Expected: {"status":"healthy",...}

# 3. Backend direct access
curl https://marketedge-platform-staging.onrender.com/health
# Expected: {"status":"healthy",...}

# 4. Auth0 integration
curl -I https://staging.zebra.associates/login
# Should return 200 or redirect to Auth0
```

### End-to-End Integration Test

**Manual Testing Checklist**:
- [ ] Open https://staging.zebra.associates in browser
- [ ] Homepage loads without errors
- [ ] Click "Login" button
- [ ] Redirects to Auth0 login page
- [ ] Log in with test credentials
- [ ] Redirects back to staging.zebra.associates
- [ ] User session established
- [ ] Dashboard loads with data
- [ ] API calls succeed (check Network tab)
- [ ] No CORS errors in console
- [ ] Logout works correctly

## Post-Deployment Tasks

### Update Documentation

- [ ] Update README with staging environment details
- [ ] Document staging credentials in secure location
- [ ] Update deployment runbook with any lessons learned
- [ ] Create staging environment diagram

### Configure Monitoring

```bash
# Set up Vercel Analytics
# Navigate to: Vercel Dashboard > Project > Analytics

# Set up uptime monitoring (external service)
# Examples: UptimeRobot, Pingdom, StatusCake
# Monitor: https://staging.zebra.associates/health
```

### Increase DNS TTL

```bash
# After verification (24-48 hours), increase TTL for performance
# Google Domains > zebra.associates > DNS
# Update staging CNAME TTL: 300 → 3600 (1 hour)
```

### Configure Backup Strategy

- [ ] Database: Daily backups of staging database
- [ ] Code: Git branches protected (staging branch)
- [ ] Environment variables: Securely documented
- [ ] SSL certificates: Auto-renewed by Vercel/Render

## Rollback Procedures

### DNS Rollback
```bash
# If staging needs to be taken down:
# Google Domains > DNS > Delete staging CNAME record
# Propagation: 5-30 minutes
```

### Backend Rollback
```bash
# Render Dashboard > Service > Rollback
# Select previous deployment
# Or redeploy from Git:
git checkout staging
git reset --hard [previous-commit]
git push origin staging --force
```

### Frontend Rollback
```bash
# Vercel Dashboard > Deployments
# Find previous successful deployment
# Click "..." > Promote to Production
```

## Troubleshooting

### Issue: DNS Not Resolving After 30 Minutes

**Check**:
```bash
dig staging.zebra.associates +trace
```

**Solution**:
- Verify CNAME record in Google Domains
- Check for typos in record data
- Contact Google Domains support

### Issue: SSL Certificate Not Provisioning

**Check**: Vercel domain status

**Solution**:
- Ensure DNS is resolving correctly
- Wait up to 60 minutes
- Remove and re-add domain in Vercel

### Issue: 500 Errors on Backend

**Check**: Render logs
```bash
# Render Dashboard > Logs
# Look for errors in application startup
```

**Common Causes**:
- Missing environment variables
- Database connection failure
- Invalid Auth0 configuration

### Issue: CORS Errors

**Check**: Browser console and Network tab

**Solution**:
- Verify CORS_ORIGINS in backend includes staging URL
- Ensure middleware order correct (CORS first)
- Check preflight requests succeed

### Issue: Auth0 Redirect Errors

**Check**: Auth0 application settings

**Solution**:
- Verify callback URLs match exactly
- Check Auth0 client ID/secret
- Ensure Auth0 application enabled

## Maintenance Schedule

**Daily**:
- Monitor uptime and performance
- Check error logs for issues

**Weekly**:
- Review SSL certificate status
- Verify backups completing

**Monthly**:
- Test rollback procedures
- Update dependencies
- Review and optimize TTL values

**Quarterly**:
- Full disaster recovery test
- Security audit
- Performance optimization review

## Contact Information

**Technical Support**:
- Vercel: support@vercel.com
- Render: support@render.com
- Google Domains: Support via dashboard
- Auth0: support@auth0.com

**Internal Contacts**:
- DevOps Lead: Maya
- Development Team: dev agent
- QA Team: qa-orch agent

## Success Criteria

- [ ] Backend deployed and healthy on Render
- [ ] Frontend deployed on Vercel
- [ ] DNS resolving to Vercel
- [ ] SSL certificate active
- [ ] Auth0 integration working
- [ ] Full authentication flow functional
- [ ] API calls succeeding
- [ ] No CORS errors
- [ ] Monitoring configured
- [ ] Documentation updated

---

Document Version: 1.0
Last Updated: October 3, 2025
Author: Maya (DevOps Engineer)
Status: Ready for Production