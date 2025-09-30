'use client'

import { useState, useEffect, createContext, useContext } from 'react'
import { User } from '@/types/auth'
import { authService } from '@/services/auth'
import { hasApplicationAccess as checkAppAccess, getAccessibleApplications as getApps } from '@/utils/application-access'
import { normalizeApplicationAccess } from '@/utils/application-access-fix'
// PRODUCTION FIX: Remove timer-utils dependency to avoid function reference issues
// import { safeClearInterval, ensureTimerFunctions } from '@/utils/timer-utils'

interface EnhancedUser extends User {
  created_at?: string
  updated_at?: string
}

interface TenantInfo {
  id: string
  name: string
  industry: string
  subscription_plan: string
}

interface AuthState {
  user: EnhancedUser | null
  tenant: TenantInfo | null
  permissions: string[]
  isLoading: boolean
  isAuthenticated: boolean
  isInitialized: boolean
}

interface AuthContextType extends AuthState {
  login: (loginData: { code: string; redirect_uri: string; state?: string }) => Promise<any>
  logout: (allDevices?: boolean) => Promise<void>
  refreshUser: () => Promise<void>
  hasPermission: (permission: string) => boolean
  hasAnyPermission: (permissions: string[]) => boolean
  hasRole: (role: string) => boolean
  checkSession: () => Promise<any>
  extendSession: () => Promise<any>
  getTenantContext: () => TenantInfo | null
  validateTenantAccess: (requiredTenant: string) => boolean
  hasApplicationAccess: (application: string) => boolean
  getAccessibleApplications: () => string[]
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuthContext = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider')
  }
  return context
}

