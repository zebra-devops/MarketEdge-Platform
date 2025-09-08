'use client'

import React, { createContext, useContext, useMemo, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { 
  useAllFeatureFlags, 
  useFeatureFlagCache,
  featureFlagKeys 
} from '@/hooks/useFeatureFlags'
import { useFeatureFlagUpdates } from '@/hooks/useFeatureFlagUpdates'
import { FeatureFlagContextType } from '@/types/feature-flags'

interface FeatureFlagProviderProps {
  children: React.ReactNode
  preloadFlags?: string[]
  enableRealTimeUpdates?: boolean
  debugMode?: boolean
}

const FeatureFlagContext = createContext<FeatureFlagContextType | undefined>(undefined)

/**
 * Feature Flag Provider Component
 * 
 * Provides a centralized context for feature flag management with:
 * - Automatic loading of all enabled features
 * - Cache management and optimization
 * - Real-time updates (when available)
 * - Debug utilities
 */
export const FeatureFlagProvider: React.FC<FeatureFlagProviderProps> = ({
  children,
  preloadFlags = [],
  enableRealTimeUpdates = true,
  debugMode = process.env.NODE_ENV === 'development'
}) => {
  const { isAuthenticated, user } = useAuth()
  const { allFlags, isLoading: allFlagsLoading } = useAllFeatureFlags()
  const cache = useFeatureFlagCache()
  const updates = useFeatureFlagUpdates()

  // Preload specified flags on mount
  useEffect(() => {
    if (isAuthenticated && preloadFlags.length > 0) {
      cache.preloadFlags(preloadFlags)
      
      if (debugMode) {
        console.log('[FeatureFlags] Preloading flags:', preloadFlags)
      }
    }
  }, [isAuthenticated, preloadFlags, cache, debugMode])

  // Subscribe to real-time updates for all flags
  useEffect(() => {
    if (!enableRealTimeUpdates || !isAuthenticated) return

    const flagKeys = Object.keys(allFlags)
    if (flagKeys.length === 0) return

    const unsubscribe = updates.subscribe(flagKeys)
    
    if (debugMode) {
      console.log('[FeatureFlags] Subscribed to real-time updates for:', flagKeys)
    }

    return unsubscribe
  }, [enableRealTimeUpdates, isAuthenticated, allFlags, updates, debugMode])

  // Context value implementation
  const contextValue = useMemo<FeatureFlagContextType>(() => {
    const isFeatureEnabled = (flagKey: string): boolean => {
      // First check all flags cache
      if (allFlags[flagKey]) {
        return allFlags[flagKey].enabled
      }
      
      // Fallback to individual flag cache
      const cachedFlag = cache.getCachedFlag(flagKey)
      if (cachedFlag) {
        return cachedFlag.enabled
      }
      
      // Default to false if not found
      return false
    }

    const getFeatureConfig = (flagKey: string): Record<string, any> | null => {
      // First check all flags cache
      if (allFlags[flagKey]) {
        return allFlags[flagKey].config
      }
      
      // Fallback to individual flag cache
      const cachedFlag = cache.getCachedFlag(flagKey)
      if (cachedFlag) {
        return cachedFlag.config || null
      }
      
      return null
    }

    const areAnyFeaturesEnabled = (flagKeys: string[]): boolean => {
      return flagKeys.some(flagKey => isFeatureEnabled(flagKey))
    }

    const areAllFeaturesEnabled = (flagKeys: string[]): boolean => {
      return flagKeys.every(flagKey => isFeatureEnabled(flagKey))
    }

    const getEnabledFeatures = (): string[] => {
      const enabledFromAllFlags = Object.entries(allFlags)
        .filter(([_, flagData]) => flagData.enabled)
        .map(([flagKey]) => flagKey)
      
      return enabledFromAllFlags
    }

    const invalidateFlag = (flagKey: string) => {
      cache.invalidateFlag(flagKey)
      
      if (debugMode) {
        console.log('[FeatureFlags] Invalidated flag cache:', flagKey)
      }
    }

    const invalidateAllFlags = () => {
      cache.invalidateAllFlags()
      
      if (debugMode) {
        console.log('[FeatureFlags] Invalidated all flag caches')
      }
    }

    const preloadFlags = (flagKeys: string[]) => {
      cache.preloadFlags(flagKeys)
      
      if (debugMode) {
        console.log('[FeatureFlags] Preloading flags:', flagKeys)
      }
    }

    return {
      isFeatureEnabled,
      getFeatureConfig,
      areAnyFeaturesEnabled,
      areAllFeaturesEnabled,
      getEnabledFeatures,
      invalidateFlag,
      invalidateAllFlags,
      preloadFlags,
      isInitialized: isAuthenticated,
      isLoading: allFlagsLoading,
      lastUpdated: undefined // TODO: Add last updated tracking
    }
  }, [allFlags, cache, debugMode, isAuthenticated, allFlagsLoading])

  // Debug logging
  useEffect(() => {
    if (debugMode && isAuthenticated) {
      console.group('[FeatureFlags] Provider State')
      console.log('Authenticated:', isAuthenticated)
      console.log('User ID:', user?.id)
      console.log('Loading:', allFlagsLoading)
      console.log('All Flags:', allFlags)
      console.log('Enabled Features:', contextValue.getEnabledFeatures())
      console.log('Real-time Updates Connected:', updates.isConnected)
      if (updates.connectionError) {
        console.warn('Real-time Update Error:', updates.connectionError)
      }
      console.groupEnd()
    }
  }, [debugMode, isAuthenticated, user?.id, allFlagsLoading, allFlags, contextValue, updates])

  return (
    <FeatureFlagContext.Provider value={contextValue}>
      {children}
    </FeatureFlagContext.Provider>
  )
}

/**
 * Hook to access feature flag context
 */
export const useFeatureFlagContext = (): FeatureFlagContextType => {
  const context = useContext(FeatureFlagContext)
  
  if (!context) {
    throw new Error('useFeatureFlagContext must be used within a FeatureFlagProvider')
  }
  
  return context
}

/**
 * HOC for components that need feature flag context
 */
export function withFeatureFlags<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  flagKeys?: string[]
) {
  const WithFeatureFlagsComponent = (props: P) => {
    const featureFlags = useFeatureFlagContext()
    
    // Preload specified flags
    useEffect(() => {
      if (flagKeys && flagKeys.length > 0) {
        featureFlags.preloadFlags(flagKeys)
      }
    }, [flagKeys, featureFlags])

    return <WrappedComponent {...props} />
  }

  WithFeatureFlagsComponent.displayName = `withFeatureFlags(${
    WrappedComponent.displayName || WrappedComponent.name
  })`

  return WithFeatureFlagsComponent
}

