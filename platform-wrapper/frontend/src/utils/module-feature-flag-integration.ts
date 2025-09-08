/**
 * Module-Feature Flag Integration Utilities
 * Provides utilities for integrating modules with feature flags
 */

import { APPLICATION_REGISTRY, ApplicationConfig, GLOBAL_FEATURE_FLAGS } from '@/components/ui/ApplicationRegistry'
import { ModuleFeatureFlagResponse, AnalyticsModule } from '@/types/module-feature-flags'

/**
 * Generate hierarchical flag keys for modules
 */
export const generateModuleFlagKey = (
  moduleId: string, 
  level: 'enabled' | 'capability' | 'feature' = 'enabled',
  name?: string
): string => {
  const normalizedModuleId = moduleId.replace(/-/g, '_')
  
  switch (level) {
    case 'enabled':
      return `modules.${normalizedModuleId}.enabled`
    case 'capability':
      return `modules.${normalizedModuleId}.capabilities.${name?.replace(/-/g, '_')}`
    case 'feature':
      return `modules.${normalizedModuleId}.features.${name?.replace(/-/g, '_')}`
    default:
      return `modules.${normalizedModuleId}.enabled`
  }
}

/**
 * Generate bulk flag operations for module management
 */
export const generateModuleBulkOperation = (
  moduleIds: string[],
  action: 'enable' | 'disable' | 'configure',
  options: {
    rolloutPercentage?: number
    scope?: 'global' | 'organisation' | 'sector' | 'user'
    config?: Record<string, any>
  } = {}
) => {
  return {
    action,
    module_ids: moduleIds,
    flag_pattern: `modules.{module_id}.enabled`,
    config: options.config || {},
    scope: options.scope || 'organisation',
    rollout_percentage: options.rolloutPercentage || 100
  }
}

/**
 * Map ApplicationRegistry to Module-Flag requirements
 */
export const mapApplicationToModuleFlags = (application: ApplicationConfig): {
  required_module_flags: string[]
  optional_module_flags: string[]
  capability_flags: string[]
} => {
  const moduleId = application.moduleId
  
  return {
    required_module_flags: [
      generateModuleFlagKey(moduleId, 'enabled'),
      ...application.requiredFlags
    ],
    optional_module_flags: application.optionalFlags,
    capability_flags: application.features.map(feature => 
      generateModuleFlagKey(moduleId, 'capability', feature.toLowerCase().replace(/\s+/g, '_'))
    )
  }
}

/**
 * Validate module-flag consistency across the platform
 */
export const validateModuleFlagConsistency = (): {
  valid: boolean
  issues: Array<{
    type: 'missing_flag' | 'orphaned_flag' | 'naming_inconsistency'
    severity: 'error' | 'warning'
    message: string
    moduleId?: string
    flagKey?: string
    suggestion?: string
  }>
} => {
  const issues: any[] = []
  
  // Check each application in the registry
  APPLICATION_REGISTRY.forEach(app => {
    const moduleId = app.moduleId
    const expectedModuleFlag = generateModuleFlagKey(moduleId, 'enabled')
    
    // Check if required module flag is in the required flags
    if (!app.requiredFlags.includes(expectedModuleFlag)) {
      issues.push({
        type: 'missing_flag',
        severity: 'error' as const,
        message: `Application '${app.id}' is missing required module flag`,
        moduleId,
        flagKey: expectedModuleFlag,
        suggestion: `Add '${expectedModuleFlag}' to requiredFlags array`
      })
    }
    
    // Check for naming consistency
    app.requiredFlags.forEach(flagKey => {
      if (flagKey.startsWith(`modules.${moduleId.replace(/-/g, '_')}`)) {
        if (!flagKey.match(/^modules\.[a-z_]+\.(enabled|features|capabilities)\./)) {
          issues.push({
            type: 'naming_inconsistency',
            severity: 'warning' as const,
            message: `Flag key '${flagKey}' doesn't follow naming convention`,
            moduleId,
            flagKey,
            suggestion: 'Use pattern: modules.{module_id}.{level}.{name}'
          })
        }
      }
    })
  })
  
  return {
    valid: issues.filter(i => i.severity === 'error').length === 0,
    issues
  }
}

