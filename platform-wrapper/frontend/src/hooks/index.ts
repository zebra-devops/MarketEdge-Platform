// Authentication hooks
export { useAuth, useAuthContext } from './useAuth'

// Application access hooks
export { useApplicationAccess } from './useApplicationAccess'

// Route protection hooks
export { useRouteProtection } from './useRouteProtection'

// Feature flag hooks
export {
  useFeatureFlag,
  useFeatureFlags,
  useAllFeatureFlags,
  useFeatureFlagCache,
  featureFlagKeys
} from './useFeatureFlags'

export {
  useFeatureFlagUpdates,
  useFeatureFlagSubscription,
  useFeatureFlagEventEmitter
} from './useFeatureFlagUpdates'

// Module feature flag hooks
export {
  useModuleFeatureFlags,
  useModuleDiscovery,
  useModuleFlagHierarchy,
  useModuleCapabilities,
  useAccessibleModules,
  useModuleHealth,
  useModuleFeatureFlagCache,
  useModuleDashboard,
  moduleFeatureFlagKeys
} from './useModuleFeatureFlags'

export {
  useModuleFeatureFlag,
  useMultipleModuleFeatureFlags,
  useApplicationFeatureFlags,
  useApplicationAccess,
  useFeatureFlaggedRoute
} from './useModuleFeatureFlag'