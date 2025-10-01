'use client'

import { useState, useEffect } from 'react'
import {
  ChartBarIcon,
  CogIcon,
  EyeIcon,
  CubeIcon,
  AdjustmentsHorizontalIcon,
  StarIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'
import { Organisation } from '@/types/api'

interface OrganisationApplicationConfigProps {
  organisation: Organisation
  onSave: (config: OrganisationAppConfig) => void
  onCancel: () => void
}

interface ApplicationConfig {
  applicationId: string
  name: string
  enabled: boolean
  capabilities: CapabilityConfig[]
  settings: {
    maturityLevel: 'basic' | 'intermediate' | 'advanced'
    dataRetention: '1_year' | '2_years' | '5_years' | 'indefinite'
    exportFormats: string[]
    tier: 'basic' | 'professional' | 'enterprise'
  }
}

interface CapabilityConfig {
  id: string
  name: string
  enabled: boolean
  state: 'preview' | 'beta' | 'ga'
  isRequired: boolean
  tier: 'basic' | 'professional' | 'enterprise'
  description: string
  comingSoon?: boolean
  eta?: string
}

interface OrganisationAppConfig {
  organisationId: string
  applications: ApplicationConfig[]
}

const mockApplicationsConfig: ApplicationConfig[] = [
  {
    applicationId: 'CAUSAL_EDGE',
    name: 'Causal Edge',
    enabled: true,
    capabilities: [
      {
        id: 'core-platform',
        name: 'Core Platform',
        enabled: true,
        state: 'ga',
        isRequired: true,
        tier: 'basic',
        description: 'Essential dashboard and data management'
      },
      {
        id: 'geolift-analysis',
        name: 'Geolift Analysis',
        enabled: true,
        state: 'ga',
        isRequired: false,
        tier: 'professional',
        description: 'Geographic lift testing and analysis'
      },
      {
        id: 'price-elasticity',
        name: 'Price Elasticity',
        enabled: false,
        state: 'beta',
        isRequired: false,
        tier: 'enterprise',
        description: 'Dynamic pricing and elasticity modeling',
        comingSoon: true,
        eta: 'Q2 2024'
      },
      {
        id: 'consultant-dialogue',
        name: 'Consultant Dialogue',
        enabled: true,
        state: 'preview',
        isRequired: false,
        tier: 'professional',
        description: 'AI-powered consultation and recommendations'
      }
    ],
    settings: {
      maturityLevel: 'intermediate',
      dataRetention: '2_years',
      exportFormats: ['csv', 'xlsx', 'pdf'],
      tier: 'professional'
    }
  },
  {
    applicationId: 'MARKET_EDGE',
    name: 'Market Edge',
    enabled: false,
    capabilities: [
      {
        id: 'core-dashboard',
        name: 'Core Dashboard',
        enabled: false,
        state: 'ga',
        isRequired: true,
        tier: 'basic',
        description: 'Market overview and competitive positioning'
      },
      {
        id: 'competitor-tracking',
        name: 'Competitor Tracking',
        enabled: false,
        state: 'ga',
        isRequired: false,
        tier: 'professional',
        description: 'Real-time competitor monitoring'
      },
      {
        id: 'market-forecasting',
        name: 'Market Forecasting',
        enabled: false,
        state: 'beta',
        isRequired: false,
        tier: 'enterprise',
        description: 'Predictive market trend analysis'
      }
    ],
    settings: {
      maturityLevel: 'basic',
      dataRetention: '1_year',
      exportFormats: ['csv'],
      tier: 'basic'
    }
  },
  {
    applicationId: 'VALUE_EDGE',
    name: 'Value Edge',
    enabled: true,
    capabilities: [
      {
        id: 'roi-tracking',
        name: 'ROI Tracking',
        enabled: true,
        state: 'beta',
        isRequired: true,
        tier: 'basic',
        description: 'Return on investment measurement'
      },
      {
        id: 'value-optimization',
        name: 'Value Optimization',
        enabled: false,
        state: 'preview',
        isRequired: false,
        tier: 'enterprise',
        description: 'Automated value optimization recommendations'
      }
    ],
    settings: {
      maturityLevel: 'advanced',
      dataRetention: '5_years',
      exportFormats: ['csv', 'xlsx', 'json'],
      tier: 'enterprise'
    }
  }
]

export function OrganisationApplicationConfig({
  organisation,
  onSave,
  onCancel
}: OrganisationApplicationConfigProps) {
  const [config, setConfig] = useState<OrganisationAppConfig>({
    organisationId: organisation.id,
    applications: mockApplicationsConfig
  })

  const getApplicationIcon = (appId: string) => {
    switch (appId) {
      case 'CAUSAL_EDGE': return ChartBarIcon
      case 'MARKET_EDGE': return EyeIcon
      case 'VALUE_EDGE': return CogIcon
      default: return CubeIcon
    }
  }

  const getStateColor = (state: CapabilityConfig['state']) => {
    switch (state) {
      case 'ga': return 'bg-green-100 text-green-800 border-green-300'
      case 'beta': return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'preview': return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      default: return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getStateIcon = (state: CapabilityConfig['state']) => {
    switch (state) {
      case 'ga': return CheckCircleIcon
      case 'beta': return ExclamationCircleIcon
      case 'preview': return ClockIcon
      default: return ClockIcon
    }
  }

  const getTierIcon = (tier: CapabilityConfig['tier']) => {
    switch (tier) {
      case 'enterprise': return StarIcon
      case 'professional': return AdjustmentsHorizontalIcon
      default: return null
    }
  }

  const getTierColor = (tier: CapabilityConfig['tier']) => {
    switch (tier) {
      case 'enterprise': return 'text-purple-600'
      case 'professional': return 'text-blue-600'
      default: return 'text-gray-600'
    }
  }

  const toggleApplicationEnabled = (appId: string, enabled: boolean) => {
    setConfig(prev => ({
      ...prev,
      applications: prev.applications.map(app =>
        app.applicationId === appId
          ? {
              ...app,
              enabled,
              capabilities: app.capabilities.map(cap => ({
                ...cap,
                enabled: enabled && (cap.isRequired || cap.enabled)
              }))
            }
          : app
      )
    }))
  }

  const toggleCapabilityEnabled = (appId: string, capabilityId: string, enabled: boolean) => {
    setConfig(prev => ({
      ...prev,
      applications: prev.applications.map(app =>
        app.applicationId === appId
          ? {
              ...app,
              capabilities: app.capabilities.map(cap =>
                cap.id === capabilityId
                  ? { ...cap, enabled }
                  : cap
              )
            }
          : app
      )
    }))
  }

  const updateApplicationSettings = (appId: string, settings: Partial<ApplicationConfig['settings']>) => {
    setConfig(prev => ({
      ...prev,
      applications: prev.applications.map(app =>
        app.applicationId === appId
          ? { ...app, settings: { ...app.settings, ...settings } }
          : app
      )
    }))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">
            {organisation.name} - Application Configuration
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Configure application access and capabilities for this client
          </p>
          <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
            <span>Industry: {organisation.industry}</span>
            <span>•</span>
            <span>Plan: {organisation.subscription_plan}</span>
          </div>
        </div>
        <div className="flex gap-3">
          <Button onClick={onCancel} variant="secondary">
            Cancel
          </Button>
          <Button onClick={() => onSave(config)} variant="primary">
            Save Configuration
          </Button>
        </div>
      </div>

      <div className="space-y-8">
        {config.applications.map((app) => {
          const IconComponent = getApplicationIcon(app.applicationId)

          return (
            <div key={app.applicationId} className="bg-white border border-gray-200 rounded-lg">
              {/* Application Header */}
              <div className="p-6 border-b border-gray-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl flex items-center justify-center mr-4">
                      <IconComponent className="h-7 w-7 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900">{app.name}</h4>
                      <p className="text-sm text-gray-500">
                        {app.capabilities.filter(c => c.enabled).length} of {app.capabilities.length} capabilities enabled
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={app.enabled}
                        onChange={(e) => toggleApplicationEnabled(app.applicationId, e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm font-medium text-gray-700">
                        {app.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </label>
                  </div>
                </div>
              </div>

              {app.enabled && (
                <>
                  {/* Capabilities */}
                  <div className="p-6 border-b border-gray-100">
                    <h5 className="text-base font-medium text-gray-900 mb-4">Capabilities</h5>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {app.capabilities.map((capability) => {
                        const StateIcon = getStateIcon(capability.state)
                        const TierIcon = getTierIcon(capability.tier)

                        return (
                          <div
                            key={capability.id}
                            className={`border rounded-lg p-4 ${
                              capability.enabled
                                ? 'border-blue-200 bg-blue-50'
                                : 'border-gray-200 bg-white'
                            } ${capability.comingSoon ? 'opacity-75' : ''}`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center mb-2">
                                  <StateIcon className="h-4 w-4 text-gray-500 mr-2" />
                                  <h6 className="text-sm font-medium text-gray-900">
                                    {capability.name}
                                  </h6>
                                  {capability.isRequired && (
                                    <span className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                                      Required
                                    </span>
                                  )}
                                  {capability.comingSoon && (
                                    <span className="ml-2 px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">
                                      Coming {capability.eta}
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-gray-600 mb-2">
                                  {capability.description}
                                </p>
                                <div className="flex items-center space-x-2">
                                  <span className={`inline-flex px-2 py-1 text-xs rounded border ${getStateColor(capability.state)}`}>
                                    {capability.state.toUpperCase()}
                                  </span>
                                  {TierIcon && (
                                    <div className="flex items-center">
                                      <TierIcon className={`h-3 w-3 ${getTierColor(capability.tier)}`} />
                                      <span className={`ml-1 text-xs capitalize ${getTierColor(capability.tier)}`}>
                                        {capability.tier}
                                      </span>
                                    </div>
                                  )}
                                </div>
                              </div>
                              {!capability.comingSoon && (
                                <label className="flex items-center ml-4">
                                  <input
                                    type="checkbox"
                                    checked={capability.enabled}
                                    disabled={capability.isRequired}
                                    onChange={(e) =>
                                      toggleCapabilityEnabled(
                                        app.applicationId,
                                        capability.id,
                                        e.target.checked
                                      )
                                    }
                                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                                  />
                                </label>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Settings */}
                  <div className="p-6">
                    <h5 className="text-base font-medium text-gray-900 mb-4">Settings</h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Maturity Level
                        </label>
                        <select
                          value={app.settings.maturityLevel}
                          onChange={(e) => updateApplicationSettings(app.applicationId, {
                            maturityLevel: e.target.value as any
                          })}
                          className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                        >
                          <option value="basic">Basic</option>
                          <option value="intermediate">Intermediate</option>
                          <option value="advanced">Advanced</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Data Retention
                        </label>
                        <select
                          value={app.settings.dataRetention}
                          onChange={(e) => updateApplicationSettings(app.applicationId, {
                            dataRetention: e.target.value as any
                          })}
                          className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                        >
                          <option value="1_year">1 Year</option>
                          <option value="2_years">2 Years</option>
                          <option value="5_years">5 Years</option>
                          <option value="indefinite">Indefinite</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Client Tier
                        </label>
                        <select
                          value={app.settings.tier}
                          onChange={(e) => updateApplicationSettings(app.applicationId, {
                            tier: e.target.value as any
                          })}
                          className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                        >
                          <option value="basic">Basic</option>
                          <option value="professional">Professional</option>
                          <option value="enterprise">Enterprise</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Export Formats
                        </label>
                        <div className="text-sm text-gray-600">
                          {app.settings.exportFormats.join(', ')}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Based on tier selection
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}