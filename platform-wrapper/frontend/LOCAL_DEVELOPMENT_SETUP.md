# Local Development Setup & Troubleshooting Guide

## Quick Start

### 1. Backend Setup (Terminal 1)
```bash
cd /Users/matt/Sites/MarketEdge/platform-wrapper/backend
source venv/bin/activate  # if using virtual environment
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info --reload
```

### 2. Frontend Setup (Terminal 2)
```bash
cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend
npm run dev
# Note: If port 3000 is taken, Next.js will automatically use 3001
```

### 3. Database Setup (if needed)
```bash
# Ensure PostgreSQL is running
brew services start postgresql
# Ensure Redis is running  
brew services start redis
```

## Configuration Files

### Environment Files Priority (Frontend)
1. `.env.development` - Development-specific settings (highest priority)
2. `.env.local` - Local overrides 
3. `.env` - Default settings

### Current Configuration
- **Frontend**: http://localhost:3001 (auto-selected if 3000 is busy)
- **Backend**: http://localhost:8000
- **Auth0 Callback**: http://localhost:3001/callback

## Common Issues & Solutions

### 1. React Hydration Warnings ✅ FIXED
**Issue**: `Warning: Extra attributes from the server: __processed_5852b7c4...`

**Cause**: Browser extensions (like ad blockers) inject attributes into the DOM

**Solution**: Added `suppressHydrationWarning` to HTML and body elements
```tsx
<html lang="en" suppressHydrationWarning>
  <body className={inter.className} suppressHydrationWarning>
```

### 2. Infinite Loop Detection ✅ FIXED
**Issue**: `NUCLEAR CIRCUIT BREAKER: Infinite loop detected`

**Cause**: Overly aggressive duplicate request detection

**Solution**: Improved circuit breaker logic:
- Uses longer auth code keys for better uniqueness
- Waits for existing promises instead of rejecting
- Clears failed auth codes to allow retries

### 3. 403 Forbidden Errors on API Calls

**Root Cause**: Authentication is required for protected endpoints

**To Debug**:
1. Check the AuthDebugPanel (bottom-right in development)
2. Verify token is present: `✅ Has Token: true`
3. Test API connectivity: Should show `API: Connected`
4. Check CORS: Should show `CORS: OK - Origin Allowed`

**Authentication Flow**:
1. Visit http://localhost:3001
2. Click "Login" 
3. Complete Auth0 flow
4. Should redirect to http://localhost:3001/callback
5. Tokens stored in cookies and localStorage
6. Subsequent API calls include `Authorization: Bearer <token>` header

### 4. CORS Configuration ✅ FIXED
**Backend** `.env` includes:
```
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","http://localhost:3002","https://app.zebra.associates"]
```

**Test CORS**:
```bash
curl -H "Origin: http://localhost:3001" http://localhost:8000/cors-debug
```

### 5. Port Conflicts
- If port 3000 is busy, Next.js will use 3001 automatically
- Backend always uses port 8000
- Update Auth0 callback URL if using different port

## Development Tools

### AuthDebugPanel
- **Location**: Bottom-right corner (development only)
- **Shows**: Authentication state, connectivity, environment info
- **Refresh**: Click "Refresh" button to update information

### API Endpoints for Testing
- **Health Check**: http://localhost:8000/health
- **CORS Debug**: http://localhost:8000/cors-debug
- **API Base**: http://localhost:8000/api/v1/

### Browser DevTools
1. **Network Tab**: Check API calls for proper headers
2. **Application Tab**: Check cookies and localStorage
3. **Console**: Look for auth-related logs

## Auth0 Configuration

### Required Settings in Auth0 Dashboard
1. **Allowed Callback URLs**: 
   - `http://localhost:3000/callback`
   - `http://localhost:3001/callback` 
   - `https://app.zebra.associates/callback`

2. **Allowed Web Origins**:
   - `http://localhost:3000`
   - `http://localhost:3001`
   - `https://app.zebra.associates`

3. **Allowed Logout URLs**:
   - `http://localhost:3000`
   - `http://localhost:3001`
   - `https://app.zebra.associates`

## Environment Variables Reference

### Frontend (.env.development)
```
NEXT_PUBLIC_AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
NEXT_PUBLIC_DEBUG=true
```

### Backend (.env)
```
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr
AUTH0_CALLBACK_URL=http://localhost:3001/callback
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","http://localhost:3002","https://app.zebra.associates"]
ENVIRONMENT=development
DEBUG=true
```

## Troubleshooting Checklist

### Before Starting Development
- [ ] PostgreSQL running (`brew services start postgresql`)
- [ ] Redis running (`brew services start redis`)
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)

### Authentication Issues
- [ ] Auth0 configuration matches environment variables
- [ ] Callback URLs configured in Auth0
- [ ] Backend running on port 8000
- [ ] CORS debug shows origin allowed
- [ ] AuthDebugPanel shows connection status

### API Issues  
- [ ] Token present in AuthDebugPanel
- [ ] API health check responds (`curl http://localhost:8000/health`)
- [ ] Proper Authorization header in network requests
- [ ] Check backend logs for errors

### Production vs Development
- Development uses `http://localhost:*` 
- Production uses `https://app.zebra.associates`
- Auth0 callback URLs must match exactly
- Environment variables switch automatically

## Performance Notes
- Auto-refresh and activity tracking disabled to prevent timer issues
- Minimal middleware in development for faster debugging
- Circuit breaker improved to reduce false positives
- Hydration warnings suppressed for browser extension compatibility

## Need Help?
1. Check AuthDebugPanel first
2. Check browser console for errors
3. Check backend logs (`tail -f backend.log`)
4. Verify Auth0 configuration
5. Test individual components with curl