'use client'

import React, { useState } from 'react'
import {
  CubeIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  EyeIcon,
  CogIcon,
  FlagIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { useModuleDiscovery, useModuleFeatureFlags } from '@/hooks/useModuleFeatureFlags'
import { ModuleDiscoveryResponse } from '@/types/module-feature-flags'

interface ModuleDiscoveryProps {
  userId?: string
  onModuleSelect?: (moduleId: string) => void
  showHealthStatus?: boolean
  showCapabilities?: boolean
  className?: string
}

export const ModuleDiscovery: React.FC<ModuleDiscoveryProps> = ({
  userId,
  onModuleSelect,
  showHealthStatus = true,
  showCapabilities = true,
  className = ''
}) => {
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'enabled' | 'disabled'>('all')
  const [showDetails, setShowDetails] = useState<string | null>(null)

  const {
    enabledModules,
    disabledModules,
    isLoading,
    error,
    totalAvailable,
    userAccessible,
    refresh,
    lastUpdated
  } = useModuleDiscovery(userId)

  const moduleFlags = useModuleFeatureFlags()

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'text-green-600 bg-green-100'
      case 'degraded': return 'text-yellow-600 bg-yellow-100'
      case 'unavailable': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (health: string) => {
    switch (health) {
      case 'healthy': return CheckCircleIcon
      case 'degraded': return ExclamationTriangleIcon
      case 'unavailable': return XCircleIcon
      default: return CubeIcon
    }
  }

  const filteredEnabledModules = selectedFilter === 'disabled' ? [] : enabledModules
  const filteredDisabledModules = selectedFilter === 'enabled' ? [] : disabledModules

  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Module Discovery</h3>
          <div className="animate-spin">
            <ArrowPathIcon className="h-5 w-5 text-gray-400" />
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="animate-pulse">
                <div className="flex items-center mb-3">
                  <div className="w-8 h-8 bg-gray-200 rounded"></div>
                  <div className="ml-3">
                    <div className="h-4 bg-gray-200 rounded w-24 mb-1"></div>
                    <div className="h-3 bg-gray-200 rounded w-16"></div>
                  </div>
                </div>
                <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Module Discovery</h3>
          <button
            onClick={refresh}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Retry
          </button>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Module Discovery Failed</h3>
              <p className="mt-1 text-sm text-red-700">{error.message}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Module Discovery</h3>
          <p className="text-sm text-gray-500">
            Modules available based on your feature flags
            {lastUpdated && (
              <span className="ml-2">
                • Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {/* Filter Buttons */}
          <div className="flex rounded-lg overflow-hidden border border-gray-300">
            {[
              { key: 'all', label: 'All', count: totalAvailable },
              { key: 'enabled', label: 'Enabled', count: enabledModules.length },
              { key: 'disabled', label: 'Disabled', count: disabledModules.length }
            ].map((filter) => (
              <button
                key={filter.key}
                onClick={() => setSelectedFilter(filter.key as any)}
                className={`px-3 py-1.5 text-sm font-medium ${
                  selectedFilter === filter.key
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                {filter.label} ({filter.count})
              </button>
            ))}
          </div>
          
          <button
            onClick={refresh}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center">
            <CubeIcon className="h-6 w-6 text-gray-400" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total Available</p>
              <p className="text-lg font-semibold text-gray-900">{totalAvailable}</p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center">
            <CheckCircleIcon className="h-6 w-6 text-green-400" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Enabled</p>
              <p className="text-lg font-semibold text-gray-900">{enabledModules.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center">
            <XCircleIcon className="h-6 w-6 text-red-400" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Disabled</p>
              <p className="text-lg font-semibold text-gray-900">{disabledModules.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center">
            <FlagIcon className="h-6 w-6 text-blue-400" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">User Accessible</p>
              <p className="text-lg font-semibold text-gray-900">{userAccessible}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Enabled Modules */}
      {filteredEnabledModules.length > 0 && (
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
            Enabled Modules ({filteredEnabledModules.length})
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredEnabledModules.map((module) => {
              const StatusIcon = getStatusIcon(module.health)
              const isDetailed = showDetails === module.module_id

              return (
                <div
                  key={module.module_id}
                  className="bg-white border border-green-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => onModuleSelect?.(module.module_id)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                        <CubeIcon className="h-5 w-5 text-green-600" />
                      </div>
                      <div className="ml-3">
                        <h5 className="font-medium text-gray-900">{module.name}</h5>
                        <p className="text-sm text-gray-500">v{module.version}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {showHealthStatus && (
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getHealthColor(module.health)}`}>
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {module.health}
                        </span>
                      )}
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setShowDetails(isDetailed ? null : module.module_id)
                        }}
                        className="p-1 text-gray-400 hover:text-gray-600"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {showCapabilities && module.capabilities.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 mb-1">Capabilities:</p>
                      <div className="flex flex-wrap gap-1">
                        {module.capabilities.slice(0, 3).map((capability) => (
                          <span
                            key={capability}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {capability}
                          </span>
                        ))}
                        {module.capabilities.length > 3 && (
                          <span className="text-xs text-gray-400">
                            +{module.capabilities.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {isDetailed && (
                    <div className="mt-3 pt-3 border-t border-gray-200 text-xs">
                      <div className="space-y-2">
                        <div>
                          <span className="font-medium text-gray-700">Status: </span>
                          <span className={`font-medium ${module.status === 'active' ? 'text-green-600' : 'text-yellow-600'}`}>
                            {module.status}
                          </span>
                        </div>
                        
                        {Object.keys(module.feature_flags).length > 0 && (
                          <div>
                            <span className="font-medium text-gray-700">Feature Flags: </span>
                            <div className="mt-1 flex flex-wrap gap-1">
                              {Object.entries(module.feature_flags).map(([flagKey, enabled]) => (
                                <span
                                  key={flagKey}
                                  className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs ${
                                    enabled 
                                      ? 'bg-green-100 text-green-800' 
                                      : 'bg-red-100 text-red-800'
                                  }`}
                                >
                                  {flagKey.split('.').pop()}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {Object.keys(module.config).length > 0 && (
                          <div>
                            <span className="font-medium text-gray-700">Config Keys: </span>
                            <span className="text-gray-600">
                              {Object.keys(module.config).join(', ')}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Disabled Modules */}
      {filteredDisabledModules.length > 0 && (
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
            <XCircleIcon className="h-5 w-5 text-red-500 mr-2" />
            Disabled Modules ({filteredDisabledModules.length})
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredDisabledModules.map((module) => (
              <div
                key={module.module_id}
                className="bg-gray-50 border border-gray-200 rounded-lg p-4"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                      <CubeIcon className="h-5 w-5 text-gray-400" />
                    </div>
                    <div className="ml-3">
                      <h5 className="font-medium text-gray-900">{module.name}</h5>
                      <p className="text-sm text-gray-500">Disabled</p>
                    </div>
                  </div>
                  
                  {module.can_enable && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      Can Enable
                    </span>
                  )}
                </div>

                <div className="text-sm text-gray-600 mb-2">
                  <span className="font-medium">Reason: </span>
                  {module.reason}
                </div>

                {module.missing_flags.length > 0 && (
                  <div className="text-xs">
                    <span className="font-medium text-gray-700">Missing Flags: </span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {module.missing_flags.map((flagKey) => (
                        <span
                          key={flagKey}
                          className="inline-flex items-center px-1.5 py-0.5 rounded bg-red-100 text-red-800"
                        >
                          {flagKey.split('.').pop()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {enabledModules.length === 0 && disabledModules.length === 0 && (
        <div className="text-center py-12">
          <CubeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No modules found</h3>
          <p className="mt-1 text-sm text-gray-500">
            No modules are currently available for discovery.
          </p>
          <div className="mt-6">
            <button
              onClick={refresh}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Refresh Discovery
            </button>
          </div>
        </div>
      )}
    </div>
  )
}