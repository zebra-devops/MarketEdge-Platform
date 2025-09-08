'use client'

import React, { useState } from 'react'
import { 
  ChartBarIcon, 
  CogIcon, 
  EyeIcon,
  ArrowTopRightOnSquareIcon,
  BuildingOfficeIcon,
  UsersIcon,
  ChartPieIcon,
  FlagIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'
import { ApplicationConfig, APPLICATION_REGISTRY } from './ApplicationRegistry'
import { useApplicationAccess } from '@/hooks/useModuleFeatureFlag'
import { useRouter } from 'next/navigation'

interface FeatureFlaggedApplicationRegistryProps {
  onApplicationSelect?: (application: ApplicationConfig) => void
  filter?: {
    category?: ApplicationConfig['category']
    status?: ApplicationConfig['status']
  }
  showFlagStatus?: boolean
  showModuleHealth?: boolean
  className?: string
}

interface ApplicationCardWithFlagsProps {
  application: ApplicationConfig
  onSelect?: (application: ApplicationConfig) => void
  showFlagStatus?: boolean
  showModuleHealth?: boolean
  showFeatures?: boolean
  compact?: boolean
  className?: string
}

function ApplicationCardWithFlags({ 
  application, 
  onSelect,
  showFlagStatus = true,
  showModuleHealth = true,
  showFeatures = true,
  compact = false,
  className = ''
}: ApplicationCardWithFlagsProps) {
  const { icon: Icon, color } = application
  const router = useRouter()
  const [showDetails, setShowDetails] = useState(false)

  // Use the application access hook to check flags and module status
  const {
    canAccessApplication,
    canAccessFeature,
    canUseCapability,
    applicationConfig,
    moduleCapabilities,
    isLoading,
    error,
    debugInfo
  } = useApplicationAccess(application.id)

  const handleCardClick = () => {
    if (canAccessApplication && !isLoading) {
      if (onSelect) {
        onSelect(application)
      } else {
        router.push(application.route)
      }
    }
  }

  const getAccessStatus = () => {
    if (isLoading) return { status: 'loading', color: 'gray' }
    if (error) return { status: 'error', color: 'red' }
    if (canAccessApplication) return { status: 'enabled', color: 'green' }
    return { status: 'disabled', color: 'red' }
  }

  const accessStatus = getAccessStatus()

  return (
    <div 
      className={`
        bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md 
        transition-all duration-200 relative
        ${canAccessApplication && !isLoading ? 'cursor-pointer hover:-translate-y-1' : 'cursor-not-allowed opacity-75'}
        ${className}
      `}
      onClick={handleCardClick}
    >
      {/* Flag Status Indicator */}
      {showFlagStatus && (
        <div className="absolute top-3 right-3 flex items-center space-x-1">
          <div className={`w-3 h-3 rounded-full ${
            accessStatus.status === 'loading' ? 'bg-gray-400 animate-pulse' :
            accessStatus.status === 'enabled' ? 'bg-green-500' :
            accessStatus.status === 'error' ? 'bg-yellow-500' : 'bg-red-500'
          }`} />
          {showDetails && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowDetails(!showDetails)
              }}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              <FlagIcon className="h-4 w-4" />
            </button>
          )}
        </div>
      )}

      <div className={`${compact ? 'p-4' : 'p-6'}`}>
        {/* Header */}
        <div className="flex items-center mb-3">
          <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${color.gradient} flex items-center justify-center shadow-sm ${
            !canAccessApplication && !isLoading ? 'grayscale' : ''
          }`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
          <div className="ml-3 flex-1">
            <h3 className="font-semibold text-gray-900">{application.displayName}</h3>
            <div className="flex items-center space-x-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                canAccessApplication ? `bg-green-100 text-green-800` : `bg-red-100 text-red-800`
              }`}>
                {isLoading ? 'Checking...' : canAccessApplication ? 'Available' : 'Restricted'}
              </span>
              {!isLoading && canAccessApplication && (
                <ArrowTopRightOnSquareIcon className="h-3 w-3 text-gray-400" />
              )}
            </div>
          </div>
        </div>
        
        <p className="text-sm text-gray-600 mb-3">
          {application.description}
        </p>

        {/* Feature Flags Status */}
        {showFlagStatus && !compact && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>Feature Flags</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowDetails(!showDetails)
                }}
                className="text-blue-600 hover:text-blue-700"
              >
                {showDetails ? 'Hide' : 'Show'} Details
              </button>
            </div>
            
            <div className="flex items-center space-x-1">
              {/* Required Flags */}
              {application.requiredFlags.map((flagKey) => (
                <div
                  key={flagKey}
                  className={`w-2 h-2 rounded-full ${
                    debugInfo.requiredFlags[flagKey] ? 'bg-green-500' : 'bg-red-500'
                  }`}
                  title={`Required: ${flagKey} - ${debugInfo.requiredFlags[flagKey] ? 'Enabled' : 'Disabled'}`}
                />
              ))}
              
              {/* Optional Flags */}
              {application.optionalFlags.map((flagKey) => (
                <div
                  key={flagKey}
                  className={`w-2 h-2 rounded-full border ${
                    debugInfo.optionalFlags[flagKey] 
                      ? 'bg-blue-500 border-blue-500' 
                      : 'bg-gray-300 border-gray-300'
                  }`}
                  title={`Optional: ${flagKey} - ${debugInfo.optionalFlags[flagKey] ? 'Enabled' : 'Disabled'}`}
                />
              ))}
              
              {/* Module Status */}
              <div className="ml-2 flex items-center">
                <ShieldCheckIcon className={`h-3 w-3 ${
                  debugInfo.moduleEnabled 
                    ? debugInfo.moduleHealth === 'healthy' ? 'text-green-500' : 'text-yellow-500'
                    : 'text-red-500'
                }`} />
              </div>
            </div>
          </div>
        )}

        {/* Module Capabilities */}
        {showModuleHealth && moduleCapabilities.length > 0 && !compact && (
          <div className="mb-3">
            <p className="text-xs text-gray-500 mb-1">Capabilities ({moduleCapabilities.length}):</p>
            <div className="flex flex-wrap gap-1">
              {moduleCapabilities.slice(0, 3).map((capability) => (
                <span
                  key={capability}
                  className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                    canUseCapability(capability) 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {capability}
                </span>
              ))}
              {moduleCapabilities.length > 3 && (
                <span className="text-xs text-gray-400">
                  +{moduleCapabilities.length - 3}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Features List */}
        {showFeatures && !compact && (
          <div className="space-y-1">
            {application.features.slice(0, 3).map((feature, index) => (
              <div key={index} className="flex items-center text-xs text-gray-500">
                <div className={`w-1.5 h-1.5 rounded-full ${
                  canAccessApplication ? `bg-${color.primary}` : 'bg-gray-400'
                } mr-2`} />
                {feature}
              </div>
            ))}
            {application.features.length > 3 && (
              <div className="text-xs text-gray-400 pl-3.5">
                +{application.features.length - 3} more features
              </div>
            )}
          </div>
        )}

        {/* Detailed Flag Information */}
        {showDetails && (
          <div className="mt-4 pt-3 border-t border-gray-200 text-xs space-y-2">
            <div>
              <span className="font-medium text-gray-700">Required Flags:</span>
              <div className="mt-1 space-y-1">
                {application.requiredFlags.map((flagKey) => (
                  <div key={flagKey} className="flex items-center justify-between">
                    <span className="text-gray-600">{flagKey}</span>
                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs ${
                      debugInfo.requiredFlags[flagKey] 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {debugInfo.requiredFlags[flagKey] ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {application.optionalFlags.length > 0 && (
              <div>
                <span className="font-medium text-gray-700">Optional Flags:</span>
                <div className="mt-1 space-y-1">
                  {application.optionalFlags.map((flagKey) => (
                    <div key={flagKey} className="flex items-center justify-between">
                      <span className="text-gray-600">{flagKey}</span>
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs ${
                        debugInfo.optionalFlags[flagKey] 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {debugInfo.optionalFlags[flagKey] ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div>
              <span className="font-medium text-gray-700">Module Status:</span>
              <div className="mt-1 flex items-center justify-between">
                <span className="text-gray-600">{application.moduleId}</span>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs ${
                    debugInfo.moduleEnabled 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {debugInfo.moduleEnabled ? 'Enabled' : 'Disabled'}
                  </span>
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs ${
                    debugInfo.moduleHealth === 'healthy' ? 'bg-green-100 text-green-800' :
                    debugInfo.moduleHealth === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {debugInfo.moduleHealth}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs">
            <div className="flex items-center text-red-800">
              <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
              Error: {error.message}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function FeatureFlaggedApplicationRegistry({ 
  onApplicationSelect,
  filter,
  showFlagStatus = true,
  showModuleHealth = true,
  className = ''
}: FeatureFlaggedApplicationRegistryProps) {
  let applications = APPLICATION_REGISTRY

  // Apply filters
  if (filter?.category) {
    applications = applications.filter(app => app.category === filter.category)
  }
  if (filter?.status) {
    applications = applications.filter(app => app.status === filter.status)
  }

  // Sort by priority
  applications = applications.sort((a, b) => a.priority - b.priority)

  const categoryIcons = {
    analytics: ChartPieIcon,
    intelligence: BuildingOfficeIcon,
    optimization: UsersIcon
  }

  return (
    <div className={`space-y-8 ${className}`}>
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Application Registry
        </h2>
        <p className="text-gray-600">
          Access applications based on your feature flags and permissions
        </p>
      </div>

      {/* Applications Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {applications.map((app) => (
          <ApplicationCardWithFlags
            key={app.id}
            application={app}
            onSelect={onApplicationSelect}
            showFlagStatus={showFlagStatus}
            showModuleHealth={showModuleHealth}
            showFeatures={true}
          />
        ))}
      </div>

      {/* Categories Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-8 border-t border-gray-200">
        {Object.entries(categoryIcons).map(([category, Icon]) => {
          const categoryApps = applications.filter(app => app.category === category)
          if (categoryApps.length === 0) return null

          return (
            <div key={category} className="text-center">
              <Icon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <h3 className="font-medium text-gray-900 capitalize">{category}</h3>
              <p className="text-sm text-gray-500">{categoryApps.length} application{categoryApps.length !== 1 ? 's' : ''}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}