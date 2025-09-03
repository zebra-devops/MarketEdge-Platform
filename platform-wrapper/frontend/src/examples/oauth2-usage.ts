/**
 * OAuth2 Authentication Flow Usage Examples
 * Complete implementation for Epic 1 & 2 production access
 */

import { authService } from '@/services/auth'
import { featureFlagApiService } from '@/services/feature-flag-api'
import { adminFeatureFlagService } from '@/services/admin-feature-flags'

/**
 * Example 1: Initialize authentication on app startup
 */
export async function initializeAuthentication() {
  // Check if this is an Auth0 callback
  const urlParams = new URLSearchParams(window.location.search)
  const authCode = urlParams.get('code')
  const state = urlParams.get('state')
  
  if (authCode && window.location.pathname.includes('/auth/callback')) {
    try {
      console.log('Handling Auth0 callback...')
      await authService.handleOAuth2Callback(authCode, state || undefined)
      
      // Redirect to main app after successful authentication
      window.location.href = '/dashboard'
      return
    } catch (error) {
      console.error('Authentication callback failed:', error)
      // Redirect to home page on error
      window.location.href = '/'
      return
    }
  }
  
  // Check if user needs to authenticate
  if (authService.requiresAuthentication()) {
    console.log('User not authenticated, redirecting to Auth0...')
    await authService.initiateOAuth2Login()
    return
  }
  
  console.log('User is authenticated and ready')
}

/**
 * Example 2: Access Epic 1 - Module System features
 */
export async function loadModuleFeatures() {
  try {
    // Check authentication first
    if (authService.requiresAuthentication(true)) {
      return // Will auto-redirect to Auth0
    }
    
    // Load enabled features for current user
    const enabledFeatures = await featureFlagApiService.getEnabledFeatures()
    console.log('Epic 1 - Enabled features:', enabledFeatures.enabled_features)
    
    // Check specific Epic 1 features
    const moduleSystemEnabled = await featureFlagApiService.checkFeatureFlag('module_system_enabled')
    const hierarchyControlEnabled = await featureFlagApiService.checkFeatureFlag('hierarchy_control_enabled')
    
    return {
      allFeatures: enabledFeatures.enabled_features,
      moduleSystem: moduleSystemEnabled.enabled,
      hierarchyControl: hierarchyControlEnabled.enabled
    }
    
  } catch (error) {
    console.error('Failed to load module features:', error)
    throw error
  }
}

/**
 * Example 3: Access Epic 2 - Feature Flag Control (Admin only)
 */
export async function loadFeatureFlagControl() {
  try {
    // Require admin access
    authService.requireAdminAccess()
    
    // Load all feature flags for admin management
    const adminFlags = await adminFeatureFlagService.getFeatureFlags()
    console.log('Epic 2 - Admin feature flags:', adminFlags.feature_flags)
    
    return adminFlags.feature_flags
    
  } catch (error) {
    if (error.message.includes('Admin privileges required')) {
      console.error('Epic 2 requires admin access:', error)
      alert('Admin access required for Feature Flag Control')
    } else if (error.message.includes('Authentication required')) {
      console.log('Authentication required, redirecting...')
      await authService.initiateOAuth2Login()
    } else {
      console.error('Failed to load feature flag control:', error)
    }
    throw error
  }
}

/**
 * Example 4: Create a new feature flag (Admin only)
 */
export async function createFeatureFlag(flagData: any) {
  try {
    // Require admin access
    authService.requireAdminAccess()
    
    const newFlag = await adminFeatureFlagService.createFeatureFlag({
      key: flagData.key,
      name: flagData.name,
      description: flagData.description,
      enabled: flagData.enabled || false,
      module_id: flagData.module_id,
      targeting_rules: flagData.targeting_rules || []
    })
    
    console.log('Feature flag created successfully:', newFlag)
    return newFlag
    
  } catch (error) {
    console.error('Failed to create feature flag:', error)
    throw error
  }
}

/**
 * Example 5: Complete authentication check for Epic access
 */
export async function verifyEpicAccess(): Promise<{
  authenticated: boolean
  adminAccess: boolean
  epic1Available: boolean
  epic2Available: boolean
}> {
  const authenticated = authService.isAuthenticated()
  const adminAccess = authService.isAdmin()
  
  let epic1Available = false
  let epic2Available = false
  
  if (authenticated) {
    try {
      // Test Epic 1 access (all users)
      await featureFlagApiService.getEnabledFeatures()
      epic1Available = true
    } catch (error) {
      console.warn('Epic 1 not accessible:', error)
    }
    
    if (adminAccess) {
      try {
        // Test Epic 2 access (admin only)
        await adminFeatureFlagService.getFeatureFlags()
        epic2Available = true
      } catch (error) {
        console.warn('Epic 2 not accessible:', error)
      }
    }
  }
  
  return {
    authenticated,
    adminAccess,
    epic1Available,
    epic2Available
  }
}