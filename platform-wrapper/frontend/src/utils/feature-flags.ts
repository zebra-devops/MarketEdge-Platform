import { FeatureFlagCache, FeatureFlagDebugInfo } from '@/types/feature-flags'

/**
 * Local storage key for feature flag cache
 */
const FEATURE_FLAG_CACHE_KEY = 'marketedge_feature_flags_cache'
const CACHE_VERSION = '1.0.0'
const DEFAULT_TTL = 5 * 60 * 1000 // 5 minutes

/**
 * Utility functions for feature flag evaluation and cache management
 */
export class FeatureFlagUtils {
  /**
   * Save feature flags to local storage for offline fallback
   */
  static saveToCache(flags: Record<string, { enabled: boolean; config: Record<string, any> }>) {
    if (typeof window === 'undefined') return

    try {
      const timestamp = Date.now()
      const cache: FeatureFlagCache = {
        flags: Object.entries(flags).reduce((acc, [flagKey, flagData]) => {
          acc[flagKey] = {
            enabled: flagData.enabled,
            config: flagData.config,
            timestamp,
            ttl: DEFAULT_TTL
          }
          return acc
        }, {} as FeatureFlagCache['flags']),
        lastSync: timestamp,
        version: CACHE_VERSION
      }

      localStorage.setItem(FEATURE_FLAG_CACHE_KEY, JSON.stringify(cache))
    } catch (error) {
      console.warn('Failed to save feature flags to cache:', error)
    }
  }

  /**
   * Load feature flags from local storage
   */
  static loadFromCache(): FeatureFlagCache | null {
    if (typeof window === 'undefined') return null

    try {
      const cachedData = localStorage.getItem(FEATURE_FLAG_CACHE_KEY)
      if (!cachedData) return null

      const cache: FeatureFlagCache = JSON.parse(cachedData)
      
      // Check cache version
      if (cache.version !== CACHE_VERSION) {
        this.clearCache()
        return null
      }

      return cache
    } catch (error) {
      console.warn('Failed to load feature flags from cache:', error)
      this.clearCache()
      return null
    }
  }

  /**
   * Get a specific flag from cache with TTL check
   */
  static getCachedFlag(flagKey: string): { enabled: boolean; config: Record<string, any> } | null {
    const cache = this.loadFromCache()
    if (!cache || !cache.flags[flagKey]) return null

    const flagData = cache.flags[flagKey]
    const now = Date.now()

    // Check if cache entry is expired
    if (now - flagData.timestamp > flagData.ttl) {
      return null
    }

    return {
      enabled: flagData.enabled,
      config: flagData.config
    }
  }

  /**
   * Clear feature flag cache
   */
  static clearCache() {
    if (typeof window === 'undefined') return

    try {
      localStorage.removeItem(FEATURE_FLAG_CACHE_KEY)
    } catch (error) {
      console.warn('Failed to clear feature flag cache:', error)
    }
  }

  /**
   * Check if flag cache is stale
   */
  static isCacheStale(): boolean {
    const cache = this.loadFromCache()
    if (!cache) return true

    const now = Date.now()
    const staleTime = 2 * 60 * 1000 // 2 minutes

    return now - cache.lastSync > staleTime
  }

  /**
   * Evaluate feature flag with fallback logic
   */
  static evaluateFlag(
    flagKey: string,
    networkResult?: { enabled: boolean; config?: Record<string, any> },
    fallbackValue: boolean = false
  ): { enabled: boolean; config: Record<string, any>; source: 'network' | 'cache' | 'fallback' } {
    // Use network result if available
    if (networkResult !== undefined) {
      return {
        enabled: networkResult.enabled,
        config: networkResult.config || {},
        source: 'network'
      }
    }

    // Try cache fallback
    const cachedFlag = this.getCachedFlag(flagKey)
    if (cachedFlag) {
      return {
        enabled: cachedFlag.enabled,
        config: cachedFlag.config,
        source: 'cache'
      }
    }

    // Use fallback value
    return {
      enabled: fallbackValue,
      config: {},
      source: 'fallback'
    }
  }

  /**
   * Batch evaluate multiple flags
   */
  static evaluateFlags(
    flagKeys: string[],
    networkResults?: Record<string, { enabled: boolean; config?: Record<string, any> }>,
    fallbackValues: Record<string, boolean> = {}
  ): Record<string, { enabled: boolean; config: Record<string, any>; source: 'network' | 'cache' | 'fallback' }> {
    const results: Record<string, { enabled: boolean; config: Record<string, any>; source: 'network' | 'cache' | 'fallback' }> = {}

    flagKeys.forEach(flagKey => {
      const networkResult = networkResults?.[flagKey]
      const fallbackValue = fallbackValues[flagKey] || false

      results[flagKey] = this.evaluateFlag(flagKey, networkResult, fallbackValue)
    })

    return results
  }

