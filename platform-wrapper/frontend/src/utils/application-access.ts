import { ApplicationAccess } from '@/types/auth'

export type ApplicationName = 'MARKET_EDGE' | 'CAUSAL_EDGE' | 'VALUE_EDGE'
export type ApplicationNameLowercase = 'market_edge' | 'causal_edge' | 'value_edge'

/**
 * Convert uppercase application name to lowercase
 */
function toLowercase(app: ApplicationName): ApplicationNameLowercase {
  const mapping: Record<ApplicationName, ApplicationNameLowercase> = {
    'MARKET_EDGE': 'market_edge',
    'CAUSAL_EDGE': 'causal_edge',
    'VALUE_EDGE': 'value_edge'
  }
  return mapping[app]
}

/**
 * Convert lowercase application name to uppercase
 */
function toUppercase(app: ApplicationNameLowercase): ApplicationName {
  const mapping: Record<ApplicationNameLowercase, ApplicationName> = {
    'market_edge': 'MARKET_EDGE',
    'causal_edge': 'CAUSAL_EDGE',
    'value_edge': 'VALUE_EDGE'
  }
  return mapping[app]
}

/**
 * Check if a user has access to a specific application
 * Supports both the old format ({ [key: string]: boolean }) and new format (ApplicationAccess[])
 */
export function hasApplicationAccess(
  applicationAccess: ApplicationAccess[] | { [key: string]: boolean } | undefined,
  application: ApplicationName | ApplicationNameLowercase
): boolean {
  if (!applicationAccess) {
    return false
  }

  // Handle new format (ApplicationAccess[])
  if (Array.isArray(applicationAccess)) {
    // Backend sends lowercase application names, so normalize to uppercase for comparison
    const isLowercase = typeof application === 'string' &&
      application.includes('_') &&
      application === application.toLowerCase()

    const appName = isLowercase
      ? toUppercase(application as ApplicationNameLowercase)
      : application as ApplicationName

    const accessRecord = applicationAccess.find(access =>
      access.application === appName || access.application === toLowercase(appName)
    )

    return accessRecord?.has_access || false
  }

  // Handle old format ({ [key: string]: boolean })
  const isLowercase = typeof application === 'string' &&
    application.includes('_') &&
    application === application.toLowerCase()

  const appName = isLowercase
    ? toUppercase(application as ApplicationNameLowercase)
    : application as ApplicationName

  return applicationAccess[appName] || false
}

/**
 * Get all applications that a user has access to
 */
export function getAccessibleApplications(
  applicationAccess: ApplicationAccess[] | { [key: string]: boolean } | undefined
): ApplicationName[] {
  if (!applicationAccess) {
    return []
  }

  // Handle new format (ApplicationAccess[])
  if (Array.isArray(applicationAccess)) {
    return applicationAccess
      .filter(access => access.has_access)
      .map(access => {
        // Convert any format to uppercase for consistency
        if (access.application === 'market_edge' || access.application === 'MARKET_EDGE') {
          return 'MARKET_EDGE' as ApplicationName
        } else if (access.application === 'causal_edge' || access.application === 'CAUSAL_EDGE') {
          return 'CAUSAL_EDGE' as ApplicationName
        } else if (access.application === 'value_edge' || access.application === 'VALUE_EDGE') {
          return 'VALUE_EDGE' as ApplicationName
        }
        return access.application as ApplicationName
      })
  }

  // Handle old format ({ [key: string]: boolean })
  return Object.entries(applicationAccess)
    .filter(([key, hasAccess]) => hasAccess && ['MARKET_EDGE', 'CAUSAL_EDGE', 'VALUE_EDGE'].includes(key))
    .map(([key]) => key as ApplicationName)
}

/**
 * Get the user's primary (first accessible) application
 */
export function getPrimaryApplication(
  applicationAccess: ApplicationAccess[] | { [key: string]: boolean } | undefined,
  preferredOrder: ApplicationName[] = ['MARKET_EDGE', 'CAUSAL_EDGE', 'VALUE_EDGE']
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
    MARKET_EDGE: '/market-edge',
    CAUSAL_EDGE: '/causal-edge',
    VALUE_EDGE: '/value-edge'
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
    MARKET_EDGE: {
      name: 'Market Edge',
      displayName: 'Market Edge',
      description: 'Competitive Intelligence & Market Analysis',
      color: 'from-blue-500 to-indigo-600',
      themeColor: 'blue'
    },
    CAUSAL_EDGE: {
      name: 'Causal Edge',
      displayName: 'Causal Edge',
      description: 'Commercial Experimentation Hub',
      color: 'from-teal-500 to-teal-600',
      themeColor: 'teal'
    },
    VALUE_EDGE: {
      name: 'Value Edge',
      displayName: 'Value Edge',
      description: 'ROI optimization and value measurement',
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
  applicationAccess: ApplicationAccess[] | { [key: string]: boolean } | undefined
): boolean {
  return getAccessibleApplications(applicationAccess).length > 0
}

/**
 * Get application icon component name for the new structure
 */
export function getApplicationIcon(application: ApplicationName): string {
  const icons: Record<ApplicationName, string> = {
    MARKET_EDGE: 'EyeIcon',
    CAUSAL_EDGE: 'ChartBarIcon',
    VALUE_EDGE: 'CogIcon'
  }

  return icons[application]
}