/**
 * Generate module flag templates for new modules
 */
export const generateModuleFlagTemplate = (
  moduleId: string,
  moduleName: string,
  capabilities: string[] = [],
  features: string[] = []
) => {
  const normalizedModuleId = moduleId.replace(/-/g, '_')
  
  const template = {
    module_id: moduleId,
    template_version: '1.0.0',
    flags: [
      // Core module flag
      {
        flag_key: generateModuleFlagKey(moduleId, 'enabled'),
        name: `${moduleName} Module`,
        description: `Enable the ${moduleName} module`,
        hierarchy_level: 'module' as const,
        is_required: true,
        default_enabled: false,
        default_config: {},
        scope_recommendations: ['organisation', 'sector'],
        rollout_strategy: 'gradual' as const
      },
      // Feature flags
      ...features.map(feature => ({
        flag_key: generateModuleFlagKey(moduleId, 'feature', feature),
        name: `${moduleName} - ${feature}`,
        description: `Enable ${feature} feature in ${moduleName}`,
        hierarchy_level: 'feature' as const,
        is_required: false,
        default_enabled: true,
        default_config: {},
        scope_recommendations: ['organisation'],
        rollout_strategy: 'immediate' as const
      })),
      // Capability flags
      ...capabilities.map(capability => ({
        flag_key: generateModuleFlagKey(moduleId, 'capability', capability),
        name: `${moduleName} - ${capability}`,
        description: `Enable ${capability} capability in ${moduleName}`,
        hierarchy_level: 'capability' as const,
        is_required: false,
        default_enabled: true,
        default_config: {
          rate_limit: 100,
          cache_ttl: 300
        },
        scope_recommendations: ['user'],
        rollout_strategy: 'user_controlled' as const
      }))
    ],
    capabilities: capabilities.map(capability => ({
      capability_name: capability,
      required_flags: [generateModuleFlagKey(moduleId, 'enabled')],
      optional_flags: [generateModuleFlagKey(moduleId, 'capability', capability)],
      config_schema: {
        type: 'object',
        properties: {
          rate_limit: { type: 'number', default: 100 },
          cache_ttl: { type: 'number', default: 300 }
        }
      }
    }))
  }
  
  return template
}

/**
 * Calculate module health score based on flags and dependencies
 */
