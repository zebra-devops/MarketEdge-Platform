'use client'

import React, { useState, useEffect } from 'react'
import {
  CubeIcon,
  PlusIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  FlagIcon,
  EyeIcon,
  AdjustmentsHorizontalIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  BoltIcon,
  BuildingOffice2Icon
} from '@heroicons/react/24/outline'
import { useModuleFeatureFlags, useModuleDiscovery, useModuleHealth } from '@/hooks/useModuleFeatureFlags'
import { apiService } from '@/services/api'
import { ModuleDiscovery } from './ModuleDiscovery'
import { ModuleFlagManager } from './ModuleFlagManager'
import { AnalyticsModule } from '@/types/module-feature-flags'

type ViewMode = 'overview' | 'discovery' | 'flags' | 'health'

interface EnhancedModuleManagerProps {
  defaultView?: ViewMode
  className?: string
}

export const EnhancedModuleManager: React.FC<EnhancedModuleManagerProps> = ({
  defaultView = 'overview',
  className = ''
}) => {
  const [currentView, setCurrentView] = useState<ViewMode>(defaultView)
  const [selectedModuleId, setSelectedModuleId] = useState<string | null>(null)
  const [modules, setModules] = useState<AnalyticsModule[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Hooks for module feature flags
  const moduleFlags = useModuleFeatureFlags()
  const moduleDiscovery = useModuleDiscovery()

  const fetchModules = async () => {
    try {
      setIsLoading(true)
      const data = await apiService.get<{modules: AnalyticsModule[]}>('/admin/modules')
      setModules(data.modules || [])
      setError(null)
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Authentication error: Please log in again')
        return
      }
      setError(err.message || 'Failed to load modules')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchModules()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'testing': return 'bg-yellow-100 text-yellow-800'
      case 'development': return 'bg-blue-100 text-blue-800'
      case 'deprecated': return 'bg-red-100 text-red-800'
      case 'disabled': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'core': return 'bg-purple-100 text-purple-800'
      case 'analytics': return 'bg-blue-100 text-blue-800'
      case 'visualization': return 'bg-green-100 text-green-800'
      case 'integration': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getViewIcon = (view: ViewMode) => {
    switch (view) {
      case 'overview': return CubeIcon
      case 'discovery': return EyeIcon
      case 'flags': return FlagIcon
      case 'health': return ShieldCheckIcon
      default: return CubeIcon
    }
  }

  const getModuleHealth = (moduleId: string): 'healthy' | 'degraded' | 'unavailable' => {
    // Check if module has required flags enabled
    const isEnabled = moduleFlags.moduleFlags[moduleId]
    if (!isEnabled) return 'unavailable'
    
    // Check discovery status
    const discoveryModule = moduleDiscovery.enabledModules.find(m => m.module_id === moduleId)
    if (!discoveryModule) return 'unavailable'
    
    return discoveryModule.health || 'healthy'
  }

  const viewTabs: Array<{ key: ViewMode; label: string; description: string }> = [
    { key: 'overview', label: 'Overview', description: 'Module registry and status' },
    { key: 'discovery', label: 'Discovery', description: 'Feature flag-driven module discovery' },
    { key: 'flags', label: 'Flag Management', description: 'Module feature flag hierarchy' },
    { key: 'health', label: 'Health Monitor', description: 'Module health and dependencies' }
  ]

  const renderViewTabs = () => (
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8" aria-label="Tabs">
        {viewTabs.map((tab) => {
          const Icon = getViewIcon(tab.key)
          const isActive = currentView === tab.key
          
          return (
            <button
              key={tab.key}
              onClick={() => setCurrentView(tab.key)}
              className={`group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                isActive
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className={`mr-2 h-5 w-5 ${
                isActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
              }`} />
              <div className="text-left">
                <div>{tab.label}</div>
                <div className="text-xs opacity-75">{tab.description}</div>
              </div>
            </button>
          )
        })}
      </nav>
    </div>
  )

  const renderOverview = () => {
    if (isLoading) {
      return (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-6">
                <div className="animate-pulse">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-gray-200 rounded"></div>
                    <div className="ml-4 flex-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )
    }

    return (
      <div className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-5">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CubeIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Modules</dt>
                    <dd className="text-lg font-medium text-gray-900">{modules.length}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CheckCircleIcon className="h-6 w-6 text-green-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Active</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {modules.filter(m => m.status === 'active').length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <FlagIcon className="h-6 w-6 text-blue-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Flag Enabled</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {moduleFlags.enabledModules.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ShieldCheckIcon className="h-6 w-6 text-purple-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Core Modules</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {modules.filter(m => m.is_core).length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <BuildingOffice2Icon className="h-6 w-6 text-yellow-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Licensed</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {modules.filter(m => m.requires_license).length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modules Grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {modules.map((module) => {
            const health = getModuleHealth(module.id)
            const isEnabled = moduleFlags.moduleFlags[module.id] || false
            const capabilities = moduleFlags.moduleCapabilities[module.id] || []

            return (
              <div 
                key={module.id} 
                className={`bg-white overflow-hidden shadow rounded-lg border-l-4 ${
                  isEnabled ? 'border-l-green-400' : 'border-l-red-400'
                }`}
              >
                <div className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <CubeIcon className={`h-10 w-10 ${
                          isEnabled ? 'text-green-600' : 'text-gray-400'
                        }`} />
                      </div>
                      <div className="ml-4 flex-1">
                        <h3 className="text-lg font-medium text-gray-900">{module.name}</h3>
                        <p className="text-sm text-gray-500">v{module.version}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {/* Health Status */}
                      <div className={`w-3 h-3 rounded-full ${
                        health === 'healthy' ? 'bg-green-500' :
                        health === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                      }`} title={`Health: ${health}`} />
                      
                      {/* Feature Flag Status */}
                      <FlagIcon className={`h-4 w-4 ${
                        isEnabled ? 'text-green-500' : 'text-gray-400'
                      }`} title={`Feature Flags: ${isEnabled ? 'Enabled' : 'Disabled'}`} />
                    </div>
                  </div>
                  
                  <p className="mt-4 text-sm text-gray-600 line-clamp-3">
                    {module.description}
                  </p>
                  
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(module.status)}`}>
                      {module.status}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTypeColor(module.module_type)}`}>
                      {module.module_type}
                    </span>
                    {module.is_core && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        Core
                      </span>
                    )}
                    {module.requires_license && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        Licensed
                      </span>
                    )}
                    {isEnabled && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Flag Enabled
                      </span>
                    )}
                  </div>
                  
                  {/* Capabilities */}
                  {capabilities.length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs text-gray-500 mb-1">Capabilities ({capabilities.length}):</p>
                      <div className="flex flex-wrap gap-1">
                        {capabilities.slice(0, 3).map((capability) => (
                          <span
                            key={capability}
                            className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {capability}
                          </span>
                        ))}
                        {capabilities.length > 3 && (
                          <span className="text-xs text-gray-400">
                            +{capabilities.length - 3}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {module.pricing_tier && (
                    <div className="mt-2">
                      <span className="text-xs text-gray-500">
                        Pricing: <span className="font-medium">{module.pricing_tier}</span>
                      </span>
                    </div>
                  )}
                  
                  {module.dependencies.length > 0 && (
                    <div className="mt-2">
                      <span className="text-xs text-gray-500">
                        Dependencies: {module.dependencies.join(', ')}
                      </span>
                    </div>
                  )}
                  
                  <div className="mt-6 flex justify-between items-center">
                    <div className="flex space-x-2">
                      <button 
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                        onClick={() => {
                          setSelectedModuleId(module.id)
                          setCurrentView('flags')
                        }}
                      >
                        <FlagIcon className="h-3 w-3 mr-1" />
                        Flags
                      </button>
                      <button 
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                        onClick={() => {
                          setSelectedModuleId(module.id)
                          setCurrentView('health')
                        }}
                      >
                        <ShieldCheckIcon className="h-3 w-3 mr-1" />
                        Health
                      </button>
                      <button className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50">
                        <ChartBarIcon className="h-3 w-3 mr-1" />
                        Analytics
                      </button>
                    </div>
                    <span className="text-xs text-gray-400">
                      {new Date(module.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
        
        {modules.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <CubeIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No modules found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Analytics modules will appear here once they are registered.
            </p>
          </div>
        )}
      </div>
    )
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case 'overview':
        return renderOverview()
      case 'discovery':
        return <ModuleDiscovery onModuleSelect={setSelectedModuleId} />
      case 'flags':
        return <ModuleFlagManager moduleId={selectedModuleId || undefined} onModuleSelect={setSelectedModuleId} />
      case 'health':
        return <div className="text-center py-12 text-gray-500">Module health monitoring coming soon...</div>
      default:
        return renderOverview()
    }
  }

  if (error && currentView === 'overview') {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Enhanced Module Manager</h2>
          <button
            onClick={fetchModules}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Retry
          </button>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading Modules</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Enhanced Module Manager</h2>
          <p className="mt-1 text-sm text-gray-500">
            Comprehensive module management with feature flag integration
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => {
              fetchModules()
              moduleFlags.refetch()
              moduleDiscovery.refresh()
            }}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Refresh All
          </button>
        </div>
      </div>

      {renderViewTabs()}
      
      <div className="mt-6">
        {renderCurrentView()}
      </div>
    </div>
  )
}