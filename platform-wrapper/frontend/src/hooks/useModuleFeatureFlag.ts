'use client'

import { useMemo } from 'react'
import { useFeatureFlags } from './useFeatureFlags'
import { useModuleFeatureFlags, useModuleDiscovery } from './useModuleFeatureFlags'
import { APPLICATION_REGISTRY } from '@/components/ui/ApplicationRegistry'

/**
 * Hook for checking a specific module's feature flags
 * Combines module-level and capability-level flag checking
 */
export function useModuleFeatureFlag(
  moduleId: string,
  capability?: string
) {
  const moduleFlags = useModuleFeatureFlags()
  const discovery = useModuleDiscovery()

  // Get application config for the module
  const appConfig = useMemo(() => 
    APPLICATION_REGISTRY.find(app => app.moduleId === moduleId),
    [moduleId]
  )

  // Check if module is enabled via feature flags
  const isModuleEnabled = moduleFlags.moduleFlags[moduleId] || false

  // Check if specific capability is enabled
  const hasCapability = capability 
    ? moduleFlags.moduleCapabilities[moduleId]?.includes(capability) || false
    : true

  // Get module discovery info
  const discoveryModule = useMemo(() => 
    discovery.enabledModules.find(m => m.module_id === moduleId) ||
    discovery.disabledModules.find(m => m.module_id === moduleId),
    [discovery.enabledModules, discovery.disabledModules, moduleId]
  )

  // Build hierarchical flag key for the module
  const getModuleFlagKey = (flagSuffix: string) => {
    return `modules.${moduleId.replace(/-/g, '_')}.${flagSuffix}`
  }

  // Build capability flag key
  const getCapabilityFlagKey = (capabilityName: string) => {
    return `modules.${moduleId.replace(/-/g, '_')}.capabilities.${capabilityName}`
  }

  // Get module configuration
  const moduleConfig = moduleFlags.moduleConfigs[moduleId] || {}

  return {
    // Module state
    isModuleEnabled,
    hasCapability,
    isAvailable: !!discoveryModule,
    
    // Module info
    moduleConfig,
    appConfig,
    discoveryModule,
    
    // Capabilities
    availableCapabilities: moduleFlags.moduleCapabilities[moduleId] || [],
    
    // Health
    health: discoveryModule?.health || 'unavailable',
    isHealthy: discoveryModule?.health === 'healthy',
    
    // Loading states
    isLoading: moduleFlags.isLoading || discovery.isLoading,
    error: moduleFlags.error || discovery.error,
    
    // Utility functions
    getModuleFlagKey,
    getCapabilityFlagKey,
    
    // Refresh function
    refresh: () => {
      moduleFlags.refetch()
      discovery.refresh()
    }
  }
}

/**
 * Hook for checking multiple module feature flags at once
 */
export function useMultipleModuleFeatureFlags(moduleIds: string[]) {
  const moduleFlags = useModuleFeatureFlags()
  const discovery = useModuleDiscovery()

  const results = useMemo(() => {
    return moduleIds.reduce((acc, moduleId) => {
      const appConfig = APPLICATION_REGISTRY.find(app => app.moduleId === moduleId)
      const isEnabled = moduleFlags.moduleFlags[moduleId] || false
      const capabilities = moduleFlags.moduleCapabilities[moduleId] || []
      const config = moduleFlags.moduleConfigs[moduleId] || {}
      
      const discoveryModule = discovery.enabledModules.find(m => m.module_id === moduleId) ||
                            discovery.disabledModules.find(m => m.module_id === moduleId)

      acc[moduleId] = {
        isEnabled,
        capabilities,
        config,
        appConfig,
        discoveryModule,
        health: discoveryModule?.health || 'unavailable'
      }
      return acc
    }, {} as Record<string, {
      isEnabled: boolean
      capabilities: string[]
      config: Record<string, any>
      appConfig?: typeof APPLICATION_REGISTRY[0]
      discoveryModule?: any
      health: string
    }>)
  }, [moduleIds, moduleFlags, discovery])

  return {
    modules: results,
    isLoading: moduleFlags.isLoading || discovery.isLoading,
    error: moduleFlags.error || discovery.error,
    enabledCount: Object.values(results).filter(m => m.isEnabled).length,
    totalCount: moduleIds.length,
    refresh: () => {
      moduleFlags.refetch()
      discovery.refresh()
    }
  }
}

/**
 * Hook for application-aware feature flag checking
 * Integrates with ApplicationRegistry for complete feature control
 */
