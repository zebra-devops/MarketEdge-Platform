'use client'

import { useState, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import {
  ChartBarIcon,
  ShareIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import {
  ChartBarIcon as ChartBarIconSolid,
  ShareIcon as ShareIconSolid,
  SparklesIcon as SparklesIconSolid,
} from '@heroicons/react/24/solid'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { 
  ApplicationName,
  hasApplicationAccess,
  getApplicationInfo,
  getApplicationRoute
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

const applications: Application[] = [
  {
    id: 'market_edge',
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
    id: 'causal_edge',
    name: 'Causal Edge',
    displayName: 'Causal Edge',
    route: '/causal-edge',
    outlineIcon: ShareIcon,
    solidIcon: ShareIconSolid,
    color: 'from-green-500 to-emerald-600',
    themeColor: 'green',
    description: 'Business Process & Causal Analysis'
  },
  {
    id: 'value_edge',
    name: 'Value Edge',
    displayName: 'Value Edge',
    route: '/value-edge',
    outlineIcon: SparklesIcon,
    solidIcon: SparklesIconSolid,
    color: 'from-purple-500 to-violet-600',
    themeColor: 'purple',
    description: 'Value Engineering & ROI Analysis'
  }
]

interface ApplicationIconsProps {
  className?: string
  userApplicationAccess?: ApplicationAccess[]
}

export default function ApplicationIcons({ 
  className = '', 
  userApplicationAccess = []
}: ApplicationIconsProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [currentApplication, setCurrentApplication] = useState<Application | null>(null)
  const [isLoading, setIsLoading] = useState<ApplicationName | null>(null)
  const [tooltipVisible, setTooltipVisible] = useState<ApplicationName | null>(null)

  // Get current application from pathname
  useEffect(() => {
    const currentApp = applications.find(app => pathname.startsWith(app.route))
    if (currentApp) {
      setCurrentApplication(currentApp)
      // Save to localStorage (client-side only)
      if (typeof window !== 'undefined') {
        localStorage.setItem('currentApplication', currentApp.id)
      }
    } else {
      // Try to restore from localStorage (client-side only)
      if (typeof window !== 'undefined') {
        const savedAppId = localStorage.getItem('currentApplication') as ApplicationName
        const savedApp = applications.find(app => app.id === savedAppId)
        if (savedApp && hasUserAccess(savedApp)) {
          setCurrentApplication(savedApp)
        }
      }
    }
  }, [pathname, userApplicationAccess])

  // Filter applications based on user application access
  const accessibleApplications = applications.filter(app => hasUserAccess(app))

  function hasUserAccess(app: Application): boolean {
    return hasApplicationAccess(userApplicationAccess, app.id)
  }

  const handleApplicationSwitch = async (application: Application) => {
    if (application.id === currentApplication?.id || isLoading) return
    
    setIsLoading(application.id)
    try {
      // Save to localStorage (client-side only)
      if (typeof window !== 'undefined') {
        localStorage.setItem('currentApplication', application.id)
      }
      
      // Navigate to the application
      router.push(application.route)
      setCurrentApplication(application)
      setTooltipVisible(null)
    } catch (error) {
      console.error('Failed to switch application:', error)
    } finally {
      setIsLoading(null)
    }
  }

  // Don't show if user has access to only one application or none
  if (accessibleApplications.length <= 1) {
    return null
  }

  return (
    <div className={`flex items-center space-x-1 sm:space-x-2 ${className}`}>
      {accessibleApplications.map((application) => {
        const isCurrent = application.id === currentApplication?.id
        const isLoadingThis = isLoading === application.id
        const IconComponent = isCurrent ? application.solidIcon : application.outlineIcon
        
        return (
          <div key={application.id} className="relative">
            <button
              onClick={() => handleApplicationSwitch(application)}
              onMouseEnter={() => setTooltipVisible(application.id)}
              onMouseLeave={() => setTooltipVisible(null)}
              onTouchStart={() => setTooltipVisible(application.id)}
              onTouchEnd={() => setTimeout(() => setTooltipVisible(null), 2000)} // Hide after 2s on mobile
              disabled={isLoadingThis}
              className={`
                relative group p-1.5 sm:p-2 rounded-lg transition-all duration-200 ease-in-out
                ${isCurrent 
                  ? `bg-gradient-to-br ${application.color} text-white shadow-md ring-2 ring-white ring-opacity-50` 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100 active:bg-gray-200'
                }
                ${isLoadingThis ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:scale-105 active:scale-95'}
                focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
                transform-gpu
              `}
              aria-label={`Switch to ${application.displayName}`}
              title={application.displayName}
            >
              {isLoadingThis ? (
                <LoadingSpinner size="sm" className="w-5 h-5 sm:w-6 sm:h-6" />
              ) : (
                <>
                  <IconComponent className="w-5 h-5 sm:w-6 sm:h-6" />
                  
                  {/* Active indicator */}
                  {isCurrent && (
                    <div className="absolute -bottom-0.5 left-1/2 transform -translate-x-1/2">
                      <div className="w-1 h-1 bg-white rounded-full shadow-sm"></div>
                    </div>
                  )}
                </>
              )}
            </button>
            
            {/* Tooltip - only show on desktop hover or mobile touch */}
            {tooltipVisible === application.id && !isLoadingThis && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-50 pointer-events-none">
                <div className="bg-gray-900 text-white px-2 py-1.5 sm:px-3 sm:py-2 rounded-md text-xs sm:text-sm whitespace-nowrap shadow-lg max-w-xs">
                  <div className="font-medium">{application.displayName}</div>
                  <div className="text-xs opacity-90 hidden sm:block">{application.description}</div>
                  
                  {/* Tooltip arrow */}
                  <div className="absolute top-full left-1/2 transform -translate-x-1/2">
                    <div className="border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}