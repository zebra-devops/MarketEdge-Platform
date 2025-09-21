# Auth0 Staging Tenant Configuration Guide

## Executive Summary

This guide establishes complete Auth0 staging isolation for MarketEdge Platform preview environments, protecting production authentication while enabling safe development testing for the £925K Zebra Associates opportunity.

**CRITICAL REQUIREMENT**: Separate Auth0 tenant/application prevents production Auth0 contamination from staging/preview environments.

## Current State Assessment

### Production Auth0 Configuration
- **Domain**: `dev-g8trhgbfdq2sk2m8.us.auth0.com`
- **Client ID**: `mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr`
- **Application**: PlatformWrapperAuth (Production)
- **Status**: Active, supporting Matt.Lindop super_admin access

### Staging Environment Needs
- **Preview URLs**: `https://*-onrender.com/*` (dynamic Render preview deployments)
- **Testing Requirements**: Isolated authentication for feature testing
- **Security**: Zero production Auth0 impact from staging activities

## 1. Auth0 Staging Tenant Creation

### Step 1.1: Create New Auth0 Application

**Navigate to Auth0 Dashboard:**
```
https://manage.auth0.com/dashboard/us/dev-g8trhgbfdq2sk2m8/applications
```

**Create New Application:**
1. Click "Create Application"
2. **Application Name**: `MarketEdge-Staging`
3. **Application Type**: Single Page Application (SPA)
4. Click "Create"

### Step 1.2: Basic Application Configuration

**Application Settings (Settings Tab):**

**Name**: `MarketEdge-Staging`
**Description**: `MarketEdge Platform Staging Environment - Preview Deployments`
**Application Type**: `Single Page Application`
**Token Endpoint Authentication Method**: `None`

## 2. Critical Auth0 Staging Configuration

### Step 2.1: Application URIs Configuration

**IMPORTANT**: Use wildcard patterns to support dynamic Render preview URLs.

#### Allowed Callback URLs
```
https://*.onrender.com/callback,
https://localhost:3000/callback,
https://marketedge-staging-*.onrender.com/callback,
https://pr-*-marketedge-platform.onrender.com/callback
```

#### Allowed Logout URLs
```
https://*.onrender.com/,
https://localhost:3000/,
https://marketedge-staging-*.onrender.com/,
https://pr-*-marketedge-platform.onrender.com/
```

#### Allowed Web Origins
```
https://*.onrender.com,
https://localhost:3000,
https://marketedge-staging-*.onrender.com,
https://pr-*-marketedge-platform.onrender.com
```

#### Allowed Origins (CORS)
```
https://*.onrender.com,
https://localhost:3000,
https://marketedge-staging-*.onrender.com,
https://pr-*-marketedge-platform.onrender.com
```

### Step 2.2: Advanced Settings

**Grant Types (Advanced Settings → Grant Types):**
- ✅ Authorization Code
- ✅ Refresh Token
- ✅ Implicit (for SPA compatibility)

**JWT Settings (Advanced Settings → Settings):**
- **JsonWebToken Signature Algorithm**: RS256
- **OIDC Conformant**: Enabled

## 3. Render Environment Variables Configuration

### Step 3.1: Staging Auth0 Credentials

**After creating Auth0 staging application, collect:**

```bash
# New staging credentials (to be obtained from Auth0 dashboard)
AUTH0_DOMAIN_STAGING="dev-g8trhgbfdq2sk2m8.us.auth0.com"  # Same domain, different app
AUTH0_CLIENT_ID_STAGING="[NEW_STAGING_CLIENT_ID]"
AUTH0_CLIENT_SECRET_STAGING="[NEW_STAGING_CLIENT_SECRET]"
AUTH0_AUDIENCE_STAGING="https://api.marketedge-staging.onrender.com"
```

### Step 3.2: Render Dashboard Configuration

**Access Render Dashboard:**
```
https://dashboard.render.com/web/[service-id]/environment
```

**Add Environment Variables:**

1. **AUTH0_DOMAIN_STAGING**
   - Value: `dev-g8trhgbfdq2sk2m8.us.auth0.com`
   - Environment: All environments

2. **AUTH0_CLIENT_ID_STAGING**
   - Value: `[NEW_STAGING_CLIENT_ID]`
   - Environment: All environments

3. **AUTH0_CLIENT_SECRET_STAGING**
   - Value: `[NEW_STAGING_CLIENT_SECRET]`
   - Environment: All environments
   - **IMPORTANT**: Mark as secret/encrypted

4. **AUTH0_AUDIENCE_STAGING**
   - Value: `https://api.marketedge-staging.onrender.com`
   - Environment: All environments

## 4. Backend Configuration Updates

### Step 4.1: Update Configuration Settings

**File**: `/app/core/config.py`

**Add staging Auth0 configuration:**

