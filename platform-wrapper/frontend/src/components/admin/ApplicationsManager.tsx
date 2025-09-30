'use client'

import { useState, useEffect } from 'react'
import { useOrganisationContext } from '@/components/providers/OrganisationProvider'
import {
  CubeIcon,
  ChartBarIcon,
  CogIcon,
  EyeIcon,
  PlayIcon,
  PauseIcon,
  AdjustmentsHorizontalIcon,
  BuildingOffice2Icon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  StarIcon
} from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'

interface Application {
  id: string
  name: string
  description: string
  icon: string
  status: 'active' | 'inactive' | 'beta'
  organizationsEnabled: number
  totalOrganizations: number
  capabilities: Capability[]
}

interface Capability {
  id: string
  name: string
  description: string
  state: 'preview' | 'beta' | 'ga' | 'deprecated'
  isRequired: boolean
  enabledOrganizations: number
  tier: 'basic' | 'professional' | 'enterprise'
}

interface CapabilityState {
  [applicationId: string]: {
    [capabilityId: string]: boolean
  }
}

const mockApplications: Application[] = [
  {
    id: 'CAUSAL_EDGE',
    name: 'Causal Edge',
    description: 'Advanced causal analysis and intervention testing platform',
    icon: 'chart',
    status: 'active',
    organizationsEnabled: 3,
    totalOrganizations: 5,
    capabilities: [
      {
        id: 'core-platform',
        name: 'Core Platform',
        description: 'Essential dashboard and data management',
        state: 'ga',
        isRequired: true,
        enabledOrganizations: 3,
        tier: 'basic'
      },
      {
        id: 'geolift-analysis',
        name: 'Geolift Analysis',
        description: 'Geographic lift testing and analysis',
        state: 'ga',
        isRequired: false,
        enabledOrganizations: 2,
        tier: 'professional'
      },
      {
        id: 'price-elasticity',
        name: 'Price Elasticity',
        description: 'Dynamic pricing and elasticity modeling',
        state: 'beta',
        isRequired: false,
        enabledOrganizations: 1,
        tier: 'enterprise'
      },
      {
        id: 'consultant-dialogue',
        name: 'Consultant Dialogue',
        description: 'AI-powered consultation and recommendations',
        state: 'preview',
        isRequired: false,
        enabledOrganizations: 3,
        tier: 'professional'
      }
    ]
  },
  {
    id: 'MARKET_EDGE',
    name: 'Market Edge',
    description: 'Competitive intelligence and market analysis',
    icon: 'eye',
    status: 'active',
    organizationsEnabled: 2,
    totalOrganizations: 5,
    capabilities: [
      {
        id: 'core-dashboard',
        name: 'Core Dashboard',
        description: 'Market overview and competitive positioning',
        state: 'ga',
        isRequired: true,
        enabledOrganizations: 2,
        tier: 'basic'
      },
      {
        id: 'competitor-tracking',
        name: 'Competitor Tracking',
        description: 'Real-time competitor monitoring',
        state: 'ga',
        isRequired: false,
        enabledOrganizations: 1,
        tier: 'professional'
      },
      {
        id: 'market-forecasting',
        name: 'Market Forecasting',
        description: 'Predictive market trend analysis',
        state: 'beta',
        isRequired: false,
        enabledOrganizations: 0,
        tier: 'enterprise'
      }
    ]
  },
  {
    id: 'VALUE_EDGE',
    name: 'Value Edge',
    description: 'ROI optimization and value measurement platform',
    icon: 'cog',
    status: 'beta',
    organizationsEnabled: 1,
    totalOrganizations: 5,
    capabilities: [
      {
        id: 'roi-tracking',
        name: 'ROI Tracking',
        description: 'Return on investment measurement',
        state: 'beta',
        isRequired: true,
        enabledOrganizations: 1,
        tier: 'basic'
      },
      {
        id: 'value-optimization',
        name: 'Value Optimization',
        description: 'Automated value optimization recommendations',
        state: 'preview',
        isRequired: false,
        enabledOrganizations: 0,
        tier: 'enterprise'
      }
    ]
  }
]

