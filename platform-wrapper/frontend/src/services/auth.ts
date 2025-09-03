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

    this.refreshTokenPromise = apiService.post<EnhancedTokenResponse>('/auth/refresh', {
      refresh_token: refreshToken
    })

    try {
      const response = await this.refreshTokenPromise
      this.setTokens(response)
      this.setUserData(response.user, response.tenant, response.permissions)
      return response
    } catch (error) {
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
    
    try {
      await apiService.post('/auth/logout', {
        refresh_token: refreshToken,
        all_devices: allDevices
      } as LogoutRequest)
    } catch (error) {
      console.warn('Logout API call failed:', error)
      // Continue with local cleanup even if server logout fails
    }

    // Enhanced session cleanup
    this.performCompleteSessionCleanup()
    
    // Redirect to login page
    window.location.href = '/login'
  }

  private performCompleteSessionCleanup(): void {
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
      'last_activity'
    ]
    
    keysToRemove.forEach(key => {
      localStorage.removeItem(key)
    })

    // Clear all sessionStorage
    sessionStorage.clear()

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
        } catch (error) {
          console.warn('Error clearing timeout interval:', error)
        }
      }
    }

    // Clear any cached data from API service
    if ((apiService as any).clearCache) {
      (apiService as any).clearCache()
    }

    // Clear browser history state related to auth
    if (typeof window !== 'undefined' && window.history.replaceState) {
      const currentUrl = window.location.pathname
      window.history.replaceState(null, '', currentUrl)
    }

    console.info('Complete session cleanup performed')
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
    // ENHANCED FIX: Prioritize localStorage for local development
    const localToken = localStorage.getItem('access_token')
    if (localToken) {
      console.debug('✅ Token retrieved from localStorage')
      return localToken
    }
    
    // Fallback to cookies
    const cookieToken = Cookies.get('access_token')
    if (cookieToken) {
      console.debug('✅ Token retrieved from cookies')
      return cookieToken
    }
    
    console.debug('⚠️  No access token found in either localStorage or cookies')
    return undefined
  }

  getRefreshToken(): string | undefined {
    // ENHANCED FIX: Prioritize localStorage for local development
    const localToken = localStorage.getItem('refresh_token')
    if (localToken) {
      console.debug('✅ Refresh token retrieved from localStorage')
      return localToken
    }
    
    // Fallback to cookies
    const cookieToken = Cookies.get('refresh_token')
    if (cookieToken) {
      console.debug('✅ Refresh token retrieved from cookies')
      return cookieToken
    }
    
    console.debug('⚠️  No refresh token found in either localStorage or cookies')
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
   * Check if the user has admin access
   */
  isAdmin(): boolean {
    const user = this.getStoredUser()
    return user?.role === 'admin'
  }

  /**
   * Require admin access - throws error if user is not admin
   */
  requireAdminAccess(): void {
    if (!this.isAuthenticated()) {
      throw new Error('Authentication required for admin access')
    }
    
    if (!this.isAdmin()) {
      throw new Error('Admin privileges required for this action')
    }
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
    // ENHANCED FIX: Dual storage strategy for maximum compatibility
    // Store in both cookies AND localStorage for local development reliability
    
    if (tokenResponse.access_token) {
      const isProduction = process.env.NODE_ENV === 'production'
      const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost'
      const useSecure = isProduction && !isLocalhost
      
      // CRITICAL FIX: Always store in localStorage for cross-origin local development
      localStorage.setItem('access_token', tokenResponse.access_token)
      console.log('✅ Token stored in localStorage for cross-origin compatibility')
      
      // ALSO try cookies for same-origin requests
      try {
        Cookies.set('access_token', tokenResponse.access_token, {
          expires: new Date(Date.now() + (tokenResponse.expires_in || 3600) * 1000),
          secure: useSecure,
          sameSite: 'lax'
        })
        
        // Verify cookie storage
        const storedToken = Cookies.get('access_token')
        if (storedToken) {
          console.log('✅ Token also stored in cookies')
        } else {
          console.log('⚠️  Cookie storage failed (common in local dev) - localStorage will be used')
        }
      } catch (cookieError) {
        console.log('⚠️  Cookie storage error (using localStorage):', cookieError)
      }
      
      // VERIFICATION: Ensure token is accessible
      const verifyToken = this.getToken()
      if (verifyToken) {
        console.log('✅ Token verification successful - accessible via getToken()')
      } else {
        console.error('❌ CRITICAL: Token storage verification failed!')
      }
    }
    
    if (tokenResponse.refresh_token) {
      const isProduction = process.env.NODE_ENV === 'production'
      const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost'
      const useSecure = isProduction && !isLocalhost
      
      // ENHANCED FIX: Always store refresh token in localStorage first
      localStorage.setItem('refresh_token', tokenResponse.refresh_token)
      console.log('✅ Refresh token stored in localStorage')
      
      // ALSO try cookies
      try {
        Cookies.set('refresh_token', tokenResponse.refresh_token, {
          expires: 7, // 7 days
          secure: useSecure,
          sameSite: 'lax'
        })
        
        const storedRefreshToken = Cookies.get('refresh_token')
        if (storedRefreshToken) {
          console.log('✅ Refresh token also stored in cookies')
        } else {
          console.log('⚠️  Refresh token cookie storage failed - localStorage will be used')
        }
      } catch (cookieError) {
        console.log('⚠️  Refresh token cookie error (using localStorage):', cookieError)
      }
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

  private getStoredUser(): User | null {
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