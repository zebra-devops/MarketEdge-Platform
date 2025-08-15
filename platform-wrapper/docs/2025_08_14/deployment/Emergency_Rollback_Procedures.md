# Emergency Rollback Procedures - Railway Backend

**Status**: 🚨 EMERGENCY PROCEDURES  
**Date**: August 14, 2025  
**Context**: £925K Odeon Demo - 70 hours remaining  

## Immediate Status Check

### **Before Any Rollback - Validate Current Status**

```bash
# Test basic health (should return 200 OK)
curl -s https://marketedge-backend-production.up.railway.app/health

# Test Auth0 integration (should return auth_url)
curl -s "https://marketedge-backend-production.up.railway.app/api/v1/auth/auth0-url?redirect_uri=https://frontend-5r7ft62po-zebraassociates-projects.vercel.app/callback"

# Expected Response:
# {"auth_url":"https://dev-g8trhgbfdq2sk2m8.us.auth0.com/authorize?..."}
```

## Emergency Rollback Scenarios

### **Scenario 1: Total Backend Failure**

**Symptoms**: 
- Health endpoint not responding
- 500/502/503 errors from Railway
- Application won't start

**Immediate Action**:
```bash
# 1. Switch to Railway dashboard
# 2. Go to Deployments tab
# 3. Find last known working deployment: b59194f (Initial commit)
# 4. Click "Redeploy" on that deployment
# 5. Monitor deployment logs
```

**Timeline**: 3-5 minutes for rollback completion

### **Scenario 2: Auth0 Integration Broken**

**Symptoms**:
- Auth0 URL endpoint returns errors
- Authentication flow fails
- CORS errors from frontend

**Immediate Action**:
```bash
# Verify current environment variables
railway variables | grep -E "(AUTH0|CORS)"

# Known Good Configuration:
railway variables --set 'CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"]'

# Redeploy to pick up environment changes
railway up
```

**Timeline**: 2-3 minutes for fix + deployment

### **Scenario 3: Database Connection Issues**

**Symptoms**:
- Health endpoint shows database errors
- API calls return 500 errors
- Database connection timeouts

**Immediate Action**:
```bash
# Check current database URL
railway variables | grep DATABASE_URL

# Verify Railway PostgreSQL service is running
# Check Railway dashboard for service status

# If database URL is wrong, contact Railway support immediately
# Fallback: Use previous working deployment
```

**Timeline**: 5-10 minutes (may require Railway support)

### **Scenario 4: CORS Issues**

**Symptoms**:
- Frontend can't connect to backend
- "CORS origin not allowed" errors
- OPTIONS requests failing

**Quick Fix**:
```bash
# Fix CORS configuration immediately
railway variables --set 'CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"]'

# Redeploy
railway up

# Test immediately
curl -H "Origin: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app" \
"https://marketedge-backend-production.up.railway.app/api/v1/auth/auth0-url?redirect_uri=https://frontend-5r7ft62po-zebraassociates-projects.vercel.app/callback"
```

**Timeline**: 1-2 minutes

## Demo Day Emergency Contacts

### **Primary Response Team**
- **DevOps Lead**: Available during demo hours
- **Railway Support**: Platform-level issues  
- **Auth0 Support**: Authentication issues (if needed)

### **Emergency Communication Plan**
1. **Immediate**: Slack/Teams notification to technical team
2. **5 minutes**: Stakeholder notification if issue not resolved
3. **10 minutes**: Escalation to senior technical leadership
4. **15 minutes**: Consider demo delay if critical issues persist

## Pre-Demo Validation Checklist

### **30 Minutes Before Demo**
```bash
# Full system validation
curl -s https://marketedge-backend-production.up.railway.app/health | jq .
curl -s "https://marketedge-backend-production.up.railway.app/api/v1/auth/auth0-url?redirect_uri=https://frontend-5r7ft62po-zebraassociates-projects.vercel.app/callback" | jq .

# Expected Results:
# Health: {"status":"healthy","version":"1.0.0","timestamp":...}  
# Auth0: {"auth_url":"https://dev-g8trhgbfdq2sk2m8.us.auth0.com/..."}
```

### **5 Minutes Before Demo**
```bash
# Quick health check
curl -s https://marketedge-backend-production.up.railway.app/health

# Should return: {"status":"healthy",...} in <100ms
```

## Recovery Commands - Copy & Paste Ready

### **Complete Railway Redeploy**
```bash
cd /Users/matt/Sites/MarketEdge/platform-wrapper/backend
railway up
```

### **Environment Variable Reset**
```bash
# Core variables that must be correct:
railway variables --set 'CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"]'
railway variables --set "ENVIRONMENT=production"
railway variables --set "DEBUG=false"
```

### **Health Check URLs**
```bash
# Basic health (must work)
https://marketedge-backend-production.up.railway.app/health

# Auth0 test (must work)  
https://marketedge-backend-production.up.railway.app/api/v1/auth/auth0-url?redirect_uri=https://frontend-5r7ft62po-zebraassociates-projects.vercel.app/callback
```

## Known Good Configuration Backup

### **Environment Variables - Last Known Working**
```bash
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr
DATABASE_URL=postgresql://postgres:***@postgres.railway.internal:5432/railway
REDIS_URL=redis://default:***@redis.railway.internal:6379  
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"]
ENVIRONMENT=production
DEBUG=false
RATE_LIMIT_ENABLED=false
```

### **Last Known Working Deployment**
```bash
Commit: b59194f Initial commit: MarketEdge Platform with Phase 1 complete implementation
Railway Deployment: Available in deployment history
```

## Decision Matrix - When to Rollback

| Issue Severity | Response Time | Action |
|---------------|---------------|---------|
| **Critical** - Demo blocking | < 2 minutes | Immediate rollback to last working deployment |
| **High** - Auth/CORS issues | < 5 minutes | Fix environment variables + redeploy |  
| **Medium** - Performance slow | < 10 minutes | Monitor, fix if possible, rollback if needed |
| **Low** - Minor errors | < 30 minutes | Log for post-demo, don't interrupt demo |

## Post-Rollback Validation

### **Mandatory Checks After Any Rollback**
1. Health endpoint responding (< 100ms)
2. Auth0 URL generation working  
3. CORS headers present
4. Database connectivity confirmed
5. Frontend can connect to backend

### **Demo Workflow Test**
1. Frontend loads without CORS errors
2. Auth0 login button works
3. API calls return expected data
4. No console errors in browser dev tools

## Success Criteria

**✅ Rollback Successful If**:
- Health endpoint: HTTP 200 in <100ms
- Auth0 endpoint: Returns valid auth_url
- No CORS errors from frontend
- Application logs show no errors
- Demo workflow completes end-to-end

**❌ Escalate If**:
- Rollback doesn't resolve issue within 10 minutes
- Multiple rollback attempts needed
- Infrastructure-level Railway issues
- Database connectivity completely lost

---

## Emergency Escalation

**If rollback procedures don't resolve issues within 15 minutes:**

1. **Technical Escalation**: Contact Railway enterprise support
2. **Business Escalation**: Notify stakeholders of potential demo impact  
3. **Contingency Plan**: Switch to local development demo setup if available
4. **Documentation**: Log all actions taken for post-incident review

---

*Emergency Rollback Procedures*  
*Generated with Claude Code - DevOps Infrastructure*  
*For £925K Odeon Demo - August 14, 2025*