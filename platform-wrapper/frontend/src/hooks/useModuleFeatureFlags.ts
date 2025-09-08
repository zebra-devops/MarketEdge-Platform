'use client'

import { useQuery, useQueryClient } from 'react-query'
import { useAuth } from './useAuth'
import { moduleFeatureFlagApiService } from '@/services/module-feature-flag-api'
import {
  UseModuleFeatureFlagsResult,
  UseModuleDiscoveryResult,
  UseModuleFlagHierarchyResult,
  ModuleFeatureFlagOptions,
  ModuleFeatureFlagError,
  ModuleDiscoveryResponse
} from '@/types/module-feature-flags'

// Query key factory for module feature flags
export const moduleFeatureFlagKeys = {
  all: ['moduleFeatureFlags'] as const,
  modules: () => ['moduleFeatureFlags', 'modules'] as const,
  module: (moduleId: string) => ['moduleFeatureFlags', 'module', moduleId] as const,
  discovery: (userId?: string) => ['moduleFeatureFlags', 'discovery', userId] as const,
  hierarchy: (moduleId: string) => ['moduleFeatureFlags', 'hierarchy', moduleId] as const,
  capabilities: (moduleId: string) => ['moduleFeatureFlags', 'capabilities', moduleId] as const,
  health: (moduleId: string) => ['moduleFeatureFlags', 'health', moduleId] as const,
  accessible: () => ['moduleFeatureFlags', 'accessible'] as const,
}

// Default options
const DEFAULT_OPTIONS: Required<ModuleFeatureFlagOptions> = {
  includeDisabled: false,
  moduleTypes: [],
  categories: [],
  requiredFlagsOnly: false,
  includeInherited: true,
  hierarchyDepth: 4,
  cacheTime: 5 * 60 * 1000, // 5 minutes
  staleTime: 2 * 60 * 1000, // 2 minutes
  refetchInterval: false,
  preloadCapabilities: true,
  batchSize: 10,
}

/**
 * Hook for getting all module feature flags and their states
 */
export function useModuleFeatureFlags(
  options: ModuleFeatureFlagOptions = {}
): UseModuleFeatureFlagsResult {
  const { user, isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options }
  
  const query = useQuery({
    queryKey: moduleFeatureFlagKeys.modules(),
    queryFn: () => moduleFeatureFlagApiService.getModulesWithFlags(),
    enabled: isAuthenticated,
    cacheTime: mergedOptions.cacheTime,
    staleTime: mergedOptions.staleTime,
    refetchInterval: mergedOptions.refetchInterval,
    onError: (error) => {
      console.error('🚨 EMERGENCY: Module feature flags check failed for Zebra Associates:', error)
      // Log additional debug info for emergency troubleshooting
      console.error('Error details:', {
        message: error?.message,
        status: error?.status,
        response: error?.response
      })
    },
  })

  const refetch = () => {
    queryClient.invalidateQueries(moduleFeatureFlagKeys.modules())
    return query.refetch()
  }

  // Process module flags data
  const moduleFlags: Record<string, boolean> = {}
  const moduleConfigs: Record<string, Record<string, any>> = {}
  const enabledModules: string[] = []
  const disabledModules: string[] = []
  const moduleCapabilities: Record<string, string[]> = {}

  if (query.data) {
    query.data.forEach(moduleData => {
      // EMERGENCY FIX: Handle both new format (from getModulesWithFlags) and legacy format
      let moduleId: string
      let hasRequiredFlags = true // Default to true for emergency modules
      let healthStatus = 'healthy'
      let availableCapabilities: string[] = []
      
      if (moduleData.module && moduleData.module.id) {
        // New expected format
        moduleId = moduleData.module.id
        hasRequiredFlags = moduleData.module.required_flags?.every(
          flagKey => moduleData.enabled_flags[flagKey]?.enabled
        ) ?? true
        healthStatus = moduleData.health_status || 'healthy'
        availableCapabilities = moduleData.available_capabilities || []
      } else if (moduleData.module_id) {
        // Fallback format from API service
        moduleId = moduleData.module_id
        healthStatus = moduleData.health_status || 'healthy'
        availableCapabilities = moduleData.available_capabilities || []
      } else {
        // Emergency fallback - treat as simple string or object
        console.warn('Unknown module data format, using emergency handling:', moduleData)
        moduleId = typeof moduleData === 'string' ? moduleData : 
                  moduleData.id || moduleData.module_id || 'unknown_module'
      }

      // Module is enabled if all required flags are enabled
      const moduleEnabled = hasRequiredFlags && healthStatus !== 'unavailable'

      moduleFlags[moduleId] = moduleEnabled
      
      if (moduleEnabled) {
        enabledModules.push(moduleId)
      } else {
        disabledModules.push(moduleId)
      }

      // Collect module configurations with safe access
      moduleConfigs[moduleId] = {}
      if (moduleData.enabled_flags && typeof moduleData.enabled_flags === 'object') {
        Object.entries(moduleData.enabled_flags).forEach(([flagKey, flagData]) => {
          if (flagData && typeof flagData === 'object') {
            moduleConfigs[moduleId][flagKey] = flagData.config || {}
          }
        })
      }

      // Collect capabilities
      moduleCapabilities[moduleId] = availableCapabilities
    })
  }

  return {
    moduleFlags,
    moduleConfigs,
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    enabledModules,
    disabledModules,
    moduleCapabilities,
    refetch,
    lastUpdated: query.dataUpdatedAt ? new Date(query.dataUpdatedAt) : undefined,
  }
}