```python
class Settings(BaseSettings):
    # Existing production Auth0 settings
    AUTH0_DOMAIN: str
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str
    AUTH0_CALLBACK_URL: str = "http://localhost:3000/callback"

    # NEW: Staging Auth0 settings
    AUTH0_DOMAIN_STAGING: Optional[str] = None
    AUTH0_CLIENT_ID_STAGING: Optional[str] = None
    AUTH0_CLIENT_SECRET_STAGING: Optional[str] = None
    AUTH0_AUDIENCE_STAGING: Optional[str] = None

    def get_auth0_config(self) -> Dict[str, str]:
        """Get Auth0 configuration based on environment"""
        if self.ENVIRONMENT.lower() in ["staging", "preview"]:
            # Use staging Auth0 configuration
            return {
                "domain": self.AUTH0_DOMAIN_STAGING or self.AUTH0_DOMAIN,
                "client_id": self.AUTH0_CLIENT_ID_STAGING or self.AUTH0_CLIENT_ID,
                "client_secret": self.AUTH0_CLIENT_SECRET_STAGING or self.AUTH0_CLIENT_SECRET,
                "audience": self.AUTH0_AUDIENCE_STAGING or f"https://api.{self.AUTH0_DOMAIN}",
            }
        else:
            # Use production Auth0 configuration
            return {
                "domain": self.AUTH0_DOMAIN,
                "client_id": self.AUTH0_CLIENT_ID,
                "client_secret": self.AUTH0_CLIENT_SECRET,
                "audience": f"https://api.{self.AUTH0_DOMAIN}",
            }
```

### Step 4.2: Update Auth0 Integration

**File**: `/app/auth/auth0.py`

**Update to use environment-aware configuration:**

```python
# Modify auth0.py to use settings.get_auth0_config()
from app.core.config import settings

def get_auth0_config():
    """Get environment-appropriate Auth0 configuration"""
    return settings.get_auth0_config()

# Update all Auth0 API calls to use get_auth0_config()
```

## 5. Render.yaml Configuration Updates

### Step 5.1: Update Preview Environment Variables

**File**: `/render.yaml`

**Update envVars section for preview environments:**

```yaml
envVars:
  # Environment identification
  - key: ENVIRONMENT
    value: production
    previewValue: staging

  # Auth0 Configuration - Production (unchanged)
  - key: AUTH0_DOMAIN
    sync: false
  - key: AUTH0_CLIENT_ID
    sync: false
  - key: AUTH0_CLIENT_SECRET
    sync: false
  - key: AUTH0_AUDIENCE
    sync: false

  # NEW: Auth0 Configuration - Staging (for preview environments)
  - key: AUTH0_DOMAIN_STAGING
    sync: false
  - key: AUTH0_CLIENT_ID_STAGING
    sync: false
  - key: AUTH0_CLIENT_SECRET_STAGING
    sync: false
  - key: AUTH0_AUDIENCE_STAGING
    sync: false

  # CORS Configuration for staging
  - key: ALLOWED_ORIGINS
    value: "https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com"
    previewValue: "https://*.onrender.com,https://localhost:3000"
```

## 6. Frontend Configuration Updates

### Step 6.1: Environment-Aware Auth0 Configuration

**Create environment detection logic:**

```typescript
// utils/auth0-config.ts
export const getAuth0Config = () => {
  const isStaging = process.env.NODE_ENV === 'development' ||
                   window.location.hostname.includes('onrender.com');

  if (isStaging) {
    return {
      domain: process.env.NEXT_PUBLIC_AUTH0_DOMAIN_STAGING || 'dev-g8trhgbfdq2sk2m8.us.auth0.com',
      clientId: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID_STAGING || '[STAGING_CLIENT_ID]',
      audience: process.env.NEXT_PUBLIC_AUTH0_AUDIENCE_STAGING || 'https://api.marketedge-staging.onrender.com',
      redirectUri: window.location.origin + '/callback',
    };
  }

  return {
    domain: process.env.NEXT_PUBLIC_AUTH0_DOMAIN || 'dev-g8trhgbfdq2sk2m8.us.auth0.com',
    clientId: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID || 'mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr',
    audience: process.env.NEXT_PUBLIC_AUTH0_AUDIENCE || 'https://api.marketedge-platform.onrender.com',
    redirectUri: window.location.origin + '/callback',
  };
};
```

## 7. Testing and Verification

### Step 7.1: Staging Authentication Flow Test

**Create preview environment:**
1. Create GitHub PR to trigger Render preview deployment
2. Access preview URL: `https://pr-[number]-marketedge-platform.onrender.com`
3. Test authentication flow:
   - Click "Sign In"
   - Verify Auth0 login page loads
   - Complete authentication
   - Verify successful callback redirect
   - Confirm staging Auth0 application is used

### Step 7.2: Production Isolation Verification

**Verify production unaffected:**
1. Access production URL: `https://marketedge-platform.onrender.com`
2. Test authentication with Matt.Lindop account
3. Verify super_admin access to feature flags
4. Confirm production Auth0 application still used

