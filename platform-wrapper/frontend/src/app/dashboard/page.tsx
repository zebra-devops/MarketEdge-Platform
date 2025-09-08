'use client'

import { useAuthContext } from '@/hooks/useAuth'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useQuery } from 'react-query'
import { apiService } from '@/services/api'
import { Tool, Organisation } from '@/types/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import Button from '@/components/ui/Button'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { 
  getAccessibleApplications, 
  getPrimaryApplication, 
  getApplicationRoute,
  getApplicationInfo,
  hasAnyApplicationAccess 
} from '@/utils/application-access'
import { 
  ChartBarIcon,
  CogIcon,
  EyeIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

export default function DashboardPage() {
  const { user, isLoading: authLoading } = useAuthContext()
  const router = useRouter()

  const { data: tools, isLoading: toolsLoading } = useQuery<Tool[]>(
    'tools',
    () => apiService.get('/tools'),
    { enabled: !!user }
  )

  const { data: organisation, isLoading: orgLoading } = useQuery<Organisation>(
    'organisation',
    () => apiService.get('/organisations/current'),
    { enabled: !!user }
  )

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  // Get user's accessible applications
  const accessibleApps = getAccessibleApplications(user?.application_access)
  const primaryApp = getPrimaryApplication(user?.application_access)
  
  // Function to navigate to application
  const navigateToApp = (appName: string) => {
    const appRoute = getApplicationRoute(appName as any)
    router.push(appRoute)
  }

  if (authLoading || !user) {
    return <LoadingSpinner />
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user.first_name}!
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Access your business intelligence tools and manage your account.
          </p>
        </div>

        {orgLoading ? (
          <LoadingSpinner />
        ) : organisation ? (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Organisation Details</h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Name</dt>
                <dd className="text-sm text-gray-900">{organisation.name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Industry</dt>
                <dd className="text-sm text-gray-900">{organisation.industry || 'Not specified'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Subscription Plan</dt>
                <dd className="text-sm text-gray-900 capitalize">{organisation.subscription_plan}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd className="text-sm text-gray-900">
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                    organisation.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {organisation.is_active ? 'Active' : 'Inactive'}
                  </span>
                </dd>
              </div>
            </dl>
          </div>
        ) : null}

        {/* Applications Section */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-gray-900">Your Applications</h2>
            {primaryApp && (
              <Button 
                onClick={() => navigateToApp(primaryApp)}
                className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700"
              >
                Go to {getApplicationInfo(primaryApp).name}
              </Button>
            )}
          </div>

          {!hasAnyApplicationAccess(user?.application_access) ? (
            <div className="text-center py-12">
              <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No Applications Available</h3>
              <p className="mt-1 text-sm text-gray-500">
                You don't have access to any applications yet. Please contact your administrator.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {accessibleApps.map((appName) => {
                const appInfo = getApplicationInfo(appName)
                const IconComponent = appName === 'market_edge' ? ChartBarIcon : 
                                     appName === 'causal_edge' ? CogIcon : EyeIcon
                
                return (
                  <div
                    key={appName}
                    className="relative group cursor-pointer"
                    onClick={() => navigateToApp(appName)}
                  >
                    <div className="bg-gradient-to-br from-white to-gray-50 rounded-xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-all duration-300 group-hover:-translate-y-1">
                      <div className="flex items-center mb-4">
                        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${appInfo.color} flex items-center justify-center shadow-md`}>
                          <IconComponent className="h-7 w-7 text-white" />
                        </div>
                        <div className="ml-4 flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">
                            {appInfo.name}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {appInfo.description}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                          Active
                        </span>
                        <span className="text-xs text-gray-500 group-hover:text-indigo-600 transition-colors">
                          Click to access →
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Legacy Tools Section (if needed) */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Legacy Tools</h2>
          {toolsLoading ? (
            <LoadingSpinner />
          ) : tools && tools.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {tools.map((tool) => (
                <div
                  key={tool.id}
                  className={`border rounded-lg p-4 ${
                    tool.has_access 
                      ? 'border-green-200 bg-green-50' 
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <h3 className="font-medium text-gray-900">{tool.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{tool.description}</p>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-xs text-gray-500">v{tool.version}</span>
                    {tool.has_access ? (
                      <Button size="sm">Access Tool</Button>
                    ) : (
                      <Button size="sm" variant="secondary" disabled>
                        No Access
                      </Button>
                    )}
                  </div>
                  {tool.has_access && tool.subscription_tier && (
                    <div className="mt-2">
                      <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                        {tool.subscription_tier}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No legacy tools available.</p>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}