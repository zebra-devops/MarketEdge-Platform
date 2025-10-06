# Staging Environment Operations Guide

**Quick Reference for MarketEdge Platform Staging Operations**

---

## Environment Overview

| Component | URL | Status |
|-----------|-----|--------|
| Frontend | https://staging.zebra.associates | ✅ Live |
| Backend API | https://marketedge-platform-staging.onrender.com | ✅ Live |
| Auth0 Domain | dev-g8trhgbfdq2sk2m8.us.auth0.com | ✅ Configured |
| Client ID | 9FRjf82esKN4fx3iY337CT1jpvNVFbAP | Staging |

---

## Quick Health Checks

### Frontend Health Check
```bash
curl -I https://staging.zebra.associates
# Expect: HTTP/2 200
```

### Backend Health Check
```bash
curl -s https://marketedge-platform-staging.onrender.com/health | jq '.status'
# Expect: "healthy"
```

### DNS Check
```bash
dig staging.zebra.associates +short
# Expect: cname.vercel-dns.com and IP addresses
```

### Full Backend Health Details
```bash
curl -s https://marketedge-platform-staging.onrender.com/health | jq '.'
```

---

## Common Operations

### Deploy New Version

```bash
# Navigate to frontend directory
cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend

# Deploy to Vercel
vercel deploy --yes

# Get deployment URL from output, then create alias
vercel alias set <deployment-url> staging.zebra.associates
```

### Update Environment Variables

```bash
# List current variables
vercel env ls

# Remove variable
vercel env rm <VARIABLE_NAME> preview --yes

# Add new variable
echo "<value>" | vercel env add <VARIABLE_NAME> preview

# Pull variables locally
vercel env pull .env.vercel --environment=preview
```

### View Deployment Logs

```bash
# View logs for specific deployment
vercel logs <deployment-url>

# Or view logs via dashboard
# Visit: https://vercel.com/zebraassociates-projects/frontend
```

### Rollback Deployment

```bash
# List recent deployments
vercel list

# Alias previous deployment
vercel alias set <previous-deployment-url> staging.zebra.associates
```

---

## Testing Authentication

### Test Login Flow

1. Navigate to: https://staging.zebra.associates
2. Click "Login" button
3. Should redirect to Auth0 login page
4. Enter credentials
5. Should redirect back to: https://staging.zebra.associates/api/auth/callback
6. Should be logged in and see dashboard

### Verify Auth0 Configuration

Required settings in Auth0 dashboard:

**Allowed Callback URLs:**
```
https://staging.zebra.associates/api/auth/callback
https://staging.zebra.associates/callback
```

**Allowed Logout URLs:**
```
https://staging.zebra.associates
https://staging.zebra.associates/login
```

**Allowed Web Origins:**
```
https://staging.zebra.associates
```

**Allowed Origins (CORS):**
```
https://staging.zebra.associates
https://marketedge-platform-staging.onrender.com
```

---

## Monitoring & Debugging

### Check Build Status

```bash
# View recent deployments
vercel list

# Check specific deployment
vercel inspect <deployment-url>
```

### Debug Environment Variables

```bash
# Pull current environment variables
cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend
vercel env pull .env.vercel.debug --environment=preview

# View variables
cat .env.vercel.debug | grep -E "API|AUTH0"
```

### Check Backend Services

```bash
# Full health check with service status
curl -s https://marketedge-platform-staging.onrender.com/health | jq '{
  status: .status,
  database: .services.database,
  redis: .services.redis,
  cold_start_time: .cold_start_time
}'
```

### Test API Endpoints

```bash
# Test public endpoints
curl -I https://marketedge-platform-staging.onrender.com/api/v1/health

# Test authenticated endpoints (requires token)
curl -H "Authorization: Bearer <token>" \
     https://marketedge-platform-staging.onrender.com/api/v1/organizations
```

---

## Configuration Files

### Key Files

| File | Purpose | Location |
|------|---------|----------|
| `.env.staging` | Staging environment variables | `/platform-wrapper/frontend/.env.staging` |
| `vercel-staging.json` | Vercel staging configuration | `/platform-wrapper/frontend/vercel-staging.json` |
| `vercel.json` | Main Vercel configuration | `/platform-wrapper/frontend/vercel.json` |

### Update Configuration

```bash
# Edit staging environment file
vi /Users/matt/Sites/MarketEdge/platform-wrapper/frontend/.env.staging

# Edit Vercel configuration
vi /Users/matt/Sites/MarketEdge/platform-wrapper/frontend/vercel-staging.json

# Commit changes
git add platform-wrapper/frontend/.env.staging platform-wrapper/frontend/vercel-staging.json
git commit -m "config: update staging configuration"

# Deploy with new configuration
cd platform-wrapper/frontend
vercel deploy --yes
```

---

## Troubleshooting

### Issue: Frontend Shows Loading Spinner Forever

**Possible Causes:**
1. API URL incorrect
2. CORS error
3. Backend down
4. Auth0 configuration missing

**Debug Steps:**
```bash
# Check browser console for errors
# Open: https://staging.zebra.associates
# Open Developer Tools → Console tab
# Look for CORS or API errors

# Verify API URL
vercel env pull .env.debug --environment=preview
cat .env.debug | grep NEXT_PUBLIC_API_BASE_URL

# Test backend directly
curl -s https://marketedge-platform-staging.onrender.com/health | jq '.status'
```

