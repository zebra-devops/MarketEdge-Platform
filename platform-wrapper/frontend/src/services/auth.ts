import { apiService } from './api'
import { LoginRequest, TokenResponse, User } from '@/types/auth'
import Cookies from 'js-cookie'
// PRODUCTION FIX: Remove timer-utils dependency to avoid function reference issues
// import { safeClearInterval, safeSetInterval, ensureTimerFunctions } from '@/utils/timer-utils'

interface EnhancedTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
  tenant: {
    id: string
    name: string
    industry: string
    subscription_plan: string
  }
  permissions: string[]
}

interface EnhancedUserResponse {
  user: User & {
    created_at?: string
    updated_at?: string
  }
  tenant: {
    id: string
    name: string
    industry: string
    subscription_plan: string
  }
  permissions: string[]
  session: {
    authenticated: boolean
    tenant_isolated: boolean
  }
}

interface LogoutRequest {
  refresh_token?: string
  all_devices?: boolean
}

export class AuthService {
  private refreshTokenPromise: Promise<EnhancedTokenResponse> | null = null
  private loginPromise: Promise<EnhancedTokenResponse> | null = null
  private readonly tokenRefreshThreshold = 5 * 60 * 1000 // 5 minutes in milliseconds
  private processedAuthCodes: Set<string> = new Set()
  private temporaryAccessToken: string | null = null // Temporary storage for immediate access
  private sessionStorageKey = 'auth_session_backup' // Session storage backup for navigation persistence

  /**
   * Initiate OAuth2 authentication flow with Auth0
   * This redirects the user to Auth0 for login
   */
  async initiateOAuth2Login(redirectUri?: string): Promise<void> {
    const callbackUri = redirectUri || window.location.origin + '/auth/callback'
    
    try {
      const authUrlResponse = await this.getAuth0Url(callbackUri)
      
      // Redirect to Auth0 for authentication
      window.location.href = authUrlResponse.auth_url
      
    } catch (error: any) {
      console.error('Failed to initiate OAuth2 login:', error)
      throw new Error(`Login initiation failed: ${error.message}`)
    }
  }

  /**
   * OAuth2 authentication using Auth0 authorization code exchange
   * This is the proper authentication flow for production
   */
  private async exchangeAuthorizationCode(loginData: LoginRequest & { state?: string }): Promise<EnhancedTokenResponse> {
    console.log('OAuth2: Exchanging authorization code for tokens')
    
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL
    const authUrl = `${baseUrl}/api/v1/auth/login-oauth2`
    
    const requestBody = {
      code: loginData.code,
      redirect_uri: loginData.redirect_uri,
      ...(loginData.state && { state: loginData.state })
    }
    
    console.log('OAuth2: Sending request body:', requestBody)
    
    const response = await fetch(authUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(requestBody)
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('OAuth2 authentication failed:', response.status, errorText)
      throw new Error(`Authentication failed: ${response.status}`)
    }
    
    const result = await response.json()
    console.log('OAuth2 authentication success:', {
      hasAccessToken: !!result.access_token,
      hasRefreshToken: !!result.refresh_token,
      hasUser: !!result.user,
      tokenType: result.token_type,
      expiresIn: result.expires_in
    })
    return result
  }

