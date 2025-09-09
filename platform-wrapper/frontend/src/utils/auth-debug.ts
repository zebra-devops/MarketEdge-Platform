/**
 * Authentication debugging utilities
 * CRITICAL: Use this to diagnose token retrieval issues for Zebra Associates admin access
 */

import { authService } from '../services/auth'
import Cookies from 'js-cookie'

export interface AuthDebugInfo {
  tokenFound: boolean
  tokenSource: 'localStorage' | 'cookies' | 'authService' | 'none'
  tokenLength?: number
  tokenPreview?: string
  localStorageAvailable: boolean
  cookiesAvailable: boolean
  storageContents: {
    localStorage: string[]
    cookies: string
  }
  authServiceState: {
    isAuthenticated: boolean
    isAdmin: boolean
    userRole: string | null
    permissions: string[]
  }
}

/**
 * Comprehensive authentication state debugging
 */
export function debugAuthState(): AuthDebugInfo {
  console.log('🔍 Starting comprehensive auth debug...')
  
  // Test localStorage availability
  let localStorageAvailable = false
  try {
    localStorage.setItem('test', 'test')
    localStorage.removeItem('test')
    localStorageAvailable = true
  } catch (e) {
    console.warn('LocalStorage not available:', e)
  }
  
  // Test cookies availability  
  let cookiesAvailable = false
  try {
    document.cookie = 'test=test'
    cookiesAvailable = document.cookie.includes('test=test')
    // Clean up test cookie
    document.cookie = 'test=; expires=Thu, 01 Jan 1970 00:00:00 GMT'
  } catch (e) {
    console.warn('Cookies not available:', e)
  }
  
  // Try to get token from different sources
  let token: string | null = null
  let tokenSource: AuthDebugInfo['tokenSource'] = 'none'
  
  // Try localStorage first
  if (localStorageAvailable) {
    token = localStorage.getItem('access_token')
    if (token) tokenSource = 'localStorage'
  }
  
  // Try cookies
  if (!token && cookiesAvailable) {
    token = Cookies.get('access_token') || null
    if (token) tokenSource = 'cookies'
  }
  
  // Try auth service
  if (!token) {
    try {
      token = authService.getToken() || null
      if (token) tokenSource = 'authService'
    } catch (e) {
      console.warn('Auth service token retrieval failed:', e)
    }
  }
  
  // Get storage contents for debugging
  const storageContents = {
    localStorage: localStorageAvailable ? Object.keys(localStorage) : [],
    cookies: cookiesAvailable ? document.cookie : 'N/A'
  }
  
  // Get auth service state
  const authServiceState = {
    isAuthenticated: authService.isAuthenticated(),
    isAdmin: authService.isAdmin(),
    userRole: authService.getUserRole(),
    permissions: authService.getUserPermissions()
  }
  
  const debugInfo: AuthDebugInfo = {
    tokenFound: !!token,
    tokenSource,
    tokenLength: token?.length,
    tokenPreview: token ? `${token.substring(0, 20)}...${token.substring(token.length - 10)}` : undefined,
    localStorageAvailable,
    cookiesAvailable,
    storageContents,
    authServiceState
  }
  
  // Log comprehensive debug info
  console.log('🔍 Auth Debug Results:')
  console.log('   Token Status:', debugInfo.tokenFound ? '✅ FOUND' : '❌ MISSING')
  console.log('   Token Source:', debugInfo.tokenSource)
  if (debugInfo.tokenFound) {
    console.log('   Token Length:', debugInfo.tokenLength)
    console.log('   Token Preview:', debugInfo.tokenPreview)
  }
  console.log('   LocalStorage:', debugInfo.localStorageAvailable ? '✅ Available' : '❌ Blocked')
  console.log('   Cookies:', debugInfo.cookiesAvailable ? '✅ Available' : '❌ Blocked')
  console.log('   Auth State:', {
    authenticated: debugInfo.authServiceState.isAuthenticated,
    admin: debugInfo.authServiceState.isAdmin,
    role: debugInfo.authServiceState.userRole,
    permissions: debugInfo.authServiceState.permissions.length
  })
  
  return debugInfo
}

/**
 * Test admin API access specifically
 */
