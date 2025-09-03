import { apiService } from './api'
import { FeatureFlag, FeatureFlagCreate, FeatureFlagUpdate } from '@/types/feature-flags'

export interface AdminFeatureFlagResponse {
  feature_flags: FeatureFlag[]
  total_count: number
  page?: number
  page_size?: number
}

export class AdminFeatureFlagService {
  /**
   * Get all feature flags (admin only)
   */
  async getFeatureFlags(moduleId?: string, enabledOnly?: boolean): Promise<AdminFeatureFlagResponse> {
    const params = new URLSearchParams()
    if (moduleId) params.append('module_id', moduleId)
    if (enabledOnly) params.append('enabled_only', 'true')
    
    const query = params.toString() ? `?${params.toString()}` : ''
    return await apiService.get<AdminFeatureFlagResponse>(`/admin/feature-flags${query}`)
  }

  /**
   * Create a new feature flag (admin only)
   */
  async createFeatureFlag(flagData: FeatureFlagCreate): Promise<FeatureFlag> {
    return await apiService.post<FeatureFlag>('/admin/feature-flags', flagData)
  }

  /**
   * Update an existing feature flag (admin only)
   */
  async updateFeatureFlag(flagId: string, updates: FeatureFlagUpdate): Promise<FeatureFlag> {
    return await apiService.put<FeatureFlag>(`/admin/feature-flags/${flagId}`, updates)
  }

  /**
   * Delete a feature flag (admin only)
   */
  async deleteFeatureFlag(flagId: string): Promise<void> {
    return await apiService.delete<void>(`/admin/feature-flags/${flagId}`)
  }

  /**
   * Toggle a feature flag's enabled state (admin only)
   */
  async toggleFeatureFlag(flagId: string, enabled: boolean): Promise<FeatureFlag> {
    return await apiService.put<FeatureFlag>(`/admin/feature-flags/${flagId}`, { enabled })
  }

  /**
   * Get feature flag usage analytics (admin only)
   */
  async getFeatureFlagAnalytics(flagId: string): Promise<any> {
    return await apiService.get(`/admin/feature-flags/${flagId}/analytics`)
  }
}

export const adminFeatureFlagService = new AdminFeatureFlagService()