# Quick Start: DNS Configuration for staging.zebra.associates

## TL;DR - Immediate Actions Required

### Current Status
- Domain: zebra.associates hosted on Google Cloud DNS
- Production: app.zebra.associates → Vercel (working)
- Staging: staging.zebra.associates → NOT CONFIGURED
- Backend: marketedge-platform-staging.onrender.com → NOT DEPLOYED (404)

### Critical Finding
**WARNING**: Backend staging service is not deployed yet. Shows 404 on:
- https://marketedge-platform-staging.onrender.com/health
- https://marketedge-platform-staging.onrender.com/

### 3-Step Setup (After Backend Deployed)

#### Step 1: Configure DNS (Google Domains)
1. Login to Google Domains: https://domains.google.com
2. Navigate to: zebra.associates > DNS
3. Add CNAME record:
   ```
   Host: staging
   Type: CNAME
   Data: cname.vercel-dns.com
   TTL: 300
   ```

#### Step 2: Configure Vercel
1. Deploy frontend to Vercel (staging environment)
2. Vercel Dashboard > Domains > Add `staging.zebra.associates`
3. Wait 5-10 minutes for SSL certificate

#### Step 3: Verify
```bash
# Check DNS
dig staging.zebra.associates +short
# Expected: cname.vercel-dns.com

# Check HTTPS
curl -I https://staging.zebra.associates
# Expected: 200 OK with SSL
```

## DNS Record Comparison

### Current Production (Working)
```
app.zebra.associates
└── CNAME: cname.vercel-dns.com
    ├── Resolves to: 76.76.21.61, 76.76.21.241
    ├── SSL: Active (Let's Encrypt)
    └── Status: Healthy
```

### Staging (To Configure)
```
staging.zebra.associates
└── CNAME: cname.vercel-dns.com (TO ADD)
    ├── Will resolve to: Vercel IPs
    ├── SSL: Auto-provisioned by Vercel
    └── Status: Not configured
```

## Recommended Architecture

```
┌─────────────────────────────────────────────┐
│  DNS: staging.zebra.associates              │
│  Provider: Google Cloud DNS                  │
└──────────────────┬──────────────────────────┘
                   │ CNAME
                   ▼
┌─────────────────────────────────────────────┐
│  Vercel Edge Network                         │
│  Domain: staging.zebra.associates            │
│  SSL: Let's Encrypt (auto)                   │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────┐    ┌──────────────────────┐
│   Frontend   │    │      Backend API      │
│   Next.js    │───▶│  Render Staging       │
│   Vercel     │    │  marketedge-platform- │
│              │    │  staging.onrender.com │
└──────────────┘    └──────────────────────┘
```

## Pre-Deployment Checklist

### Backend (Render) - REQUIRED FIRST
- [ ] Create Render service: marketedge-platform-staging
- [ ] Configure environment variables (DATABASE_URL, AUTH0_*, etc.)
- [ ] Deploy service (Git push to staging branch)
- [ ] Verify health endpoint returns 200: `/health`
- [ ] Verify API docs accessible: `/docs`

### Frontend (Vercel)
- [ ] Create Vercel project for staging
- [ ] Set environment variable: `NEXT_PUBLIC_API_URL=https://marketedge-platform-staging.onrender.com`
- [ ] Deploy to Vercel
- [ ] Verify deployment on `*.vercel.app` URL

### DNS (Google Domains)
- [ ] Access to Google Domains account confirmed
- [ ] DNS zone for zebra.associates accessible
- [ ] Able to add/modify CNAME records

### Auth0
- [ ] Staging application created in Auth0
- [ ] Callback URL configured: `https://staging.zebra.associates/api/auth/callback`
- [ ] Client ID and Secret available

## Environment Variables Required

### Backend (Render)
```bash
ENVIRONMENT=staging
DATABASE_URL=postgresql://...
AUTH0_DOMAIN=marketedge.eu.auth0.com
AUTH0_CLIENT_ID=[staging-client-id]
AUTH0_CLIENT_SECRET=[staging-secret]
FRONTEND_URL=https://staging.zebra.associates
CORS_ORIGINS=https://staging.zebra.associates,http://localhost:3000
```