/**
 * Hook for module discovery - getting available modules based on feature flags
 */
export function useModuleDiscovery(
  userId?: string,
  options: Omit<ModuleFeatureFlagOptions, 'hierarchyDepth'> = {}
): UseModuleDiscoveryResult {
  const { user, isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options }
  const effectiveUserId = userId || user?.id
  
  const query = useQuery({
    queryKey: moduleFeatureFlagKeys.discovery(effectiveUserId),
    queryFn: () => moduleFeatureFlagApiService.discoverEnabledModules(
      effectiveUserId,
      user?.organisation_id
    ),
    enabled: isAuthenticated,
    cacheTime: mergedOptions.cacheTime,
    staleTime: mergedOptions.staleTime,
    refetchInterval: mergedOptions.refetchInterval,
    onError: (error) => {
      console.error('🚨 CRITICAL: Module discovery failed for Zebra Associates:', error)
      // Enhanced error logging for emergency troubleshooting
      console.error('Discovery error details:', {
        message: error?.message,
        status: error?.response?.status,
        url: error?.config?.url,
        data: error?.response?.data
      })
    },
  })

  const refresh = () => {
    queryClient.invalidateQueries(moduleFeatureFlagKeys.discovery(effectiveUserId))
    return query.refetch()
  }

  return {
    enabledModules: query.data?.available_modules?.filter(m => m.enabled) || query.data?.enabled_modules || [],
    disabledModules: query.data?.available_modules?.filter(m => !m.enabled) || query.data?.disabled_modules || [],
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    totalAvailable: query.data?.total_modules || query.data?.total_available || 0,
    userAccessible: query.data?.enabled_modules || query.data?.user_accessible || 0,
    refresh,
    lastUpdated: query.dataUpdatedAt ? new Date(query.dataUpdatedAt) : undefined,
  }
}

/**
 * Hook for getting module flag hierarchy and inheritance
 */
export function useModuleFlagHierarchy(
  moduleId: string,
  options: Pick<ModuleFeatureFlagOptions, 'hierarchyDepth' | 'includeInherited' | 'cacheTime' | 'staleTime'> = {}
): UseModuleFlagHierarchyResult {
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options }
  
  const query = useQuery({
    queryKey: moduleFeatureFlagKeys.hierarchy(moduleId),
    queryFn: () => moduleFeatureFlagApiService.getModuleFlagHierarchy(moduleId),
    enabled: isAuthenticated && !!moduleId,
    cacheTime: mergedOptions.cacheTime,
    staleTime: mergedOptions.staleTime,
    onError: (error) => {
      console.warn(`Module flag hierarchy check failed for '${moduleId}':`, error)
    },
  })

  const refetch = () => {
    queryClient.invalidateQueries(moduleFeatureFlagKeys.hierarchy(moduleId))
    return query.refetch()
  }

  // Extract effective flags and configs
  const effectiveFlags: Record<string, boolean> = {}
  const flagConfigs: Record<string, Record<string, any>> = {}

  if (query.data?.effective_flags) {
    Object.entries(query.data.effective_flags).forEach(([flagKey, flagData]) => {
      effectiveFlags[flagKey] = flagData.enabled
      flagConfigs[flagKey] = flagData.config || {}
    })
  }

  const getInheritanceChain = (flagKey: string) => {
    if (!query.data?.inheritance_chain) return []
    return query.data.inheritance_chain.filter(chain => chain.flag_key === flagKey)
  }

  return {
    hierarchy: query.data || null,
    effectiveFlags,
    flagConfigs,
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    getInheritanceChain,
    refetch,
  }
}