export function ApplicationsManager() {
  const { accessibleOrganisations, isSuperAdmin } = useOrganisationContext()
  const [applications, setApplications] = useState<Application[]>(mockApplications)
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null)
  const [isConfigureModalOpen, setIsConfigureModalOpen] = useState(false)

  const getApplicationIcon = (iconType: string) => {
    switch (iconType) {
      case 'chart': return ChartBarIcon
      case 'eye': return EyeIcon
      case 'cog': return CogIcon
      default: return CubeIcon
    }
  }

  const getStateColor = (state: Capability['state']) => {
    switch (state) {
      case 'ga': return 'bg-green-100 text-green-800 border-green-300'
      case 'beta': return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'preview': return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'deprecated': return 'bg-gray-100 text-gray-800 border-gray-300'
      default: return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getStateIcon = (state: Capability['state']) => {
    switch (state) {
      case 'ga': return CheckCircleIcon
      case 'beta': return ExclamationCircleIcon
      case 'preview': return ClockIcon
      case 'deprecated': return PauseIcon
      default: return ClockIcon
    }
  }

  const getTierIcon = (tier: Capability['tier']) => {
    switch (tier) {
      case 'enterprise': return StarIcon
      case 'professional': return AdjustmentsHorizontalIcon
      default: return null
    }
  }

  const getTierColor = (tier: Capability['tier']) => {
    switch (tier) {
      case 'enterprise': return 'text-purple-600'
      case 'professional': return 'text-blue-600'
      default: return 'text-gray-600'
    }
  }

  const handleConfigureCapabilities = (application: Application) => {
    setSelectedApplication(application)
    setIsConfigureModalOpen(true)
  }

  if (!isSuperAdmin) {
    return (
      <div className="text-center py-8">
        <CubeIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">Super admin access required for application management</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Applications & Capabilities</h2>
          <p className="text-gray-600 mt-1">
            Manage consulting tools and their capabilities across client organizations
          </p>
        </div>
        <div className="text-sm text-gray-500">
          <span className="font-medium">{applications.length}</span> Applications
        </div>
      </div>

      {/* Applications Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {applications.map((app) => {
          const IconComponent = getApplicationIcon(app.icon)
          const enablementPercentage = Math.round((app.organizationsEnabled / app.totalOrganizations) * 100)

          return (
            <div key={app.id} className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="p-6">
                {/* Application Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl flex items-center justify-center">
                      <IconComponent className="h-7 w-7 text-blue-600" />
                    </div>
                    <div className="ml-3">
                      <h3 className="text-lg font-semibold text-gray-900">{app.name}</h3>
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        app.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : app.status === 'beta'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                      }`}>
                        {app.status === 'active' ? 'Active' : app.status === 'beta' ? 'Beta' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                </div>

                <p className="text-sm text-gray-600 mb-4">{app.description}</p>

                {/* Enablement Stats */}
                <div className="mb-4">
                  <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
                    <span>Organization Enablement</span>
                    <span>{enablementPercentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${enablementPercentage}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500 mt-1">
                    <span>{app.organizationsEnabled} enabled</span>
                    <span>{app.totalOrganizations} total</span>
                  </div>
                </div>

                {/* Capabilities Summary */}
                <div className="mb-4">
                  <div className="flex items-center justify-between text-sm text-gray-700 mb-2">
                    <span className="font-medium">Capabilities</span>
                    <span className="text-gray-500">{app.capabilities.length} total</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {app.capabilities.map((capability) => {
                      const StateIcon = getStateIcon(capability.state)
                      return (
                        <div
                          key={capability.id}
                          className={`inline-flex items-center px-2 py-1 text-xs rounded border ${getStateColor(capability.state)}`}
                        >
                          <StateIcon className="h-3 w-3 mr-1" />
                          {capability.name}
                          {capability.isRequired && (
                            <span className="ml-1 text-red-500">*</span>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleConfigureCapabilities(app)}
                    variant="primary"
                    size="sm"
                    className="flex-1"
                  >
                    Configure Capabilities
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="flex items-center"
                  >
                    <BuildingOffice2Icon className="h-4 w-4 mr-1" />
                    {app.organizationsEnabled}
                  </Button>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Configure Capabilities Modal */}
      {isConfigureModalOpen && selectedApplication && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-lg flex items-center justify-center mr-3">
                    {(() => {
                      const IconComponent = getApplicationIcon(selectedApplication.icon)
                      return <IconComponent className="h-6 w-6 text-blue-600" />
                    })()}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {selectedApplication.name} - Capabilities Configuration
                    </h3>
                    <p className="text-sm text-gray-600">
                      Manage capabilities and client access across organizations
                    </p>
                  </div>
                </div>
                <Button
                  onClick={() => setIsConfigureModalOpen(false)}
                  variant="secondary"
                  size="sm"
                >
                  ✕
                </Button>
              </div>
            </div>

            <div className="p-6">
              <div className="space-y-6">
                {selectedApplication.capabilities.map((capability) => {
                  const StateIcon = getStateIcon(capability.state)
                  const TierIcon = getTierIcon(capability.tier)

                  return (
                    <div key={capability.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center mb-2">
                            <StateIcon className="h-5 w-5 text-gray-500 mr-2" />
                            <h4 className="text-lg font-medium text-gray-900">{capability.name}</h4>
                            {capability.isRequired && (
                              <span className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                                Required
                              </span>
                            )}
                            <span className={`ml-2 px-2 py-1 text-xs rounded border ${getStateColor(capability.state)}`}>
                              {capability.state.toUpperCase()}
                            </span>
                            {TierIcon && (
                              <div className="ml-2 flex items-center">
                                <TierIcon className={`h-4 w-4 ${getTierColor(capability.tier)}`} />
                                <span className={`ml-1 text-xs capitalize ${getTierColor(capability.tier)}`}>
                                  {capability.tier}
                                </span>
                              </div>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mb-3">{capability.description}</p>
                          <div className="text-sm text-gray-500">
                            <strong>{capability.enabledOrganizations}</strong> of{' '}
                            <strong>{selectedApplication.totalOrganizations}</strong> organizations enabled
                          </div>
                        </div>
                        <div className="flex flex-col gap-2 ml-4">
                          <Button variant="secondary" size="sm">
                            Configure Access
                          </Button>
                          <Button variant="secondary" size="sm">
                            Rollout Settings
                          </Button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}