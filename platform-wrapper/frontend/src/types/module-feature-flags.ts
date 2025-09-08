import { FeatureFlag } from './feature-flags'

// Core module-feature flag types
export interface ModuleFeatureFlag extends FeatureFlag {
  module_id: string
  hierarchy_level: 'global' | 'module' | 'feature' | 'capability'
  parent_flag?: string
  child_flags?: string[]
  is_inherited?: boolean
  inheritance_source?: string
}

export interface AnalyticsModule {
  id: string
  name: string
  description: string
  version: string
  module_type: string
  status: 'active' | 'testing' | 'development' | 'deprecated' | 'disabled'
  is_core: boolean
  requires_license: boolean
  pricing_tier?: string
  dependencies: string[]
  created_at: string
  updated_at: string
  
  // Feature flag integration
  feature_flags: ModuleFeatureFlag[]
  required_flags: string[]
  optional_flags: string[]
  flag_namespace: string
  capabilities: ModuleCapability[]
}

export interface ModuleCapability {
  id: string
  name: string
  description: string
  flag_key: string
  is_required: boolean
  config_schema?: Record<string, any>
  dependencies?: string[]
}

// API request/response types
export interface ModuleFeatureFlagResponse {
  module: AnalyticsModule
  enabled_flags: Record<string, {
    flag_key: string
    enabled: boolean
    config: Record<string, any>
    inherited_from?: string
  }>
  available_capabilities: string[]
  disabled_capabilities: string[]
  health_status: 'healthy' | 'degraded' | 'unavailable'
}

export interface ModuleFeatureFlagLinkRequest {
  flag_keys: string[]
  flag_mappings: Record<string, {
    flag_key: string
    capability?: string
    is_required: boolean
    default_config?: Record<string, any>
  }>
  namespace_prefix?: string
}

export interface ModuleDiscoveryResponse {
  enabled_modules: Array<{
    module_id: string
    name: string
    version: string
    status: string
    capabilities: string[]
    feature_flags: Record<string, boolean>
    config: Record<string, any>
    health: 'healthy' | 'degraded' | 'unavailable'
  }>
  disabled_modules: Array<{
    module_id: string
    name: string
    reason: string
    missing_flags: string[]
    can_enable: boolean
  }>
  total_available: number
  user_accessible: number
}

export interface ModuleFlagHierarchy {
  module_id: string
  hierarchy: {
    global: Array<{
      flag_key: string
      name: string
      enabled: boolean
      affects_module: boolean
    }>
    module: Array<{
      flag_key: string
      name: string
      enabled: boolean
      overrides_global: boolean
      parent_flag?: string
    }>
    features: Record<string, Array<{
      flag_key: string
      name: string
      enabled: boolean
      capability: string
      parent_flag?: string
    }>>
    capabilities: Record<string, Array<{
      flag_key: string
      name: string
      enabled: boolean
      config: Record<string, any>
      parent_flag?: string
    }>>
  }
  effective_flags: Record<string, {
    enabled: boolean
    source: 'global' | 'module' | 'feature' | 'capability'
    config: Record<string, any>
  }>
  inheritance_chain: Array<{
    level: string
    flag_key: string
    enabled: boolean
    overridden_by?: string
  }>
}

export interface BulkModuleFlagOperation {
  action: 'enable' | 'disable' | 'configure'
  module_ids: string[]
  flag_pattern?: string // e.g., "*.enabled" or "module.{module_id}.*"
  config?: Record<string, any>
  scope?: 'global' | 'organisation' | 'sector' | 'user'
  rollout_percentage?: number
}

// Hook types for module feature flags
export interface UseModuleFeatureFlagsResult {
  moduleFlags: Record<string, boolean>
  moduleConfigs: Record<string, Record<string, any>>
  isLoading: boolean
  error: Error | null
  enabledModules: string[]
  disabledModules: string[]
  moduleCapabilities: Record<string, string[]>
  refetch: () => void
  lastUpdated?: Date
}