/**
 * Hook for checking specific module capabilities
 */
export function useModuleCapabilities(
  moduleId: string,
  capabilities: string[],
  options: Pick<ModuleFeatureFlagOptions, 'cacheTime' | 'staleTime'> = {}
) {
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options }
  
  const query = useQuery({
    queryKey: moduleFeatureFlagKeys.capabilities(moduleId),
    queryFn: () => moduleFeatureFlagApiService.checkModuleCapabilities(moduleId, capabilities),
    enabled: isAuthenticated && !!moduleId && capabilities.length > 0,
    cacheTime: mergedOptions.cacheTime,
    staleTime: mergedOptions.staleTime,
    onError: (error) => {
      console.warn(`Module capabilities check failed for '${moduleId}':`, error)
    },
  })

  const refetch = () => {
    queryClient.invalidateQueries(moduleFeatureFlagKeys.capabilities(moduleId))
    return query.refetch()
  }

  const hasCapability = (capability: string): boolean => {
    return query.data?.[capability] || false
  }

  const getEnabledCapabilities = (): string[] => {
    if (!query.data) return []
    return Object.entries(query.data)
      .filter(([, enabled]) => enabled)
      .map(([capability]) => capability)
  }

  const getDisabledCapabilities = (): string[] => {
    if (!query.data) return []
    return Object.entries(query.data)
      .filter(([, enabled]) => !enabled)
      .map(([capability]) => capability)
  }

  return {
    capabilities: query.data || {},
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    hasCapability,
    getEnabledCapabilities,
    getDisabledCapabilities,
    refetch,
    lastUpdated: query.dataUpdatedAt ? new Date(query.dataUpdatedAt) : undefined,
  }
}

/**
 * Hook for getting user's accessible modules (simplified module discovery)
 */
export function useAccessibleModules(
  options: Pick<ModuleFeatureFlagOptions, 'cacheTime' | 'staleTime' | 'refetchInterval'> = {}
) {
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options }
  
  const query = useQuery({
    queryKey: moduleFeatureFlagKeys.accessible(),
    queryFn: () => moduleFeatureFlagApiService.getUserAccessibleModules(),
    enabled: isAuthenticated,
    cacheTime: mergedOptions.cacheTime,
    staleTime: mergedOptions.staleTime,
    refetchInterval: mergedOptions.refetchInterval,
    onError: (error) => {
      console.warn('Accessible modules check failed:', error)
    },
  })

  const refresh = () => {
    queryClient.invalidateQueries(moduleFeatureFlagKeys.accessible())
    return query.refetch()
  }

  return {
    accessibleModules: query.data?.enabled_modules || [],
    restrictedModules: query.data?.disabled_modules || [],
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    refresh,
    lastUpdated: query.dataUpdatedAt ? new Date(query.dataUpdatedAt) : undefined,
  }
}

/**
 * Hook for module health monitoring including flag dependencies
 */
export function useModuleHealth(
  moduleId: string,
  options: Pick<ModuleFeatureFlagOptions, 'cacheTime' | 'staleTime' | 'refetchInterval'> = {}
) {
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options }
  
  const query = useQuery({
    queryKey: moduleFeatureFlagKeys.health(moduleId),
    queryFn: () => moduleFeatureFlagApiService.getModuleHealth(moduleId),
    enabled: isAuthenticated && !!moduleId,
    cacheTime: mergedOptions.cacheTime,
    staleTime: mergedOptions.staleTime,
    refetchInterval: mergedOptions.refetchInterval || 60000, // Default 1min for health checks
    onError: (error) => {
      console.warn(`Module health check failed for '${moduleId}':`, error)
    },
  })

  const refresh = () => {
    queryClient.invalidateQueries(moduleFeatureFlagKeys.health(moduleId))
    return query.refetch()
  }

  const isHealthy = (): boolean => {
    return query.data?.status === 'healthy'
  }

  const isDegraded = (): boolean => {
    return query.data?.status === 'degraded'
  }

  const isUnavailable = (): boolean => {
    return query.data?.status === 'unavailable'
  }

  return {
    health: query.data || null,
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    isHealthy,
    isDegraded,
    isUnavailable,
    refresh,
    lastUpdated: query.dataUpdatedAt ? new Date(query.dataUpdatedAt) : undefined,
  }
}

