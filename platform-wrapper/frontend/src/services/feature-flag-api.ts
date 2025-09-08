import { apiService } from './api'
import { 
  FeatureFlagEvaluationResponse, 
  EnabledFeaturesResponse,
  FeatureFlagError
} from '@/types/feature-flags'

class FeatureFlagApiService {
  /**
   * Check if a specific feature flag is enabled for the current user
   */
  async checkFeatureFlag(flagKey: string): Promise<FeatureFlagEvaluationResponse> {
    try {
      const response = await apiService.get<FeatureFlagEvaluationResponse>(`/features/${flagKey}`)
      return response
    } catch (error: any) {
      // Convert API errors to FeatureFlagError
      if (error.response?.status === 404) {
        throw new FeatureFlagError(`Feature flag '${flagKey}' not found`, flagKey, 404)
      }
      if (error.response?.status === 403) {
        throw new FeatureFlagError(`Access denied for feature flag '${flagKey}'`, flagKey, 403)
      }
      throw new FeatureFlagError(
        error.message || `Failed to check feature flag '${flagKey}'`,
        flagKey,
        error.response?.status
      )
    }
  }

  /**
   * Get all enabled features for the current user
   */
  async getEnabledFeatures(moduleId?: string): Promise<EnabledFeaturesResponse> {
    try {
      const url = moduleId ? `/features/enabled?module_id=${moduleId}` : '/features/enabled'
      const response = await apiService.get<EnabledFeaturesResponse>(url)
      return response
    } catch (error: any) {
      throw new FeatureFlagError(
        error.message || 'Failed to get enabled features',
        undefined,
        error.response?.status
      )
    }
  }

  /**
   * Batch check multiple feature flags
   */
  async checkMultipleFlags(flagKeys: string[]): Promise<Record<string, FeatureFlagEvaluationResponse>> {
    try {
      // Since the backend doesn't have a bulk endpoint, we'll make parallel requests
      const promises = flagKeys.map(async (flagKey) => {
        try {
          const result = await this.checkFeatureFlag(flagKey)
          return { flagKey, result }
        } catch (error) {
          // Return disabled for non-existent flags instead of throwing
          if (error instanceof FeatureFlagError && error.statusCode === 404) {
            return {
              flagKey,
              result: {
                flag_key: flagKey,
                enabled: false,
                user_id: '',
                reason: 'Flag not found'
              }
            }
          }
          throw error
        }
      })

      const results = await Promise.all(promises)
      
      // Convert to record format
      return results.reduce((acc, { flagKey, result }) => {
        acc[flagKey] = result
        return acc
      }, {} as Record<string, FeatureFlagEvaluationResponse>)
      
    } catch (error: any) {
      throw new FeatureFlagError(
        error.message || 'Failed to check multiple feature flags',
        undefined,
        error.response?.status
      )
    }
  }

  /**
   * Preload flags into cache (for performance)
   */
  async preloadFlags(flagKeys: string[]): Promise<void> {
    try {
      // Fire parallel requests without waiting for results
      // This helps with cache warming
      flagKeys.forEach(flagKey => {
        this.checkFeatureFlag(flagKey).catch(error => {
          // Silently fail for preloading - we don't want to break the app
          console.warn(`Failed to preload flag '${flagKey}':`, error.message)
        })
      })
    } catch (error) {
      // Silent failure for preloading
      console.warn('Failed to preload flags:', error)
    }
  }

  /**
   * Health check for feature flag service
   */
  async healthCheck(): Promise<{ status: 'healthy' | 'degraded'; timestamp: string }> {
    try {
      // Try to get enabled features as a health check
      await this.getEnabledFeatures()
      return {
        status: 'healthy',
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        status: 'degraded',
        timestamp: new Date().toISOString()
      }
    }
  }
}

export const featureFlagApiService = new FeatureFlagApiService()