/**
 * Component for conditionally rendering based on feature flags
 */
interface ConditionalFeatureProps {
  flag: string
  fallback?: React.ReactNode
  children: React.ReactNode
  requireAll?: string[] // All of these flags must be enabled
  requireAny?: string[] // At least one of these flags must be enabled
}

export const ConditionalFeature: React.FC<ConditionalFeatureProps> = ({
  flag,
  fallback = null,
  children,
  requireAll = [],
  requireAny = []
}) => {
  const featureFlags = useFeatureFlagContext()
  
  // Check main flag
  let shouldRender = featureFlags.isFeatureEnabled(flag)
  
  // Check requireAll flags
  if (shouldRender && requireAll.length > 0) {
    shouldRender = featureFlags.areAllFeaturesEnabled(requireAll)
  }
  
  // Check requireAny flags
  if (shouldRender && requireAny.length > 0) {
    shouldRender = featureFlags.areAnyFeaturesEnabled(requireAny)
  }
  
  if (!shouldRender) {
    return <>{fallback}</>
  }
  
  return <>{children}</>
}

/**
 * Hook for debugging feature flags
 */
export const useFeatureFlagDebug = () => {
  const featureFlags = useFeatureFlagContext()
  const { allFlags } = useAllFeatureFlags()
  
  const debugInfo = useMemo(() => {
    const enabledFlags = featureFlags.getEnabledFeatures()
    const flagDetails = Object.entries(allFlags).map(([flagKey, flagData]) => ({
      flagKey,
      enabled: flagData.enabled,
      name: flagData.name,
      config: flagData.config,
      module_id: flagData.module_id
    }))
    
    return {
      enabledFlags,
      flagDetails,
      totalFlags: Object.keys(allFlags).length,
      enabledCount: enabledFlags.length
    }
  }, [featureFlags, allFlags])
  
  const logDebugInfo = () => {
    console.group('[FeatureFlags] Debug Info')
    console.table(debugInfo.flagDetails)
    console.log('Enabled Flags:', debugInfo.enabledFlags)
    console.log('Total Flags:', debugInfo.totalFlags)
    console.log('Enabled Count:', debugInfo.enabledCount)
    console.groupEnd()
  }
  
  return {
    debugInfo,
    logDebugInfo
  }
}