/**
 * Utility hook for module feature flag cache management
 */
export function useModuleFeatureFlagCache() {
  const queryClient = useQueryClient()
  
  const invalidateModule = (moduleId: string) => {
    queryClient.invalidateQueries(moduleFeatureFlagKeys.module(moduleId))
    queryClient.invalidateQueries(moduleFeatureFlagKeys.hierarchy(moduleId))
    queryClient.invalidateQueries(moduleFeatureFlagKeys.capabilities(moduleId))
    queryClient.invalidateQueries(moduleFeatureFlagKeys.health(moduleId))
  }

  const invalidateAllModules = () => {
    queryClient.invalidateQueries(moduleFeatureFlagKeys.all)
  }

  const invalidateDiscovery = () => {
    queryClient.invalidateQueries(moduleFeatureFlagKeys.discovery())
    queryClient.invalidateQueries(moduleFeatureFlagKeys.accessible())
  }

  const preloadModule = async (moduleId: string, capabilities: string[] = []) => {
    try {
      const promises = [
        queryClient.prefetchQuery({
          queryKey: moduleFeatureFlagKeys.hierarchy(moduleId),
          queryFn: () => moduleFeatureFlagApiService.getModuleFlagHierarchy(moduleId),
          staleTime: DEFAULT_OPTIONS.staleTime,
        }),
        queryClient.prefetchQuery({
          queryKey: moduleFeatureFlagKeys.health(moduleId),
          queryFn: () => moduleFeatureFlagApiService.getModuleHealth(moduleId),
          staleTime: DEFAULT_OPTIONS.staleTime,
        })
      ]

      if (capabilities.length > 0) {
        promises.push(
          queryClient.prefetchQuery({
            queryKey: moduleFeatureFlagKeys.capabilities(moduleId),
            queryFn: () => moduleFeatureFlagApiService.checkModuleCapabilities(moduleId, capabilities),
            staleTime: DEFAULT_OPTIONS.staleTime,
          })
        )
      }

      await Promise.allSettled(promises)
    } catch (error) {
      console.warn(`Failed to preload module '${moduleId}':`, error)
    }
  }

  return {
    invalidateModule,
    invalidateAllModules,
    invalidateDiscovery,
    preloadModule,
  }
}

/**
 * Convenience hook that combines multiple module feature flag hooks
 */
export function useModuleDashboard(moduleId: string, capabilities: string[] = []) {
  const moduleFlags = useModuleFeatureFlags()
  const hierarchy = useModuleFlagHierarchy(moduleId)
  const moduleCapabilities = useModuleCapabilities(moduleId, capabilities)
  const health = useModuleHealth(moduleId)

  const isModuleEnabled = moduleFlags.moduleFlags[moduleId] || false
  const moduleConfig = moduleFlags.moduleConfigs[moduleId] || {}

  return {
    // Module state
    isModuleEnabled,
    moduleConfig,
    
    // Detailed data
    flags: moduleFlags,
    hierarchy,
    capabilities: moduleCapabilities,
    health,
    
    // Convenience methods
    hasCapability: moduleCapabilities.hasCapability,
    isHealthy: health.isHealthy,
    
    // Loading states
    isLoading: moduleFlags.isLoading || hierarchy.isLoading || 
               moduleCapabilities.isLoading || health.isLoading,
               
    // Error states
    hasError: !!(moduleFlags.error || hierarchy.error || 
                moduleCapabilities.error || health.error),
                
    // Refresh methods
    refresh: () => {
      moduleFlags.refetch()
      hierarchy.refetch()
      moduleCapabilities.refetch()
      health.refresh()
    }
  }
}