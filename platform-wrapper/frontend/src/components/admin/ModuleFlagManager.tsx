'use client'

import React, { useState } from 'react'
import {
  FlagIcon,
  CubeIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  Cog6ToothIcon,
  ArrowPathIcon,
  PlusIcon,
  EyeIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline'
import { useModuleFlagHierarchy, useModuleFeatureFlags } from '@/hooks/useModuleFeatureFlags'
import { ModuleFlagHierarchy } from '@/types/module-feature-flags'

interface ModuleFlagManagerProps {
  moduleId?: string
  onModuleSelect?: (moduleId: string) => void
  showHierarchy?: boolean
  showInheritance?: boolean
  className?: string
}

interface FlagHierarchyNodeProps {
  level: string
  flags: Array<{
    flag_key: string
    name: string
    enabled: boolean
    [key: string]: any
  }>
  effectiveFlags: Record<string, any>
  onFlagSelect?: (flagKey: string) => void
  isExpanded: boolean
  onToggleExpanded: () => void
}

const FlagHierarchyNode: React.FC<FlagHierarchyNodeProps> = ({
  level,
  flags,
  effectiveFlags,
  onFlagSelect,
  isExpanded,
  onToggleExpanded
}) => {
  const getLevelColor = (level: string) => {
    switch (level) {
      case 'global': return 'text-blue-600 bg-blue-100 border-blue-200'
      case 'module': return 'text-green-600 bg-green-100 border-green-200'
      case 'features': return 'text-purple-600 bg-purple-100 border-purple-200'
      case 'capabilities': return 'text-orange-600 bg-orange-100 border-orange-200'
      default: return 'text-gray-600 bg-gray-100 border-gray-200'
    }
  }

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'global': return FlagIcon
      case 'module': return CubeIcon
      case 'features': return Cog6ToothIcon
      case 'capabilities': return AdjustmentsHorizontalIcon
      default: return FlagIcon
    }
  }

  const LevelIcon = getLevelIcon(level)

  if (flags.length === 0) return null

  return (
    <div className="border border-gray-200 rounded-lg mb-4">
      <button
        onClick={onToggleExpanded}
        className={`w-full flex items-center justify-between p-4 ${getLevelColor(level)} rounded-t-lg border-b`}
      >
        <div className="flex items-center">
          <LevelIcon className="h-5 w-5 mr-2" />
          <h4 className="text-lg font-medium capitalize">{level} Flags ({flags.length})</h4>
        </div>
        {isExpanded ? (
          <ChevronDownIcon className="h-5 w-5" />
        ) : (
          <ChevronRightIcon className="h-5 w-5" />
        )}
      </button>

      {isExpanded && (
        <div className="p-4 space-y-3">
          {flags.map((flag) => {
            const isEffective = effectiveFlags[flag.flag_key]?.enabled
            const effectiveSource = effectiveFlags[flag.flag_key]?.source
            const isOverridden = effectiveSource !== level

            return (
              <div
                key={flag.flag_key}
                className={`flex items-center justify-between p-3 rounded-lg border ${
                  isEffective 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                } ${isOverridden ? 'opacity-60' : ''}`}
                onClick={() => onFlagSelect?.(flag.flag_key)}
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    isEffective ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  
                  <div>
                    <p className="font-medium text-gray-900">{flag.name}</p>
                    <p className="text-sm text-gray-500">{flag.flag_key}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <div className="text-right">
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        flag.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {flag.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                      
                      {isOverridden && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Overridden by {effectiveSource}
                        </span>
                      )}
                    </div>
                    
                    {effectiveSource && (
                      <p className="text-xs text-gray-500 mt-1">
                        Effective: {isEffective ? 'Enabled' : 'Disabled'} ({effectiveSource})
                      </p>
                    )}
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onFlagSelect?.(flag.flag_key)
                    }}
                    className="p-1 text-gray-400 hover:text-gray-600"
                  >
                    <EyeIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export const ModuleFlagManager: React.FC<ModuleFlagManagerProps> = ({
  moduleId: initialModuleId,
  onModuleSelect,
  showHierarchy = true,
  showInheritance = true,
  className = ''
}) => {
  const [selectedModuleId, setSelectedModuleId] = useState(initialModuleId)
  const [selectedFlag, setSelectedFlag] = useState<string | null>(null)
  const [expandedLevels, setExpandedLevels] = useState<Record<string, boolean>>({
    global: true,
    module: true,
    features: false,
    capabilities: false
  })

  const moduleFlags = useModuleFeatureFlags()
  const hierarchy = useModuleFlagHierarchy(selectedModuleId || '')

  const toggleLevelExpanded = (level: string) => {
    setExpandedLevels(prev => ({
      ...prev,
      [level]: !prev[level]
    }))
  }

  const handleModuleSelect = (moduleId: string) => {
    setSelectedModuleId(moduleId)
    onModuleSelect?.(moduleId)
  }

  const handleFlagSelect = (flagKey: string) => {
    setSelectedFlag(flagKey)
  }

  if (moduleFlags.isLoading || (selectedModuleId && hierarchy.isLoading)) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Module Flag Manager</h3>
          <div className="animate-spin">
            <ArrowPathIcon className="h-5 w-5 text-gray-400" />
          </div>
        </div>
        
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 rounded w-full"></div>
                  <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (moduleFlags.error || (selectedModuleId && hierarchy.error)) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Module Flag Manager</h3>
          <button
            onClick={() => {
              moduleFlags.refetch()
              if (selectedModuleId) hierarchy.refetch()
            }}
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
              <h3 className="text-sm font-medium text-red-800">Failed to Load Module Flags</h3>
              <p className="mt-1 text-sm text-red-700">
                {moduleFlags.error?.message || hierarchy.error?.message}
              </p>
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
          <h3 className="text-lg font-medium text-gray-900">Module Flag Manager</h3>
          <p className="text-sm text-gray-500">
            Manage feature flags and their hierarchical relationships
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              moduleFlags.refetch()
              if (selectedModuleId) hierarchy.refetch()
            }}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Module Selection */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-md font-medium text-gray-900 mb-4">Select Module</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {moduleFlags.enabledModules.map((moduleId) => (
            <button
              key={moduleId}
              onClick={() => handleModuleSelect(moduleId)}
              className={`flex items-center p-3 rounded-lg border text-left transition-colors ${
                selectedModuleId === moduleId
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <CubeIcon className="h-5 w-5 mr-3" />
              <div>
                <p className="font-medium">{moduleId}</p>
                <p className="text-xs opacity-75">
                  {moduleFlags.moduleCapabilities[moduleId]?.length || 0} capabilities
                </p>
              </div>
            </button>
          ))}
          
          {moduleFlags.disabledModules.map((moduleId) => (
            <button
              key={moduleId}
              onClick={() => handleModuleSelect(moduleId)}
              className={`flex items-center p-3 rounded-lg border text-left transition-colors opacity-60 ${
                selectedModuleId === moduleId
                  ? 'border-red-500 bg-red-50 text-red-700'
                  : 'border-gray-200 bg-gray-50 text-gray-500 hover:bg-gray-100'
              }`}
            >
              <CubeIcon className="h-5 w-5 mr-3" />
              <div>
                <p className="font-medium">{moduleId}</p>
                <p className="text-xs opacity-75">Disabled</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Module Flag Hierarchy */}
      {selectedModuleId && hierarchy.hierarchy && showHierarchy && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-md font-medium text-gray-900">
              Flag Hierarchy: {selectedModuleId}
            </h4>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setExpandedLevels({ global: true, module: true, features: true, capabilities: true })}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Expand All
              </button>
              <button
                onClick={() => setExpandedLevels({ global: false, module: false, features: false, capabilities: false })}
                className="text-sm text-gray-600 hover:text-gray-700"
              >
                Collapse All
              </button>
            </div>
          </div>

          {/* Global Flags */}
          <FlagHierarchyNode
            level="global"
            flags={hierarchy.hierarchy.global}
            effectiveFlags={hierarchy.effectiveFlags}
            onFlagSelect={handleFlagSelect}
            isExpanded={expandedLevels.global}
            onToggleExpanded={() => toggleLevelExpanded('global')}
          />

          {/* Module Flags */}
          <FlagHierarchyNode
            level="module"
            flags={hierarchy.hierarchy.module}
            effectiveFlags={hierarchy.effectiveFlags}
            onFlagSelect={handleFlagSelect}
            isExpanded={expandedLevels.module}
            onToggleExpanded={() => toggleLevelExpanded('module')}
          />

          {/* Feature Flags */}
          {Object.keys(hierarchy.hierarchy.features).length > 0 && (
            <div>
              {Object.entries(hierarchy.hierarchy.features).map(([featureName, featureFlags]) => (
                <FlagHierarchyNode
                  key={featureName}
                  level={`features.${featureName}`}
                  flags={featureFlags}
                  effectiveFlags={hierarchy.effectiveFlags}
                  onFlagSelect={handleFlagSelect}
                  isExpanded={expandedLevels.features}
                  onToggleExpanded={() => toggleLevelExpanded('features')}
                />
              ))}
            </div>
          )}

          {/* Capability Flags */}
          {Object.keys(hierarchy.hierarchy.capabilities).length > 0 && (
            <div>
              {Object.entries(hierarchy.hierarchy.capabilities).map(([capabilityName, capabilityFlags]) => (
                <FlagHierarchyNode
                  key={capabilityName}
                  level={`capabilities.${capabilityName}`}
                  flags={capabilityFlags}
                  effectiveFlags={hierarchy.effectiveFlags}
                  onFlagSelect={handleFlagSelect}
                  isExpanded={expandedLevels.capabilities}
                  onToggleExpanded={() => toggleLevelExpanded('capabilities')}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Flag Inheritance Chain */}
      {selectedFlag && hierarchy.hierarchy && showInheritance && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-md font-medium text-gray-900 mb-4">
            Inheritance Chain: {selectedFlag}
          </h4>
          
          <div className="space-y-3">
            {hierarchy.getInheritanceChain(selectedFlag).map((chainItem, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  chainItem.enabled ? 'bg-green-500' : 'bg-red-500'
                }`} />
                
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-gray-900">{chainItem.level}</p>
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        chainItem.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {chainItem.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                      
                      {chainItem.overridden_by && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Overridden by {chainItem.overridden_by}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <p className="font-medium text-gray-900">Effective State</p>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                hierarchy.effectiveFlags[selectedFlag]?.enabled 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {hierarchy.effectiveFlags[selectedFlag]?.enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Source: {hierarchy.effectiveFlags[selectedFlag]?.source}
            </p>
          </div>
        </div>
      )}

      {/* Summary */}
      {selectedModuleId && hierarchy.hierarchy && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center">
              <FlagIcon className="h-6 w-6 text-blue-400" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Flags</p>
                <p className="text-lg font-semibold text-gray-900">
                  {Object.keys(hierarchy.effectiveFlags).length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center">
              <CheckCircleIcon className="h-6 w-6 text-green-400" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Enabled</p>
                <p className="text-lg font-semibold text-gray-900">
                  {Object.values(hierarchy.effectiveFlags).filter(f => f.enabled).length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center">
              <XCircleIcon className="h-6 w-6 text-red-400" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Disabled</p>
                <p className="text-lg font-semibold text-gray-900">
                  {Object.values(hierarchy.effectiveFlags).filter(f => !f.enabled).length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Inherited</p>
                <p className="text-lg font-semibold text-gray-900">
                  {hierarchy.inheritance_chain.length}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!selectedModuleId && (
        <div className="text-center py-12">
          <CubeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Select a Module</h3>
          <p className="mt-1 text-sm text-gray-500">
            Choose a module above to view its feature flag hierarchy.
          </p>
        </div>
      )}
    </div>
  )
}