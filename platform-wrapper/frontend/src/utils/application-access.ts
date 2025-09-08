import { ApplicationAccess } from '@/types/auth'

export type ApplicationName = 'market_edge' | 'causal_edge' | 'value_edge'

/**
 * Check if a user has access to a specific application
 */
export function hasApplicationAccess(
  applicationAccess: ApplicationAccess[] | undefined,
  application: ApplicationName
): boolean {
  if (!applicationAccess || !Array.isArray(applicationAccess)) {
    return false
  }

  const access = applicationAccess.find(item => item.application === application)
  return access?.has_access || false
}

/**
 * Get all applications that a user has access to
 */
export function getAccessibleApplications(
  applicationAccess: ApplicationAccess[] | undefined
): ApplicationName[] {
  if (!applicationAccess || !Array.isArray(applicationAccess)) {
    return []
  }

  return applicationAccess
    .filter(item => item.has_access)
    .map(item => item.application)
}

/**
 * Get the user's primary (first accessible) application
 */
export function getPrimaryApplication(
  applicationAccess: ApplicationAccess[] | undefined,
  preferredOrder: ApplicationName[] = ['market_edge', 'causal_edge', 'value_edge']
): ApplicationName | null {
  const accessible = getAccessibleApplications(applicationAccess)
  
  if (accessible.length === 0) {
    return null
  }

  // Return the first application in preferred order that user has access to
  for (const app of preferredOrder) {
    if (accessible.includes(app)) {
      return app
    }
  }

  // Fallback to first accessible application
  return accessible[0] || null
}

/**
 * Get the route path for an application
 */
export function getApplicationRoute(application: ApplicationName): string {
  const routes: Record<ApplicationName, string> = {
    market_edge: '/market-edge',
    causal_edge: '/causal-edge',
    value_edge: '/value-edge'
  }
  
  return routes[application]
}

/**
 * Get application display information
 */
export function getApplicationInfo(application: ApplicationName) {
  const info: Record<ApplicationName, {
    name: string
    displayName: string
    description: string
    color: string
    themeColor: string
  }> = {
    market_edge: {
      name: 'Market Edge',
      displayName: 'Market Edge',
      description: 'Competitive Intelligence & Market Analysis',
      color: 'from-blue-500 to-indigo-600',
      themeColor: 'blue'
    },
    causal_edge: {
      name: 'Causal Edge', 
      displayName: 'Causal Edge',
      description: 'Business Process & Causal Analysis',
      color: 'from-green-500 to-emerald-600',
      themeColor: 'green'
    },
    value_edge: {
      name: 'Value Edge',
      displayName: 'Value Edge', 
      description: 'Value Engineering & ROI Analysis',
      color: 'from-purple-500 to-violet-600',
      themeColor: 'purple'
    }
  }
  
  return info[application]
}

/**
 * Check if user has access to any applications
 */
export function hasAnyApplicationAccess(
  applicationAccess: ApplicationAccess[] | undefined
): boolean {
  return getAccessibleApplications(applicationAccess).length > 0
}