export const calculateModuleHealthScore = (
  moduleData: ModuleFeatureFlagResponse,
  dependencies: string[] = []
): {
  score: number // 0-100
  status: 'healthy' | 'degraded' | 'unavailable'
  factors: Array<{
    name: string
    score: number
    weight: number
    status: 'pass' | 'warn' | 'fail'
  }>
} => {
  const factors = []
  
  // Required flags health (40% weight)
  const requiredFlagsEnabled = moduleData.module.required_flags.every(
    flagKey => moduleData.enabled_flags[flagKey]?.enabled
  )
  factors.push({
    name: 'Required Flags',
    score: requiredFlagsEnabled ? 100 : 0,
    weight: 0.4,
    status: requiredFlagsEnabled ? 'pass' as const : 'fail' as const
  })
  
  // Module status health (20% weight)
  const moduleStatusScore = {
    'active': 100,
    'testing': 80,
    'development': 60,
    'deprecated': 30,
    'disabled': 0
  }[moduleData.module.status] || 0
  
  factors.push({
    name: 'Module Status',
    score: moduleStatusScore,
    weight: 0.2,
    status: moduleStatusScore >= 80 ? 'pass' as const : 
            moduleStatusScore >= 50 ? 'warn' as const : 'fail' as const
  })
  
  // Dependencies health (20% weight)
  const dependencyScore = dependencies.length === 0 ? 100 : 
    (dependencies.filter(dep => 
      moduleData.enabled_flags[generateModuleFlagKey(dep, 'enabled')]?.enabled
    ).length / dependencies.length) * 100
  
  factors.push({
    name: 'Dependencies',
    score: dependencyScore,
    weight: 0.2,
    status: dependencyScore >= 80 ? 'pass' as const :
            dependencyScore >= 50 ? 'warn' as const : 'fail' as const
  })
  
  // Capabilities health (20% weight)
  const availableCapabilities = moduleData.available_capabilities.length
  const totalCapabilities = availableCapabilities + moduleData.disabled_capabilities.length
  const capabilityScore = totalCapabilities === 0 ? 100 : 
    (availableCapabilities / totalCapabilities) * 100
  
  factors.push({
    name: 'Capabilities',
    score: capabilityScore,
    weight: 0.2,
    status: capabilityScore >= 80 ? 'pass' as const :
            capabilityScore >= 50 ? 'warn' as const : 'fail' as const
  })
  
  // Calculate weighted score
  const totalScore = factors.reduce((sum, factor) => 
    sum + (factor.score * factor.weight), 0
  )
  
  const status = totalScore >= 80 ? 'healthy' :
                totalScore >= 50 ? 'degraded' : 'unavailable'
  
  return {
    score: Math.round(totalScore),
    status,
    factors
  }
}

/**
 * Generate feature flag migration plan for existing modules
 */
export const generateFlagMigrationPlan = (
  existingModules: AnalyticsModule[],
  targetFlagStructure: 'hierarchical' | 'flat' = 'hierarchical'
): {
  migration_steps: Array<{
    step: number
    description: string
    moduleId: string
    actions: Array<{
      type: 'create_flag' | 'update_flag' | 'migrate_flag' | 'deprecate_flag'
      flag_key: string
      from_key?: string
      config: Record<string, any>
    }>
  }>
  rollback_plan: Array<{
    step: number
    actions: Array<{
      type: 'restore_flag' | 'remove_flag'
      flag_key: string
      backup_config?: Record<string, any>
    }>
  }>
} => {
  const migrationSteps: any[] = []
  const rollbackPlan: any[] = []
  
  existingModules.forEach((module, index) => {
    const stepNumber = index + 1
    
    if (targetFlagStructure === 'hierarchical') {
      // Migrate to hierarchical structure
      const newModuleFlag = generateModuleFlagKey(module.id, 'enabled')
      
      migrationSteps.push({
        step: stepNumber,
        description: `Migrate ${module.name} to hierarchical flag structure`,
        moduleId: module.id,
        actions: [
          {
            type: 'create_flag',
            flag_key: newModuleFlag,
            config: {
              name: `${module.name} Module`,
              description: `Enable the ${module.name} module`,
              is_enabled: module.status === 'active',
              scope: 'organisation',
              rollout_percentage: 100
            }
          },
          // Create capability flags
          ...module.capabilities.map(cap => ({
            type: 'create_flag' as const,
            flag_key: generateModuleFlagKey(module.id, 'capability', cap.name),
            config: {
              name: `${module.name} - ${cap.name}`,
              description: cap.description,
              is_enabled: !cap.is_required, // Optional capabilities start disabled
              scope: 'user',
              rollout_percentage: 0
            }
          }))
        ]
      })
      
      // Rollback plan
      rollbackPlan.push({
        step: stepNumber,
        actions: [
          {
            type: 'remove_flag',
            flag_key: newModuleFlag
          },
          ...module.capabilities.map(cap => ({
            type: 'remove_flag' as const,
            flag_key: generateModuleFlagKey(module.id, 'capability', cap.name)
          }))
        ]
      })
    }
  })
  
  return {
    migration_steps: migrationSteps,
    rollback_plan: rollbackPlan
  }
}

/**
 * Integration health check for the entire module-flag system
 */
