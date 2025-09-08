import { User } from './auth'

// Core feature flag types
export interface FeatureFlag {
  id: string
  flag_key: string
  name: string
  description?: string
  is_enabled: boolean
  rollout_percentage: number
  scope: FeatureFlagScope
  status: FeatureFlagStatus
  config: Record<string, any>
  allowed_sectors: string[]
  blocked_sectors: string[]
  module_id?: string
  created_at: string
  updated_at: string
  created_by?: string
  updated_by?: string
}

export type FeatureFlagScope = 'global' | 'organisation' | 'sector' | 'user'
export type FeatureFlagStatus = 'active' | 'inactive' | 'deprecated'

// API response types
export interface FeatureFlagEvaluationResponse {
  flag_key: string
  enabled: boolean
  user_id: string
  config?: Record<string, any>
  reason?: string
}

export interface EnabledFeaturesResponse {
  enabled_features: Record<string, {
    name: string
    config: Record<string, any>
    module_id?: string
  }>
  user_id: string
  organisation_id: string
}

// Hook return types
export interface UseFeatureFlagResult {
  isEnabled: boolean
  isLoading: boolean
  error: Error | null
  config: Record<string, any> | null
  refetch: () => void
  lastUpdated?: Date
}

export interface UseFeatureFlagsResult {
  flags: Record<string, boolean>
  isLoading: boolean
  error: Error | null
  configs: Record<string, Record<string, any>>
  refetch: () => void
  lastUpdated?: Date
}

export interface UseAllFeatureFlagsResult {
  allFlags: Record<string, {
    enabled: boolean
    name: string
    config: Record<string, any>
    module_id?: string
  }>
  isLoading: boolean
  error: Error | null
  refetch: () => void
  lastUpdated?: Date
}

// Context types
export interface FeatureFlagContextType {
  // Single flag evaluation
  isFeatureEnabled: (flagKey: string) => boolean
  getFeatureConfig: (flagKey: string) => Record<string, any> | null
  
  // Bulk operations
  areAnyFeaturesEnabled: (flagKeys: string[]) => boolean
  areAllFeaturesEnabled: (flagKeys: string[]) => boolean
  getEnabledFeatures: () => string[]
  
  // Cache management
  invalidateFlag: (flagKey: string) => void
  invalidateAllFlags: () => void
  preloadFlags: (flagKeys: string[]) => void
  
  // State
  isInitialized: boolean
  isLoading: boolean
  lastUpdated?: Date
}

// Configuration types
export interface FeatureFlagOptions {
  fallbackValue?: boolean
  cacheTime?: number
  staleTime?: number
  refetchInterval?: number | false
  refetchOnWindowFocus?: boolean
  retryCount?: number
  enabled?: boolean
}

export interface FeatureFlagsOptions {
  fallbackValues?: Record<string, boolean>
  cacheTime?: number
  staleTime?: number
  refetchInterval?: number | false
  refetchOnWindowFocus?: boolean
  retryCount?: number
  enabled?: boolean
}

// Utility types
export interface FeatureFlagWithResolvedHooks<T = any> extends React.ComponentType<T> {
  displayName?: string
}

export interface WithFeatureFlagProps {
  featureFlags?: Record<string, boolean>
  featureFlagsLoading?: boolean
  featureFlagsError?: Error | null
}

// Error types
export class FeatureFlagError extends Error {
  constructor(
    message: string,
    public readonly flagKey?: string,
    public readonly statusCode?: number
  ) {
    super(message)
    this.name = 'FeatureFlagError'
  }
}

// Event types for real-time updates
export interface FeatureFlagUpdateEvent {
  type: 'flag_updated' | 'flag_created' | 'flag_deleted' | 'bulk_update'
  flagKey?: string
  flags?: string[]
  data?: Partial<FeatureFlag>
  timestamp: string
  userId?: string
  organisationId?: string
}

export interface UseFeatureFlagUpdatesResult {
  subscribe: (flagKeys: string | string[]) => () => void
  unsubscribe: (flagKeys: string | string[]) => void
  isConnected: boolean
  lastEvent?: FeatureFlagUpdateEvent
  connectionError?: Error
}

// Local storage fallback types
export interface FeatureFlagCache {
  flags: Record<string, {
    enabled: boolean
    config: Record<string, any>
    timestamp: number
    ttl: number
  }>
  lastSync: number
  version: string
}

// Debug types
export interface FeatureFlagDebugInfo {
  flagKey: string
  enabled: boolean
  config: Record<string, any>
  source: 'cache' | 'network' | 'fallback'
  evaluationTime: number
  reason?: string
  user: Pick<User, 'id' | 'organisation_id'>
  organisation?: string
  cacheStatus?: 'hit' | 'miss' | 'stale'
}