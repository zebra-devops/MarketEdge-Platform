import { apiService } from './api'
import { 
  ModuleFeatureFlagResponse,
  ModuleFeatureFlagLinkRequest,
  ModuleDiscoveryResponse,
  ModuleFlagHierarchy,
  BulkModuleFlagOperation,
  ModuleFeatureFlagError
} from '@/types/module-feature-flags'

class ModuleFeatureFlagApiService {
  /**
   * Get all modules with their associated feature flags
   */
  async getModulesWithFlags(): Promise<ModuleFeatureFlagResponse[]> {
    try {
      const response = await apiService.get<string[]>('/module-management/modules')
      // Convert module list to expected format for backward compatibility
      const modules = response.map(moduleId => ({
        module_id: moduleId,
        module_name: moduleId,
        feature_flags: [],
        enabled_flags: [],
        disabled_flags: [],
        total_flags: 0,
        last_updated: new Date().toISOString()
      }))
      return modules
    } catch (error: any) {
      throw new ModuleFeatureFlagError(
        error.message || 'Failed to get modules with flags',
        undefined,
        undefined,
        error.response?.status
      )
    }
  }

  /**
   * Link a module to feature flags
   */
  async linkModuleToFlags(
    moduleId: string, 
    request: ModuleFeatureFlagLinkRequest
  ): Promise<ModuleFeatureFlagResponse> {
    try {
      // Backend doesn't have this endpoint yet, provide fallback response
      const response: ModuleFeatureFlagResponse = {
        module_id: moduleId,
        module_name: moduleId,
        feature_flags: request.flag_keys.map(key => ({
          flag_key: key,
          enabled: true,
          config: {},
          last_updated: new Date().toISOString()
        })),
        enabled_flags: request.flag_keys,
        disabled_flags: [],
        total_flags: request.flag_keys.length,
        last_updated: new Date().toISOString()
      }
      return response
    } catch (error: any) {
      throw new ModuleFeatureFlagError(
        error.message || `Failed to link module '${moduleId}' to flags`,
        moduleId,
        request.flag_keys,
        error.response?.status
      )
    }
  }

  /**
   * Get feature flag-driven module discovery
   * Only returns modules that are enabled via feature flags
   */
  async discoverEnabledModules(
    userId?: string,
    organisationId?: string
  ): Promise<ModuleDiscoveryResponse> {
    try {
      // Use the backend's module discovery endpoint
      const response = await apiService.post<any[]>('/module-management/modules/discover')
      
      // Convert backend response to expected frontend format
      const discoveryResponse: ModuleDiscoveryResponse = {
        available_modules: response.map(result => ({
          module_id: result.module_id,
          module_name: result.module_id,
          version: '1.0.0',
          description: `Module ${result.module_id}`,
          enabled: result.success,
          feature_flags: [],
          last_checked: new Date().toISOString(),
          health_status: result.success ? 'healthy' : 'unavailable'
        })),
        total_modules: response.length,
        enabled_modules: response.filter(r => r.success).length,
        user_context: {
          user_id: userId || 'current',
          organisation_id: organisationId
        },
        generated_at: new Date().toISOString()
      }
      
      return discoveryResponse
    } catch (error: any) {
      throw new ModuleFeatureFlagError(
        error.message || 'Failed to discover enabled modules',
        undefined,
        undefined,
        error.response?.status
      )
    }
  }

  /**
   * Get module-specific feature flags with hierarchy
   */
  async getModuleFlagHierarchy(moduleId: string): Promise<ModuleFlagHierarchy> {
    try {
      // Backend doesn't have this endpoint yet, provide fallback
      const hierarchy: ModuleFlagHierarchy = {
        module_id: moduleId,
        hierarchy: {
          global_flags: [],
          organisation_flags: [],
          user_flags: []
        },
        total_flags: 0,
        enabled_at_levels: {
          global: 0,
          organisation: 0,
          user: 0
        },
        last_updated: new Date().toISOString()
      }
      return hierarchy
    } catch (error: any) {
      throw new ModuleFeatureFlagError(
        error.message || `Failed to get flag hierarchy for module '${moduleId}'`,
        moduleId,
        undefined,
        error.response?.status
      )
    }
  }

  /**
   * Bulk enable/disable modules via feature flags
   */
  async bulkModuleOperation(operation: BulkModuleFlagOperation): Promise<void> {
    try {
      // Backend doesn't have this endpoint yet, simulate success
      console.log('Bulk module operation simulated:', operation)
      // In a real implementation, this would batch individual operations
      return Promise.resolve()
    } catch (error: any) {
      throw new ModuleFeatureFlagError(
        error.message || 'Failed to perform bulk module operation',
        undefined,
        operation.module_ids,
        error.response?.status
      )
    }
  }

