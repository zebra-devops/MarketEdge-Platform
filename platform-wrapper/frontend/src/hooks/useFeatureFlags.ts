'use client'

import { useQuery, useQueryClient } from 'react-query'
import { useAuth } from './useAuth'
import { featureFlagApiService } from '@/services/feature-flag-api'
import {
  UseFeatureFlagResult,
  UseFeatureFlagsResult,
  UseAllFeatureFlagsResult,
  FeatureFlagOptions,
  FeatureFlagsOptions,
  FeatureFlagError
} from '@/types/feature-flags'

// Query key factory for consistent cache management
export const featureFlagKeys = {
  all: ['featureFlags'] as const,
  single: (flagKey: string) => ['featureFlags', 'single', flagKey] as const,
  multiple: (flagKeys: string[]) => ['featureFlags', 'multiple', flagKeys.sort().join(',')] as const,
  enabled: (moduleId?: string) => ['featureFlags', 'enabled', moduleId] as const,
  user: (userId: string) => ['featureFlags', 'user', userId] as const,
}

// Default options
const DEFAULT_OPTIONS: Required<FeatureFlagOptions> = {
  fallbackValue: false,
  cacheTime: 5 * 60 * 1000, // 5 minutes
  staleTime: 2 * 60 * 1000, // 2 minutes
  refetchInterval: false,
  refetchOnWindowFocus: true,
  retryCount: 2,
  enabled: true,
}

/**
 * Hook for checking a single feature flag
 * 
 * @param flagKey - The feature flag key to check
 * @param options - Configuration options
 * @returns UseFeatureFlagResult with flag state and utilities
 */
export function useFeatureFlag(
  flagKey: string,
  options: FeatureFlagOptions = {}
): UseFeatureFlagResult {
  const { user, isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options }
  
  const query = useQuery({
    queryKey: featureFlagKeys.single(flagKey),
    queryFn: () => featureFlagApiService.checkFeatureFlag(flagKey),
    enabled: isAuthenticated && mergedOptions.enabled && !!flagKey,
    cacheTime: mergedOptions.cacheTime,
    staleTime: mergedOptions.staleTime,
    refetchInterval: mergedOptions.refetchInterval,
    refetchOnWindowFocus: mergedOptions.refetchOnWindowFocus,
    retry: mergedOptions.retryCount,
    onError: (error) => {
      console.warn(`Feature flag check failed for '${flagKey}':`, error)
    },
  })

  const refetch = () => {
    queryClient.invalidateQueries(featureFlagKeys.single(flagKey))
    return query.refetch()
  }

  // Determine flag state with fallback
  let isEnabled = mergedOptions.fallbackValue
  let config: Record<string, any> | null = null
  let error: Error | null = null

  if (query.data) {
    isEnabled = query.data.enabled
    config = query.data.config || null
  } else if (query.error) {
    error = query.error instanceof Error ? query.error : new Error('Unknown error')
    // Use fallback for errors unless it's a definitive "disabled" response
    if (query.error instanceof FeatureFlagError && query.error.statusCode === 404) {
      isEnabled = false // Flag doesn't exist, so it's definitely disabled
    }
  }

  return {
    isEnabled,
    isLoading: query.isLoading,
    error,
    config,
    refetch,
    lastUpdated: query.dataUpdatedAt ? new Date(query.dataUpdatedAt) : undefined,
  }
}

/**
 * Hook for checking multiple feature flags
 * 
 * @param flagKeys - Array of feature flag keys to check
 * @param options - Configuration options
 * @returns UseFeatureFlagsResult with flags state and utilities
 */