  /**
   * Generate debug information for feature flags
   */
  static generateDebugInfo(
    flagKey: string,
    evaluation: { enabled: boolean; config: Record<string, any>; source: string },
    user: { id: string; organisation_id?: string },
    evaluationTime: number
  ): FeatureFlagDebugInfo {
    return {
      flagKey,
      enabled: evaluation.enabled,
      config: evaluation.config,
      source: evaluation.source as any,
      evaluationTime,
      user: {
        id: user.id,
        organisation_id: user.organisation_id
      },
      cacheStatus: evaluation.source === 'cache' ? 'hit' : evaluation.source === 'network' ? 'miss' : undefined
    }
  }

  /**
   * Create a feature flag key from component/module context
   */
  static createFlagKey(module: string, feature: string, variant?: string): string {
    const parts = [module, feature]
    if (variant) parts.push(variant)
    return parts.join('.')
  }

  /**
   * Parse flag key into components
   */
  static parseFlagKey(flagKey: string): { module?: string; feature: string; variant?: string } {
    const parts = flagKey.split('.')
    
    if (parts.length === 1) {
      return { feature: parts[0] }
    } else if (parts.length === 2) {
      return { module: parts[0], feature: parts[1] }
    } else if (parts.length === 3) {
      return { module: parts[0], feature: parts[1], variant: parts[2] }
    }

    return { feature: flagKey } // Fallback for complex flag keys
  }

  /**
   * Validate flag configuration
   */
  static validateFlagConfig(config: Record<string, any>): { valid: boolean; errors: string[] } {
    const errors: string[] = []

    if (config && typeof config !== 'object') {
      errors.push('Config must be an object')
    }

    if (config && Array.isArray(config)) {
      errors.push('Config cannot be an array')
    }

    return {
      valid: errors.length === 0,
      errors
    }
  }

  /**
   * Merge flag configurations with precedence rules
   */
  static mergeConfigs(
    defaultConfig: Record<string, any> = {},
    flagConfig: Record<string, any> = {},
    userConfig: Record<string, any> = {}
  ): Record<string, any> {
    // User config takes precedence over flag config over default config
    return {
      ...defaultConfig,
      ...flagConfig,
      ...userConfig
    }
  }

  /**
   * Check if user is in rollout percentage
   */
  static isUserInRollout(userId: string, flagKey: string, percentage: number): boolean {
    if (percentage >= 100) return true
    if (percentage <= 0) return false

    // Create deterministic hash from user ID and flag key
    const input = `${userId}:${flagKey}`
    let hash = 0
    
    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }

    // Get percentage (0-99)
    const userPercentage = Math.abs(hash) % 100
    return userPercentage < percentage
  }

  /**
   * Format flag value for display
   */
  static formatFlagValue(enabled: boolean, config?: Record<string, any>): string {
    if (!enabled) return 'Disabled'
    if (!config || Object.keys(config).length === 0) return 'Enabled'
    
    const configStr = JSON.stringify(config, null, 2)
    return `Enabled with config: ${configStr}`
  }

  /**
   * Get flag performance metrics
   */
  static getFlagMetrics(): {
    cacheHitRate: number
    cacheSize: number
    lastSync: number | null
    staleFlags: number
  } {
    const cache = this.loadFromCache()
    if (!cache) {
      return {
        cacheHitRate: 0,
        cacheSize: 0,
        lastSync: null,
        staleFlags: 0
      }
    }

    const now = Date.now()
    const flags = Object.values(cache.flags)
    const staleFlags = flags.filter(flag => now - flag.timestamp > flag.ttl).length

    return {
      cacheHitRate: 0, // Would need to track hits/misses
      cacheSize: flags.length,
      lastSync: cache.lastSync,
      staleFlags
    }
  }
}

/**
 * Feature flag evaluation functions for direct use
 */

/**
 * Simple feature flag check with fallback
 */
export function checkFeatureFlag(
  flagKey: string,
  fallback: boolean = false,
  cachedFlags?: Record<string, boolean>
): boolean {
  if (cachedFlags && flagKey in cachedFlags) {
    return cachedFlags[flagKey]
  }

  const cachedFlag = FeatureFlagUtils.getCachedFlag(flagKey)
  if (cachedFlag) {
    return cachedFlag.enabled
  }

  return fallback
}

/**
 * Get feature flag configuration with fallback
 */
export function getFeatureFlagConfig(
  flagKey: string,
  fallback: Record<string, any> = {},
  cachedConfigs?: Record<string, Record<string, any>>
): Record<string, any> {
  if (cachedConfigs && flagKey in cachedConfigs) {
    return cachedConfigs[flagKey]
  }

  const cachedFlag = FeatureFlagUtils.getCachedFlag(flagKey)
  if (cachedFlag) {
    return cachedFlag.config
  }

  return fallback
}

/**
 * Check if any of the provided flags are enabled
 */
export function checkAnyFeatureFlags(
  flagKeys: string[],
  fallback: boolean = false,
  cachedFlags?: Record<string, boolean>
): boolean {
  return flagKeys.some(flagKey => checkFeatureFlag(flagKey, fallback, cachedFlags))
}

/**
 * Check if all of the provided flags are enabled
 */
export function checkAllFeatureFlags(
  flagKeys: string[],
  fallback: boolean = false,
  cachedFlags?: Record<string, boolean>
): boolean {
  return flagKeys.every(flagKey => checkFeatureFlag(flagKey, fallback, cachedFlags))
}