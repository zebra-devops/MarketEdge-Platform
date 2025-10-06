# DNS Configuration Guide for staging.zebra.associates

## Current DNS Infrastructure Analysis

### DNS Provider Information
- **Provider**: Google Domains / Google Cloud DNS
- **Nameservers**:
  - ns-cloud-d1.googledomains.com
  - ns-cloud-d2.googledomains.com
  - ns-cloud-d3.googledomains.com
  - ns-cloud-d4.googledomains.com

### Current Production Configuration
- **Domain**: app.zebra.associates
- **Type**: CNAME record
- **Target**: cname.vercel-dns.com
- **Resolution**: 76.76.21.61, 76.76.21.241 (Vercel IPs)
- **Status**: Active and resolving correctly

### Staging Service Status
- **Backend Service**: marketedge-platform-staging.onrender.com
- **Current Status**: Service not deployed (404 response)
- **Production Service**: marketedge-platform.onrender.com (healthy)

## Recommended DNS Configuration

### Option 1: Full Stack on Vercel (RECOMMENDED)
This approach mirrors the production setup and provides the best performance and consistency.

#### DNS Records to Create:
```dns
staging.zebra.associates    CNAME    cname.vercel-dns.com    TTL: 300
```

#### Vercel Configuration:
1. Deploy frontend to Vercel with project name: `marketedge-staging`
2. Add custom domain in Vercel Dashboard: `staging.zebra.associates`
3. Configure environment variables in Vercel:
   ```
   NEXT_PUBLIC_API_URL=https://marketedge-platform-staging.onrender.com
   NEXT_PUBLIC_AUTH0_DOMAIN=marketedge.eu.auth0.com
   NEXT_PUBLIC_AUTH0_CLIENT_ID=[staging-client-id]
   NEXT_PUBLIC_AUTH0_REDIRECT_URI=https://staging.zebra.associates/api/auth/callback
   ```

### Option 2: Separate Backend/Frontend Subdomains
This approach provides clear separation between services but requires more DNS management.

#### DNS Records to Create:
```dns
staging.zebra.associates         CNAME    cname.vercel-dns.com              TTL: 300
staging-api.zebra.associates     CNAME    marketedge-platform-staging.onrender.com    TTL: 300
```

#### Configuration:
- Frontend accesses backend via: `https://staging-api.zebra.associates`
- Clear separation of concerns
- Independent scaling and deployment

### Option 3: Direct Backend Access (Development Only)
For backend-only testing without frontend deployment.

#### DNS Records to Create:
```dns
staging-api.zebra.associates    CNAME    marketedge-platform-staging.onrender.com    TTL: 300
```

## SSL/TLS Certificate Configuration

### Vercel (Frontend)
- **Automatic**: Vercel automatically provisions and renews Let's Encrypt certificates
- **No action required**: Certificate issued within minutes of domain verification
- **Features**: Auto-renewal, wildcard support, HTTP/2

### Render (Backend)
1. Navigate to Render Dashboard → Your Service → Settings → Custom Domains
2. Add custom domain: `staging-api.zebra.associates` (if using separate subdomain)
3. Render will automatically:
   - Provision Let's Encrypt certificate
   - Configure SSL termination
   - Enable auto-renewal

## Implementation Steps

### Step 1: Deploy Backend to Render Staging
```bash
# Ensure staging service is deployed on Render
# Service Name: marketedge-platform-staging
# Branch: staging or main
# Environment: staging
```

### Step 2: Deploy Frontend to Vercel
```bash
# From platform-wrapper/frontend directory
vercel --prod --env=staging
```

### Step 3: Configure DNS in Google Domains
1. Log into Google Domains dashboard
2. Navigate to DNS settings for zebra.associates
3. Add CNAME record:
   - Host: `staging`
   - Type: `CNAME`
   - Data: `cname.vercel-dns.com`
   - TTL: `300` (5 minutes for testing, increase to 3600 later)

### Step 4: Configure Vercel Domain
1. Go to Vercel Dashboard → Project Settings → Domains
2. Add domain: `staging.zebra.associates`
3. Vercel will verify DNS and provision SSL certificate

### Step 5: Update Auth0 Configuration
Add to Auth0 Application Settings:
- Allowed Callback URLs: `https://staging.zebra.associates/api/auth/callback`
- Allowed Logout URLs: `https://staging.zebra.associates`
- Allowed Web Origins: `https://staging.zebra.associates`

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   DNS Resolution Flow                    │
└─────────────────────────────────────────────────────────┘

User Request: staging.zebra.associates
         ↓
Google Cloud DNS (NS Records)
         ↓
CNAME: staging.zebra.associates → cname.vercel-dns.com
         ↓
