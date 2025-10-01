'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import {
  ChartBarIcon,
  ShareIcon,
  SparklesIcon,
  ChevronDownIcon,
  Squares2X2Icon
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
    description: 'Pricing Experiments & Causal Analysis'
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
    description: 'Value Engineering & ROI Analysis'
  }
]

interface ApplicationSwitcherProps {
  className?: string
  userApplicationAccess?: ApplicationAccess[]
  variant?: 'desktop' | 'mobile'
}

export default function ApplicationSwitcher({
  className = '',
  userApplicationAccess = [],
  variant = 'desktop'
}: ApplicationSwitcherProps) {
  console.log('🔍 ApplicationSwitcher called:', { userApplicationAccess, variant, className })
  const router = useRouter()
  const pathname = usePathname()
  const [currentApplication, setCurrentApplication] = useState<Application | null>(null)
  const [isLoading, setIsLoading] = useState<ApplicationName | null>(null)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

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

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [isDropdownOpen])

  // Handle keyboard navigation
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (!isDropdownOpen) return

      switch (event.key) {
        case 'Escape':
          setIsDropdownOpen(false)
          break
        case 'ArrowDown':
          event.preventDefault()
          // Focus next application option
          break
        case 'ArrowUp':
          event.preventDefault()
          // Focus previous application option
          break
        case 'Enter':
          event.preventDefault()
          // Select focused application
          break
      }
    }

    if (isDropdownOpen) {
      document.addEventListener('keydown', handleKeyDown)
      return () => {
        document.removeEventListener('keydown', handleKeyDown)
      }
    }
  }, [isDropdownOpen])

  // Filter applications based on user application access
  const accessibleApplications = applications.filter(app => hasUserAccess(app))

  // Debug logging
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    console.log('ApplicationSwitcher Debug:', {
      userApplicationAccess,
      accessibleApplications: accessibleApplications.map(app => app.id),
      currentApplication: currentApplication?.id,
      variant
    })
  }

  function hasUserAccess(app: Application): boolean {
    return hasApplicationAccess(userApplicationAccess, app.id)
  }

  const handleApplicationSwitch = async (application: Application) => {
    if (application.id === currentApplication?.id || isLoading) return

    setIsLoading(application.id)
    setIsDropdownOpen(false)

    try {
      // Save to localStorage (client-side only)
      if (typeof window !== 'undefined') {
        localStorage.setItem('currentApplication', application.id)
      }

      // Navigate to the application
      router.push(application.route)
      setCurrentApplication(application)
    } catch (error) {
      console.error('Failed to switch application:', error)
    } finally {
      setIsLoading(null)
    }
  }

  // Don't show if user has access to no applications (temporarily show even with 1 app for debugging)
  if (accessibleApplications.length === 0) {
    return null
  }

  // Mobile variant - integrated into mobile menu
  if (variant === 'mobile') {
    return (
      <div className={`space-y-3 ${className}`}>
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-1">
          Applications ({accessibleApplications.length})
        </div>

        {/* Current Application */}
        {currentApplication && (
          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
            <div className="flex items-center">
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${currentApplication.color} flex items-center justify-center shadow-sm`}>
                <currentApplication.solidIcon className="h-4 w-4 text-white" />
              </div>
              <div className="ml-3 flex-1">
                <div className="text-sm font-medium text-gray-900">{currentApplication.displayName}</div>
                <div className="text-xs text-gray-500">Current Application</div>
              </div>
            </div>
          </div>
        )}

        {/* Other Applications */}
        <div className="space-y-1">
          {accessibleApplications
            .filter(app => app.id !== currentApplication?.id)
            .map((application) => {
              const isLoadingThis = isLoading === application.id

              return (
                <button
                  key={application.id}
                  onClick={() => handleApplicationSwitch(application)}
                  disabled={isLoadingThis}
                  className="w-full flex items-center p-3 rounded-lg text-left hover:bg-gray-50 active:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  aria-label={`Switch to ${application.displayName}`}
                >
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${application.color} flex items-center justify-center shadow-sm`}>
                    {isLoadingThis ? (
                      <LoadingSpinner size="sm" className="w-4 h-4" />
                    ) : (
                      <application.outlineIcon className="h-4 w-4 text-white" />
                    )}
                  </div>
                  <div className="ml-3 flex-1">
                    <div className="text-sm font-medium text-gray-900">{application.displayName}</div>
                    <div className="text-xs text-gray-500">{application.description}</div>
                  </div>
                </button>
              )
            })}
        </div>
      </div>
    )
  }

  // Desktop variant - dropdown button
  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="flex items-center space-x-2 px-3 py-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 active:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        aria-label="Switch applications"
        aria-expanded={isDropdownOpen}
        aria-haspopup="menu"
      >
        <Squares2X2Icon className="h-4 w-4 text-gray-500" />
        <span className="text-sm font-medium text-gray-700">Apps</span>
        <div className="flex items-center space-x-1">
          <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
            {accessibleApplications.length}
          </span>
          <ChevronDownIcon
            className={`h-4 w-4 text-gray-400 transition-transform duration-200 ${
              isDropdownOpen ? 'transform rotate-180' : ''
            }`}
          />
        </div>
      </button>

      {/* Dropdown Menu */}
      {isDropdownOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-50">
          <div className="px-4 py-2 border-b border-gray-100">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Switch Application
            </div>
          </div>

          <div className="py-2">
            {accessibleApplications.map((application) => {
              const isCurrent = application.id === currentApplication?.id
              const isLoadingThis = isLoading === application.id

              return (
                <button
                  key={application.id}
                  onClick={() => handleApplicationSwitch(application)}
                  disabled={isLoadingThis || isCurrent}
                  className={`w-full flex items-center px-4 py-3 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset ${
                    isCurrent
                      ? 'bg-blue-50 text-blue-900'
                      : 'hover:bg-gray-50 active:bg-gray-100 text-gray-900'
                  }`}
                  aria-label={`Switch to ${application.displayName}`}
                  role="menuitem"
                >
                  <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${application.color} flex items-center justify-center shadow-sm flex-shrink-0`}>
                    {isLoadingThis ? (
                      <LoadingSpinner size="sm" className="w-5 h-5" />
                    ) : (
                      <application.solidIcon className="h-5 w-5 text-white" />
                    )}
                  </div>

                  <div className="ml-4 flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-sm truncate">{application.displayName}</div>
                      {isCurrent && (
                        <div className="ml-2 flex-shrink-0">
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mt-1 line-clamp-2">{application.description}</div>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Footer with keyboard shortcuts hint */}
          <div className="px-4 py-2 border-t border-gray-100">
            <div className="text-xs text-gray-400">
              Use ↑↓ arrow keys to navigate, Enter to select, Esc to close
            </div>
          </div>
        </div>
      )}
    </div>
  )
}