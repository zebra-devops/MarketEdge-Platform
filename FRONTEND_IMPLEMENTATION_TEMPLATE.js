/**
 * MarketEdge Frontend Authentication & API Integration
 * Complete implementation for £925K Opportunity
 * 
 * This template resolves all authentication and CORS issues
 */

class MarketEdgeAPI {
  constructor() {
    this.baseURL = 'https://marketedge-platform.onrender.com/api/v1';
    this.redirectURI = 'https://app.zebra.associates/auth/callback';
    this.accessToken = this.getStoredToken();
  }

  // Token Management
  getStoredToken() {
    return localStorage.getItem('marketedge_access_token');
  }

  setToken(token) {
    this.accessToken = token;
    localStorage.setItem('marketedge_access_token', token);
  }

  clearToken() {
    this.accessToken = null;
    localStorage.removeItem('marketedge_access_token');
  }

  // Authentication Flow
  async initiateLogin() {
    try {
      const response = await fetch(`${this.baseURL}/auth/auth0-url?redirect_uri=${encodeURIComponent(this.redirectURI)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`Failed to get auth URL: ${response.status}`);
      }

      const data = await response.json();
      
      // Redirect to Auth0 login
      window.location.href = data.auth_url;
      
    } catch (error) {
      console.error('Login initiation error:', error);
      this.showError('Failed to initiate login. Please try again.');
    }
  }

  async handleAuthCallback() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');

      if (!code) {
        throw new Error('No authorization code received');
      }

      // Exchange code for tokens
      const response = await fetch(`${this.baseURL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          code: code,
          redirect_uri: this.redirectURI,
          state: state
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Authentication failed: ${errorData.detail || response.status}`);
      }

      const authData = await response.json();
      
      // Store tokens
      this.setToken(authData.access_token);
      
      // Store user info
      localStorage.setItem('marketedge_user', JSON.stringify(authData.user));
      localStorage.setItem('marketedge_tenant', JSON.stringify(authData.tenant));
      localStorage.setItem('marketedge_permissions', JSON.stringify(authData.permissions));

      return authData;

    } catch (error) {
      console.error('Auth callback error:', error);
      this.showError(`Authentication failed: ${error.message}`);
      throw error;
    }
  }

  // API Request Handler
  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Origin': 'https://app.zebra.associates'
    };

    // Add authorization header if token exists
    if (this.accessToken) {
      defaultHeaders['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const requestOptions = {
      credentials: 'include',
      headers: {
        ...defaultHeaders,
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, requestOptions);

      // Handle authentication errors
      if (response.status === 401) {
        this.clearToken();
        this.initiateLogin();
        throw new Error('Authentication expired. Please log in again.');
      }

      if (response.status === 403) {
        throw new Error('You do not have permission to access this feature.');
      }

      if (response.status === 404) {
        throw new Error('Feature not found. Please check if the endpoint is correct.');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error(`API Request Error (${endpoint}):`, error);
      throw error;
    }
  }

  // Feature Flags API (Admin Only)
  async getFeatureFlags(moduleId = null, enabledOnly = false) {
    const params = new URLSearchParams();
    if (moduleId) params.append('module_id', moduleId);
    if (enabledOnly) params.append('enabled_only', 'true');
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return await this.makeRequest(`/admin/feature-flags${query}`);
  }

  async createFeatureFlag(flagData) {
    return await this.makeRequest('/admin/feature-flags', {
      method: 'POST',
      body: JSON.stringify(flagData)
    });
  }

  async updateFeatureFlag(flagId, updates) {
    return await this.makeRequest(`/admin/feature-flags/${flagId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  // Features API (All Users)
  async getEnabledFeatures(moduleId = null) {
    const params = moduleId ? `?module_id=${encodeURIComponent(moduleId)}` : '';
    return await this.makeRequest(`/features/enabled${params}`);
  }

  async checkFeatureFlag(flagKey) {
    return await this.makeRequest(`/features/${encodeURIComponent(flagKey)}`);
  }

  // User API
  async getCurrentUser() {
    return await this.makeRequest('/auth/me');
  }

  async checkSession() {
    return await this.makeRequest('/auth/session/check');
  }

  // System API
  async getSystemStatus() {
    return await this.makeRequest('/system/status');
  }

  // Utility Methods
  isAuthenticated() {
    return !!this.accessToken;
  }

  getUserInfo() {
    const userStr = localStorage.getItem('marketedge_user');
    return userStr ? JSON.parse(userStr) : null;
  }

  getTenantInfo() {
    const tenantStr = localStorage.getItem('marketedge_tenant');
    return tenantStr ? JSON.parse(tenantStr) : null;
  }

  getUserPermissions() {
    const permsStr = localStorage.getItem('marketedge_permissions');
    return permsStr ? JSON.parse(permsStr) : [];
  }

  hasPermission(permission) {
    const permissions = this.getUserPermissions();
    return permissions.includes(permission);
  }

  isAdmin() {
    const user = this.getUserInfo();
    return user?.role === 'admin';
  }

  showError(message) {
    // Implement your error display logic
    console.error('MarketEdge API Error:', message);
    // Example: show toast notification, modal, etc.
    alert(`Error: ${message}`);
  }

  showSuccess(message) {
    // Implement your success display logic
    console.log('MarketEdge API Success:', message);
  }

  async logout() {
    try {
      await this.makeRequest('/auth/logout', {
        method: 'POST',
        body: JSON.stringify({
          refresh_token: localStorage.getItem('marketedge_refresh_token'),
          all_devices: false
        })
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear all stored data
      this.clearToken();
      localStorage.removeItem('marketedge_user');
      localStorage.removeItem('marketedge_tenant');
      localStorage.removeItem('marketedge_permissions');
      localStorage.removeItem('marketedge_refresh_token');
    }
  }
}

// Usage Examples
const api = new MarketEdgeAPI();

// Example: Initialize authentication on page load
document.addEventListener('DOMContentLoaded', async () => {
  if (window.location.pathname === '/auth/callback') {
    // Handle Auth0 callback
    try {
      await api.handleAuthCallback();
      api.showSuccess('Successfully logged in!');
      // Redirect to main app
      window.location.href = '/dashboard';
    } catch (error) {
      api.showError('Login failed. Please try again.');
      window.location.href = '/';
    }
    return;
  }

  // Check if user is authenticated
  if (api.isAuthenticated()) {
    try {
      // Verify session is still valid
      await api.checkSession();
      console.log('User is authenticated');
    } catch (error) {
      console.log('Session expired, redirecting to login');
      api.initiateLogin();
    }
  }
});

// Example: Load feature flags for admin users
async function loadFeatureFlags() {
  if (!api.isAdmin()) {
    api.showError('Admin access required to view feature flags');
    return;
  }

  try {
    const response = await api.getFeatureFlags();
    console.log('Feature flags:', response.feature_flags);
    // Display in UI
    displayFeatureFlags(response.feature_flags);
  } catch (error) {
    api.showError(`Failed to load feature flags: ${error.message}`);
  }
}

// Example: Load enabled features for current user
async function loadEnabledFeatures() {
  try {
    const response = await api.getEnabledFeatures();
    console.log('Enabled features:', response.enabled_features);
    // Configure app based on enabled features
    configureAppFeatures(response.enabled_features);
  } catch (error) {
    api.showError(`Failed to load enabled features: ${error.message}`);
  }
}

// Example: Check specific feature flag
async function checkFeature(flagKey) {
  try {
    const response = await api.checkFeatureFlag(flagKey);
    return response.enabled;
  } catch (error) {
    console.error(`Failed to check feature ${flagKey}:`, error);
    return false; // Default to disabled on error
  }
}

// Example implementations (customize for your UI framework)
function displayFeatureFlags(flags) {
  // Implement UI display logic
  console.log('Displaying feature flags:', flags);
}

function configureAppFeatures(enabledFeatures) {
  // Configure app based on enabled features
  console.log('Configuring app with features:', enabledFeatures);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = MarketEdgeAPI;
}

// Global access for browser environments
if (typeof window !== 'undefined') {
  window.MarketEdgeAPI = MarketEdgeAPI;
}