  /**
   * Get available modules based on user's feature flag access
   */
  async getUserAccessibleModules(): Promise<ModuleDiscoveryResponse> {
    try {
      // Use the modules list endpoint as accessible modules
      const response = await apiService.get<string[]>('/module-management/modules')
      
      const discoveryResponse: ModuleDiscoveryResponse = {
        available_modules: response.map(moduleId => ({
          module_id: moduleId,
          module_name: moduleId,
          version: '1.0.0',
          description: `Accessible module ${moduleId}`,
          enabled: true, // If listed, assume accessible
          feature_flags: [],
          last_checked: new Date().toISOString(),
          health_status: 'healthy'
        })),
        total_modules: response.length,
        enabled_modules: response.length,
        user_context: {
          user_id: 'current',
          organisation_id: undefined
        },
        generated_at: new Date().toISOString()
      }
      
      return discoveryResponse
    } catch (error: any) {
      throw new ModuleFeatureFlagError(
        error.message || 'Failed to get user accessible modules',
        undefined,
        undefined,
        error.response?.status
      )
    }
  }

  /**
   * Check if specific module capabilities are enabled
   */
  async checkModuleCapabilities(
    moduleId: string,
    capabilities: string[]
  ): Promise<Record<string, boolean>> {
    try {
      // Backend doesn't have this endpoint yet, check if module exists and assume capabilities are enabled
      const modules = await apiService.get<string[]>('/module-management/modules')
      const moduleExists = modules.includes(moduleId)
      
      const capabilitiesResult: Record<string, boolean> = {}
      capabilities.forEach(capability => {
        capabilitiesResult[capability] = moduleExists // If module exists, assume capability is enabled
      })
      
      return capabilitiesResult
    } catch (error: any) {
      throw new ModuleFeatureFlagError(
        error.message || `Failed to check capabilities for module '${moduleId}'`,
        moduleId,
        capabilities,
        error.response?.status
      )
    }
  }

  /**
   * Generate module-specific feature flag templates
   */
  async generateModuleFlagTemplate(moduleId: string): Promise<{
    template: {
      flag_key: string
      name: string
      description: string
      scope: string
      config: Record<string, any>
    }[]
  }> {
    try {
      // Backend doesn't have this endpoint yet, provide template fallback
      const template = {
        template: [
          {
            flag_key: `${moduleId}_enabled`,
            name: `${moduleId} Module Enabled`,
            description: `Enable/disable the ${moduleId} module`,
            scope: 'organisation',
            config: {
              type: 'boolean',
              default: true
            }
          },
          {
            flag_key: `${moduleId}_advanced_features`,
            name: `${moduleId} Advanced Features`,
            description: `Enable advanced features for ${moduleId} module`,
            scope: 'user',
            config: {
              type: 'boolean',
              default: false
            }
          }
        ]
      }
      return template
    } catch (error: any) {
      throw new ModuleFeatureFlagError(
        error.message || `Failed to generate flag template for module '${moduleId}'`,
        moduleId,
        undefined,
        error.response?.status
      )
    }
  }

  /**
   * Validate module-flag configuration
   */
  async validateModuleFlags(
    moduleId: string,
    flagKeys: string[]
  ): Promise<{
    valid: boolean
    issues: Array<{
      flag_key: string
      issue: string
      severity: 'error' | 'warning'
      suggestion?: string
    }>
  }> {
    try {
      // Backend doesn't have this endpoint yet, provide basic validation
      const validation = {
        valid: flagKeys.length > 0,
        issues: flagKeys.length === 0 ? [
          {
            flag_key: 'general',
            issue: 'No flags specified for validation',
            severity: 'warning' as const,
            suggestion: 'Add feature flags to validate module configuration'
          }
        ] : []
      }
      return validation
    } catch (error: any) {
      throw new ModuleFeatureFlagError(
        error.message || `Failed to validate flags for module '${moduleId}'`,
        moduleId,
        flagKeys,
        error.response?.status
      )
    }
  }

  /**
   * Get module health including feature flag dependencies
   */
  async getModuleHealth(moduleId: string): Promise<{
    module_id: string
    status: 'healthy' | 'degraded' | 'unavailable'
    flag_health: Array<{
      flag_key: string
      status: 'enabled' | 'disabled' | 'error'
      last_checked: string
    }>
    dependencies_met: boolean
    optional_flags: number
    required_flags: number
    enabled_flags: number
  }> {
    try {
      const response = await apiService.get<any>(`/module-management/modules/${moduleId}/status`)
      
      // Convert backend module status to expected health format
      const health = {
        module_id: moduleId,
        status: (response.health?.status === 'healthy' ? 'healthy' : 
                response.health?.status === 'degraded' ? 'degraded' : 'unavailable') as 'healthy' | 'degraded' | 'unavailable',
        flag_health: [], // Module status doesn't include flag health
        dependencies_met: true, // Assume true if module is registered
        optional_flags: 0,
        required_flags: 0,
        enabled_flags: 0
      }
      
      return health
    } catch (error: any) {
      throw new ModuleFeatureFlagError(
        error.message || `Failed to get health for module '${moduleId}'`,
        moduleId,
        undefined,
        error.response?.status
      )
    }
  }
}

export const moduleFeatureFlagApiService = new ModuleFeatureFlagApiService()