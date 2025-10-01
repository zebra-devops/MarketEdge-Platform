import { ApplicationAccess } from '@/types/auth'
import { 
  getPrimaryApplication, 
  getApplicationRoute, 
  hasAnyApplicationAccess 
} from '@/utils/application-access'

/**
 * Determine where to redirect a user after login based on their application access
 */
export function getPostLoginRedirect(
  applicationAccess: ApplicationAccess[] | undefined,
  intendedDestination?: string
): string {
  // If user intended to go somewhere specific and has access, honor that
  if (intendedDestination && intendedDestination !== '/login') {
    // Check if the intended destination is an application route
    const appRoutes = ['/market-edge', '/causal-edge', '/value-edge']
    const isAppRoute = appRoutes.some(route => intendedDestination.startsWith(route))
    
    if (isAppRoute) {
      // Extract application name from route
      const appName = intendedDestination.includes('/market-edge') ? 'MARKET_EDGE' :
                     intendedDestination.includes('/causal-edge') ? 'CAUSAL_EDGE' :
                     intendedDestination.includes('/value-edge') ? 'VALUE_EDGE' : null
      
      if (appName) {
        const hasAccess = applicationAccess?.find(app => app.application === appName)?.has_access
        if (hasAccess) {
          return intendedDestination
        }
      }
    } else {
      // For non-application routes (like dashboard, settings), allow access
      return intendedDestination
    }
  }

  // If user has no application access, send to dashboard
  if (!hasAnyApplicationAccess(applicationAccess)) {
    return '/dashboard'
  }

  // Get user's primary application
  const primaryApp = getPrimaryApplication(applicationAccess)
  if (primaryApp) {
    return getApplicationRoute(primaryApp)
  }

  // Fallback to dashboard
  return '/dashboard'
}

/**
 * Check if a route requires specific application access
 */
export function getRequiredApplicationForRoute(pathname: string): string | null {
  if (pathname.startsWith('/market-edge')) return 'MARKET_EDGE'
  if (pathname.startsWith('/causal-edge')) return 'CAUSAL_EDGE'
  if (pathname.startsWith('/value-edge')) return 'VALUE_EDGE'
  return null
}

/**
 * Check if user can access a given route
 */
export function canAccessRoute(
  pathname: string,
  applicationAccess: ApplicationAccess[] | undefined
): boolean {
  const requiredApp = getRequiredApplicationForRoute(pathname)
  
  if (!requiredApp) {
    // Non-application routes are generally accessible
    return true
  }

  const access = applicationAccess?.find(app => app.application === requiredApp)
  return access?.has_access || false
}