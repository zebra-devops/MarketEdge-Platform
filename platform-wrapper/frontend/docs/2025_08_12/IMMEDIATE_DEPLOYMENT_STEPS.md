# IMMEDIATE DEPLOYMENT STEPS - CORS & Auth0 Fix

## CRITICAL: Execute These Steps NOW

**Status:** READY FOR DEPLOYMENT  
**Time Required:** 15-30 minutes  
**Risk Level:** LOW - Configuration changes only  

---

## STEP 1: Railway Backend CORS Configuration (CRITICAL)

### Access Railway Dashboard
1. Go to: https://railway.app/project/e6f51f81-f649-4529-90fe-d491a578591d
2. Select the **backend service** (MarketEdge Backend)
3. Navigate to **Variables** tab

### Add Environment Variables
Add these variables (or update if they exist):

```bash
FRONTEND_URL=https://frontend-bnaxvfa9k-zebraassociates-projects.vercel.app
CORS_ORIGINS=https://frontend-bnaxvfa9k-zebraassociates-projects.vercel.app,http://localhost:3000,http://localhost:3001
```

### Deploy Changes
1. Click **Deploy** button in Railway
2. Wait for deployment to complete (~2-3 minutes)
3. Verify deployment status shows "Active"

---

## STEP 2: Auth0 Configuration Update (CRITICAL)

### Access Auth0 Dashboard
1. Go to: https://manage.auth0.com/dashboard
2. Navigate to **Applications** 
3. Select **MarketEdge Platform Wrapper** (Client ID: mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr)

### Update Application Settings
In the **Settings** tab, update these fields:

#### Allowed Callback URLs
```
https://frontend-bnaxvfa9k-zebraassociates-projects.vercel.app/callback,
http://localhost:3000/callback
```

#### Allowed Logout URLs  
```
https://frontend-bnaxvfa9k-zebraassociates-projects.vercel.app/login,
http://localhost:3000/login
```

#### Allowed Web Origins
```
https://frontend-bnaxvfa9k-zebraassociates-projects.vercel.app,
http://localhost:3000
```

#### Allowed Origins (CORS)
```
https://frontend-bnaxvfa9k-zebraassociates-projects.vercel.app,
http://localhost:3000
```

### Save Changes
1. Scroll to bottom and click **Save Changes**
2. Wait for confirmation message

---

## STEP 3: Verify Vercel Environment Variables (OPTIONAL)

The frontend environment is already correctly configured, but verify:

### Check Vercel Dashboard
1. Go to: https://vercel.com/zebraassociates-projects/frontend
2. Navigate to **Settings** > **Environment Variables**
3. Verify these are set:

```bash
NEXT_PUBLIC_API_BASE_URL=https://marketedge-backend-production.up.railway.app
NEXT_PUBLIC_AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr
```

### Redeploy Frontend (if needed)
If variables were changed:
1. Go to **Deployments** tab
2. Click **Redeploy** on latest deployment

---

## STEP 4: IMMEDIATE TESTING (REQUIRED)

### Test 1: CORS Verification
```bash
# Run from your terminal
cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend
./verify-cors-fix.sh
```

**Expected Results:**
- ✅ Backend is accessible
- ✅ CORS preflight successful  
- ✅ Auth0 URL endpoint accessible
- ✅ Frontend is accessible

### Test 2: Manual Auth Flow
1. Open: https://frontend-bnaxvfa9k-zebraassociates-projects.vercel.app
2. Click **"Sign in with Auth0"**
3. **Check browser console** - NO CORS errors should appear
4. Should redirect to Auth0 login page
5. After login, should redirect back to frontend

### Test 3: Network Tab Verification
1. Open browser **Developer Tools** (F12)
2. Go to **Network** tab
3. Click login button
4. Look for API call to: `https://marketedge-backend-production.up.railway.app/api/v1/auth/auth0-url`
5. **Status should be 200** (not blocked by CORS)

---

## TROUBLESHOOTING

### If CORS Still Fails
1. **Check Railway deployment status** - Ensure backend deployed successfully
2. **Verify environment variables** - Double-check spelling and URLs  
3. **Clear browser cache** - Hard refresh (Ctrl+F5)
4. **Check Railway logs** - Look for CORS-related errors

### If Auth0 Redirect Fails
1. **Verify Auth0 URLs** - Ensure no trailing slashes or typos
2. **Check Auth0 logs** - Go to Auth0 Dashboard > Monitoring > Logs
3. **Verify client ID** - Ensure it matches in both frontend and Auth0

### If Frontend 401 Errors  
1. **Check if auth is required** - Some pages may require authentication
2. **Try incognito mode** - Eliminates cached auth state
3. **Clear all cookies/localStorage** - Fresh session

---

## SUCCESS CRITERIA

✅ **CORS Test Passes:** No CORS errors in browser console  
✅ **Auth0 Login Works:** Can click login and reach Auth0  
✅ **Callback Works:** Can login and return to dashboard  
✅ **API Calls Succeed:** Network tab shows 200 responses  

---

## EMERGENCY CONTACTS

- **Railway Issues:** Check Railway status page
- **Auth0 Issues:** Check Auth0 status page  
- **Vercel Issues:** Check Vercel status page

---

## POST-DEPLOYMENT CHECKLIST

- [ ] Railway backend environment variables updated
- [ ] Railway backend redeployed successfully
- [ ] Auth0 application settings updated
- [ ] CORS verification script passes
- [ ] Manual login flow tested
- [ ] No console errors on login
- [ ] Auth0 callback works
- [ ] User can access dashboard after login

---

**STATUS:** Ready for immediate execution  
**NEXT:** Execute steps 1-2, then test immediately  
**TIMELINE:** Complete within 30 minutes for demo readiness