export async function testAdminApiAccess(): Promise<{
  success: boolean
  error?: string
  statusCode?: number
  debugInfo: AuthDebugInfo
}> {
  console.log('🧪 Testing admin API access...')
  
  const debugInfo = debugAuthState()
  
  try {
    // Import apiService dynamically to avoid circular dependencies
    const { apiService } = await import('../services/api')
    
    // Test a simple admin endpoint
    const response = await apiService.get('/admin/feature-flags')
    
    console.log('✅ Admin API test successful!')
    return {
      success: true,
      debugInfo
    }
  } catch (error: any) {
    console.error('❌ Admin API test failed:', error)
    
    return {
      success: false,
      error: error.message || 'Unknown error',
      statusCode: error.response?.status,
      debugInfo
    }
  }
}

/**
 * Force token refresh and re-test
 */
export async function refreshAndTest(): Promise<{
  refreshSuccess: boolean
  apiTestSuccess: boolean
  debugInfo: AuthDebugInfo
  errors: string[]
}> {
  console.log('🔄 Attempting token refresh and re-test...')
  
  const errors: string[] = []
  let refreshSuccess = false
  let apiTestSuccess = false
  
  try {
    // Try to refresh the token
    await authService.refreshToken()
    refreshSuccess = true
    console.log('✅ Token refresh successful')
  } catch (refreshError: any) {
    refreshSuccess = false
    errors.push(`Token refresh failed: ${refreshError.message}`)
    console.error('❌ Token refresh failed:', refreshError)
  }
  
  // Test API access regardless of refresh result
  const apiTest = await testAdminApiAccess()
  apiTestSuccess = apiTest.success
  
  if (!apiTestSuccess && apiTest.error) {
    errors.push(`API test failed: ${apiTest.error}`)
  }
  
  return {
    refreshSuccess,
    apiTestSuccess,
    debugInfo: apiTest.debugInfo,
    errors
  }
}

/**
 * Emergency token troubleshooting - try multiple recovery strategies
 */
export async function emergencyTokenRecovery(): Promise<{
  recoveryAttempts: string[]
  finalResult: AuthDebugInfo
  recommendations: string[]
}> {
  console.log('🚨 Starting emergency token recovery...')
  
  const recoveryAttempts: string[] = []
  const recommendations: string[] = []
  
  // Strategy 1: Check if user needs to re-authenticate
  let currentState = debugAuthState()
  recoveryAttempts.push(`Initial state: Token ${currentState.tokenFound ? 'found' : 'missing'} via ${currentState.tokenSource}`)
  
  if (!currentState.tokenFound) {
    recommendations.push('User needs to log in again - no valid token found')
    
    // Strategy 2: Check for tokens in different storage mechanisms
    if (!currentState.localStorageAvailable) {
      recommendations.push('LocalStorage blocked - may be due to browser security settings')
    }
    
    if (!currentState.cookiesAvailable) {
      recommendations.push('Cookies blocked - may be due to third-party cookie restrictions')
    }
    
    // Strategy 3: Check authentication service state
    if (!currentState.authServiceState.isAuthenticated) {
      recommendations.push('Auth service reports user as not authenticated')
    }
    
    if (!currentState.authServiceState.isAdmin) {
      recommendations.push('User lacks admin privileges - check role assignment')
    }
  } else {
    // Token exists but might not be working
    recoveryAttempts.push('Token found - testing API access...')
    
    const apiTest = await testAdminApiAccess()
    if (!apiTest.success) {
      if (apiTest.statusCode === 401) {
        recommendations.push('Token expired or invalid - attempt token refresh')
      } else if (apiTest.statusCode === 403) {
        recommendations.push('Token valid but insufficient permissions - check admin role')
      } else {
        recommendations.push(`API error ${apiTest.statusCode}: ${apiTest.error}`)
      }
      
      // Try refresh
      recoveryAttempts.push('Attempting token refresh...')
      const refreshResult = await refreshAndTest()
      recoveryAttempts.push(`Refresh result: ${refreshResult.refreshSuccess ? 'success' : 'failed'}`)
      
      currentState = refreshResult.debugInfo
    } else {
      recoveryAttempts.push('API access test successful')
      recommendations.push('Authentication working correctly')
    }
  }
  
  return {
    recoveryAttempts,
    finalResult: currentState,
    recommendations
  }
}

// Make functions available globally for browser console debugging
if (typeof window !== 'undefined') {
  (window as any).debugAuthState = debugAuthState;
  (window as any).testAdminApiAccess = testAdminApiAccess;
  (window as any).refreshAndTest = refreshAndTest;
  (window as any).emergencyTokenRecovery = emergencyTokenRecovery;
  
  console.log('🔧 Auth debug functions available in console:');
  console.log('   - debugAuthState()');
  console.log('   - testAdminApiAccess()');
  console.log('   - refreshAndTest()');
  console.log('   - emergencyTokenRecovery()');
}