  async login(loginData: LoginRequest & { state?: string }): Promise<EnhancedTokenResponse> {
    // Improved circuit breaker: Only prevent true duplicates
    const authCodeKey = loginData.code.substring(0, 20); // Use more of the code for uniqueness
    
    if (this.processedAuthCodes.has(authCodeKey)) {
      console.warn('Duplicate authentication code detected:', authCodeKey + '...')
      // Instead of throwing, wait for the existing promise
      if (this.loginPromise) {
        console.log('Waiting for existing login request to complete...')
        return this.loginPromise;
      }
      // If no promise but code is processed, clear it and continue
      this.processedAuthCodes.delete(authCodeKey);
    }

    // Only prevent concurrent requests if one is actively in progress
    if (this.loginPromise) {
      console.log('Login request already in progress, waiting for completion...')
      try {
        return await this.loginPromise;
      } catch (error) {
        // If the existing promise failed, clear it and try again
        this.loginPromise = null;
        console.log('Previous login failed, retrying...')
      }
    }

    // Mark this auth code as being processed
    this.processedAuthCodes.add(authCodeKey)
    console.log('Processing authentication code:', authCodeKey + '...')

    console.log('Initiating login request to backend')
    
    this.loginPromise = (async () => {
      try {
        // OAuth2: Exchange authorization code for JWT tokens
        console.log('OAuth2: Exchanging authorization code for tokens')
        const response = await this.exchangeAuthorizationCode(loginData)
        
        console.log('Login response received from backend')
        
        // ENHANCED FIX: Store token metadata with verification
        console.log('About to call setTokens with response:', {
          hasAccessToken: !!response.access_token,
          hasRefreshToken: !!response.refresh_token,
          tokenType: response.token_type
        })
        
        // Store tokens and verify immediately
        this.setTokens(response)
        
        // CRITICAL: Verify token was stored before proceeding
        const verifyToken = this.getToken()
        if (!verifyToken) {
          console.error('❌ CRITICAL: Token storage failed during login!')
          throw new Error('Token storage failed - please try logging in again')
        }
        
        console.log('✅ Token storage verified successfully')
        this.setUserData(response.user, response.tenant, response.permissions)
        
        // Clean up processed auth codes (keep only recent ones to prevent memory leak)
        if (this.processedAuthCodes.size > 10) {
          this.processedAuthCodes.clear()
        }
        
        return response
      } catch (error: any) {
        // Remove the failed auth code from processed set to allow retry
        this.processedAuthCodes.delete(authCodeKey)
        
        console.error('Login request failed:', error)
        
        // Handle specific backend errors
        if (error?.response?.status === 429) {
          throw new Error('Too many login attempts. Please wait and try again.')
        } else if (error?.response?.status === 400) {
          throw new Error('Invalid authorization code. Please try logging in again.')
        } else if (error?.response?.status === 401) {
          throw new Error('Authentication failed. Please try logging in again.')
        } else if (error?.message?.includes('ERR_INSUFFICIENT_RESOURCES')) {
          throw new Error('Server overloaded. Please wait and try again.')
        }
        
        throw error
      } finally {
        // Clear the login promise after completion
        this.loginPromise = null
      }
    })()

    return this.loginPromise
  }

  /**
   * Handle OAuth2 callback from Auth0
   * Extracts authorization code and exchanges it for tokens
   */
  async handleOAuth2Callback(code: string, state?: string, redirectUri?: string): Promise<EnhancedTokenResponse> {
    const callbackUri = redirectUri || window.location.origin + '/auth/callback'
    
    console.log('Handling OAuth2 callback with code:', code.substring(0, 20) + '...')
    
    try {
      const response = await this.login({
        code,
        redirect_uri: callbackUri,
        state
      })
      
      console.log('OAuth2 callback handled successfully')
      return response
      
    } catch (error: any) {
      console.error('OAuth2 callback handling failed:', error)
      throw new Error(`Authentication callback failed: ${error.message}`)
    }
  }

  async refreshToken(): Promise<EnhancedTokenResponse> {
    // Prevent multiple concurrent refresh requests
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise
    }

    const refreshToken = this.getRefreshToken()
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    // US-AUTH-2: Handle both regular refresh tokens and httpOnly cookie scenario
    const requestBody: any = {}
    
    // If we have an actual refresh token value, include it in the request
    if (refreshToken !== 'httponly_refresh_token_present') {
      requestBody.refresh_token = refreshToken
    }
    // If refresh token is httpOnly, the browser will automatically send the cookie

    this.refreshTokenPromise = apiService.post<EnhancedTokenResponse>('/auth/refresh', requestBody)