Vercel Edge Network (Global CDN)
         ├── Frontend: Next.js Application
         │   └── API Calls → Backend
         └── SSL: Let's Encrypt Certificate
                    ↓
Backend API: marketedge-platform-staging.onrender.com
         ├── FastAPI Application
         ├── PostgreSQL Database (Staging)
         └── Redis Cache (Staging)

┌─────────────────────────────────────────────────────────┐
│                  Service Architecture                     │
└─────────────────────────────────────────────────────────┘

staging.zebra.associates (Vercel)
├── Next.js Frontend
│   ├── /app (App Router)
│   ├── /api/auth (Auth0 callbacks)
│   └── Static Assets (CDN cached)
│
├── Environment Variables
│   ├── NEXT_PUBLIC_API_URL → Backend
│   ├── AUTH0_* → Authentication
│   └── VERCEL_ENV=staging
│
└── API Integration
    └── marketedge-platform-staging.onrender.com
        ├── /api/v1/* (REST endpoints)
        ├── /health (Health check)
        └── /docs (OpenAPI documentation)
```

## Verification Checklist

### DNS Propagation (5-30 minutes)
```bash
# Check DNS propagation
dig staging.zebra.associates +short
# Expected: cname.vercel-dns.com

# Check from multiple DNS servers
dig @8.8.8.8 staging.zebra.associates +short
dig @1.1.1.1 staging.zebra.associates +short

# Use online tool
# https://www.whatsmydns.net/#CNAME/staging.zebra.associates
```

### SSL Certificate Verification
```bash
# Check SSL certificate
openssl s_client -connect staging.zebra.associates:443 -servername staging.zebra.associates < /dev/null 2>/dev/null | openssl x509 -noout -dates

# Check certificate chain
curl -vI https://staging.zebra.associates 2>&1 | grep -E "(SSL|certificate|issuer)"
```

### Backend Health Check
```bash
# Direct backend check (if deployed)
curl https://marketedge-platform-staging.onrender.com/health

# Through custom domain (if configured)
curl https://staging-api.zebra.associates/health
```

### Frontend Accessibility
```bash
# Check frontend response
curl -I https://staging.zebra.associates

# Check specific pages
curl -I https://staging.zebra.associates/login
curl -I https://staging.zebra.associates/dashboard
```

### Auth0 Callback Testing
```bash
# Verify Auth0 redirects work
curl -I "https://staging.zebra.associates/api/auth/callback?code=test"
# Should return 302 or 400 (not 404)
```

### Full Stack Integration Test
```bash
# Test complete flow
curl https://staging.zebra.associates/api/health
# Should proxy to backend and return health status
```

## Troubleshooting Guide

### Issue: DNS Not Resolving
- **Check**: TTL may not have expired (wait up to 5 minutes)
- **Solution**: Clear DNS cache
  ```bash
  # macOS
  sudo dscacheutil -flushcache
  # Linux
  sudo systemd-resolve --flush-caches
  ```

### Issue: SSL Certificate Error
- **Check**: Certificate may still be provisioning
- **Solution**: Wait 5-10 minutes, Vercel/Render auto-provisions certificates

### Issue: 404 on Backend
- **Check**: Render service deployment status
- **Solution**: Ensure staging service is deployed and running on Render

### Issue: CORS Errors
- **Check**: Backend CORS configuration
- **Solution**: Update CORS allowed origins to include `https://staging.zebra.associates`

### Issue: Auth0 Redirect Errors
- **Check**: Auth0 application settings
- **Solution**: Add staging URLs to allowed callbacks/origins

## Maintenance Recommendations

1. **TTL Management**:
   - Testing: 300 seconds (5 minutes)
   - Production: 3600 seconds (1 hour)

2. **Monitoring**:
   - Set up uptime monitoring for staging.zebra.associates
   - Configure alerts for SSL certificate expiry (though auto-renewed)
   - Monitor backend health endpoint

3. **Regular Verification**:
   - Weekly: Check SSL certificate validity
   - Monthly: Verify DNS resolution from multiple regions
   - Quarterly: Review and update DNS TTL values

## Contact Information

- **DNS Provider**: Google Domains Support
- **Frontend Hosting**: Vercel Support (support@vercel.com)
- **Backend Hosting**: Render Support (support@render.com)
- **Domain Owner**: Zebra Associates

## Next Steps

1. **Immediate**: Deploy backend service to Render staging environment
2. **Next**: Deploy frontend to Vercel with staging configuration
3. **Then**: Configure DNS CNAME record in Google Domains
4. **Finally**: Verify all endpoints and update Auth0 settings

---

Document Version: 1.0
Last Updated: October 3, 2025
Author: Maya (DevOps Engineer)