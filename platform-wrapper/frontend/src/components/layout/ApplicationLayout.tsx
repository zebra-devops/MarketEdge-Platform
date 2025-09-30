'use client'

import React from 'react'
import { useAuthContext } from '@/hooks/useAuth'
import { useRouter, usePathname } from 'next/navigation'
import { 
  ChartBarIcon,
  CogIcon,
  EyeIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import { Fragment, useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import ApplicationSwitcher from '@/components/ui/ApplicationSwitcher'
import { AccountMenu } from '@/components/ui/AccountMenu'
import { 
  hasApplicationAccess, 
  getApplicationInfo,
  ApplicationName 
} from '@/utils/application-access'

interface ApplicationLayoutProps {
  children: React.ReactNode
  application: ApplicationName
  className?: string
}

const applicationIcons = {
  MARKET_EDGE: ChartBarIcon,
  CAUSAL_EDGE: CogIcon,
  VALUE_EDGE: EyeIcon
}

export default function ApplicationLayout({ 
  children, 
  application, 
  className = '' 
}: ApplicationLayoutProps) {
  const { user, isLoading } = useAuthContext()
  const router = useRouter()
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // Get application info
  const appInfo = getApplicationInfo(application)
  const IconComponent = applicationIcons[application]

  // Check if user has access to this application
  const hasAccess = hasApplicationAccess(user?.application_access, application)

  // TEMPORARY: Bypass redirect for debugging causal-edge access
  React.useEffect(() => {
    if (!isLoading && user && !hasAccess && application !== 'CAUSAL_EDGE') {
      router.push('/dashboard')
    }
  }, [user, hasAccess, isLoading, router, application])

  if (isLoading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  // TEMPORARY: Allow causal_edge access for debugging
  if (!hasAccess && application !== 'CAUSAL_EDGE') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  return (
    <div className={`min-h-screen bg-gray-50 app-theme-${appInfo.themeColor} transition-theme ${className}`}>
      {/* Mobile menu */}
      <Transition.Root show={mobileMenuOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50 lg:hidden" onClose={setMobileMenuOpen}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-gray-900/80" />
          </Transition.Child>

          <div className="fixed inset-0 flex">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                <Transition.Child
                  as={Fragment}
                  enter="ease-in-out duration-300"
                  enterFrom="opacity-0"
                  enterTo="opacity-100"
                  leave="ease-in-out duration-300"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
                >
                  <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                    <button
                      type="button"
                      className="-m-2.5 p-2.5"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <span className="sr-only">Close sidebar</span>
                      <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
                    </button>
                  </div>
                </Transition.Child>

                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-4">
                  <div className="flex h-16 shrink-0 items-center">
                    <div className="flex items-center">
                      <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${appInfo.color} flex items-center justify-center shadow-sm`}>
                        <IconComponent className="h-5 w-5 text-white" />
                      </div>
                      <h1 className="ml-3 text-lg font-bold text-gray-900">{appInfo.name}</h1>
                    </div>
                  </div>
                  
                  <nav className="flex flex-1 flex-col">
                    <div className="mb-4">
                      <ApplicationSwitcher
                        userApplicationAccess={user?.application_access}
                        variant="mobile"
                        className="justify-start"
                      />
                    </div>
                  </nav>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>

      {/* Header */}
      <div className="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left side - App branding */}
            <div className="flex items-center">
              <div className="flex items-center">
                {application === 'CAUSAL_EDGE' ? (
                  /* Custom three-bar logo for Causal Edge - matching PNG design */
                  <div className="mr-4">
                    <div className="w-10 h-10 flex flex-col justify-center">
                      <div className="space-y-1">
                        <div className="w-10 h-1.5 bg-gradient-to-r from-teal-400 to-teal-500" style={{clipPath: 'polygon(0 0, 85% 0, 100% 100%, 15% 100%)'}}></div>
                        <div className="w-10 h-1.5 bg-gradient-to-r from-teal-500 to-teal-600" style={{clipPath: 'polygon(0 0, 85% 0, 100% 100%, 15% 100%)'}}></div>
                        <div className="w-10 h-1.5 bg-gradient-to-r from-teal-600 to-teal-700" style={{clipPath: 'polygon(0 0, 85% 0, 100% 100%, 15% 100%)'}}></div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${appInfo.color} flex items-center justify-center shadow-md mr-4`}>
                    <IconComponent className="h-6 w-6 text-white" />
                  </div>
                )}
                <div>
                  <h1 className="text-xl font-bold text-gray-900">{appInfo.name}</h1>
                  <p className="text-sm text-gray-600">{appInfo.description}</p>
                </div>
                {application === 'CAUSAL_EDGE' && (
                  <button
                    onClick={() => router.push('/dashboard')}
                    className="ml-6 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                  >
                    ← Back to Dashboard
                  </button>
                )}
              </div>
            </div>

            {/* Right side - Navigation and user menu */}
            <div className="flex items-center gap-4">
              {/* Desktop Application Switcher */}
              <div className="hidden lg:block">
                <ApplicationSwitcher
                  userApplicationAccess={user?.application_access}
                  variant="desktop"
                />
              </div>

              {/* Account Menu */}
              <AccountMenu />
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Application theme styles */}
      <style jsx>{`
        :global(.app-theme-${appInfo.themeColor}) {
          --primary-50: ${appInfo.themeColor === 'blue' ? 'rgb(239 246 255)' :
                         appInfo.themeColor === 'green' ? 'rgb(240 253 244)' :
                         appInfo.themeColor === 'teal' ? 'rgb(240 253 250)' :
                         'rgb(250 245 255)'};
          --primary-500: ${appInfo.themeColor === 'blue' ? 'rgb(59 130 246)' :
                          appInfo.themeColor === 'green' ? 'rgb(34 197 94)' :
                          appInfo.themeColor === 'teal' ? 'rgb(20 184 166)' :
                          'rgb(168 85 247)'};
          --primary-600: ${appInfo.themeColor === 'blue' ? 'rgb(37 99 235)' :
                          appInfo.themeColor === 'green' ? 'rgb(22 163 74)' :
                          appInfo.themeColor === 'teal' ? 'rgb(13 148 136)' :
                          'rgb(147 51 234)'};
        }
        
        :global(.transition-theme) {
          transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
        }
      `}</style>

      {/* Application indicator for smooth transitions */}
      <div 
        className={`fixed bottom-4 left-4 px-3 py-2 rounded-full bg-gradient-to-r ${appInfo.color} text-white text-xs font-medium shadow-lg transition-all duration-500 transform translate-y-0 opacity-100`}
        id="app-indicator"
      >
        <div className="flex items-center space-x-2">
          <IconComponent className="h-3 w-3" />
          <span>{appInfo.name}</span>
        </div>
      </div>
    </div>
  )
}