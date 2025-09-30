import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { authService } from '@/services/auth'

interface RouteProtectionOptions {
  requireAuth?: boolean
  requiredPermissions?: string[]
  requiredRole?: string
  redirectTo?: string
  allowedRoles?: string[]
  requiredTenant?: string
  allowCrossTenant?: boolean
}

interface RouteProtectionState {
  isLoading: boolean
  isAuthorized: boolean
  user: any
  tenant: any
  permissions: string[]
}

export function useRouteProtection(options: RouteProtectionOptions = {}): RouteProtectionState {
  const {
    requireAuth = true,
    requiredPermissions = [],
    requiredRole,
    redirectTo = '/login',
    allowedRoles = [],
    requiredTenant,
    allowCrossTenant = false
  } = options

  const router = useRouter()
  const [state, setState] = useState<RouteProtectionState>({
    isLoading: true,
    isAuthorized: false,
    user: null,
    tenant: null,
    permissions: []
  })

  useEffect(() => {
    let mounted = true

    const checkAuthorization = async () => {
      try {
        // Check if authentication is required
        if (!requireAuth) {
          if (mounted) {
            setState({
              isLoading: false,
              isAuthorized: true,
              user: null,
              tenant: null,
              permissions: []
            })
          }
          return
        }

        // Check if user is authenticated
        const isAuthenticated = authService.isAuthenticated()
        if (!isAuthenticated) {
          if (mounted) {
            setState({
              isLoading: false,
              isAuthorized: false,
              user: null,
              tenant: null,
              permissions: []
            })
            router.push(redirectTo)
          }
          return
        }

        // Get user data
        const userResponse = await authService.getCurrentUser()
        const permissions = authService.getUserPermissions()
        const userRole = authService.getUserRole()

        // Check role requirements
        if (requiredRole && userRole !== requiredRole) {
          console.warn(`Access denied: Required role "${requiredRole}", but user has role "${userRole}"`)
          if (mounted) {
            setState({
              isLoading: false,
              isAuthorized: false,
              user: userResponse.user,
              tenant: userResponse.tenant,
              permissions
            })
            router.push('/unauthorized')
          }
          return
        }

        // Check allowed roles
        if (allowedRoles.length > 0 && userRole && !allowedRoles.includes(userRole)) {
          console.warn(`Access denied: User role "${userRole}" not in allowed roles:`, allowedRoles)
          if (mounted) {
            setState({
              isLoading: false,
              isAuthorized: false,
              user: userResponse.user,
              tenant: userResponse.tenant,
              permissions
            })
            router.push('/unauthorized')
          }
          return
        }

        // Check permission requirements
        if (requiredPermissions.length > 0) {
          const hasRequiredPermissions = authService.hasAnyPermission(requiredPermissions)
          if (!hasRequiredPermissions) {
            console.warn('Access denied: Missing required permissions:', requiredPermissions)
            if (mounted) {
              setState({
                isLoading: false,
                isAuthorized: false,
                user: userResponse.user,
                tenant: userResponse.tenant,
                permissions
              })
              router.push('/unauthorized')
            }
            return
          }
        }

        // Check tenant requirements for multi-tenant access control
        if (requiredTenant && !allowCrossTenant) {
          const userTenantId = userResponse.tenant?.id
          if (userTenantId !== requiredTenant) {
            console.warn(`Access denied: Tenant mismatch. Required: ${requiredTenant}, User: ${userTenantId}`)
            if (mounted) {
              setState({
                isLoading: false,
                isAuthorized: false,
                user: userResponse.user,
                tenant: userResponse.tenant,
                permissions
              })
              router.push('/unauthorized?reason=tenant_mismatch')
            }
            return
          }
        }

        // Check for admin-only cross-tenant access
        if (allowCrossTenant && userRole !== 'admin') {
          console.warn('Access denied: Cross-tenant access requires admin role')
          if (mounted) {
            setState({
              isLoading: false,
              isAuthorized: false,
              user: userResponse.user,
              tenant: userResponse.tenant,
              permissions
            })
            router.push('/unauthorized?reason=insufficient_role')
          }
          return
        }

        // User is authorized
        if (mounted) {
          setState({
            isLoading: false,
            isAuthorized: true,
            user: userResponse.user,
            tenant: userResponse.tenant,
            permissions
          })
        }

      } catch (error) {
        console.error('Route protection check failed:', error)
        if (mounted) {
          setState({
            isLoading: false,
            isAuthorized: false,
            user: null,
            tenant: null,
            permissions: []
          })
          
          // If it's an auth error, redirect to login
          if ((error as any)?.response?.status === 401) {
            router.push(redirectTo)
          } else {
            router.push('/error')
          }
        }
      }
    }

    checkAuthorization()

    return () => {
      mounted = false
    }
  }, [requireAuth, requiredPermissions, requiredRole, redirectTo, allowedRoles, router])

  return state
}

// Higher-order component for route protection  
export function withRouteProtection<P extends object>(
  Component: React.ComponentType<P>,
  options: RouteProtectionOptions = {}
) {
  return function ProtectedComponent(props: P) {
    const protection = useRouteProtection(options)

    if (protection.isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
        </div>
      )
    }

    if (!protection.isAuthorized) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
            <p className="text-gray-600">You do not have permission to access this page.</p>
          </div>
        </div>
      )
    }

    return <Component {...props} />
  }
}

// Specific hooks for common use cases
export function useAdminRoute() {
  return useRouteProtection({
    requireAuth: true,
    requiredRole: 'admin',
    redirectTo: '/login'
  })
}

export function useManagerRoute() {
  return useRouteProtection({
    requireAuth: true,
    allowedRoles: ['admin', 'manager'],
    redirectTo: '/login'
  })
}

export function useUserRoute(requiredPermissions: string[] = []) {
  return useRouteProtection({
    requireAuth: true,
    requiredPermissions,
    redirectTo: '/login'
  })
}

// Tenant-specific route protection hooks
export function useTenantRoute(tenantId: string, requiredPermissions: string[] = []) {
  return useRouteProtection({
    requireAuth: true,
    requiredTenant: tenantId,
    requiredPermissions,
    redirectTo: '/login'
  })
}

export function useCrossTenantAdminRoute(requiredPermissions: string[] = []) {
  return useRouteProtection({
    requireAuth: true,
    requiredRole: 'admin',
    allowCrossTenant: true,
    requiredPermissions,
    redirectTo: '/login'
  })
}

export function useOrgSpecificRoute(requiredPermissions: string[] = []) {
  return useRouteProtection({
    requireAuth: true,
    requiredPermissions: [...requiredPermissions, 'read:organization'],
    redirectTo: '/login'
  })
}