export function useApplicationFeatureFlags(applicationId: string) {
  const appConfig = APPLICATION_REGISTRY.find(app => app.id === applicationId)
  
  // Use standard feature flags hook for required flags
  const requiredFlags = useFeatureFlags(
    appConfig?.requiredFlags || [],
    { fallbackValues: {} }
  )
  
  // Use standard feature flags hook for optional flags
  const optionalFlags = useFeatureFlags(
    appConfig?.optionalFlags || [],
    { fallbackValues: {} }
  )

  // Use module-specific flags
  const moduleFlag = useModuleFeatureFlag(
    appConfig?.moduleId || applicationId
  )

  // Check if application is available
  const isApplicationEnabled = useMemo(() => {
    if (!appConfig) return false
    
    // All required flags must be enabled
    const requiredEnabled = appConfig.requiredFlags.every(
      flagKey => requiredFlags.flags[flagKey]
    )
    
    // Module must be enabled
    const moduleEnabled = moduleFlag.isModuleEnabled
    
    return requiredEnabled && moduleEnabled
  }, [appConfig, requiredFlags.flags, moduleFlag.isModuleEnabled])

  // Get enhanced configuration
  const enhancedConfig = useMemo(() => {
    const config: Record<string, any> = {}
    
    // Merge required flag configs
    appConfig?.requiredFlags.forEach(flagKey => {
      config[flagKey] = requiredFlags.configs[flagKey] || {}
    })
    
    // Merge optional flag configs
    appConfig?.optionalFlags.forEach(flagKey => {
      config[flagKey] = optionalFlags.configs[flagKey] || {}
    })
    
    // Merge module config
    Object.assign(config, moduleFlag.moduleConfig)
    
    return config
  }, [appConfig, requiredFlags.configs, optionalFlags.configs, moduleFlag.moduleConfig])

  return {
    // Application state
    isApplicationEnabled,
    appConfig,
    
    // Flag states
    requiredFlags: requiredFlags.flags,
    optionalFlags: optionalFlags.flags,
    
    // Module state
    isModuleEnabled: moduleFlag.isModuleEnabled,
    moduleCapabilities: moduleFlag.availableCapabilities,
    moduleHealth: moduleFlag.health,
    
    // Enhanced configuration
    config: enhancedConfig,
    
    // Loading states
    isLoading: requiredFlags.isLoading || optionalFlags.isLoading || moduleFlag.isLoading,
    error: requiredFlags.error || optionalFlags.error || moduleFlag.error,
    
    // Utility functions
    hasFeature: (featureName: string) => {
      return [...(appConfig?.requiredFlags || []), ...(appConfig?.optionalFlags || [])]
        .some(flagKey => flagKey.includes(featureName) && 
              (requiredFlags.flags[flagKey] || optionalFlags.flags[flagKey]))
    },
    
    hasCapability: (capability: string) => {
      return moduleFlag.availableCapabilities.includes(capability)
    },
    
    // Refresh function
    refresh: () => {
      requiredFlags.refetch()
      optionalFlags.refetch()
      moduleFlag.refresh()
    }
  }
}

/**
 * Hook for checking if user has access to specific application features
 * based on both feature flags and module capabilities
 */
export function useApplicationAccess(applicationId: string) {
  const appFlags = useApplicationFeatureFlags(applicationId)
  
  return {
    // Access control
    canAccessApplication: appFlags.isApplicationEnabled,
    canAccessFeature: (featureName: string) => appFlags.hasFeature(featureName),
    canUseCapability: (capability: string) => appFlags.hasCapability(capability),
    
    // Application info
    applicationConfig: appFlags.appConfig,
    moduleCapabilities: appFlags.moduleCapabilities,
    
    // State
    isLoading: appFlags.isLoading,
    error: appFlags.error,
    
    // Debug info
    debugInfo: {
      requiredFlags: appFlags.requiredFlags,
      optionalFlags: appFlags.optionalFlags,
      moduleEnabled: appFlags.isModuleEnabled,
      moduleHealth: appFlags.moduleHealth,
      config: appFlags.config
    },
    
    refresh: appFlags.refresh
  }
}

/**
 * Higher-order hook for feature flag-aware routing
 */
export function useFeatureFlaggedRoute(
  routePath: string,
  requiredFlags: string[] = [],
  fallbackPath: string = '/dashboard'
) {
  const flags = useFeatureFlags(requiredFlags)
  
  const canAccessRoute = useMemo(() => {
    return requiredFlags.every(flagKey => flags.flags[flagKey])
  }, [requiredFlags, flags.flags])

  return {
    canAccess: canAccessRoute,
    shouldRedirect: !canAccessRoute && !flags.isLoading,
    redirectTo: fallbackPath,
    isLoading: flags.isLoading,
    error: flags.error,
    missingFlags: requiredFlags.filter(flagKey => !flags.flags[flagKey])
  }
}