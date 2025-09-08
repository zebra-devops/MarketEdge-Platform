'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useQueryClient } from 'react-query'
import { useAuth } from './useAuth'
import { featureFlagKeys } from './useFeatureFlags'
import {
  UseFeatureFlagUpdatesResult,
  FeatureFlagUpdateEvent
} from '@/types/feature-flags'

interface SubscriptionManager {
  flagKeys: Set<string>
  listeners: Set<(event: FeatureFlagUpdateEvent) => void>
}

/**
 * Hook for subscribing to real-time feature flag updates
 * 
 * This hook provides a way to listen for feature flag changes and automatically
 * invalidate React Query cache entries when flags are updated.
 * 
 * Note: Since WebSocket/SSE infrastructure isn't implemented in the current backend,
 * this hook provides the interface and can be easily connected to real-time updates
 * when the infrastructure is available. For now, it provides polling-based updates
 * as a fallback.
 */
export function useFeatureFlagUpdates(): UseFeatureFlagUpdatesResult {
  const { user, isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  
  const [isConnected, setIsConnected] = useState(false)
  const [lastEvent, setLastEvent] = useState<FeatureFlagUpdateEvent | undefined>()
  const [connectionError, setConnectionError] = useState<Error | undefined>()
  
  const subscriptionsRef = useRef<SubscriptionManager>({
    flagKeys: new Set(),
    listeners: new Set()
  })
  
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const lastPollRef = useRef<Record<string, number>>({})

  // Initialize connection (or polling fallback)
  useEffect(() => {
    if (!isAuthenticated || !user) {
      setIsConnected(false)
      return
    }

    // TODO: When WebSocket/SSE is available, replace this with real connection
    // For now, we'll simulate connection state
    setIsConnected(true)
    setConnectionError(undefined)

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
      setIsConnected(false)
    }
  }, [isAuthenticated, user])

  // Polling fallback for checking flag updates
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
    }

    if (subscriptionsRef.current.flagKeys.size === 0) {
      return
    }

    pollIntervalRef.current = setInterval(async () => {
      const flagKeys = Array.from(subscriptionsRef.current.flagKeys)
      
      // Check if any cached flags are stale and need refreshing
      for (const flagKey of flagKeys) {
        const queryKey = featureFlagKeys.single(flagKey)
        const queryState = queryClient.getQueryState(queryKey)
        
        if (queryState && queryState.dataUpdatedAt) {
          const timeSinceUpdate = Date.now() - queryState.dataUpdatedAt
          const staleTime = 2 * 60 * 1000 // 2 minutes
          
          if (timeSinceUpdate > staleTime) {
            // Invalidate stale flags to trigger refetch
            queryClient.invalidateQueries(queryKey)
            
            // Simulate update event
            const event: FeatureFlagUpdateEvent = {
              type: 'flag_updated',
              flagKey,
              timestamp: new Date().toISOString(),
              userId: user?.id,
              organisationId: user?.organisation_id
            }
            
            setLastEvent(event)
            
            // Notify listeners
            subscriptionsRef.current.listeners.forEach(listener => {
              try {
                listener(event)
              } catch (error) {
                console.warn('Error in feature flag update listener:', error)
              }
            })
          }
        }
      }
    }, 30000) // Poll every 30 seconds
  }, [queryClient, user])

  const subscribe = useCallback((flagKeys: string | string[]): (() => void) => {
    const keys = Array.isArray(flagKeys) ? flagKeys : [flagKeys]
    
    keys.forEach(key => {
      subscriptionsRef.current.flagKeys.add(key)
    })

    // Start polling if not already started
    startPolling()

    // Return unsubscribe function
    return () => {
      keys.forEach(key => {
        subscriptionsRef.current.flagKeys.delete(key)
      })
      
      // If no more subscriptions, stop polling
      if (subscriptionsRef.current.flagKeys.size === 0 && pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
    }
  }, [startPolling])

  const unsubscribe = useCallback((flagKeys: string | string[]) => {
    const keys = Array.isArray(flagKeys) ? flagKeys : [flagKeys]
    
    keys.forEach(key => {
      subscriptionsRef.current.flagKeys.delete(key)
    })

    // If no more subscriptions, stop polling
    if (subscriptionsRef.current.flagKeys.size === 0 && pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }, [])

  // Add event listener for custom events
  const addEventListener = useCallback((listener: (event: FeatureFlagUpdateEvent) => void) => {
    subscriptionsRef.current.listeners.add(listener)
    
    return () => {
      subscriptionsRef.current.listeners.delete(listener)
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
      subscriptionsRef.current.flagKeys.clear()
      subscriptionsRef.current.listeners.clear()
    }
  }, [])

  return {
    subscribe,
    unsubscribe,
    isConnected,
    lastEvent,
    connectionError,
    addEventListener,
  }
}

/**
 * Hook for subscribing to specific flag updates with automatic cleanup
 * 
 * @param flagKeys - Flag keys to subscribe to
 * @param onUpdate - Callback when flags are updated
 */
export function useFeatureFlagSubscription(
  flagKeys: string | string[],
  onUpdate?: (event: FeatureFlagUpdateEvent) => void
) {
  const updates = useFeatureFlagUpdates()
  
  useEffect(() => {
    const unsubscribe = updates.subscribe(flagKeys)
    
    let removeEventListener: (() => void) | undefined
    
    if (onUpdate) {
      removeEventListener = updates.addEventListener((event) => {
        const keys = Array.isArray(flagKeys) ? flagKeys : [flagKeys]
        
        // Only call onUpdate if the event is for one of our subscribed flags
        if (event.flagKey && keys.includes(event.flagKey)) {
          onUpdate(event)
        } else if (event.type === 'bulk_update' && event.flags) {
          const hasMatchingFlag = event.flags.some(flag => keys.includes(flag))
          if (hasMatchingFlag) {
            onUpdate(event)
          }
        }
      })
    }
    
    return () => {
      unsubscribe()
      if (removeEventListener) {
        removeEventListener()
      }
    }
  }, [flagKeys, onUpdate, updates])

  return {
    isConnected: updates.isConnected,
    lastEvent: updates.lastEvent,
    connectionError: updates.connectionError,
  }
}

/**
 * Utility for manually triggering flag update events
 * This is useful for testing or when you know a flag has been updated externally
 */
export function useFeatureFlagEventEmitter() {
  const queryClient = useQueryClient()
  
  const emitFlagUpdate = useCallback((flagKey: string, data?: any) => {
    // Invalidate the specific flag cache
    queryClient.invalidateQueries(featureFlagKeys.single(flagKey))
    
    // Also invalidate any bulk queries that might include this flag
    queryClient.invalidateQueries(featureFlagKeys.enabled())
    
    // Create and dispatch custom event
    const event: FeatureFlagUpdateEvent = {
      type: 'flag_updated',
      flagKey,
      data,
      timestamp: new Date().toISOString(),
    }

    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('featureFlag:update', { detail: event }))
    }
  }, [queryClient])

  const emitBulkUpdate = useCallback((flagKeys: string[]) => {
    // Invalidate all affected queries
    flagKeys.forEach(flagKey => {
      queryClient.invalidateQueries(featureFlagKeys.single(flagKey))
    })
    queryClient.invalidateQueries(featureFlagKeys.enabled())
    
    const event: FeatureFlagUpdateEvent = {
      type: 'bulk_update',
      flags: flagKeys,
      timestamp: new Date().toISOString(),
    }

    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('featureFlag:bulkUpdate', { detail: event }))
    }
  }, [queryClient])

  return {
    emitFlagUpdate,
    emitBulkUpdate,
  }
}