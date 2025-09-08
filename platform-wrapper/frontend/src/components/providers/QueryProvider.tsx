'use client'

import React from 'react'
import { QueryClient, QueryClientProvider, QueryCache } from 'react-query'
import { FeatureFlagUtils } from '@/utils/feature-flags'

// Create query cache with event handlers
const queryCache = new QueryCache({
  onSuccess: (data, query) => {
    // Save feature flag data to local cache for offline fallback
    if (query.queryKey[0] === 'featureFlags') {
      try {
        if (query.queryKey[1] === 'enabled') {
          // Save all enabled features to cache
          const enabledFeatures = (data as any)?.enabled_features
          if (enabledFeatures) {
            const flagsForCache = Object.entries(enabledFeatures).reduce((acc, [key, value]: [string, any]) => {
              acc[key] = {
                enabled: true,
                config: value.config || {}
              }
              return acc
            }, {} as Record<string, { enabled: boolean; config: Record<string, any> }>)
            
            FeatureFlagUtils.saveToCache(flagsForCache)
          }
        } else if (query.queryKey[1] === 'single') {
          // Save individual flag to cache
          const flagKey = query.queryKey[2] as string
          const flagData = data as any
          if (flagKey && flagData) {
            const cacheData = { [flagKey]: { enabled: flagData.enabled, config: flagData.config || {} } }
            FeatureFlagUtils.saveToCache(cacheData)
          }
        }
      } catch (error) {
        console.warn('Failed to update feature flag cache:', error)
      }
    }
  },
  onError: (error, query) => {
    // Log feature flag errors for monitoring
    if (query.queryKey[0] === 'featureFlags') {
      console.warn('Feature flag query error:', {
        queryKey: query.queryKey,
        error: error instanceof Error ? error.message : error
      })
    }
  }
})

const queryClient = new QueryClient({
  queryCache,
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      // Feature flag specific defaults
      staleTime: 2 * 60 * 1000, // 2 minutes
      cacheTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      retry: 1,
    },
  },
})

export const QueryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}