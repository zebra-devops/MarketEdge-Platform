'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthContext } from '@/hooks/useAuth'
import { 
  hasApplicationAccess, 
  ApplicationName,
  getPrimaryApplication,
  getApplicationRoute 
} from '@/utils/application-access'

interface UseApplicationAccessOptions {
  redirectTo?: string
  redirectToPrimary?: boolean
}

/**
 * Hook for protecting application routes and handling access control
 */
export function useApplicationAccess(
  requiredApplication: ApplicationName,
  options: UseApplicationAccessOptions = {}
) {
  const { user, isLoading, isAuthenticated } = useAuthContext()
  const router = useRouter()
  const { redirectTo = '/dashboard', redirectToPrimary = false } = options

  const hasAccess = hasApplicationAccess(user?.application_access, requiredApplication)
  const isReady = !isLoading && isAuthenticated && user

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated || !user) {
        router.push('/login')
        return
      }

      if (!hasAccess) {
        if (redirectToPrimary) {
          const primaryApp = getPrimaryApplication(user.application_access)
          if (primaryApp) {
            const primaryRoute = getApplicationRoute(primaryApp)
            router.push(primaryRoute)
          } else {
            router.push(redirectTo)
          }
        } else {
          router.push(redirectTo)
        }
      }
    }
  }, [isLoading, isAuthenticated, user, hasAccess, router, redirectTo, redirectToPrimary])

  return {
    hasAccess,
    isLoading,
    isAuthenticated,
    user,
    isReady: isReady && hasAccess
  }
}

/**
 * Hook for checking if user has access to any applications
 */
export function useAnyApplicationAccess() {
  const { user, isLoading, isAuthenticated } = useAuthContext()
  
  const hasAnyAccess = user?.application_access?.some(app => app.has_access) || false
  const isReady = !isLoading && isAuthenticated && user

  return {
    hasAnyAccess,
    isLoading,
    isAuthenticated,
    user,
    isReady
  }
}