export const useAuth = (): AuthContextType => {
  const [state, setState] = useState<AuthState>({
    user: null,
    tenant: null,
    permissions: [],
    isLoading: true,
    isAuthenticated: false,
    isInitialized: false
  })

  useEffect(() => {
    initializeAuth()
  }, [])

  // Initialize timer-based features only on client-side after mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // PRODUCTION FIX: Simplified timer initialization
      console.log('Initializing auth services with native timer support')
      
      // Initialize auto-refresh and activity tracking
      authService.initializeAutoRefresh()
      authService.initializeActivityTracking()

      // Cleanup function to clear intervals when component unmounts
      return () => {
        const refreshInterval = (window as any).__authRefreshInterval
        const timeoutInterval = (window as any).__sessionTimeoutInterval
        
        if (refreshInterval) {
          try {
            if (typeof window.clearInterval === 'function') {
              window.clearInterval(refreshInterval)
            }
            delete (window as any).__authRefreshInterval
          } catch (error) {
            console.warn('Error clearing refresh interval in cleanup:', error)
          }
        }
        
        if (timeoutInterval) {
          try {
            if (typeof window.clearInterval === 'function') {
              window.clearInterval(timeoutInterval)
            }
            delete (window as any).__sessionTimeoutInterval
          } catch (error) {
            console.warn('Error clearing timeout interval in cleanup:', error)
          }
        }
      }
    }
  }, [state.isAuthenticated]) // Re-initialize when auth state changes

  const initializeAuth = async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }))


      // CRITICAL FIX: Enhanced token detection with comprehensive logging
      console.log('🔍 Initializing authentication...')

      // First check if we have tokens stored
      const hasToken = authService.getToken()
      const hasRefreshToken = authService.getRefreshToken()
      const storedUser = authService.getStoredUser ? authService.getStoredUser() : null

      console.log('Token Status:', {
        accessToken: hasToken ? 'FOUND' : 'MISSING',
        refreshToken: hasRefreshToken ? 'FOUND' : 'MISSING',
        storedUser: storedUser ? `${storedUser.email} (${storedUser.role})` : 'MISSING'
      })

      // Check if user has valid authentication
      if (authService.isAuthenticated()) {
        console.log('✅ Auth service reports user as authenticated, fetching user data...')
        
        try {
          // Get current user data from backend to ensure it's still valid
          const userResponse = await authService.getCurrentUser()
          const permissions = authService.getUserPermissions ? authService.getUserPermissions() : []
          
          console.log('✅ Successfully retrieved user data from backend:', {
            email: userResponse.user?.email || userResponse.email,
            role: userResponse.user?.role || userResponse.role,
            tenant: userResponse.tenant?.name,
            permissions: permissions.length
          })
          
          // Normalize user data to ensure application_access is in correct format
          const normalizedUser = normalizeApplicationAccess(userResponse.user || userResponse)

          setState({
            user: normalizedUser,
            tenant: userResponse.tenant || null,
            permissions,
            isLoading: false,
            isAuthenticated: true,
            isInitialized: true
          })
        } catch (error: any) {
          console.error('❌ Failed to get current user:', error)
          console.log('Token validation failed, will attempt refresh or clear auth...')
          
          // Check if it's a token expiry issue (401) and we have a refresh token
          if (error?.response?.status === 401 && hasRefreshToken) {
            console.log('🔄 Attempting token refresh due to 401 error...')
            try {
              const refreshResponse = await authService.refreshToken()
              console.log('✅ Token refresh successful, retrying user fetch...')
              
              // Retry getting user data with new token
              const userResponse = await authService.getCurrentUser()
              const permissions = authService.getUserPermissions ? authService.getUserPermissions() : []

              // Normalize user data to ensure application_access is in correct format
              const normalizedUser = normalizeApplicationAccess(userResponse.user || userResponse)

              setState({
                user: normalizedUser,
                tenant: userResponse.tenant || null,
                permissions,
                isLoading: false,
                isAuthenticated: true,
                isInitialized: true
              })
              
              console.log('✅ Successfully recovered authentication via token refresh')
              return
            } catch (refreshError) {
              console.error('❌ Token refresh failed:', refreshError)
            }
          }
          
          // Clear invalid tokens and redirect to login
          console.log('🧹 Clearing invalid authentication tokens...')
          await authService.logout()
          setState({
            user: null,
            tenant: null,
            permissions: [],
            isLoading: false,
            isAuthenticated: false,
            isInitialized: true
          })
        }
      } else {
        console.log('⚠️  Auth service reports user as not authenticated')
        
        // Check if we have tokens but auth service doesn't recognize them
        if (hasToken) {
          console.log('🔍 Found token but auth service says not authenticated - attempting validation...')
          try {
            // Try to validate the token by calling the backend
            const userResponse = await authService.getCurrentUser()
            console.log('✅ Token is actually valid! Updating auth state...')
            
            const permissions = authService.getUserPermissions ? authService.getUserPermissions() : []

            // Normalize user data to ensure application_access is in correct format
            const normalizedUser = normalizeApplicationAccess(userResponse.user || userResponse)

            setState({
              user: normalizedUser,
              tenant: userResponse.tenant || null,
              permissions,
              isLoading: false,
              isAuthenticated: true,
              isInitialized: true
            })
            return
          } catch (validationError) {
            console.log('❌ Token validation failed, clearing auth state')
          }
        }
        
        setState({
          user: null,
          tenant: null,
          permissions: [],
          isLoading: false,
          isAuthenticated: false,
          isInitialized: true
        })
      }
    } catch (error) {
      console.error('❌ Auth initialization failed with unexpected error:', error)
      setState({
        user: null,
        tenant: null,
        permissions: [],
        isLoading: false,
        isAuthenticated: false,
        isInitialized: true
      })
    }
  }

  const login = async (loginData: { code: string; redirect_uri: string; state?: string }) => {
    setState(prev => ({ ...prev, isLoading: true }))
    
    try {
      const response = await authService.login(loginData)
      
      setState({
        user: response.user || response,
        tenant: response.tenant || null,
        permissions: response.permissions || [],
        isLoading: false,
        isAuthenticated: true,
        isInitialized: true
      })

      return response
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        user: null,
        tenant: null,
        permissions: [],
        isAuthenticated: false
      }))
      throw error
    }
  }

  const logout = async (allDevices: boolean = false) => {
    setState(prev => ({ ...prev, isLoading: true }))
    
    try {
      await authService.logout(allDevices)
    } catch (error) {
      console.warn('Logout error:', error)
    } finally {
      setState({
        user: null,
        tenant: null,
        permissions: [],
        isLoading: false,
        isAuthenticated: false,
        isInitialized: true
      })
    }
  }

  const refreshUser = async () => {
    try {
      const userResponse = await authService.getCurrentUser()
      const permissions = authService.getUserPermissions ? authService.getUserPermissions() : []

      // Normalize user data to ensure application_access is in correct format
      const normalizedUser = normalizeApplicationAccess(userResponse.user || userResponse)

      setState(prev => ({
        ...prev,
        user: normalizedUser,
        tenant: userResponse.tenant || null,
        permissions
      }))
    } catch (error) {
      console.error('Failed to refresh user data:', error)
      // Clear auth state on refresh failure
      setState(prev => ({
        ...prev,
        user: null,
        tenant: null,
        permissions: [],
        isAuthenticated: false
      }))
      await authService.logout()
      throw error
    }
  }

  const hasPermission = (permission: string): boolean => {
    return authService.hasPermission ? authService.hasPermission(permission) : false
  }

  const hasAnyPermission = (permissions: string[]): boolean => {
    return authService.hasAnyPermission ? authService.hasAnyPermission(permissions) : false
  }

  const hasRole = (role: string): boolean => {
    return authService.getUserRole ? authService.getUserRole() === role : false
  }

  const checkSession = async () => {
    try {
      return authService.checkSession ? await authService.checkSession() : { valid: true }
    } catch (error) {
      console.error('Session check failed:', error)
      throw error
    }
  }

  const extendSession = async () => {
    try {
      return authService.extendSession ? await authService.extendSession() : { extended: true }
    } catch (error) {
      console.error('Session extension failed:', error)
      throw error
    }
  }

  const getTenantContext = (): TenantInfo | null => {
    return state.tenant
  }

  const validateTenantAccess = (requiredTenant: string): boolean => {
    if (!state.tenant || !state.isAuthenticated) {
      return false
    }
    return state.tenant.id === requiredTenant
  }

  const hasApplicationAccess = (application: string): boolean => {
    return checkAppAccess(state.user?.application_access, application as any)
  }

  const getAccessibleApplications = (): string[] => {
    return getApps(state.user?.application_access)
  }

  return {
    ...state,
    login,
    logout,
    refreshUser,
    hasPermission,
    hasAnyPermission,
    hasRole,
    checkSession,
    extendSession,
    getTenantContext,
    validateTenantAccess,
    hasApplicationAccess,
    getAccessibleApplications
  }
}

export { AuthContext }