### Step 7.3: Multi-Environment Testing

**Test matrix:**
- ✅ Production → Production Auth0
- ✅ Staging/Preview → Staging Auth0
- ✅ Local Development → Staging Auth0
- ✅ No cross-contamination between environments

## 8. Emergency Procedures

### Step 8.1: Staging Auth0 Issues

**If staging Auth0 fails:**
1. **Immediate fallback**: Update staging to use production Auth0 temporarily
2. **Isolate**: Ensure no impact on production authentication
3. **Fix**: Review staging Auth0 application configuration
4. **Test**: Verify staging Auth0 restoration

### Step 8.2: Production Protection

**If production affected:**
1. **STOP**: Halt all staging/preview deployments immediately
2. **ISOLATE**: Revert to production-only Auth0 configuration
3. **VERIFY**: Test Matt.Lindop access and super_admin functionality
4. **RESOLVE**: Fix staging configuration without production impact

## 9. Security Considerations

### Step 9.1: Staging Data Isolation

**Staging Environment Security:**
- Separate Auth0 application prevents production user access in staging
- Staging database isolated from production data
- Test users cannot access production resources

### Step 9.2: Preview Environment Security

**Preview URL Security:**
- Wildcard redirect URIs limited to `*.onrender.com` domain
- Preview environments auto-expire after 7 days
- No persistent sensitive data in preview environments

## 10. Success Criteria

### ✅ Complete Staging Isolation
- [ ] Staging Auth0 application created and configured
- [ ] Wildcard redirect URIs support all preview URLs
- [ ] Environment variables configured in Render dashboard
- [ ] Backend configuration updated for environment-aware Auth0
- [ ] Frontend configuration supports environment detection

### ✅ Production Protection
- [ ] Production Auth0 configuration unchanged and functional
- [ ] Matt.Lindop super_admin access preserved
- [ ] No production authentication disruption during staging setup
- [ ] Zebra Associates opportunity protected

### ✅ Preview Environment Testing
- [ ] Preview deployments can authenticate with staging Auth0
- [ ] Authentication flow works end-to-end in preview environments
- [ ] No CORS or callback URL errors in staging
- [ ] Feature flag testing possible in isolated staging environment

## 11. Implementation Checklist

### Phase 1: Auth0 Staging Setup
- [ ] Create MarketEdge-Staging application in Auth0
- [ ] Configure wildcard redirect URIs for Render preview URLs
- [ ] Collect staging Auth0 credentials (domain, client ID, secret)
- [ ] Document staging application configuration

### Phase 2: Render Configuration
- [ ] Add staging Auth0 environment variables to Render dashboard
- [ ] Update render.yaml with staging environment variable overrides
- [ ] Configure preview environment variable mappings
- [ ] Test environment variable availability in preview deployments

### Phase 3: Backend Updates
- [ ] Update app/core/config.py with staging Auth0 settings
- [ ] Modify app/auth/auth0.py for environment-aware configuration
- [ ] Test local development with staging Auth0
- [ ] Verify backend can switch between production and staging Auth0

### Phase 4: Frontend Updates
- [ ] Create environment-aware Auth0 configuration utility
- [ ] Update frontend Auth0 initialization logic
- [ ] Test frontend authentication with staging Auth0
- [ ] Verify callback handling for preview URLs

### Phase 5: Testing and Validation
- [ ] Create test PR to generate preview environment
- [ ] Test complete authentication flow in preview environment
- [ ] Verify production authentication unaffected
- [ ] Document testing results and any issues found

### Phase 6: Documentation and Handoff
- [ ] Create operational procedures for staging Auth0 management
- [ ] Document troubleshooting procedures for staging authentication
- [ ] Provide access credentials and dashboard information
- [ ] Complete production deployment verification

## Contact and Support

**Auth0 Dashboard Access:**
- Production App: `https://manage.auth0.com/dashboard/us/dev-g8trhgbfdq2sk2m8/applications/[prod-app-id]`
- Staging App: `https://manage.auth0.com/dashboard/us/dev-g8trhgbfdq2sk2m8/applications/[staging-app-id]`

**Render Dashboard Access:**
- Service: `https://dashboard.render.com/web/[service-id]`
- Environment Variables: `https://dashboard.render.com/web/[service-id]/environment`

**Emergency Escalation:**
1. Production authentication issues → Immediate production rollback
2. Staging configuration issues → Fall back to production Auth0 temporarily
3. Preview environment failures → Disable preview generation until resolved

---

**Implementation Status**: Ready for immediate execution
**Risk Level**: LOW - Isolated staging setup with production protection
**Dependencies**: Auth0 dashboard access, Render dashboard access
**Impact**: Enables safe staging authentication testing for £925K opportunity

---

*This configuration establishes complete Auth0 staging isolation, protecting production authentication while enabling comprehensive preview environment testing for the MarketEdge Platform and Zebra Associates opportunity.*