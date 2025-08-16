# Epic 2: Render Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. Redis Connection Errors
**Symptoms:** Application logs show "Redis connection failed"
**Solution:** 
- Verify REDIS_URL is set to the Internal Database URL from marketedge-redis
- Format should be: `redis://marketedge-redis:6379`
- Check Redis service is running in Render dashboard

### 2. Database Connection Errors  
**Symptoms:** Application logs show "Database connection failed"
**Solution:**
- Verify DATABASE_URL is set to the Internal Database URL from marketedge-postgres
- Format should be: `postgresql://user:password@marketedge-postgres:5432/dbname`
- Check PostgreSQL service is running in Render dashboard

### 3. Auth0 Authentication Errors
**Symptoms:** Frontend shows authentication failures
**Solution:**
- Verify AUTH0_CLIENT_SECRET is set correctly
- Check AUTH0_DOMAIN and AUTH0_CLIENT_ID values
- Update Auth0 callback URLs to include Render URLs

### 4. CORS Errors
**Symptoms:** Frontend cannot connect to backend API
**Solution:**  
- Verify CORS_ORIGINS includes your frontend URL
- Must include: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app
- Format: `["https://frontend-url.com","http://localhost:3000"]`

### 5. Service Won't Start
**Symptoms:** Render service shows "Build failed" or "Deploy failed"
**Solution:**
- Check build logs in Render dashboard
- Verify Dockerfile path is correct
- Ensure PORT environment variable is set to 8000
- Check for missing dependencies in requirements.txt

## Validation Commands

```bash
# Health check
curl https://marketedge-platform.onrender.com/health

# CORS test
curl -H "Origin: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS https://marketedge-platform.onrender.com/api/v1/health

# Check logs
render logs -f --service-name marketedge-platform
```

## Recovery Procedures

### Emergency Rollback
1. Go to Render dashboard
2. Find previous successful deployment
3. Click "Redeploy" on that version

### Environment Variable Reset
1. Export current environment variables
2. Reset problematic variables
3. Redeploy service
4. Test functionality

### Complete Service Recreation
1. Export environment variables
2. Delete current service (keep databases)
3. Recreate service with same configuration
4. Restore environment variables
5. Redeploy

## Success Criteria
- ✅ Health endpoint returns 200 OK
- ✅ Redis connection working  
- ✅ Database connection working
- ✅ CORS configured for frontend
- ✅ Auth0 authentication functional
- ✅ Frontend can communicate with backend

