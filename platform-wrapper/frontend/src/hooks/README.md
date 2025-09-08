# Feature Flag Hook System

This directory contains a comprehensive feature flag system for the MarketEdge platform, implementing US-201: Feature Flag Hook System.

## Overview

The feature flag system provides:

- **React Hooks**: Easy-to-use hooks for component-level flag evaluation
- **React Query Integration**: Automatic caching, background updates, and optimistic updates
- **TypeScript Support**: Full type safety with proper generics
- **Error Handling**: Graceful fallbacks and retry logic
- **Real-time Updates**: Subscription-based updates (polling fallback when WebSocket unavailable)
- **Local Storage Fallback**: Offline support with cached flag values
- **Context Provider**: Centralized flag management and utilities
- **Debug Tools**: Development utilities for flag inspection

## Quick Start

### 1. Setup Providers (Already done in layout.tsx)

```tsx
import { FeatureFlagProvider } from '@/components/providers/FeatureFlagProvider'

<FeatureFlagProvider
  preloadFlags={['market_edge.enhanced_ui', 'admin.advanced_controls']}
  enableRealTimeUpdates={true}
  debugMode={process.env.NODE_ENV === 'development'}
>
  <YourApp />
</FeatureFlagProvider>
```

### 2. Use Feature Flags in Components

```tsx
import { useFeatureFlag } from '@/hooks/useFeatureFlags'
import { ConditionalFeature } from '@/components/providers/FeatureFlagProvider'

function MyComponent() {
  // Single flag check
  const { isEnabled, isLoading, config } = useFeatureFlag('market_edge.enhanced_ui', {
    fallbackValue: false
  })

  if (isLoading) return <Spinner />

  return (
    <div>
      {/* Method 1: Direct conditional rendering */}
      {isEnabled && (
        <div>Enhanced UI is enabled with config: {JSON.stringify(config)}</div>
      )}

      {/* Method 2: Using ConditionalFeature component */}
      <ConditionalFeature
        flag="admin.advanced_controls"
        fallback={<div>Advanced controls not available</div>}
      >
        <AdvancedControlsPanel />
      </ConditionalFeature>
    </div>
  )
}
```

## Hooks API Reference

### `useFeatureFlag(flagKey, options)`

Check a single feature flag.

**Parameters:**
- `flagKey: string` - The feature flag key
- `options: FeatureFlagOptions` - Configuration options

**Returns:** `UseFeatureFlagResult`
- `isEnabled: boolean` - Whether the flag is enabled
- `isLoading: boolean` - Loading state
- `error: Error | null` - Any errors
- `config: Record<string, any> | null` - Flag configuration
- `refetch: () => void` - Manual refetch function
- `lastUpdated?: Date` - Last update timestamp

**Example:**
```tsx
const { isEnabled, config, isLoading } = useFeatureFlag('analytics.real_time', {
  fallbackValue: false,
  staleTime: 60 * 1000, // 1 minute
  cacheTime: 5 * 60 * 1000, // 5 minutes
})
```

### `useFeatureFlags(flagKeys, options)`

Check multiple feature flags efficiently.

**Parameters:**
- `flagKeys: string[]` - Array of feature flag keys
- `options: FeatureFlagsOptions` - Configuration options

**Returns:** `UseFeatureFlagsResult`
- `flags: Record<string, boolean>` - Flag states by key
- `isLoading: boolean` - Loading state
- `error: Error | null` - Any errors
- `configs: Record<string, Record<string, any>>` - Flag configurations by key
- `refetch: () => void` - Manual refetch function

**Example:**
```tsx
const { flags, configs } = useFeatureFlags(
  ['admin.user_management', 'admin.audit_logs', 'admin.security_controls'],
  {
    fallbackValues: {
      'admin.user_management': false,
      'admin.audit_logs': true,
      'admin.security_controls': false,
    }
  }
)

// Usage
if (flags['admin.user_management']) {
  // Show user management UI
}
```

### `useAllFeatureFlags(moduleId?, options)`

Get all enabled features for the current user.

**Parameters:**
- `moduleId?: string` - Optional module filter
- `options: Omit<FeatureFlagOptions, 'fallbackValue'>` - Configuration options

