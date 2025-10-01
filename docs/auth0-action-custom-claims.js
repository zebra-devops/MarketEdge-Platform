/**
 * Auth0 Action: Add MarketEdge Custom Claims to Token
 *
 * Purpose: Enriches Auth0 access tokens with MarketEdge-specific user context
 *          (tenant_id, role, permissions, industry, organisation_name)
 *
 * Epic: US-2 - Add custom claims to Auth0 tokens
 * Part of: Epic #35 "One Auth to Rule Them All – Zebra-Safe Edition"
 *
 * SETUP INSTRUCTIONS:
 * ====================
 *
 * 1. Go to Auth0 Dashboard > Actions > Flows > Login
 * 2. Click "+" to create a new Custom Action
 * 3. Name: "MarketEdge Custom Claims"
 * 4. Trigger: Login / Post Login
 * 5. Copy this entire file content into the code editor
 * 6. Add Secrets (click "Secrets" icon on left sidebar):
 *    - MARKETEDGE_API_URL: Your backend URL (e.g., "https://marketedge-platform.onrender.com")
 *    - MARKETEDGE_API_SECRET: Generate a secure random string (min 32 chars)
 * 7. Click "Deploy"
 * 8. In the Login Flow, drag this action to run AFTER the Auth0 default action
 * 9. Apply the flow
 *
 * BACKEND CONFIGURATION:
 * ======================
 * Add to your backend .env file:
 *   AUTH0_ACTION_SECRET=<same secret as MARKETEDGE_API_SECRET above>
 *
 * NAMESPACE:
 * ==========
 * Auth0 requires custom claims to use a namespaced format to prevent
 * collisions with standard OIDC claims. We use: https://marketedge.com/
 *
 * CLAIMS ADDED:
 * =============
 * - https://marketedge.com/tenant_id: User's organisation UUID
 * - https://marketedge.com/role: User's role (super_admin, admin, manager, viewer)
 * - https://marketedge.com/permissions: Array of permission strings
 * - https://marketedge.com/industry: Organisation's industry type
 * - https://marketedge.com/organisation_name: Organisation name
 *
 * FLOW:
 * =====
 * 1. User authenticates with Auth0
 * 2. This action runs during token generation
 * 3. Action calls MarketEdge backend /api/v1/auth/user-context
 * 4. Backend returns user's tenant context
 * 5. Action adds custom claims to access token
 * 6. Token is issued to frontend
 *
 * ERROR HANDLING:
 * ===============
 * - If backend call fails, login proceeds with Auth0 defaults
 * - Errors are logged to Auth0 Monitoring > Logs
 * - Backend endpoint validates secret and returns 401 if invalid
 *
 * TESTING:
 * ========
 * After deployment, test by:
 * 1. Login as matt.lindop@zebra.associates
 * 2. Check token in browser DevTools > Application > Local Storage
 * 3. Decode token at jwt.io - verify custom claims are present
 * 4. Run US-0 smoke test: npm run test:smoke
 *
 * MONITORING:
 * ===========
 * - Auth0 Dashboard > Monitoring > Logs (search for "MarketEdge Custom Claims")
 * - Backend logs: grep "user_context" in application logs
 * - Token size should be < 3.5 KB (check in Auth0 dashboard)
 */

/**
 * Handler that will be called during the execution of a PostLogin flow.
 *
 * @param {Event} event - Details about the user and the context in which they are logging in.
 * @param {PostLoginAPI} api - Interface whose methods can be used to change the behavior of the login.
 */