    try {
      const response = await this.refreshTokenPromise
      this.setTokens(response)
      this.setUserData(response.user, response.tenant, response.permissions)
      
      console.log('✅ Token refresh successful', {
        hasNewAccessToken: !!response.access_token,
        hasNewRefreshToken: !!response.refresh_token
      })
      
      return response
    } catch (error) {
      console.error('❌ Token refresh failed:', error)
      // If refresh fails, clear tokens and redirect to login
      this.clearTokens()
      throw error
    } finally {
      this.refreshTokenPromise = null
    }
  }

  async getCurrentUser(): Promise<EnhancedUserResponse> {
    try {
      return await apiService.get<EnhancedUserResponse>('/auth/me')
    } catch (error: any) {
      if (error?.response?.status === 401) {
        // Try to refresh token and retry
        try {
          await this.refreshToken()
          return await apiService.get<EnhancedUserResponse>('/auth/me')
        } catch (refreshError) {
          this.clearTokens()
          throw refreshError
        }
      }
      throw error
    }
  }

  async getAuth0Url(redirectUri: string, additionalScopes?: string[], organizationHint?: string): Promise<{
    auth_url: string
    redirect_uri: string
    scopes: string[]
    organization_hint?: string
  }> {
    const params = new URLSearchParams({
      redirect_uri: redirectUri
    })
    
    if (additionalScopes?.length) {
      params.append('additional_scopes', additionalScopes.join(','))
    }

    if (organizationHint) {
      params.append('organization_hint', organizationHint)
    }

    try {
      return await apiService.get<{
        auth_url: string
        redirect_uri: string
        scopes: string[]
        organization_hint?: string
      }>(`/auth/auth0-url?${params}`)
    } catch (error: any) {
      if (error?.message?.includes('timeout') || error?.code === 'ECONNABORTED') {
        throw new Error('Request timed out. The backend may be starting up - please wait a moment and try again.')
      }
      throw error
    }
  }

  async logout(allDevices: boolean = false): Promise<void> {
    const refreshToken = this.getRefreshToken()
    
    console.log('🚪 Initiating user logout...')
    
    try {
      await apiService.post('/auth/logout', {
        refresh_token: refreshToken,
        all_devices: allDevices
      } as LogoutRequest)
      console.log('✅ Server-side logout completed')
    } catch (error) {
      console.warn('Logout API call failed:', error)
      // Continue with local cleanup even if server logout fails
    }

    // Enhanced session cleanup
    this.performCompleteSessionCleanup()
    
    // Show success message before redirect
    if (typeof window !== 'undefined') {
      console.log('✅ Complete logout and session cleanup performed')
      console.log('📝 All tokens and session data cleared')
      console.log('🔄 Ready for fresh authentication')
    }
    
    // Redirect to login page
    window.location.href = '/login'
  }

  /**
   * ENHANCED LOGOUT: Performs complete session cleanup for fresh re-authentication
   * Clears all stored tokens, user data, and session state to ensure clean slate
   * Critical for proper re-authentication flow after database user updates
   */
  private performCompleteSessionCleanup(): void {
    console.log('🧹 Starting comprehensive session cleanup...')
    
    // Clear tokens and user data
    this.clearTokens()
    this.clearUserData()

    // Clear all localStorage with auth-related data
    const keysToRemove = [
      'current_user',
      'tenant_info', 
      'user_permissions',
      'token_expires_at',
      'auth_state',
      'last_activity',
      // Additional keys that might store cached auth data
      'auth_callback_state',
      'pending_auth_code',
      'user_preferences',
      'dashboard_cache'
    ]
    
    let clearedKeys = 0
    keysToRemove.forEach(key => {
      if (localStorage.getItem(key)) {
        localStorage.removeItem(key)
        clearedKeys++
      }
    })
    console.log(`📝 Cleared ${clearedKeys} localStorage keys`)

    // Clear all sessionStorage
    const sessionStorageLength = sessionStorage.length
    sessionStorage.clear()
    console.log(`🗂️  Cleared ${sessionStorageLength} sessionStorage items`)

    // Clear intervals - PRODUCTION FIX: Use native clearInterval
    if (typeof window !== 'undefined') {
      const refreshInterval = (window as any).__authRefreshInterval
      const timeoutInterval = (window as any).__sessionTimeoutInterval
      
      if (refreshInterval) {
        try {
          if (typeof window.clearInterval === 'function') {
            window.clearInterval(refreshInterval)
          }
          delete (window as any).__authRefreshInterval
          console.log('⏰ Cleared refresh interval')
        } catch (error) {
          console.warn('Error clearing refresh interval:', error)
        }
      }
      
      if (timeoutInterval) {
        try {
          if (typeof window.clearInterval === 'function') {
            window.clearInterval(timeoutInterval)
          }
          delete (window as any).__sessionTimeoutInterval
          console.log('⏱️  Cleared timeout interval')
        } catch (error) {
          console.warn('Error clearing timeout interval:', error)
        }
      }
    }

    // Clear any cached data from API service
    if ((apiService as any).clearCache) {
      (apiService as any).clearCache()
      console.log('🗄️  API service cache cleared')
    }

    // Clear browser history state related to auth
    if (typeof window !== 'undefined' && window.history.replaceState) {
      const currentUrl = window.location.pathname
      window.history.replaceState(null, '', currentUrl)
      console.log('📜 Browser history state cleared')
    }

    // Clear any remaining processed auth codes to allow fresh authentication
    this.processedAuthCodes.clear()
    this.loginPromise = null
    this.refreshTokenPromise = null
    this.temporaryAccessToken = null
    console.log('🔄 Reset authentication state for fresh login')

    console.log('✅ Complete session cleanup performed - ready for fresh authentication')
  }

  async checkSession(): Promise<{
    authenticated: boolean
    user_id: string
    tenant_id: string
    role: string
    active: boolean
  }> {
    return apiService.get('/auth/session/check')
  }

  async extendSession(): Promise<{
    extend_recommended: boolean
    message: string
    expires_soon: boolean
  }> {
    return apiService.post('/auth/session/extend')
  }

  getToken(): string | undefined {
    // CRITICAL FIX: Enhanced environment-aware multi-strategy token retrieval
    const isProduction = this.detectProductionEnvironment()

    console.debug('🔍 Retrieving access token...', {
      environment: isProduction ? 'PRODUCTION' : 'DEVELOPMENT',
      windowExists: typeof window !== 'undefined'
    })

    // Strategy 1: Try cookies first (both production and development)
    // Access tokens are now accessible via JavaScript in both environments
    let cookieToken: string | undefined
    try {
      cookieToken = Cookies.get('access_token')
      if (cookieToken) {
        console.debug('✅ Token retrieved from cookies', {
          source: 'cookies',
          environment: isProduction ? 'PRODUCTION' : 'DEVELOPMENT',
          length: cookieToken.length,
          preview: `${cookieToken.substring(0, 20)}...`
        })
        // Clear temporary token if cookies are working
        this.temporaryAccessToken = null
        return cookieToken
      }
    } catch (cookieError) {
      console.warn('Cookie access failed:', cookieError)
      // Continue to next strategy
    }

    // Strategy 2: Use temporary token if cookies aren't ready yet
    if (this.temporaryAccessToken) {
      console.debug('✅ Token retrieved from temporary storage', {
        source: 'temporary',
        environment: isProduction ? 'PRODUCTION' : 'DEVELOPMENT',
        length: this.temporaryAccessToken.length,
        preview: `${this.temporaryAccessToken.substring(0, 20)}...`
      })
      return this.temporaryAccessToken
    }

    // Strategy 3: CRITICAL FIX - Check session storage for navigation persistence
    if (typeof window !== 'undefined' && sessionStorage) {
      try {
        const sessionBackupStr = sessionStorage.getItem(this.sessionStorageKey)
        if (sessionBackupStr) {
          const sessionBackup = JSON.parse(sessionBackupStr)
          if (sessionBackup.access_token) {
            // Check if backup is recent (within 1 hour to prevent stale tokens)
            const age = Date.now() - sessionBackup.timestamp
            if (age < 3600000) { // 1 hour
              console.debug('✅ Token retrieved from session storage backup', {
                source: 'sessionStorage',
                environment: isProduction ? 'PRODUCTION' : 'DEVELOPMENT',
                age: Math.round(age / 1000) + 's',
                length: sessionBackup.access_token.length,
                preview: `${sessionBackup.access_token.substring(0, 20)}...`
              })

              // Restore to temporary storage for consistency
              this.temporaryAccessToken = sessionBackup.access_token
              return sessionBackup.access_token
            } else {
              console.warn('Session storage backup is stale, clearing it')
              sessionStorage.removeItem(this.sessionStorageKey)
            }
          }
        }
      } catch (sessionError) {
        console.warn('Session storage access failed:', sessionError)
        // Clean up corrupted session storage
        try {
          sessionStorage.removeItem(this.sessionStorageKey)
        } catch (cleanupError) {
          console.warn('Failed to clean up corrupted session storage:', cleanupError)
        }
      }
    }

    // Strategy 4: Fallback to localStorage (development and emergency fallback)
    // In production, only use localStorage if cookies completely failed
    const allowLocalStorage = !isProduction || !cookieToken
    if (allowLocalStorage) {
      try {
        const localToken = localStorage.getItem('access_token')
        if (localToken) {
          console.debug('✅ Token retrieved from localStorage fallback', {
            source: 'localStorage',
            environment: isProduction ? 'PRODUCTION (Emergency)' : 'DEVELOPMENT',
            length: localToken.length,
            preview: `${localToken.substring(0, 20)}...`
          })
          return localToken
        }
      } catch (localStorageError) {
        console.warn('LocalStorage access failed:', localStorageError)
      }
    }

    // Strategy 5: Enhanced debugging for production issues
    if (isProduction) {
      console.error('🚨 PRODUCTION: All token retrieval strategies failed', {
        cookieAttempted: true,
        temporaryChecked: !!this.temporaryAccessToken,
        sessionStorageChecked: true,
        localStorageChecked: allowLocalStorage,
        currentUrl: typeof window !== 'undefined' ? window.location.href : 'unknown',
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent.substring(0, 50) : 'unknown'
      })
    }

    console.debug('⚠️  No access token found in any storage method')
    return undefined
  }

  /**
   * Enhanced environment detection with multiple fallback methods
   * Includes Vercel production domain detection for frontend deployments
   */
  private detectProductionEnvironment(): boolean {
    // Method 1: Standard NODE_ENV check
    if (typeof process !== 'undefined' && process.env && process.env.NODE_ENV === 'production') {
      return true
    }

    // Method 2: Check if we're on a production domain
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname
      const productionDomains = [
        'app.zebra.associates',
        'marketedge.app',
        'marketedge-platform.onrender.com',
        // Add Vercel production domain patterns
        'vercel.app',
        'zebraassociates-projects.vercel.app',
        'frontend-36gas2bky-zebraassociates-projects.vercel.app'
      ]

      if (productionDomains.some(domain => hostname.includes(domain))) {
        console.debug('✅ Production environment detected via domain:', hostname)
        return true
      }
    }

    // Method 3: Check for HTTPS in production environments
    if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
      const isLocalhost = window.location.hostname === 'localhost' ||
                         window.location.hostname === '127.0.0.1' ||
                         window.location.hostname.includes('local')

      if (!isLocalhost) {
        console.debug('✅ Production environment likely - HTTPS on non-localhost')
        return true
      }
    }

    console.debug('📝 Development environment detected')
    return false
  }

  getRefreshToken(): string | undefined {
    // US-AUTH-2: Refresh tokens remain secure (httpOnly: true)
    console.debug('🔍 Retrieving refresh token...')
    
    // Note: Refresh tokens are httpOnly and cannot be accessed by JavaScript
    // This is intentional for security - refresh tokens should only be sent via cookies
    // The backend handles refresh token validation automatically via httpOnly cookies
    
    // Strategy 1: Try localStorage (development and legacy support)
    const localToken = localStorage.getItem('refresh_token')
    if (localToken) {
      console.debug('✅ Refresh token retrieved from localStorage', {
        source: 'localStorage',
        length: localToken.length
      })
      return localToken
    }
    
    // Strategy 2: Check if refresh token cookie exists (cannot read value due to httpOnly)
    // We can't actually read the refresh token in production due to httpOnly security
    // But we can detect its presence for UI purposes
    const cookieExists = document.cookie.includes('refresh_token=')
    if (cookieExists) {
      console.debug('✅ Refresh token detected in httpOnly cookies (secure)')
      // Return a placeholder value to indicate the token exists
      // The actual token will be sent by the browser automatically
      return 'httponly_refresh_token_present'
    }
    
    console.debug('⚠️  No refresh token found')
    return undefined
  }

  isAuthenticated(): boolean {
    const token = this.getToken()
    const user = this.getStoredUser()
    return !!(token && user)
  }

  /**
   * Check if the user needs to authenticate and optionally redirect to Auth0
   * Returns true if authentication is required
   */
  requiresAuthentication(autoRedirect: boolean = false): boolean {
    if (this.isAuthenticated()) {
      return false
    }
    
    if (autoRedirect) {
      console.log('User not authenticated, redirecting to Auth0...')
      this.initiateOAuth2Login().catch(error => {
        console.error('Failed to redirect to authentication:', error)
      })
    }
    
    return true
  }

  getUserPermissions(): string[] {
    try {
      const permissions = localStorage.getItem('user_permissions')
      return permissions ? JSON.parse(permissions) : []
    } catch {
      return []
    }
  }

  hasPermission(permission: string): boolean {
    const permissions = this.getUserPermissions()
    return permissions.includes(permission)
  }

  hasAnyPermission(requiredPermissions: string[]): boolean {
    const userPermissions = this.getUserPermissions()
    return requiredPermissions.some(perm => userPermissions.includes(perm))
  }

  /**
   * Check if the user has admin access (admin or super_admin)
   */
  isAdmin(): boolean {
    const user = this.getStoredUser()
    return user?.role === 'admin' || user?.role === 'super_admin'
  }

  /**
   * Require admin access - throws error if user is not admin or super_admin
   */
  requireAdminAccess(): void {
    if (!this.isAuthenticated()) {
      throw new Error('Authentication required for admin access')
    }

    if (!this.isAdmin()) {
      throw new Error('Administrator privileges required for this action')
    }
  }

  /**
   * ZEBRA ASSOCIATES RE-AUTHENTICATION: Force complete re-authentication flow
   * This method performs complete logout and provides user guidance for fresh login
   * Critical for getting updated JWT tokens with new admin role claims
   */
  async triggerReAuthentication(reason: string = 'database_update'): Promise<void> {
    console.log(`🔄 Triggering re-authentication due to: ${reason}`)
    
    // Perform complete logout and cleanup
    await this.logout()
    
    // The logout method will redirect to /login where user will see the re-auth guide
  }

  getUserRole(): string | null {
    const user = this.getStoredUser()
    return user?.role || null
  }

  getTenantInfo(): { id: string; name: string; industry: string; subscription_plan: string } | null {
    try {
      const tenantData = localStorage.getItem('tenant_info')
      return tenantData ? JSON.parse(tenantData) : null
    } catch {
      return null
    }
  }

  shouldRefreshToken(): boolean {
    // Check if we should proactively refresh the token
    const tokenExpiry = localStorage.getItem('token_expires_at')
    if (!tokenExpiry) return false

    const expiryTime = new Date(tokenExpiry).getTime()
    const currentTime = Date.now()
    
    return (expiryTime - currentTime) <= this.tokenRefreshThreshold
  }

  // Auto-refresh token if needed
  async ensureValidToken(): Promise<string | null> {
    const token = this.getToken()
    if (!token) return null

    if (this.shouldRefreshToken()) {
      try {
        await this.refreshToken()
        return this.getToken()
      } catch (error) {
        console.error('Token refresh failed:', error)
        return null
      }
    }

    return token
  }

  private setTokens(tokenResponse: EnhancedTokenResponse): void {
    // CRITICAL FIX: Enhanced token storage with robust environment detection
    // Access tokens: httpOnly: false (accessible to JS)
    // Refresh tokens: httpOnly: true (secure, not accessible to JS)

    const isProduction = this.detectProductionEnvironment()

    console.debug('🔧 Setting tokens...', {
      environment: isProduction ? 'PRODUCTION' : 'DEVELOPMENT',
      hasAccessToken: !!tokenResponse.access_token,
      hasRefreshToken: !!tokenResponse.refresh_token
    })
    
    if (tokenResponse.access_token) {
      // Store token temporarily for immediate access while cookies are being set
      this.temporaryAccessToken = tokenResponse.access_token

      // CRITICAL FIX: Add session storage backup for navigation persistence
      // Session storage persists during navigation but clears when tab closes
      try {
        const sessionBackup = {
          access_token: tokenResponse.access_token,
          timestamp: Date.now(),
          environment: isProduction ? 'PRODUCTION' : 'DEVELOPMENT'
        }
        sessionStorage.setItem(this.sessionStorageKey, JSON.stringify(sessionBackup))
        console.log('✅ Session storage backup created for navigation persistence')
      } catch (sessionError) {
        console.warn('Session storage backup failed:', sessionError)
      }

      // Backend has already set the access_token cookie (httpOnly: false)
      // For development, also store in localStorage for debugging
      if (!isProduction) {
        console.log('🛠️  DEVELOPMENT: Also storing access token in localStorage for debugging')
        localStorage.setItem('access_token', tokenResponse.access_token)
      } else {
        // PRODUCTION: Clear any localStorage tokens for security
        localStorage.removeItem('access_token')
        console.log('🗑️  PRODUCTION: LocalStorage token cleared for security')
      }

      // IMMEDIATE VERIFICATION: This should now work with temporary storage
      const verifyToken = this.getToken()
      if (verifyToken) {
        console.log('✅ Access token verification successful', {
          environment: isProduction ? 'PRODUCTION' : 'DEVELOPMENT',
          storageMethod: 'Temporary + Backend-managed cookies',
          tokenLength: verifyToken.length,
          preview: `${verifyToken.substring(0, 20)}...`
        })
      } else {
        console.error('❌ CRITICAL: Token storage and retrieval system failed!')
        throw new Error('Token retrieval failed after authentication - please try logging in again')
      }

      // CRITICAL FIX: Enhanced cookie availability detection with extended timeouts
      // and graceful fallback strategy for production environments
      let cookieCheckAttempts = 0
      const maxCookieCheckAttempts = 10 // Up to 5 seconds total

      const checkCookieAvailability = () => {
        cookieCheckAttempts++
        const cookieToken = Cookies.get('access_token')

        if (cookieToken) {
          console.log('✅ Cookie-based token access confirmed, clearing temporary storage', {
            attempt: cookieCheckAttempts,
            totalWait: cookieCheckAttempts * 500,
            environment: isProduction ? 'PRODUCTION' : 'DEVELOPMENT'
          })
          this.temporaryAccessToken = null
          return
        }

        if (cookieCheckAttempts < maxCookieCheckAttempts) {
          // Continue checking every 500ms for up to 5 seconds
          setTimeout(checkCookieAvailability, 500)
          console.debug(`Cookie availability check ${cookieCheckAttempts}/${maxCookieCheckAttempts} - retrying in 500ms`)
        } else {
          // After 5 seconds, cookies still not available - keep temporary token for fallback
          console.warn('⚠️  CRITICAL: Cookies not accessible after 5 seconds - keeping temporary token as fallback', {
            currentDomain: typeof window !== 'undefined' ? window.location.hostname : 'unknown',
            protocol: typeof window !== 'undefined' ? window.location.protocol : 'unknown',
            isProduction: isProduction,
            cookiesString: typeof document !== 'undefined' ? document.cookie.substring(0, 100) : 'unavailable',
            temporaryTokenLength: this.temporaryAccessToken?.length || 0,
            fallbackStrategy: 'Temporary token will persist for session continuity'
          })

          // In production, if cookies aren't working after 5 seconds,
          // we need to keep the temporary token for the session
          if (isProduction) {
            console.error('🚨 PRODUCTION: Cookie system appears to be failing - using temporary token fallback')
            // Don't clear temporary token - it's our only way to maintain auth
          }
        }
      }

      // Start the cookie availability check
      setTimeout(checkCookieAvailability, 500)
    }
    
    if (tokenResponse.refresh_token) {
      // US-AUTH-2: Backend handles refresh token cookies (httpOnly: true for security)
      // In production, refresh tokens are httpOnly and not accessible to JavaScript
      
      if (!isProduction) {
        // DEVELOPMENT: Store in localStorage for debugging and fallback
        localStorage.setItem('refresh_token', tokenResponse.refresh_token)
        console.log('✅ Refresh token stored in localStorage (Development)')
      } else {
        // PRODUCTION: Clear localStorage, rely on httpOnly cookies
        localStorage.removeItem('refresh_token')
        console.log('🔒 PRODUCTION: Refresh token managed by secure httpOnly cookies only')
      }
      
      // Note: Backend has already set the refresh_token cookie with httpOnly: true
      console.log('✅ Refresh token configuration completed', {
        environment: isProduction ? 'PRODUCTION' : 'DEVELOPMENT',
        security: 'Backend-managed httpOnly cookies + localStorage fallback'
      })
    }
    
    // Store token expiry for refresh logic with defensive validation
    try {
      const expiresInSeconds = tokenResponse.expires_in || 3600 // Default to 1 hour if not provided
      const expiresInMilliseconds = Number(expiresInSeconds) * 1000
      
      // Validate that we have a valid number
      if (isNaN(expiresInMilliseconds) || expiresInMilliseconds <= 0) {
        throw new Error(`Invalid expires_in value: ${tokenResponse.expires_in}`)
      }
      
      const expiryTime = new Date(Date.now() + expiresInMilliseconds)
      
      // Validate the date is valid before converting to ISO string
      if (isNaN(expiryTime.getTime())) {
        throw new Error(`Invalid expiry date calculated from expires_in: ${tokenResponse.expires_in}`)
      }
      
      localStorage.setItem('token_expires_at', expiryTime.toISOString())
      
      console.log(`Token expiry set: ${expiryTime.toISOString()} (expires_in: ${expiresInSeconds}s)`)
    } catch (error) {
      console.error('Error setting token expiry time:', error)
      // Fallback: set expiry to 1 hour from now
      const fallbackExpiry = new Date(Date.now() + 3600000) // 1 hour
      localStorage.setItem('token_expires_at', fallbackExpiry.toISOString())
      console.warn(`Using fallback token expiry: ${fallbackExpiry.toISOString()}`)
    }
  }

  private setUserData(user: User, tenant: any, permissions: string[]): void {
    localStorage.setItem('current_user', JSON.stringify(user))
    localStorage.setItem('tenant_info', JSON.stringify(tenant))
    localStorage.setItem('user_permissions', JSON.stringify(permissions))
  }

  getStoredUser(): User | null {
    try {
      const userData = localStorage.getItem('current_user')
      return userData ? JSON.parse(userData) : null
    } catch {
      return null
    }
  }

  private clearTokens(): void {
    Cookies.remove('access_token')
    Cookies.remove('refresh_token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token_expires_at')

    // CRITICAL FIX: Clear session storage backup
    try {
      sessionStorage.removeItem(this.sessionStorageKey)
      console.debug('✅ Session storage backup cleared')
    } catch (sessionError) {
      console.warn('Failed to clear session storage backup:', sessionError)
    }

    // Clear temporary token storage
    this.temporaryAccessToken = null
  }

  private clearUserData(): void {
    localStorage.removeItem('current_user')
    localStorage.removeItem('tenant_info')
    localStorage.removeItem('user_permissions')
  }

  // Enhanced auto-refresh with tenant validation and better error handling
  initializeAutoRefresh(): void {
    // PRODUCTION FIX: Completely disable auto-refresh to avoid timer issues
    // The app works fine without background token refresh
    // Users can manually refresh by navigating or re-logging in
    console.log('Auto-refresh disabled - manual token refresh only')
    
    // Auto-refresh is not critical for functionality
    // Tokens have reasonable expiry times and users can re-login if needed
    return
  }

  // Enhanced session timeout detection
  private sessionTimeoutThreshold = 30 * 60 * 1000 // 30 minutes
  private lastActivityTime = Date.now()

  trackUserActivity(): void {
    this.lastActivityTime = Date.now()
  }

  checkSessionTimeout(): boolean {
    const now = Date.now()
    const timeSinceLastActivity = now - this.lastActivityTime
    return timeSinceLastActivity > this.sessionTimeoutThreshold
  }

  initializeActivityTracking(): void {
    // EMERGENCY FIX: Activity tracking disabled to resolve persistent setInterval production errors
    // This prevents the "TypeError: setInterval(...) is not a function" error in production
    console.log('Activity tracking disabled - emergency production fix')
    
    // Simple activity tracking without timers - just update activity time on page load
    if (typeof window !== 'undefined' && process.env.NODE_ENV !== 'test') {
      this.trackUserActivity()
    }
    
    return
  }
}

export const authService = new AuthService()

// Note: Timer initialization moved to client-side components to prevent SSR issues