**Returns:** `UseAllFeatureFlagsResult`
- `allFlags: Record<string, FeatureFlagData>` - All enabled flags with metadata
- `isLoading: boolean` - Loading state
- `error: Error | null` - Any errors
- `refetch: () => void` - Manual refetch function

**Example:**
```tsx
const { allFlags } = useAllFeatureFlags('market_edge')

// Get all enabled market-edge specific features
const marketEdgeFeatures = Object.keys(allFlags)
```

### `useFeatureFlagUpdates()`

Subscribe to real-time feature flag updates.

**Returns:** `UseFeatureFlagUpdatesResult`
- `subscribe: (flagKeys) => unsubscribeFn` - Subscribe to flag updates
- `unsubscribe: (flagKeys) => void` - Unsubscribe from flag updates
- `isConnected: boolean` - Connection status
- `lastEvent?: FeatureFlagUpdateEvent` - Last received update

**Example:**
```tsx
const updates = useFeatureFlagUpdates()

useEffect(() => {
  const unsubscribe = updates.subscribe(['market_edge.enhanced_ui'])
  return unsubscribe
}, [])
```

### `useFeatureFlagSubscription(flagKeys, onUpdate)`

Simplified subscription hook with automatic cleanup.

**Parameters:**
- `flagKeys: string | string[]` - Flags to subscribe to
- `onUpdate?: (event) => void` - Update callback

**Example:**
```tsx
useFeatureFlagSubscription('admin.advanced_controls', (event) => {
  console.log('Flag updated:', event.flagKey)
  // Handle flag update
})
```

### `useFeatureFlagContext()`

Access the feature flag context for advanced operations.

**Returns:** `FeatureFlagContextType`
- `isFeatureEnabled: (flagKey) => boolean` - Check if flag is enabled
- `getFeatureConfig: (flagKey) => object | null` - Get flag configuration
- `areAnyFeaturesEnabled: (flagKeys) => boolean` - Check if any flags are enabled
- `areAllFeaturesEnabled: (flagKeys) => boolean` - Check if all flags are enabled
- `getEnabledFeatures: () => string[]` - Get all enabled feature keys
- `invalidateFlag: (flagKey) => void` - Invalidate flag cache
- `invalidateAllFlags: () => void` - Invalidate all flag caches
- `preloadFlags: (flagKeys) => void` - Preload flags for performance

## Components

### `ConditionalFeature`

Component for conditional rendering based on feature flags.

**Props:**
- `flag: string` - Primary flag key
- `requireAll?: string[]` - All these flags must be enabled
- `requireAny?: string[]` - At least one of these flags must be enabled
- `fallback?: ReactNode` - Fallback content when conditions not met
- `children: ReactNode` - Content to show when conditions are met

**Example:**
```tsx
<ConditionalFeature
  flag="admin.user_management"
  requireAny={['admin.advanced_controls']}
  fallback={<div>Feature not available</div>}
>
  <UserManagementPanel />
</ConditionalFeature>
```

### `withFeatureFlags(Component, flagKeys?)`

HOC for components that need feature flag access.

**Example:**
```tsx
const EnhancedComponent = withFeatureFlags(MyComponent, [
  'market_edge.enhanced_ui',
  'admin.advanced_controls'
])
```

## Configuration Options

### FeatureFlagOptions

```typescript
interface FeatureFlagOptions {
  fallbackValue?: boolean          // Default: false
  cacheTime?: number              // Default: 5 minutes
  staleTime?: number              // Default: 2 minutes
  refetchInterval?: number | false // Default: false
  refetchOnWindowFocus?: boolean  // Default: true
  retryCount?: number             // Default: 2
  enabled?: boolean               // Default: true
}
```

### FeatureFlagsOptions

```typescript
interface FeatureFlagsOptions extends FeatureFlagOptions {
  fallbackValues?: Record<string, boolean> // Fallback values per flag
}
```

## Error Handling

The system provides robust error handling:

1. **Network Errors**: Automatic retry with exponential backoff
2. **Authentication Errors**: Graceful fallback to cached values
3. **Missing Flags**: Uses fallback values instead of throwing
4. **Rate Limiting**: Respects API rate limits with proper backoff

## Performance Optimizations

