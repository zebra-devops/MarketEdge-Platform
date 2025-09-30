'use client'

import { useState, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import {
  HomeIcon,
  ChartBarIcon,
  ShareIcon,
  SparklesIcon,
  CogIcon,
  UserGroupIcon,
  BeakerIcon,
  DocumentChartBarIcon,
  LightBulbIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline'
import {
  HomeIcon as HomeIconSolid,
  ChartBarIcon as ChartBarIconSolid,
  ShareIcon as ShareIconSolid,
  SparklesIcon as SparklesIconSolid,
  CogIcon as CogIconSolid
} from '@heroicons/react/24/solid'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { useAuthContext } from '@/hooks/useAuth'
import {
  ApplicationName,
  hasApplicationAccess,
  getApplicationInfo
} from '@/utils/application-access'
import { ApplicationAccess } from '@/types/auth'

interface Application {
  id: ApplicationName
  name: string
  displayName: string
  route: string
  outlineIcon: React.ComponentType<{ className?: string }>
  solidIcon: React.ComponentType<{ className?: string }>
  color: string
  themeColor: string
  description: string
}

interface ApplicationNavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  current?: boolean
}

const applications: Application[] = [
  {
    id: 'MARKET_EDGE',
    name: 'Market Edge',
    displayName: 'Market Edge',
    route: '/market-edge',
    outlineIcon: ChartBarIcon,
    solidIcon: ChartBarIconSolid,
    color: 'from-blue-500 to-indigo-600',
    themeColor: 'blue',
    description: 'Competitive Intelligence & Market Analysis'
  },
  {
    id: 'CAUSAL_EDGE',
    name: 'Causal Edge',
    displayName: 'Causal Edge',
    route: '/causal-edge',
    outlineIcon: ShareIcon,
    solidIcon: ShareIconSolid,
    color: 'from-green-500 to-emerald-600',
    themeColor: 'green',
    description: 'Advanced causal analysis and intervention testing'
  },
  {
    id: 'VALUE_EDGE',
    name: 'Value Edge',
    displayName: 'Value Edge',
    route: '/value-edge',
    outlineIcon: SparklesIcon,
    solidIcon: SparklesIconSolid,
    color: 'from-purple-500 to-violet-600',
    themeColor: 'purple',
    description: 'ROI optimization and value measurement'
  }
]

// Application-specific navigation items
const applicationNavigation: Record<ApplicationName, ApplicationNavItem[]> = {
  MARKET_EDGE: [
    { name: 'Dashboard', href: '/market-edge', icon: HomeIcon },
    { name: 'Analysis', href: '/market-edge/analysis', icon: DocumentChartBarIcon },
    { name: 'Reports', href: '/market-edge/reports', icon: ChartBarIcon },
  ],
  CAUSAL_EDGE: [
    { name: 'Dashboard', href: '/causal-edge', icon: HomeIcon },
    { name: 'Tests', href: '/causal-edge/tests', icon: BeakerIcon },
    { name: 'New Test', href: '/causal-edge/tests/new', icon: SparklesIcon },
    { name: 'Run Analysis', href: '/causal-edge/analysis', icon: DocumentChartBarIcon },
    { name: 'Results', href: '/causal-edge/results', icon: ChartBarIcon },
    { name: 'Insights', href: '/causal-edge/insights', icon: LightBulbIcon },
    { name: 'Impact', href: '/causal-edge/impact', icon: ArrowTrendingUpIcon },
  ],
  VALUE_EDGE: [
    { name: 'Dashboard', href: '/value-edge', icon: HomeIcon },
    { name: 'Projects', href: '/value-edge/projects', icon: DocumentChartBarIcon },
    { name: 'ROI Analysis', href: '/value-edge/roi', icon: ArrowTrendingUpIcon },
  ]
}

interface NavigationProps {
  className?: string
}

export default function Navigation({ className = '' }: NavigationProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { user } = useAuthContext()
  const [currentApplication, setCurrentApplication] = useState<Application | null>(null)
  const [isLoading, setIsLoading] = useState<ApplicationName | null>(null)

  const userApplicationAccess = user?.application_access

  // Determine current application from pathname
  useEffect(() => {
    const currentApp = applications.find(app => pathname.startsWith(app.route))
    setCurrentApplication(currentApp || null)
  }, [pathname])

  const handleNavigate = async (href: string, applicationId?: ApplicationName) => {
    if (pathname === href || isLoading) return

    if (applicationId) {
      setIsLoading(applicationId)
    }

    try {
      router.push(href)
    } catch (error) {
      console.error('Failed to navigate:', error)
    } finally {
      setIsLoading(null)
    }
  }

  const hasUserAccess = (app: Application): boolean => {
    return hasApplicationAccess(userApplicationAccess, app.id)
  }

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin'
  const isDashboard = pathname === '/dashboard'

  return (
    <nav className={`flex flex-col space-y-1 ${className}`}>
      {/* 1. Home (Dashboard) */}
      <button
        onClick={() => handleNavigate('/dashboard')}
        className={`
          group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors
          ${isDashboard
            ? 'bg-gray-100 text-gray-900'
            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
          }
        `}
      >
        {isDashboard ? (
          <HomeIconSolid className="mr-3 h-5 w-5 flex-shrink-0" />
        ) : (
          <HomeIcon className="mr-3 h-5 w-5 flex-shrink-0" />
        )}
        Home
      </button>

      {/* 2. Application Switcher */}
      <div className="space-y-1">
        <div className="px-2 py-2">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Applications
          </h3>
        </div>
        {applications.map((application) => {
          const hasAccess = hasUserAccess(application)
          const isCurrent = application.id === currentApplication?.id
          const isLoadingThis = isLoading === application.id
          const IconComponent = isCurrent ? application.solidIcon : application.outlineIcon

          return (
            <button
              key={application.id}
              onClick={() => hasAccess ? handleNavigate(application.route, application.id) : undefined}
              disabled={!hasAccess || isLoadingThis}
              className={`
                group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors w-full
                ${isCurrent && hasAccess
                  ? 'bg-gray-100 text-gray-900'
                  : hasAccess
                    ? 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    : 'text-gray-400 cursor-not-allowed'
                }
                ${isLoadingThis ? 'opacity-50' : ''}
              `}
              title={hasAccess ? application.description : 'Access required'}
            >
              {isLoadingThis ? (
                <LoadingSpinner size="sm" className="mr-3 h-5 w-5 flex-shrink-0" />
              ) : (
                <IconComponent
                  className={`
                    mr-3 h-5 w-5 flex-shrink-0
                    ${!hasAccess ? 'opacity-50' : ''}
                  `}
                />
              )}
              <span className={!hasAccess ? 'opacity-50' : ''}>
                {application.displayName}
              </span>
            </button>
          )
        })}
      </div>

      {/* 3. Divider */}
      {currentApplication && (
        <div className="border-t border-gray-200 my-2" />
      )}

      {/* 4. Application Navigation (when in application) */}
      {currentApplication && applicationNavigation[currentApplication.id] && (
        <div className="space-y-1">
          <div className="px-2 py-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              {currentApplication.displayName}
            </h3>
          </div>
          {applicationNavigation[currentApplication.id].map((item) => {
            const isCurrentPage = pathname === item.href

            return (
              <button
                key={item.name}
                onClick={() => handleNavigate(item.href)}
                className={`
                  group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors w-full
                  ${isCurrentPage
                    ? 'bg-gray-100 text-gray-900'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }
                `}
              >
                <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                {item.name}
              </button>
            )
          })}
        </div>
      )}

      {/* 5. Divider */}
      {isAdmin && (
        <div className="border-t border-gray-200 my-2" />
      )}

      {/* 6. Admin Link */}
      {isAdmin && (
        <div className="space-y-1">
          <div className="px-2 py-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Administration
            </h3>
          </div>
          <button
            onClick={() => handleNavigate('/admin')}
            className={`
              group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors w-full
              ${pathname === '/admin'
                ? 'bg-gray-100 text-gray-900'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }
            `}
          >
            {pathname === '/admin' ? (
              <CogIconSolid className="mr-3 h-5 w-5 flex-shrink-0" />
            ) : (
              <CogIcon className="mr-3 h-5 w-5 flex-shrink-0" />
            )}
            Settings
          </button>
        </div>
      )}
    </nav>
  )
}