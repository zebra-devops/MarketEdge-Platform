'use client'

import React, { useState } from 'react'
import { 
  useFeatureFlag, 
  useFeatureFlags, 
  useAllFeatureFlags 
} from '@/hooks/useFeatureFlags'
import { 
  useFeatureFlagContext, 
  useFeatureFlagDebug,
  ConditionalFeature 
} from '@/components/providers/FeatureFlagProvider'
import { useFeatureFlagSubscription } from '@/hooks/useFeatureFlagUpdates'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

/**
 * Demo component showcasing feature flag hook system usage
 * This component demonstrates all the different ways to use feature flags
 */
export const FeatureFlagDemo: React.FC = () => {
  const [selectedFlag, setSelectedFlag] = useState('market_edge.enhanced_ui')
  const [bulkFlags] = useState(['market_edge.enhanced_ui', 'admin.advanced_controls', 'analytics.real_time'])

  // 1. Single feature flag usage
  const { 
    isEnabled: enhancedUI, 
    isLoading: enhancedUILoading, 
    error: enhancedUIError,
    config: enhancedUIConfig 
  } = useFeatureFlag('market_edge.enhanced_ui', {
    fallbackValue: false,
    staleTime: 60 * 1000, // 1 minute
  })

  // 2. Multiple feature flags usage
  const {
    flags: bulkFlagResults,
    isLoading: bulkFlagsLoading,
    configs: bulkFlagConfigs
  } = useFeatureFlags(bulkFlags, {
    fallbackValues: {
      'market_edge.enhanced_ui': true,
      'admin.advanced_controls': false,
      'analytics.real_time': false,
    }
  })

  // 3. All enabled features
  const { 
    allFlags, 
    isLoading: allFlagsLoading 
  } = useAllFeatureFlags()

  // 4. Context usage
  const featureFlagContext = useFeatureFlagContext()

  // 5. Debug utilities
  const { debugInfo, logDebugInfo } = useFeatureFlagDebug()

  // 6. Real-time subscription
  useFeatureFlagSubscription(
    'market_edge.enhanced_ui',
    (event) => {
      console.log('Feature flag updated:', event)
    }
  )

  const handleTestFlag = (flagKey: string) => {
    setSelectedFlag(flagKey)
  }

  return (
    <div className="p-6 space-y-8">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Feature Flag Hook System Demo</h2>
        
        {/* Single Flag Demo */}
        <section className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">1. Single Feature Flag (useFeatureFlag)</h3>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <code className="text-sm bg-gray-200 px-2 py-1 rounded">market_edge.enhanced_ui</code>
              {enhancedUILoading ? (
                <LoadingSpinner size="sm" />
              ) : (
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  enhancedUI ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {enhancedUI ? 'Enabled' : 'Disabled'}
                </span>
              )}
            </div>
            {enhancedUIError && (
              <div className="text-red-600 text-sm mb-2">Error: {enhancedUIError.message}</div>
            )}
            {enhancedUIConfig && Object.keys(enhancedUIConfig).length > 0 && (
              <div className="text-sm text-gray-600">
                Config: <code>{JSON.stringify(enhancedUIConfig, null, 2)}</code>
              </div>
            )}
          </div>
        </section>

        {/* Bulk Flags Demo */}
        <section className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">2. Multiple Feature Flags (useFeatureFlags)</h3>
          <div className="bg-gray-50 p-4 rounded-lg">
            {bulkFlagsLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <div className="space-y-2">
                {Object.entries(bulkFlagResults).map(([flagKey, enabled]) => (
                  <div key={flagKey} className="flex items-center justify-between">
                    <code className="text-sm bg-gray-200 px-2 py-1 rounded">{flagKey}</code>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {enabled ? 'ON' : 'OFF'}
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleTestFlag(flagKey)}
                      >
                        Test
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* All Flags Demo */}
        <section className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">3. All Enabled Features (useAllFeatureFlags)</h3>
          <div className="bg-gray-50 p-4 rounded-lg">
            {allFlagsLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <div className="space-y-2">
                <div className="text-sm text-gray-600 mb-3">
                  Found {Object.keys(allFlags).length} enabled features
                </div>
                {Object.entries(allFlags).map(([flagKey, flagData]) => (
                  <div key={flagKey} className="flex items-center justify-between text-sm">
                    <div>
                      <code className="bg-gray-200 px-2 py-1 rounded">{flagKey}</code>
                      <span className="ml-2 text-gray-600">{flagData.name}</span>
                      {flagData.module_id && (
                        <span className="ml-2 text-xs text-blue-600">[{flagData.module_id}]</span>
                      )}
                    </div>
                    <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-800">
                      ENABLED
                    </span>
                  </div>
                ))}
                {Object.keys(allFlags).length === 0 && (
                  <div className="text-sm text-gray-500 italic">No enabled features found</div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Context Usage Demo */}
        <section className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">4. Context Usage</h3>
          <div className="bg-gray-50 p-4 rounded-lg space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Test Flag:</label>
                <select
                  value={selectedFlag}
                  onChange={(e) => setSelectedFlag(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="market_edge.enhanced_ui">market_edge.enhanced_ui</option>
                  <option value="admin.advanced_controls">admin.advanced_controls</option>
                  <option value="analytics.real_time">analytics.real_time</option>
                  <option value="nonexistent.flag">nonexistent.flag</option>
                </select>
              </div>
              <div className="flex items-end">
                <Button onClick={() => featureFlagContext.invalidateFlag(selectedFlag)}>
                  Invalidate Cache
                </Button>
              </div>
            </div>
            
            <div className="text-sm space-y-1">
              <div>
                <strong>isFeatureEnabled({selectedFlag}):</strong>{' '}
                <span className={featureFlagContext.isFeatureEnabled(selectedFlag) ? 'text-green-600' : 'text-red-600'}>
                  {featureFlagContext.isFeatureEnabled(selectedFlag).toString()}
                </span>
              </div>
              <div>
                <strong>areAnyFeaturesEnabled([enhanced_ui, advanced_controls]):</strong>{' '}
                <span className="text-blue-600">
                  {featureFlagContext.areAnyFeaturesEnabled(['market_edge.enhanced_ui', 'admin.advanced_controls']).toString()}
                </span>
              </div>
              <div>
                <strong>Enabled Features:</strong>{' '}
                <span className="text-gray-600">[{featureFlagContext.getEnabledFeatures().join(', ')}]</span>
              </div>
            </div>
          </div>
        </section>

        {/* Conditional Rendering Demo */}
        <section className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">5. Conditional Rendering</h3>
          <div className="space-y-4">
            <ConditionalFeature
              flag="market_edge.enhanced_ui"
              fallback={<div className="p-3 bg-gray-100 rounded">Enhanced UI is disabled</div>}
            >
              <div className="p-3 bg-blue-100 text-blue-800 rounded">
                🎨 Enhanced UI is enabled! This content only shows when the flag is on.
              </div>
            </ConditionalFeature>

            <ConditionalFeature
              flag="admin.advanced_controls"
              requireAny={['market_edge.enhanced_ui']}
              fallback={<div className="p-3 bg-yellow-100 text-yellow-800 rounded">Advanced controls require enhanced UI</div>}
            >
              <div className="p-3 bg-green-100 text-green-800 rounded">
                ⚙️ Advanced controls are available!
              </div>
            </ConditionalFeature>
          </div>
        </section>

        {/* Debug Info */}
        <section>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">6. Debug Information</h3>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-gray-600">
                Total: {debugInfo.totalFlags} | Enabled: {debugInfo.enabledCount}
              </div>
              <Button size="sm" onClick={logDebugInfo}>
                Log Debug Info
              </Button>
            </div>
            <details className="text-sm">
              <summary className="cursor-pointer font-medium text-gray-700">Show Flag Details</summary>
              <div className="mt-2 space-y-1">
                {debugInfo.flagDetails.map((flag) => (
                  <div key={flag.flagKey} className="flex justify-between py-1">
                    <code className="text-xs">{flag.flagKey}</code>
                    <span className={`text-xs ${flag.enabled ? 'text-green-600' : 'text-red-600'}`}>
                      {flag.enabled ? 'ON' : 'OFF'}
                    </span>
                  </div>
                ))}
              </div>
            </details>
          </div>
        </section>
      </div>
    </div>
  )
}

/**
 * Example usage in a real component
 */
export const ExampleFeatureFlagUsage: React.FC = () => {
  const { isEnabled: showBetaFeatures } = useFeatureFlag('beta.advanced_features')
  const { isEnabled: hasAnalytics, config: analyticsConfig } = useFeatureFlag('analytics.dashboard', {
    fallbackValue: false
  })

  return (
    <div>
      <h1>My Component</h1>
      
      {/* Simple conditional rendering */}
      {showBetaFeatures && (
        <div className="beta-banner">
          🧪 You're seeing beta features!
        </div>
      )}

      {/* Using config data */}
      {hasAnalytics && (
        <div className="analytics-section">
          <h2>Analytics Dashboard</h2>
          {analyticsConfig?.showRealTime && (
            <div>Real-time data enabled</div>
          )}
        </div>
      )}

      {/* Using ConditionalFeature component */}
      <ConditionalFeature
        flag="admin.user_management"
        fallback={<div>User management not available</div>}
      >
        <div>User management controls...</div>
      </ConditionalFeature>
    </div>
  )
}