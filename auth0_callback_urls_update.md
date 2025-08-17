# Auth0 Callback URLs Configuration Guide

## Current Required Callback URLs

Update your Auth0 Application settings to include ALL these callback URLs:

```
https://app.zebra.associates/callback
https://frontend-2q61uheqm-zebraassociates-projects.vercel.app/callback
https://frontend-79pvaaolp-zebraassociates-projects.vercel.app/callback
http://localhost:3000/callback
http://localhost:3001/callback
```

## How to Update Auth0 Settings

1. **Go to Auth0 Dashboard**: https://manage.auth0.com
2. **Navigate to Applications** → Select your MarketEdge application
3. **Settings Tab** → Find "Allowed Callback URLs"
4. **Update the field** to include all URLs above (comma-separated)
5. **Save Changes**

## Current Issues Resolved

- ✅ **app.zebra.associates**: CORS fix deployed (error handler now includes CORS headers)
- ✅ **frontend-2q61uheqm**: Already working, timeout fixes deployed
- ❌ **frontend-79pvaaolp**: "Callback URL mismatch" - needs Auth0 update

## Testing After Update

Test each URL after updating Auth0:

```bash
# Test app.zebra.associates (should work after Render deployment)
curl -X POST "https://marketedge-platform.onrender.com/api/v1/auth/login" \
  -H "Origin: https://app.zebra.associates" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "code=test&redirect_uri=https://app.zebra.associates/callback"

# Test frontend-79pvaaolp (should work after Auth0 update)
curl "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://frontend-79pvaaolp-zebraassociates-projects.vercel.app/callback" \
  -H "Origin: https://frontend-79pvaaolp-zebraassociates-projects.vercel.app"

# Test frontend-2q61uheqm (should already work)
curl "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://frontend-2q61uheqm-zebraassociates-projects.vercel.app/callback" \
  -H "Origin: https://frontend-2q61uheqm-zebraassociates-projects.vercel.app"
```

## Timeline

1. **5-10 minutes**: Render deployment completes (CORS fix)
2. **Manual**: Update Auth0 callback URLs
3. **Immediate**: Test all three frontend URLs

The CORS errors should be resolved once Render deploys the error handler fix.