### Issue: Authentication Fails

**Possible Causes:**
1. Auth0 callback URLs not configured
2. Client ID mismatch
3. Auth0 application not configured

**Debug Steps:**
```bash
# Verify Auth0 Client ID
vercel env pull .env.debug --environment=preview
cat .env.debug | grep NEXT_PUBLIC_AUTH0_CLIENT_ID

# Should output: 9FRjf82esKN4fx3iY337CT1jpvNVFbAP

# Check Auth0 dashboard:
# https://manage.auth0.com/dashboard
# Navigate to Applications → MarketEdge Staging
# Verify callback URLs are configured
```

### Issue: 404 Errors on API Calls

**Possible Causes:**
1. API routes not deployed
2. Backend endpoint incorrect
3. CORS blocking requests

**Debug Steps:**
```bash
# Test backend endpoint directly
curl -I https://marketedge-platform-staging.onrender.com/api/v1/organizations

# Check CORS headers
curl -I -H "Origin: https://staging.zebra.associates" \
     https://marketedge-platform-staging.onrender.com/api/v1/organizations

# Verify API base URL
vercel env pull .env.debug --environment=preview
cat .env.debug | grep NEXT_PUBLIC_API_BASE_URL
```

### Issue: Slow Loading Times

**Possible Causes:**
1. Render cold start (expected for staging)
2. Large bundle size
3. Network latency

**Debug Steps:**
```bash
# Check backend cold start time
curl -s https://marketedge-platform-staging.onrender.com/health | jq '.cold_start_time'

# First request after inactivity will show ~2-3s
# Subsequent requests should be faster

# Check bundle size
cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend
npm run build
# Review bundle size output
```

---

## Performance Optimization

### Frontend Optimization

```bash
# Analyze bundle size
cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend
npm run build

# Check for large dependencies
npm list --depth=0

# Consider code splitting and lazy loading
# Review Next.js documentation for optimization strategies
```

### Backend Optimization

**Note:** Render staging tier has cold start delays. This is expected behavior.

**Options:**
1. Upgrade Render plan to keep service warm
2. Implement cron job to ping health endpoint every 10 minutes
3. Accept cold start delay for staging (recommended)

---

## Security Checklist

### Before User Testing

- [ ] Auth0 callback URLs configured
- [ ] HTTPS enforced on all endpoints
- [ ] Environment variables secured (not exposed in client)
- [ ] CORS properly configured
- [ ] Security headers applied
- [ ] Test users created in Auth0
- [ ] Database access restricted
- [ ] API rate limiting configured

### Regular Security Audits

```bash
# Check security headers
curl -I https://staging.zebra.associates | grep -E "X-Frame-Options|X-Content-Type-Options|Referrer-Policy"

# Verify HTTPS redirect
curl -I http://staging.zebra.associates
# Should return 301/308 redirect to HTTPS

# Test CORS configuration
curl -I -H "Origin: https://evil.com" \
     https://marketedge-platform-staging.onrender.com/health
# Should not include Access-Control-Allow-Origin: https://evil.com
```

---

## Useful Links

### Vercel Dashboard
- Project: https://vercel.com/zebraassociates-projects/frontend
- Deployments: https://vercel.com/zebraassociates-projects/frontend/deployments
- Domains: https://vercel.com/zebraassociates-projects/domains

### Render Dashboard
- Service: https://dashboard.render.com/
- Logs: Check Render dashboard for backend logs

### Auth0 Dashboard
- Application: https://manage.auth0.com/dashboard
- Navigate to: Applications → MarketEdge Staging

### Repository
- GitHub: https://github.com/zebraassociates/MarketEdge
- Documentation: /docs/2025_10_06/deployment/

---

## Emergency Contacts

**DevOps Support:** Maya (Claude Code Agent)
**Auth0 Configuration:** Check Auth0 dashboard or contact account admin
**DNS Issues:** Google Domains support
**Vercel Support:** support@vercel.com
**Render Support:** support@render.com

---

## Deployment Checklist

Use this checklist for each new deployment:

### Pre-Deployment
- [ ] Code changes committed and pushed to Git
- [ ] All tests passing locally
- [ ] Environment variables reviewed
- [ ] Breaking changes documented
- [ ] Rollback plan prepared

### Deployment
- [ ] Run `vercel deploy --yes`
- [ ] Verify deployment URL loads correctly
- [ ] Check for build errors
- [ ] Run health checks
- [ ] Create alias to staging.zebra.associates

### Post-Deployment
- [ ] Frontend accessible via HTTPS
- [ ] Backend health check passes
- [ ] Authentication flow tested
- [ ] Key user flows tested
- [ ] No console errors in browser
- [ ] Document any issues encountered

### Monitoring
- [ ] Check deployment logs for errors
- [ ] Monitor error rates in first hour
- [ ] Verify performance metrics acceptable
- [ ] Confirm monitoring alerts working

---

**Last Updated:** October 6, 2025
**Version:** 1.0
**Maintainer:** DevOps Team
