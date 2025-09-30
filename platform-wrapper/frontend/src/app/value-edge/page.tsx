'use client'

import { useEffect, useState } from 'react'
import { useAuthContext } from '@/hooks/useAuth'
import { useRouter } from 'next/navigation'
import { hasApplicationAccess } from '@/utils/application-access'
import ApplicationLayout from '@/components/layout/ApplicationLayout'
import ValueEdgeLanding from '@/components/applications/ValueEdgeLanding'
import { EyeIcon, CurrencyDollarIcon, ChartBarIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

export default function ValueEdgePage() {
  const { isAuthenticated, isLoading, user } = useAuthContext()
  const router = useRouter()
  const [showLanding, setShowLanding] = useState(true)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    } else if (!isLoading && isAuthenticated && !hasApplicationAccess(user?.application_access, 'value_edge')) {
      router.push('/dashboard')
    }
  }, [isAuthenticated, isLoading, user, router])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (!isAuthenticated || !hasApplicationAccess(user?.application_access, 'value_edge')) {
    return null
  }

  const handleGetStarted = () => {
    setShowLanding(false)
  }

  if (showLanding) {
    return (
      <ApplicationLayout application="VALUE_EDGE">
        <ValueEdgeLanding 
          onGetStarted={handleGetStarted}
          showDemoMode={true}
        />
      </ApplicationLayout>
    )
  }

  return (
    <ApplicationLayout application="VALUE_EDGE">
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4">
            <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-teal-500 flex items-center justify-center shadow-lg">
              <EyeIcon className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Value Edge</h1>
              <p className="text-gray-600">Value Engineering & ROI Analysis</p>
            </div>
          </div>
        </div>

        {/* Welcome Message */}
        <div className="bg-gradient-to-r from-purple-50 to-teal-50 border border-purple-200 rounded-lg p-6 mb-8">
          <div className="flex items-center gap-3 mb-3">
            <CurrencyDollarIcon className="h-6 w-6 text-purple-600" />
            <h2 className="text-lg font-semibold text-purple-900">
              Welcome to Value Edge
            </h2>
          </div>
          <p className="text-purple-800 mb-4">
            Maximize your return on investment through comprehensive value engineering analysis. 
            Value Edge helps you identify opportunities, measure ROI, and optimize resource allocation.
          </p>
          <div className="text-sm text-purple-700">
            <strong>Coming Soon:</strong> Advanced ROI analysis and value optimization tools
          </div>
        </div>

        {/* Feature Preview Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* ROI Analysis */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-teal-500 flex items-center justify-center">
                <CurrencyDollarIcon className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">ROI Analysis</h3>
            </div>
            <p className="text-gray-600 mb-4">
              Comprehensive return on investment analysis to evaluate the financial 
              impact of business decisions and initiatives.
            </p>
            <div className="text-sm text-gray-500">
              • Financial impact modeling
              <br />
              • Investment tracking
              <br />
              • ROI projections
            </div>
          </div>

          {/* Value Engineering */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-teal-500 flex items-center justify-center">
                <EyeIcon className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Value Engineering</h3>
            </div>
            <p className="text-gray-600 mb-4">
              Systematic approach to analyzing functions and costs to achieve 
              better value for money in all business activities.
            </p>
            <div className="text-sm text-gray-500">
              • Function analysis
              <br />
              • Cost optimization
              <br />
              • Value recommendations
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-teal-500 flex items-center justify-center">
                <ChartBarIcon className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Performance Metrics</h3>
            </div>
            <p className="text-gray-600 mb-4">
              Track and measure key value indicators to monitor the effectiveness 
              of value engineering initiatives.
            </p>
            <div className="text-sm text-gray-500">
              • Value metrics tracking
              <br />
              • Performance dashboards
              <br />
              • Trend analysis
            </div>
          </div>
        </div>

        {/* Demo Status */}
        <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-3">
            <DocumentTextIcon className="h-6 w-6 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Development Status</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Current Phase</h4>
              <p className="text-gray-600 text-sm">
                Foundation development and demo preparation for Odeon Cinema stakeholder presentation.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Next Release</h4>
              <p className="text-gray-600 text-sm">
                Post-demo expansion will include cinema-specific ROI analysis tools 
                for venue optimization and revenue enhancement.
              </p>
            </div>
          </div>
        </div>
      </div>
    </ApplicationLayout>
  )
}