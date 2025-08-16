# EPIC 2: FINAL DEPLOYMENT INSTRUCTIONS
## Complete Render Platform Configuration

**Status**: ✅ Backend confirmed down - environment variables needed  
**Mission**: Restore MarketEdge platform functionality  
**Estimated Time**: 10-15 minutes  

---

## 🚨 CRITICAL SITUATION
- **Platform Status**: DOWN (404 errors from Railway backend failure)
- **Render Services**: Created but not configured
- **Frontend**: Ready and pointing to Render URL
- **Issue**: Missing environment variables causing startup failures

---

## 📋 STEP-BY-STEP DASHBOARD CONFIGURATION

### Step 1: Access Render Dashboard
1. Open: https://dashboard.render.com
2. Ensure you're logged in to the correct account
3. Verify you see these services:
   - ✅ **marketedge-platform** (Web Service)
   - ✅ **marketedge-postgres** (PostgreSQL)
   - ✅ **marketedge-redis** (Redis)

### Step 2: Get Database Connection URLs

#### PostgreSQL Database URL:
1. Click on **"marketedge-postgres"** service
2. Find **"Internal Database URL"** section
3. Copy the URL (format: `postgresql://user:password@host:port/database`)
4. **Save this URL** - you'll need it in Step 4

#### Redis Database URL:
1. Click on **"marketedge-redis"** service  
2. Find **"Internal Database URL"** section
3. Copy the URL (format: `redis://host:port`)
4. **Save this URL** - you'll need it in Step 4

### Step 3: Configure Environment Variables
1. Click on **"marketedge-platform"** web service
2. Go to **"Environment"** tab
3. Click **"Add Environment Variable"** for each variable below

### Step 4: Required Environment Variables

Copy these EXACTLY into the Render dashboard:

```bash
# === CRITICAL DATABASE CONNECTIONS ===
DATABASE_URL = [PASTE YOUR POSTGRESQL URL FROM STEP 2]
REDIS_URL = [PASTE YOUR REDIS URL FROM STEP 2]

# === AUTH0 CONFIGURATION ===
AUTH0_CLIENT_SECRET = 9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2
AUTH0_DOMAIN = dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID = mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr
AUTH0_CALLBACK_URL = https://marketedge-platform.onrender.com/callback

# === CORS CONFIGURATION (CRITICAL) ===
CORS_ORIGINS = ["https://frontend-5r7ft62po-zebraassociates-projects.vercel.app","http://localhost:3000"]

# === APPLICATION SETTINGS ===
PORT = 8000
ENVIRONMENT = production
DEBUG = false
LOG_LEVEL = INFO

# === SECURITY ===
JWT_ALGORITHM = HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# === RATE LIMITING ===
RATE_LIMIT_ENABLED = true
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
```

### Step 5: Trigger Deployment
1. After setting ALL environment variables
2. Click **"Manual Deploy"** button
3. Select **latest commit** from dropdown
4. Click **"Deploy"**
5. Monitor the deployment process

### Step 6: Monitor Deployment
1. Watch **"Build Logs"** for any errors
2. Wait for status to show **"Live"**  
3. Should take 3-5 minutes
4. If build fails, check logs for missing variables

---

## 🔍 VALIDATION CHECKLIST

After deployment completes, verify these endpoints:

### Health Check:
```bash
curl https://marketedge-platform.onrender.com/health
```
**Expected**: `{"status": "healthy", "timestamp": "..."}`

### API Health:
```bash
curl https://marketedge-platform.onrender.com/api/v1/health  
```
**Expected**: `{"status": "ok"}`

### CORS Test:
```bash
curl -H "Origin: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app" \
     -X OPTIONS https://marketedge-platform.onrender.com/api/v1/health
```
**Expected**: CORS headers present

---

## 🎯 SUCCESS CRITERIA

### ✅ Deployment Successful When:
- [ ] All environment variables set correctly
- [ ] Build completes without errors  
- [ ] Service status shows "Live"
- [ ] Health endpoint returns 200 OK
- [ ] Redis connection working
- [ ] Database connection working
- [ ] CORS configured for frontend URL
- [ ] Frontend can authenticate users

---

## 🚨 TROUBLESHOOTING

### If Build Fails:
1. Check environment variables are exactly as specified
2. Verify DATABASE_URL and REDIS_URL are correct
3. Look for missing quotes in CORS_ORIGINS
4. Ensure PORT is set to 8000

### If Service Won't Start:
1. Check service logs in Render dashboard
2. Verify Redis service is running
3. Verify PostgreSQL service is running
4. Check for connection timeouts

### If CORS Errors Persist:
1. Verify CORS_ORIGINS includes exact frontend URL
2. Check for trailing slashes in URLs
3. Ensure JSON array format with proper quotes

---

## 📞 EMERGENCY PROCEDURES

### If Deployment Fails Completely:
1. **Export environment variables** from dashboard
2. **Delete and recreate** web service (keep databases)
3. **Restore environment variables**
4. **Redeploy from GitHub repository**

### If Need Immediate Rollback:
1. Go to **"Deploys"** tab in marketedge-platform
2. Find last **successful deployment**
3. Click **"Redeploy"** on that version

---

## 🎉 EXPECTED FINAL STATE

### After Successful Configuration:
- ✅ **Backend**: https://marketedge-platform.onrender.com (Live)
- ✅ **Frontend**: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app (Working)
- ✅ **Database**: Connected and operational
- ✅ **Redis**: Connected and operational  
- ✅ **Authentication**: Auth0 login flow working
- ✅ **CORS**: Frontend-backend communication restored
- ✅ **Epic 2**: Railway migration COMPLETE

### Platform Restoration Complete! 🚀

**Total Downtime**: ~30 minutes (Railway failure to Render restoration)  
**Migration Success**: Epic 2 objectives achieved  
**Next Priority**: Resume normal development operations