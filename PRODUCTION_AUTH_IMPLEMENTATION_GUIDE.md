# MarketEdge Production Authentication Implementation Guide

## Critical Issues Resolved for £925K Opportunity

### **Authentication Flow for Frontend (app.zebra.associates)**

#### **Step 1: Get Auth0 Authorization URL**
```javascript
// Frontend call to get Auth0 URL
const response = await fetch('https://marketedge-platform.onrender.com/api/v1/auth/auth0-url', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include'
});

const { auth_url } = await response.json();
// Redirect user to auth_url for Auth0 login
window.location.href = auth_url;
```

#### **Step 2: Handle Auth0 Callback**
```javascript
// After Auth0 redirects back with authorization code
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');
const state = urlParams.get('state');

// Exchange code for JWT tokens
const response = await fetch('https://marketedge-platform.onrender.com/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include',
  body: JSON.stringify({
    code: code,
    redirect_uri: 'https://app.zebra.associates/auth/callback',
    state: state
  })
});

const authData = await response.json();
// Store the access_token for API calls
localStorage.setItem('access_token', authData.access_token);
```

#### **Step 3: Make Authenticated API Calls**
```javascript
// Example: Get feature flags with proper authentication
const getFeatureFlags = async () => {
  const token = localStorage.getItem('access_token');
  
  // CORS preflight will be handled automatically
  const response = await fetch('https://marketedge-platform.onrender.com/api/v1/admin/feature-flags', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'Origin': 'https://app.zebra.associates'
    },
    credentials: 'include'
  });

  if (response.status === 403) {
    throw new Error('User does not have admin privileges for feature flags');
  }
  
  if (response.status === 401) {
    // Token expired, redirect to re-auth
    redirectToAuth();
    return;
  }

  return await response.json();
};

// Example: Get enabled features for current user
const getEnabledFeatures = async () => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('https://marketedge-platform.onrender.com/api/v1/features/enabled', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    credentials: 'include'
  });

  if (response.status === 401) {
    redirectToAuth();
    return;
  }

  return await response.json();
};
```

### **Correct API Endpoints**

#### **Feature Flags (Admin Only)**
- **URL**: `GET /api/v1/admin/feature-flags`
- **Requires**: Admin role + JWT token
- **Response**: List of all feature flags

#### **Enabled Features (All Users)**
- **URL**: `GET /api/v1/features/enabled`
- **Requires**: Valid JWT token
- **Response**: Features enabled for the current user

#### **Authentication Endpoints**
- **Get Auth0 URL**: `GET /api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/auth/callback`
- **Login**: `POST /api/v1/auth/login` (with Auth0 code)
- **Check User**: `GET /api/v1/auth/me` (with Bearer token)

### **CORS Configuration (Already Working)**
- ✅ Origin `https://app.zebra.associates` is allowed
- ✅ Authorization header is allowed
- ✅ Credentials are enabled
- ✅ Preflight requests work correctly

### **Error Handling**

#### **Common Error Responses**
```javascript
// 401 Unauthorized - Token expired or missing
{
  "detail": "Not authenticated"
}

// 403 Forbidden - User lacks required permissions
{
  "detail": "Not authorized"  
}

// 404 Not Found - Endpoint doesn't exist
{
  "detail": "Not Found"
}
```

#### **Frontend Error Handling**
```javascript
const handleApiError = (response, error) => {
  if (response.status === 401) {
    // Clear stored token and redirect to auth
    localStorage.removeItem('access_token');
    redirectToAuth();
    return;
  }
  
  if (response.status === 403) {
    // Show permission denied message
    showError('You do not have permission to access this feature');
    return;
  }
  
  if (response.status === 404) {
    // Check if endpoint URL is correct
    console.error('API endpoint not found. Check URL pattern.');
    showError('Feature temporarily unavailable');
    return;
  }
  
  // Generic error handling
  showError(`API Error: ${error.message}`);
};
```

### **User Permissions**

For user `matt.lindop@zebra.associates`:
- **Role**: Admin (has access to `/api/v1/admin/*` endpoints)
- **Organization**: Default or configured organization
- **Access**: All feature flags and enabled features

### **Production Testing Commands**

```bash
# Test CORS preflight (✅ Working)
curl -X OPTIONS "https://marketedge-platform.onrender.com/api/v1/admin/feature-flags" \
  -H "Origin: https://app.zebra.associates" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization,Content-Type"

# Test authenticated endpoint (after getting token)
curl -X GET "https://marketedge-platform.onrender.com/api/v1/admin/feature-flags" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

### **Implementation Priority**

1. **Immediate**: Update frontend to use correct endpoint URLs
2. **Immediate**: Implement Auth0 OAuth flow in frontend
3. **Immediate**: Add proper JWT token handling
4. **Immediate**: Add error handling for 401/403 responses

This resolves all authentication and CORS issues for the £925K Odeon opportunity.