export function useFeatureFlags(
  flagKeys: string[],
  options: FeatureFlagsOptions = {}
): UseFeatureFlagsResult {
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  
  const mergedOptions = {
    ...DEFAULT_OPTIONS,
    ...options,
    fallbackValues: options.fallbackValues || {},
  }

  // Sort flag keys for consistent cache keys
  const sortedFlagKeys = [...flagKeys].sort()
  
  const query = useQuery({
    queryKey: featureFlagKeys.multiple(sortedFlagKeys),
    queryFn: () => featureFlagApiService.checkMultipleFlags(sortedFlagKeys),
    enabled: isAuthenticated && mergedOptions.enabled && flagKeys.length > 0,
    cacheTime: mergedOptions.cacheTime,
    staleTime: mergedOptions.staleTime,
    refetchInterval: mergedOptions.refetchInterval,
    refetchOnWindowFocus: mergedOptions.refetchOnWindowFocus,
    retry: mergedOptions.retryCount,
    onError: (error) => {
      console.warn(`Feature flags check failed for keys [${flagKeys.join(', ')}]:`, error)
    },
  })

  const refetch = () => {
    queryClient.invalidateQueries(featureFlagKeys.multiple(sortedFlagKeys))
    return query.refetch()
  }

  // Build result objects
  const flags: Record<string, boolean> = {}
  const configs: Record<string, Record<string, any>> = {}

  flagKeys.forEach(flagKey => {
    if (query.data && query.data[flagKey]) {
      flags[flagKey] = query.data[flagKey].enabled
      configs[flagKey] = query.data[flagKey].config || {}
    } else {
      // Use fallback value
      flags[flagKey] = mergedOptions.fallbackValues[flagKey] ?? mergedOptions.fallbackValue
      configs[flagKey] = {}
    }
  })

  return {
    flags,
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    configs,
    refetch,
    lastUpdated: query.dataUpdatedAt ? new Date(query.dataUpdatedAt) : undefined,
  }
}

/**
 * Hook for getting all enabled features for the current user
 * 
 * @param moduleId - Optional module ID to filter features
 * @param options - Configuration options
 * @returns UseAllFeatureFlagsResult with all enabled flags
 */
export function useAllFeatureFlags(
  moduleId?: string,
  options: Omit<FeatureFlagOptions, 'fallbackValue'> = {}
): UseAllFeatureFlagsResult {
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options }
  
  const query = useQuery({
    queryKey: featureFlagKeys.enabled(moduleId),
    queryFn: () => featureFlagApiService.getEnabledFeatures(moduleId),
    enabled: isAuthenticated && mergedOptions.enabled,
    cacheTime: mergedOptions.cacheTime,
    staleTime: mergedOptions.staleTime,
    refetchInterval: mergedOptions.refetchInterval,
    refetchOnWindowFocus: mergedOptions.refetchOnWindowFocus,
    retry: mergedOptions.retryCount,
    onError: (error) => {
      console.warn('All feature flags check failed:', error)
    },
  })

  const refetch = () => {
    queryClient.invalidateQueries(featureFlagKeys.enabled(moduleId))
    return query.refetch()
  }

  // Transform API response to expected format
  const allFlags: Record<string, {
    enabled: boolean
    name: string
    config: Record<string, any>
    module_id?: string
  }> = {}

  if (query.data?.enabled_features) {
    Object.entries(query.data.enabled_features).forEach(([flagKey, flagData]) => {
      allFlags[flagKey] = {
        enabled: true, // All flags from this endpoint are enabled
        name: flagData.name,
        config: flagData.config,
        module_id: flagData.module_id,
      }
    })
  }

  return {
    allFlags,
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    refetch,
    lastUpdated: query.dataUpdatedAt ? new Date(query.dataUpdatedAt) : undefined,
  }
}

/**
 * Utility hook for cache management and optimization
 */
export function useFeatureFlagCache() {
  const queryClient = useQueryClient()
  
  const invalidateFlag = (flagKey: string) => {
    queryClient.invalidateQueries(featureFlagKeys.single(flagKey))
  }

  const invalidateMultipleFlags = (flagKeys: string[]) => {
    queryClient.invalidateQueries(featureFlagKeys.multiple(flagKeys))
  }

  const invalidateAllFlags = () => {
    queryClient.invalidateQueries(featureFlagKeys.all)
  }

  const preloadFlags = async (flagKeys: string[]) => {
    // Fire parallel prefetch requests
    const promises = flagKeys.map(flagKey => 
      queryClient.prefetchQuery({
        queryKey: featureFlagKeys.single(flagKey),
        queryFn: () => featureFlagApiService.checkFeatureFlag(flagKey),
        staleTime: DEFAULT_OPTIONS.staleTime,
      })
    )

    try {
      await Promise.allSettled(promises)
    } catch (error) {
      console.warn('Some flags failed to preload:', error)
    }
  }

  const getCachedFlag = (flagKey: string) => {
    return queryClient.getQueryData(featureFlagKeys.single(flagKey))
  }

  const setCachedFlag = (flagKey: string, data: any) => {
    queryClient.setQueryData(featureFlagKeys.single(flagKey), data)
  }

  return {
    invalidateFlag,
    invalidateMultipleFlags,
    invalidateAllFlags,
    preloadFlags,
    getCachedFlag,
    setCachedFlag,
  }
}