exports.onExecutePostLogin = async (event, api) => {
  // Get configuration from Auth0 Secrets
  const MARKETEDGE_API_URL = event.secrets.MARKETEDGE_API_URL;
  const MARKETEDGE_API_SECRET = event.secrets.MARKETEDGE_API_SECRET;

  // Validate secrets are configured
  if (!MARKETEDGE_API_URL || !MARKETEDGE_API_SECRET) {
    console.error('[MarketEdge] Missing required secrets: MARKETEDGE_API_URL or MARKETEDGE_API_SECRET');
    // Don't block login - proceed without custom claims
    return;
  }

  // Extract user information
  const userId = event.user.user_id;
  const userEmail = event.user.email;

  console.log(`[MarketEdge] Fetching custom claims for user: ${userEmail} (${userId})`);

  try {
    // Call MarketEdge backend to get user context
    const response = await fetch(`${MARKETEDGE_API_URL}/api/v1/auth/user-context`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Auth0-Secret': MARKETEDGE_API_SECRET
      },
      body: JSON.stringify({
        auth0_id: userId,
        email: userEmail
      })
    });

    // Check if request was successful
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[MarketEdge] Backend returned error ${response.status}: ${errorText}`);

      // Log specific error cases
      if (response.status === 401) {
        console.error('[MarketEdge] Invalid API secret - check AUTH0_ACTION_SECRET matches backend');
      } else if (response.status === 404) {
        console.warn(`[MarketEdge] User not found in backend: ${userEmail}`);
      }

      // Don't block login - proceed without custom claims
      return;
    }

    // Parse user context from backend
    const userContext = await response.json();

    console.log(`[MarketEdge] Successfully fetched context for ${userEmail}:`, {
      tenant_id: userContext.tenant_id,
      role: userContext.role,
      industry: userContext.industry,
      permissions_count: userContext.permissions?.length || 0
    });

    // Auth0 namespace for custom claims (required by OIDC spec)
    const namespace = 'https://marketedge.com';

    // Add custom claims to access token
    // These will be available in the JWT payload
    api.accessToken.setCustomClaim(`${namespace}/tenant_id`, userContext.tenant_id);
    api.accessToken.setCustomClaim(`${namespace}/role`, userContext.role);
    api.accessToken.setCustomClaim(`${namespace}/permissions`, userContext.permissions);
    api.accessToken.setCustomClaim(`${namespace}/industry`, userContext.industry);
    api.accessToken.setCustomClaim(`${namespace}/organisation_name`, userContext.organisation_name);

    // Also add to ID token for consistency (optional)
    api.idToken.setCustomClaim(`${namespace}/tenant_id`, userContext.tenant_id);
    api.idToken.setCustomClaim(`${namespace}/role`, userContext.role);
    api.idToken.setCustomClaim(`${namespace}/organisation_name`, userContext.organisation_name);

    console.log(`[MarketEdge] Successfully added custom claims for ${userEmail}`);

  } catch (error) {
    // Log error but don't block login
    console.error('[MarketEdge] Error fetching user context:', error.message);
    console.error('[MarketEdge] Stack trace:', error.stack);

    // Log additional details for debugging
    console.error('[MarketEdge] API URL:', MARKETEDGE_API_URL);
    console.error('[MarketEdge] User email:', userEmail);

    // Continue with login even if custom claims fail
    // User will authenticate but may have limited context
  }
};

/**
 * Handler that will be invoked when this action is resuming after an external redirect.
 * If your onExecutePostLogin function does not perform a redirect, this function can be safely ignored.
 *
 * @param {Event} event - Details about the user and the context in which they are logging in.
 * @param {PostLoginAPI} api - Interface whose methods can be used to change the behavior of the login.
 */
exports.onContinuePostLogin = async (event, api) => {
  // Not used in this action - no external redirects
};

/*
 * DEPLOYMENT CHECKLIST:
 * =====================
 *
 * □ Secrets configured in Auth0 Dashboard
 * □ Backend AUTH0_ACTION_SECRET matches MARKETEDGE_API_SECRET
 * □ Backend /api/v1/auth/user-context endpoint deployed and accessible
 * □ Action deployed in Auth0 Dashboard
 * □ Action added to Login Flow (after Auth0 default action)
 * □ Login Flow applied
 * □ Test login with matt.lindop@zebra.associates
 * □ Verify custom claims present in token (jwt.io)
 * □ Run US-0 smoke test
 * □ Monitor Auth0 logs for errors
 * □ Monitor backend logs for user_context requests
 * □ Verify token size < 3.5 KB
 *
 * ROLLBACK PROCEDURE:
 * ===================
 * If issues occur:
 * 1. Go to Auth0 Dashboard > Actions > Flows > Login
 * 2. Remove "MarketEdge Custom Claims" action from flow
 * 3. Apply the flow
 * 4. Users will continue to authenticate but without custom claims
 * 5. Backend will fall back to internal token format (until US-3)
 *
 * VERSION: 1.0.0 (US-2)
 * CREATED: 2025-09-30
 * EPIC: #35 "One Auth to Rule Them All – Zebra-Safe Edition"
 */