export interface UseModuleDiscoveryResult {
  enabledModules: ModuleDiscoveryResponse['enabled_modules']
  disabledModules: ModuleDiscoveryResponse['disabled_modules']
  isLoading: boolean
  error: Error | null
  totalAvailable: number
  userAccessible: number
  refresh: () => void
  lastUpdated?: Date
}

export interface UseModuleFlagHierarchyResult {
  hierarchy: ModuleFlagHierarchy | null
  effectiveFlags: Record<string, boolean>
  flagConfigs: Record<string, Record<string, any>>
  isLoading: boolean
  error: Error | null
  getInheritanceChain: (flagKey: string) => ModuleFlagHierarchy['inheritance_chain']
  refetch: () => void
}

// Context types
export interface ModuleFeatureFlagContextType {
  // Module availability
  isModuleEnabled: (moduleId: string) => boolean
  getEnabledModules: () => string[]
  getModuleCapabilities: (moduleId: string) => string[]
  
  // Module-specific flags
  isModuleFlagEnabled: (moduleId: string, flagKey: string) => boolean
  getModuleFlagConfig: (moduleId: string, flagKey: string) => Record<string, any> | null
  
  // Capability checks
  hasModuleCapability: (moduleId: string, capability: string) => boolean
  getCapabilityConfig: (moduleId: string, capability: string) => Record<string, any> | null
  
  // Hierarchy navigation
  getEffectiveFlags: (moduleId: string) => Record<string, boolean>
  getFlagSource: (moduleId: string, flagKey: string) => 'global' | 'module' | 'feature' | 'capability' | null
  
  // Cache management
  invalidateModule: (moduleId: string) => void
  refreshModuleDiscovery: () => void
  
  // State
  isDiscovering: boolean
  discoveryError?: Error
  lastDiscovery?: Date
}

// Configuration types
export interface ModuleFeatureFlagOptions {
  // Module filtering
  includeDisabled?: boolean
  moduleTypes?: string[]
  categories?: string[]
  
  // Flag filtering
  requiredFlagsOnly?: boolean
  includeInherited?: boolean
  hierarchyDepth?: number
  
  // Caching
  cacheTime?: number
  staleTime?: number
  refetchInterval?: number | false
  
  // Performance
  preloadCapabilities?: boolean
  batchSize?: number
}

// Error types
export class ModuleFeatureFlagError extends Error {
  constructor(
    message: string,
    public readonly moduleId?: string,
    public readonly flagKeys?: string[],
    public readonly statusCode?: number
  ) {
    super(message)
    this.name = 'ModuleFeatureFlagError'
  }
}

// Event types for real-time updates
export interface ModuleFeatureFlagUpdateEvent {
  type: 'module_enabled' | 'module_disabled' | 'module_configured' | 'flags_updated' | 'capabilities_changed'
  module_id: string
  affected_flags?: string[]
  affected_capabilities?: string[]
  previous_state?: Record<string, any>
  new_state: Record<string, any>
  timestamp: string
  user_id?: string
  organisation_id?: string
}

// Administrative types
export interface ModuleFlagTemplate {
  module_id: string
  template_version: string
  flags: Array<{
    flag_key: string
    name: string
    description: string
    hierarchy_level: 'global' | 'module' | 'feature' | 'capability'
    is_required: boolean
    default_enabled: boolean
    default_config: Record<string, any>
    scope_recommendations: string[]
    rollout_strategy?: 'immediate' | 'gradual' | 'user_controlled'
  }>
  capabilities: Array<{
    capability_name: string
    required_flags: string[]
    optional_flags: string[]
    config_schema: Record<string, any>
  }>
}

export interface ModuleHealthReport {
  module_id: string
  overall_health: 'healthy' | 'degraded' | 'unavailable'
  flag_health: Record<string, {
    status: 'enabled' | 'disabled' | 'error'
    last_checked: string
    error_message?: string
  }>
  dependency_health: Record<string, boolean>
  performance_metrics: {
    avg_response_time: number
    success_rate: number
    error_rate: number
    last_24h_requests: number
  }
  recommendations: Array<{
    type: 'performance' | 'reliability' | 'configuration'
    priority: 'high' | 'medium' | 'low'
    message: string
    action?: string
  }>
  last_health_check: string
}