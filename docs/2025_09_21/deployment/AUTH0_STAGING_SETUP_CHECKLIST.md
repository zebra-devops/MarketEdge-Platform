# Auth0 Staging Setup Checklist

## Manual Configuration Required

### 1. Create Auth0 Staging Application (5 minutes)

- [ ] Navigate to: https://manage.auth0.com/dashboard/us/dev-g8trhgbfdq2sk2m8/applications
- [ ] Click "Create Application"
- [ ] Name: `MarketEdge-Staging`
- [ ] Type: Single Page Application (SPA)
- [ ] Click "Create"

### 2. Configure Staging Application URIs (3 minutes)

**Allowed Callback URLs:**
```
https://*.onrender.com/callback,https://localhost:3000/callback,https://marketedge-staging-*.onrender.com/callback,https://pr-*-marketedge-platform.onrender.com/callback
```

**Allowed Logout URLs:**
```
https://*.onrender.com/,https://localhost:3000/,https://marketedge-staging-*.onrender.com/,https://pr-*-marketedge-platform.onrender.com/
```

**Allowed Web Origins:**
```
https://*.onrender.com,https://localhost:3000,https://marketedge-staging-*.onrender.com,https://pr-*-marketedge-platform.onrender.com
```

**Allowed Origins (CORS):**
```
https://*.onrender.com,https://localhost:3000,https://marketedge-staging-*.onrender.com,https://pr-*-marketedge-platform.onrender.com
```

- [ ] Save changes in Auth0 dashboard

### 3. Configure Render Environment Variables (5 minutes)

Navigate to: https://dashboard.render.com/web/[service-id]/environment

Add these variables:
- [ ] AUTH0_DOMAIN_STAGING = dev-g8trhgbfdq2sk2m8.us.auth0.com
- [ ] AUTH0_CLIENT_ID_STAGING = [Copy from staging Auth0 app]
- [ ] AUTH0_CLIENT_SECRET_STAGING = [Copy from staging Auth0 app] (mark as secret)
- [ ] AUTH0_AUDIENCE_STAGING = https://api.marketedge-staging.onrender.com

### 4. Testing Verification (5 minutes)

- [ ] Create test PR to trigger preview deployment
- [ ] Access preview URL when ready
- [ ] Test authentication flow: login → callback → dashboard
- [ ] Verify staging Auth0 app is used (check network tab)
- [ ] Confirm production Auth0 unaffected

## Success Criteria

✅ Preview environments use staging Auth0 application
✅ Production Auth0 configuration unchanged
✅ Wildcard redirect URIs support all preview URLs
✅ Authentication flow works in preview environments
✅ No production authentication disruption

## Emergency Rollback

If issues occur:
1. Remove staging environment variables from Render
2. Set USE_STAGING_AUTH0=false in environment variables
3. Verify production authentication restored

## Verification Commands

Test staging configuration:
```bash
# Check environment configuration
curl https://pr-[number]-marketedge-platform.onrender.com/api/v1/config/auth0

# Verify health check
curl https://pr-[number]-marketedge-platform.onrender.com/api/v1/config/health
```

Total setup time: ~15 minutes
Impact: Zero production disruption