export const performIntegrationHealthCheck = async (): Promise<{
  overall_health: 'healthy' | 'degraded' | 'critical'
  checks: Array<{
    name: string
    status: 'pass' | 'warn' | 'fail'
    message: string
    details?: any
  }>
  recommendations: string[]
}> => {
  const checks = []
  const recommendations = []
  
  try {
    // 1. Check Application Registry consistency
    const validation = validateModuleFlagConsistency()
    checks.push({
      name: 'Application Registry Consistency',
      status: validation.valid ? 'pass' as const : 'fail' as const,
      message: validation.valid ? 'All applications have consistent flag mappings' : 
               `Found ${validation.issues.length} inconsistencies`,
      details: validation.issues
    })
    
    if (!validation.valid) {
      recommendations.push('Fix application registry flag inconsistencies')
    }
    
    // 2. Check global flag usage
    const globalFlagsUsed = APPLICATION_REGISTRY.reduce((acc, app) => {
      app.requiredFlags.concat(app.optionalFlags).forEach(flag => {
        if (Object.values(GLOBAL_FEATURE_FLAGS).includes(flag)) {
          acc.add(flag)
        }
      })
      return acc
    }, new Set())
    
    checks.push({
      name: 'Global Flag Usage',
      status: globalFlagsUsed.size > 0 ? 'pass' as const : 'warn' as const,
      message: `${globalFlagsUsed.size} global flags in use`,
      details: Array.from(globalFlagsUsed)
    })
    
    // 3. Check naming conventions
    let namingIssues = 0
    APPLICATION_REGISTRY.forEach(app => {
      app.requiredFlags.concat(app.optionalFlags).forEach(flag => {
        if (flag.startsWith('modules.') && !flag.match(/^modules\.[a-z_]+\.(enabled|features|capabilities)/)) {
          namingIssues++
        }
      })
    })
    
    checks.push({
      name: 'Flag Naming Conventions',
      status: namingIssues === 0 ? 'pass' as const : 'warn' as const,
      message: namingIssues === 0 ? 'All flags follow naming conventions' : 
               `${namingIssues} flags don't follow conventions`,
      details: { namingIssues }
    })
    
    if (namingIssues > 0) {
      recommendations.push('Update flag names to follow conventions: modules.{module_id}.{level}.{name}')
    }
    
    // 4. Check module coverage
    const moduleIds = APPLICATION_REGISTRY.map(app => app.moduleId)
    const uniqueModules = new Set(moduleIds)
    
    checks.push({
      name: 'Module Coverage',
      status: uniqueModules.size === moduleIds.length ? 'pass' as const : 'warn' as const,
      message: `${uniqueModules.size} unique modules, ${moduleIds.length} total applications`,
      details: { uniqueModules: uniqueModules.size, totalApplications: moduleIds.length }
    })
    
    // Calculate overall health
    const passCount = checks.filter(c => c.status === 'pass').length
    const warnCount = checks.filter(c => c.status === 'warn').length
    const failCount = checks.filter(c => c.status === 'fail').length
    
    const overall_health = 
      failCount > 0 ? 'critical' as const :
      warnCount > 2 ? 'degraded' as const : 'healthy' as const
    
    return {
      overall_health,
      checks,
      recommendations
    }
    
  } catch (error) {
    return {
      overall_health: 'critical',
      checks: [{
        name: 'Integration Health Check',
        status: 'fail',
        message: `Health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        details: error
      }],
      recommendations: ['Fix integration health check errors before proceeding']
    }
  }
}

/**
 * Export utility functions for external use
 */
export const ModuleFlagIntegrationUtils = {
  generateModuleFlagKey,
  generateModuleBulkOperation,
  mapApplicationToModuleFlags,
  validateModuleFlagConsistency,
  generateModuleFlagTemplate,
  calculateModuleHealthScore,
  generateFlagMigrationPlan,
  performIntegrationHealthCheck
}