### Frontend (Vercel)
```bash
NEXT_PUBLIC_API_URL=https://marketedge-platform-staging.onrender.com
NEXT_PUBLIC_AUTH0_DOMAIN=marketedge.eu.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=[staging-client-id]
NEXT_PUBLIC_AUTH0_REDIRECT_URI=https://staging.zebra.associates/api/auth/callback
```

## Verification Commands

### DNS Check
```bash
# Check CNAME record
dig staging.zebra.associates CNAME +short

# Check DNS propagation globally
curl -s "https://dns.google/resolve?name=staging.zebra.associates&type=CNAME" | jq .

# Check from multiple DNS servers
dig @8.8.8.8 staging.zebra.associates +short  # Google
dig @1.1.1.1 staging.zebra.associates +short  # Cloudflare
```

### SSL Certificate Check
```bash
# Check certificate details
echo | openssl s_client -connect staging.zebra.associates:443 -servername staging.zebra.associates 2>/dev/null | openssl x509 -noout -issuer -subject -dates

# Quick SSL check
curl -vI https://staging.zebra.associates 2>&1 | grep -i "SSL"
```

### Service Health Check
```bash
# Backend health
curl https://marketedge-platform-staging.onrender.com/health | jq .

# Frontend health
curl -I https://staging.zebra.associates

# Full integration
curl https://staging.zebra.associates/api/health | jq .
```

## Timeline Estimate

| Task | Duration | Notes |
|------|----------|-------|
| Backend deployment | 5-10 min | Render build + deploy |
| Frontend deployment | 3-5 min | Vercel build + deploy |
| DNS configuration | 1 min | Add CNAME record |
| DNS propagation | 5-30 min | Global DNS update |
| SSL provisioning | 5-10 min | Automatic via Vercel |
| Auth0 configuration | 2 min | Update callback URLs |
| Verification testing | 10 min | End-to-end tests |
| **Total** | **30-60 min** | First-time setup |

## Common Issues & Quick Fixes

### Issue: Backend 404 (Current Issue)
```
Problem: marketedge-platform-staging.onrender.com returns 404
Solution: Deploy backend service to Render first
```

### Issue: DNS Not Resolving
```
Problem: dig returns NXDOMAIN
Check: Verify CNAME record saved in Google Domains
Wait: Up to 30 minutes for propagation
Fix: Clear local DNS cache (sudo dscacheutil -flushcache)
```

### Issue: SSL Certificate Error
```
Problem: Browser shows "Not Secure" warning
Check: Vercel domain configuration shows "Valid"
Wait: Up to 10 minutes for certificate provisioning
Fix: Remove and re-add domain in Vercel
```

### Issue: CORS Errors
```
Problem: Browser console shows CORS errors
Check: Backend CORS_ORIGINS includes staging URL
Fix: Update environment variable and redeploy
```

## Next Steps After DNS Configuration

1. **Immediate** (Day 1):
   - [ ] Deploy backend to Render staging
   - [ ] Configure DNS CNAME record
   - [ ] Deploy frontend to Vercel
   - [ ] Add custom domain in Vercel
   - [ ] Update Auth0 settings
   - [ ] Test complete authentication flow

2. **Short-term** (Week 1):
   - [ ] Configure monitoring (uptime checks)
   - [ ] Set up staging database backups
   - [ ] Document staging credentials
   - [ ] Create runbook for deployments

3. **Ongoing**:
   - [ ] Increase DNS TTL from 300 to 3600 (after stability)
   - [ ] Monitor SSL certificate auto-renewal
   - [ ] Regular staging environment testing
   - [ ] Keep staging in sync with production architecture

## Support Resources

- **Full Documentation**: `/docs/2025_10_03/infrastructure/staging-dns-configuration.md`
- **Deployment Runbook**: `/docs/2025_10_03/infrastructure/staging-deployment-runbook.md`
- **Google Domains DNS**: https://domains.google.com
- **Vercel Dashboard**: https://vercel.com/dashboard
- **Render Dashboard**: https://dashboard.render.com
- **Auth0 Dashboard**: https://manage.auth0.com

---

**Status**: Backend deployment required before DNS configuration
**Priority**: HIGH - Required for staging environment
**Owner**: DevOps (Maya)
**Created**: October 3, 2025