1. **Request Deduplication**: Multiple components using the same flag share requests
2. **Stale-While-Revalidate**: Shows cached data while fetching updates
3. **Background Refetching**: Keeps data fresh automatically
4. **Local Storage Fallback**: Offline support with cached values
5. **Batch Requests**: Multiple flags fetched efficiently

## Best Practices

### 1. Use Descriptive Flag Keys

```tsx
// Good
useFeatureFlag('market_edge.enhanced_competitor_analysis')

// Avoid
useFeatureFlag('feature1')
```

### 2. Provide Meaningful Fallbacks

```tsx
// Good
useFeatureFlag('admin.advanced_controls', { fallbackValue: false })

// Consider the user experience if the flag service is down
```

### 3. Handle Loading States

```tsx
const { isEnabled, isLoading } = useFeatureFlag('my.flag')

if (isLoading) {
  return <Skeleton />
}

return isEnabled ? <Feature /> : <Fallback />
```

### 4. Use Bulk Requests When Possible

```tsx
// Good - Single request for multiple flags
const { flags } = useFeatureFlags(['flag1', 'flag2', 'flag3'])

// Avoid - Multiple separate requests
const flag1 = useFeatureFlag('flag1')
const flag2 = useFeatureFlag('flag2')
const flag3 = useFeatureFlag('flag3')
```

### 5. Leverage Configuration

```tsx
const { config } = useFeatureFlag('analytics.dashboard')

// Use config for feature customization
const refreshInterval = config?.refreshInterval || 5000
const showRealTime = config?.realTimeEnabled || false
```

## Development and Debugging

### Debug Mode

Set `debugMode={true}` in FeatureFlagProvider to enable:
- Console logging of flag evaluations
- Performance metrics
- Cache hit/miss statistics
- Real-time update events

### Debug Hook

```tsx
import { useFeatureFlagDebug } from '@/components/providers/FeatureFlagProvider'

const { debugInfo, logDebugInfo } = useFeatureFlagDebug()

// Log comprehensive debug information
logDebugInfo()

// Access debug data
console.log('Total flags:', debugInfo.totalFlags)
console.log('Enabled flags:', debugInfo.enabledFlags)
```

### Testing

The hooks are fully testable with React Testing Library:

```tsx
import { renderHook } from '@testing-library/react'
import { useFeatureFlag } from '@/hooks/useFeatureFlags'

test('should return flag state', async () => {
  const { result } = renderHook(() => useFeatureFlag('test.flag'))
  
  await waitFor(() => {
    expect(result.current.isLoading).toBe(false)
  })
  
  expect(result.current.isEnabled).toBe(true)
})
```

## Migration Guide

### From Direct API Calls

```tsx
// Before
const [isEnabled, setIsEnabled] = useState(false)

useEffect(() => {
  apiService.get('/features/my.flag').then(response => {
    setIsEnabled(response.enabled)
  })
}, [])

// After
const { isEnabled } = useFeatureFlag('my.flag')
```

### From Context-Only Approach

```tsx
// Before
const featureFlags = useContext(FeatureFlagContext)
const isEnabled = featureFlags['my.flag'] || false

// After
const { isEnabled } = useFeatureFlag('my.flag', { fallbackValue: false })
```

## Troubleshooting

### Common Issues

1. **"useFeatureFlagContext must be used within a FeatureFlagProvider"**
   - Ensure FeatureFlagProvider wraps your component tree

2. **Flags always return fallback values**
   - Check authentication state
   - Verify API endpoints are accessible
   - Check network connectivity

3. **Performance issues with many flags**
   - Use `useFeatureFlags()` for bulk requests
   - Consider preloading frequently used flags
   - Increase cache time for stable flags

4. **Real-time updates not working**
   - Currently uses polling fallback
   - Check `enableRealTimeUpdates` prop
   - Verify network stability

### Debug Steps

1. Enable debug mode in FeatureFlagProvider
2. Check browser network tab for API calls
3. Inspect React Query DevTools for cache state
4. Use `useFeatureFlagDebug()` for detailed information
5. Check localStorage for cached flag values

## Future Enhancements

- WebSocket/SSE integration for true real-time updates
- A/B testing capabilities with automatic metrics collection
- Flag dependency management
- Gradual rollout controls
- Integration with analytics platforms
- Feature flag analytics dashboard