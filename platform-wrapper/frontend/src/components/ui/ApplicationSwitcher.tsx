'use client'

import { Fragment, useState, useEffect } from 'react'
import { Listbox, Transition } from '@headlessui/react'
import {
  ChevronDownIcon,
  CheckIcon,
  ChartBarIcon,
  CogIcon,
  EyeIcon,
} from '@heroicons/react/24/outline'
import { useRouter, usePathname } from 'next/navigation'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import DemoModeToggle, { useDemoModeToggle } from '@/components/ui/DemoModeToggle'
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
  icon: React.ComponentType<{ className?: string }>
  color: string
  description: string
}

const applications: Application[] = [
  {
    id: 'market_edge',
    name: 'Market Edge',
    displayName: 'Market Edge',
    route: '/market-edge',
    icon: ChartBarIcon,
    color: 'from-blue-500 to-indigo-600',
    description: 'Competitive Intelligence & Market Analysis'
  },
  {
    id: 'causal_edge',
    name: 'Causal Edge',
    displayName: 'Causal Edge',
    route: '/causal-edge',
    icon: CogIcon,
    color: 'from-green-500 to-emerald-600',
    description: 'Business Process & Causal Analysis'
  },
  {
    id: 'value_edge',
    name: 'Value Edge',
    displayName: 'Value Edge',
    route: '/value-edge',
    icon: EyeIcon,
    color: 'from-purple-500 to-violet-600',
    description: 'Value Engineering & ROI Analysis'
  }
]

interface ApplicationSwitcherProps {
  className?: string
  userPermissions?: string[]
  userApplicationAccess?: ApplicationAccess[]
  showDemoToggle?: boolean
}

export default function ApplicationSwitcher({ 
  className = '', 
  userPermissions = [],
  userApplicationAccess = [],
  showDemoToggle = true
}: ApplicationSwitcherProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [currentApplication, setCurrentApplication] = useState<Application | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)

  // Demo mode toggle functionality
  const { demoMode, toggleDemoMode } = useDemoModeToggle()

  // Get current application from pathname
  useEffect(() => {
    const currentApp = applications.find(app => pathname.startsWith(app.route))
    if (currentApp) {
      setCurrentApplication(currentApp)
      // Save to localStorage
      localStorage.setItem('currentApplication', currentApp.id)
    } else {
      // Try to restore from localStorage
      const savedAppId = localStorage.getItem('currentApplication') as ApplicationName
      const savedApp = applications.find(app => app.id === savedAppId)
      if (savedApp && hasUserAccess(savedApp)) {
        setCurrentApplication(savedApp)
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
    
    setIsLoading(true)
    try {
      // Save to localStorage
      localStorage.setItem('currentApplication', application.id)
      
      // Navigate to the application
      router.push(application.route)
      setCurrentApplication(application)
      setIsOpen(false)
    } catch (error) {
      console.error('Failed to switch application:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Don't show if user has access to only one application or none
  if (accessibleApplications.length <= 1) {
    return null
  }

  const currentAppDisplay = currentApplication || accessibleApplications[0]

  return (
    <div className={`flex items-center space-x-4 ${className}`}>
      {/* Demo Mode Toggle */}
      {showDemoToggle && (
        <DemoModeToggle
          onToggle={toggleDemoMode}
          size="sm"
          className="flex-shrink-0"
        />
      )}

      {/* Application Switcher */}
      <div className="relative">
        <Listbox value={currentApplication} onChange={handleApplicationSwitch}>
        <div className="relative">
          <Listbox.Button
            className="relative w-full min-w-[220px] cursor-pointer rounded-lg bg-white py-2 pl-3 pr-10 text-left border border-gray-300 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 sm:text-sm"
            disabled={isLoading}
          >
            <div className="flex items-center gap-3">
              {isLoading ? (
                <LoadingSpinner size="sm" />
              ) : (
                <div className={`flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br ${currentAppDisplay?.color || 'from-gray-400 to-gray-600'} flex items-center justify-center`}>
                  {currentAppDisplay?.icon && (
                    <currentAppDisplay.icon className="h-5 w-5 text-white" />
                  )}
                </div>
              )}
              
              <div className="flex-1 min-w-0">
                <div className="flex flex-col">
                  <span className="block truncate font-medium text-gray-900">
                    {currentAppDisplay?.displayName || 'Select Application'}
                  </span>
                  <span className="block truncate text-xs text-gray-500">
                    {currentAppDisplay?.description || 'Business Intelligence Platform'}
                  </span>
                </div>
              </div>
            </div>
            
            <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
              <ChevronDownIcon
                className="h-5 w-5 text-gray-400"
                aria-hidden="true"
              />
            </span>
          </Listbox.Button>
          
          <Transition
            show={isOpen}
            as={Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
            beforeEnter={() => setIsOpen(true)}
            afterLeave={() => setIsOpen(false)}
          >
            <Listbox.Options className="absolute z-50 mt-1 max-h-60 w-full min-w-[300px] overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
              <div className="px-3 py-2 text-xs font-medium text-gray-500 border-b border-gray-200">
                Switch Application
              </div>
              
              {accessibleApplications.map((application) => {
                const isCurrent = application.id === currentApplication?.id
                
                return (
                  <Listbox.Option
                    key={application.id}
                    className={({ active, selected }) =>
                      `relative cursor-pointer select-none py-3 px-3 ${
                        active || selected
                          ? 'bg-primary-50 text-primary-900'
                          : 'text-gray-900'
                      } ${isCurrent ? 'bg-primary-50' : ''}`
                    }
                    value={application}
                  >
                    {({ selected }) => (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <div className={`flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br ${application.color} flex items-center justify-center shadow-sm`}>
                            <application.icon className="h-6 w-6 text-white" />
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className={`block truncate ${isCurrent ? 'font-semibold' : 'font-medium'}`}>
                                {application.displayName}
                              </span>
                              {isCurrent && (
                                <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">
                                  Current
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-500 truncate">
                              {application.description}
                            </p>
                          </div>
                        </div>
                        
                        {isCurrent && (
                          <CheckIcon className="h-5 w-5 text-primary-600" />
                        )}
                      </div>
                    )}
                  </Listbox.Option>
                )
              })}
            </Listbox.Options>
          </Transition>
        </div>
      </Listbox>
      </div>
    </div>
  )
}