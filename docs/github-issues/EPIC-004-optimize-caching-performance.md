# Epic: Optimize Caching and Performance

**Labels:** `epic`, `enhancement`, `frontend`, `react-query`, `performance`, `priority-3`
**Milestone:** Q1 2025 - React Query Standardization
**Parent Epic:** #1 (Standardize Data Fetching with TanStack Query)
**Priority:** P3 - Medium
**Story Points:** 26
**Timeline:** Weeks 5-6

---

## Epic Overview

**Business Value:**
Implement advanced React Query features to maximize performance benefits: smart caching strategies, prefetching, offline support, and suspense boundaries. This will reduce server load, improve user experience, and enable offline functionality for critical features.

**User Impact:**
- **All Users:** Instant navigation with prefetched data, offline access to cached data
- **Admin Users:** Faster workflows with intelligent cache warming
- **Developers:** Clear caching strategies, better debugging with React Query DevTools
- **Infrastructure:** Reduced server load (60% fewer API calls)

**Current State:**
- Basic React Query caching (5min default)
- No prefetching strategies
- No offline persistence
- No cache warming for common paths
- Generic cache times for all data types

**Target State:**
- Data-type-specific cache strategies
- Prefetching on hover/navigation
- Offline support with localStorage persistence
- Suspense boundaries for better loading UX
- Optimized cache invalidation

---

## Stories in this Epic

### Phase 1: Smart Caching (Week 5)
- [ ] Story #22: Implement query key factory patterns for all domains - 5 points
- [ ] Story #23: Configure data-type-specific cache strategies - 5 points
- [ ] Story #24: Implement smart cache invalidation strategies - 3 points

### Phase 2: Prefetching & Loading (Week 5-6)
- [ ] Story #25: Add prefetching for navigation and common paths - 5 points
- [ ] Story #26: Implement suspense boundaries for loading states - 3 points

### Phase 3: Offline & Persistence (Week 6)
- [ ] Story #27: Configure cache persistence with localStorage - 3 points
- [ ] Story #28: Add offline support for critical data - 3 points

### Developer Experience (Week 6)
- [ ] Story #29: Integrate React Query DevTools for development - 2 points

**Total Story Points:** 29

---

## Success Metrics

**Performance:**
- 60% reduction in API call volume (target: 15 calls → 6 calls per session)
- 300-500ms faster navigation (cached data loads instantly)
- 80% of navigation uses prefetched data
- Zero unnecessary refetches during navigation

**User Experience:**
- Instant page transitions for cached routes
- Graceful offline experience for previously loaded data
- Smooth loading transitions with suspense
- No loading spinners for cached data

**Technical:**
- Cache hit rate > 80% for navigation
- Memory usage < 10MB for query cache
- Offline data persists across browser sessions
- Cache invalidation triggers only when necessary

---

## Acceptance Criteria for Epic Completion

### Smart Caching Requirements
- [ ] Query key factory implemented for all data domains (users, organizations, stats, etc.)
- [ ] Data-type-specific cache times configured (static data: infinite, real-time: 0)
- [ ] Cache invalidation strategies documented and implemented
- [ ] No duplicate queries during navigation
- [ ] Cache size monitored and kept under 10MB

### Prefetching Requirements
- [ ] Hover prefetching implemented for navigation links
- [ ] Next-page prefetching for paginated lists
- [ ] Common navigation paths prefetched on login
- [ ] Prefetch triggered 200ms after hover
- [ ] Prefetched data cached appropriately

### Offline Support Requirements
- [ ] Critical queries persist to localStorage
- [ ] Offline fallback displays cached data
- [ ] Network status detected and displayed to user
- [ ] Background sync on reconnection
- [ ] Stale data indicators when offline

### Loading State Requirements
- [ ] Suspense boundaries for loading states
- [ ] Skeleton loaders for predictable content
- [ ] Error boundaries for failed queries
- [ ] Loading states don't flash for cached data
- [ ] Graceful degradation for slow networks

### Developer Experience Requirements
- [ ] React Query DevTools available in development
- [ ] Cache inspection tools documented
- [ ] Query debugging guide created
- [ ] Performance monitoring dashboard
- [ ] Cache metrics logged in development

---

## Definition of Done

- [ ] All 8 stories completed and merged
- [ ] Code reviewed and approved
- [ ] Performance benchmarks met and verified
- [ ] All tests passing
- [ ] Documentation updated
- [ ] DevTools integrated and documented
- [ ] Deployed to staging and verified
- [ ] Cache behavior verified in production
- [ ] No performance regressions
- [ ] User feedback collected

---

## Technical Implementation Plan

### 1. Query Key Factory Pattern

```typescript
// Comprehensive query key factory for all domains
export const queryKeys = {
  // Users
  users: {
    all: ['users'] as const,
    lists: () => [...queryKeys.users.all, 'list'] as const,
    list: (filters: string) => [...queryKeys.users.lists(), { filters }] as const,
    details: () => [...queryKeys.users.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.users.details(), id] as const,
  },

  // Organizations
  organizations: {
    all: ['organizations'] as const,
    lists: () => [...queryKeys.organizations.all, 'list'] as const,
    list: (filters: string) => [...queryKeys.organizations.lists(), { filters }] as const,
    details: () => [...queryKeys.organizations.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.organizations.details(), id] as const,
  },

  // Admin Stats
  adminStats: {
    all: ['admin', 'stats'] as const,
    dashboard: () => [...queryKeys.adminStats.all, 'dashboard'] as const,
  },

  // Feature Flags (already exists)
  featureFlags: {
    all: ['feature-flags'] as const,
    single: (key: string) => [...queryKeys.featureFlags.all, key] as const,
  },
}
```

### 2. Data-Type-Specific Cache Configuration

```typescript
// Cache configuration by data type
export const CACHE_CONFIG = {
  // Static reference data (rarely changes)
  static: {
    staleTime: Infinity,
    cacheTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  },

  // User/org data (changes occasionally)
  userManagement: {
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
    refetchOnMount: false,
    refetchOnWindowFocus: true,
  },

  // Dashboard stats (changes frequently)
  stats: {
    staleTime: 30 * 1000, // 30 seconds
    cacheTime: 5 * 60 * 1000, // 5 minutes
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  },

  // Real-time data (always fresh)
  realtime: {
    staleTime: 0,
    cacheTime: 60 * 1000, // 1 minute
    refetchInterval: 10 * 1000, // Poll every 10 seconds
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  },
}

// Usage
export function useAdminStats() {
  return useQuery({
    queryKey: queryKeys.adminStats.dashboard(),
    queryFn: () => apiService.get('/admin/dashboard/stats'),
    ...CACHE_CONFIG.stats,
  })
}
```

### 3. Prefetching Strategy

```typescript
// Prefetch on hover
export function NavigationLink({ href, children }: Props) {
  const queryClient = useQueryClient()

  const prefetchData = () => {
    // Prefetch based on route
    if (href === '/admin/users') {
      queryClient.prefetchQuery(
        queryKeys.users.lists(),
        () => apiService.get('/users')
      )
    } else if (href === '/admin/organizations') {
      queryClient.prefetchQuery(
        queryKeys.organizations.lists(),
        () => apiService.get('/organizations')
      )
    }
  }

  return (
    <Link
      href={href}
      onMouseEnter={prefetchData}
      onTouchStart={prefetchData}
    >
      {children}
    </Link>
  )
}

// Prefetch common paths on login
export function usePrefetchCommonData() {
  const queryClient = useQueryClient()
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    if (isAuthenticated) {
      // Prefetch dashboard data
      queryClient.prefetchQuery(
        queryKeys.adminStats.dashboard(),
        () => apiService.get('/admin/dashboard/stats')
      )

      // Prefetch user's organizations
      queryClient.prefetchQuery(
        queryKeys.organizations.lists(),
        () => apiService.get('/organizations')
      )
    }
  }, [isAuthenticated, queryClient])
}
```

### 4. Cache Persistence

```typescript
// Persist cache to localStorage
import { persistQueryClient } from '@tanstack/react-query-persist-client'
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister'

const localStoragePersister = createSyncStoragePersister({
  storage: window.localStorage,
  key: 'MARKETEDGE_QUERY_CACHE',
})

// In QueryProvider
persistQueryClient({
  queryClient,
  persister: localStoragePersister,
  maxAge: 1000 * 60 * 60 * 24, // 24 hours
  dehydrateOptions: {
    shouldDehydrateQuery: (query) => {
      // Only persist specific queries
      const queryKey = query.queryKey[0]
      return ['feature-flags', 'organizations', 'users'].includes(queryKey as string)
    },
  },
})
```

### 5. Suspense Boundaries

```typescript
// App-level suspense
export function AdminPanel() {
  return (
    <Suspense fallback={<AdminPanelSkeleton />}>
      <AdminPanelContent />
    </Suspense>
  )
}

// Component-level suspense with queries
export function AdminPanelContent() {
  const { data: stats } = useAdminStats({
    suspense: true, // Triggers suspense boundary
  })

  // No need for loading state - suspense handles it
  return <StatsDisplay stats={stats} />
}
```

---

## Files to Modify/Create

### New Files
- `/src/utils/queryKeys.ts` - Centralized query key factory
- `/src/utils/cacheConfig.ts` - Cache configuration by data type
- `/src/components/shared/PrefetchLink.tsx` - Prefetching navigation component
- `/src/hooks/usePrefetchCommonData.ts` - Common data prefetching hook
- `/src/utils/queryPersistence.ts` - localStorage persistence setup

### Modified Files
- `/src/components/providers/QueryProvider.tsx` - Add persistence, DevTools
- All query hooks - Apply cache config
- `/src/components/layout/Navigation.tsx` - Use PrefetchLink
- `/src/app/admin/layout.tsx` - Add suspense boundaries

### Documentation
- `/docs/QUERY_CACHING_STRATEGY.md` - Cache strategy documentation
- `/docs/DEVELOPER_GUIDE.md` - Update with caching patterns

---

## Dependencies

**Depends On:**
- Epic #2 (Admin Panel Migration) - Query hooks must exist ✅
- Epic #3 (Mutations) - Mutations enable cache invalidation ✅

**Requires Installation:**
- `@tanstack/react-query-persist-client`
- `@tanstack/query-sync-storage-persister`
- `@tanstack/react-query-devtools`

---

## Risk Assessment

**Technical Risks:**
- **Low:** Over-caching stale data - Mitigated by appropriate stale times
- **Low:** localStorage quota exceeded - Mitigated by selective persistence
- **Low:** Cache synchronization across tabs - Mitigated by broadcast channel

**User Experience Risks:**
- **Low:** Stale data displayed offline - Mitigated by staleness indicators
- **Low:** Confusing loading states - Mitigated by consistent UX patterns

**Mitigation Strategy:**
- Conservative cache times initially
- Monitor cache size and performance
- User feedback for offline experience
- Clear staleness indicators

---

## Performance Benchmarks

### Current State (After Epic #2)
- API calls per session: ~15 (60% reduction from baseline)
- Navigation speed: Instant for cached, 300-500ms for uncached
- Cache hit rate: ~50%
- Offline support: None

### Target State (After Epic #4)
- API calls per session: ~6 (60% reduction from Epic #2, 84% from baseline)
- Navigation speed: Instant for 80% of navigations
- Cache hit rate: >80%
- Offline support: Critical data available offline

### Metrics to Track
- Cache hit/miss ratio
- API call volume (per session, per user)
- Navigation timing (LCP, FCP)
- Memory usage (query cache size)
- localStorage usage
- Prefetch success rate

---

## Testing Strategy

### Cache Testing
```typescript
describe('Query caching', () => {
  it('uses cached data for navigation', async () => {
    // Load users page
    render(<UserManagement />)
    await waitFor(() => expect(screen.getByText('User List')).toBeInTheDocument())

    // Navigate away
    router.push('/admin/dashboard')

    // Navigate back - should use cache
    router.push('/admin/users')

    // Verify no new API call
    expect(apiService.get).toHaveBeenCalledTimes(1) // Only initial call
  })

  it('invalidates cache after mutation', async () => {
    // Load users
    const { rerender } = render(<UserManagement />)

    // Create user
    await userEvent.click(screen.getByText('Create User'))
    await userEvent.click(screen.getByText('Submit'))

    // Verify refetch triggered
    await waitFor(() => {
      expect(apiService.get).toHaveBeenCalledWith('/users')
    })
  })
})
```

### Prefetching Testing
```typescript
describe('Prefetching', () => {
  it('prefetches data on hover', async () => {
    render(<Navigation />)

    // Hover over link
    await userEvent.hover(screen.getByText('Users'))

    // Wait for prefetch
    await waitFor(() => {
      expect(queryClient.getQueryData(queryKeys.users.lists())).toBeDefined()
    })
  })
})
```

### Offline Testing
```typescript
describe('Offline support', () => {
  it('displays cached data when offline', async () => {
    // Load data while online
    render(<UserManagement />)
    await waitFor(() => expect(screen.getByText('User List')).toBeInTheDocument())

    // Go offline
    window.dispatchEvent(new Event('offline'))

    // Reload page
    rerender(<UserManagement />)

    // Verify cached data displayed
    expect(screen.getByText('User List')).toBeInTheDocument()
    expect(screen.getByText('Offline - showing cached data')).toBeInTheDocument()
  })
})
```

---

## Rollout Plan

**Week 5:**
- Day 1-2: Implement query key factory and cache config (Stories #22, #23)
- Day 3: Implement smart invalidation (Story #24)
- Day 4-5: Add prefetching (Story #25)

**Week 6:**
- Day 1: Implement suspense boundaries (Story #26)
- Day 2: Add cache persistence (Story #27)
- Day 3: Add offline support (Story #28)
- Day 4: Integrate DevTools (Story #29)
- Day 5: Testing and documentation

**Week 7:**
- Day 1-2: Staging deployment and testing
- Day 3: Production deployment
- Day 4-5: Monitor performance metrics

---

## Monitoring & Metrics

### Performance Dashboard
Track in production:
- API call volume (trend over time)
- Cache hit/miss ratio
- Average navigation speed
- Query cache memory usage
- localStorage usage
- Prefetch success rate

### Alerts
- Cache hit rate drops below 70%
- API call volume increases >20%
- localStorage quota exceeded
- Query cache memory >15MB

### User Feedback
- Perceived performance improvement
- Offline experience satisfaction
- Loading state feedback

---

## React Query DevTools

```typescript
// Add to QueryProvider in development
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

export function QueryProvider({ children }: Props) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools
          initialIsOpen={false}
          position="bottom-right"
          toggleButtonProps={{ style: { marginBottom: '3rem' } }}
        />
      )}
    </QueryClientProvider>
  )
}
```

**DevTools Features:**
- Query inspection (active, stale, inactive)
- Cache explorer
- Query timeline
- Network activity
- Manual refetch/invalidation
- Cache size monitoring

---

## Reference Documentation

**TanStack Query Docs:**
- Prefetching: https://tanstack.com/query/latest/docs/react/guides/prefetching
- Caching: https://tanstack.com/query/latest/docs/react/guides/caching
- Persistence: https://tanstack.com/query/latest/docs/react/plugins/persistQueryClient
- DevTools: https://tanstack.com/query/latest/docs/react/devtools

**Best Practices:**
- Feature flags implementation (`/src/hooks/useFeatureFlags.ts`)
- Current QueryProvider (`/src/components/providers/QueryProvider.tsx`)

---

## Comments

This epic represents the "polish" phase of React Query migration. While Epics #2 and #3 provide the core functionality, Epic #4 maximizes performance and user experience benefits. The caching optimizations will reduce server costs and improve scalability, making this a high-ROI investment.

**Long-term Benefits:**
- Reduced infrastructure costs (fewer API calls)
- Better user experience (faster, offline-capable)
- Improved developer productivity (DevTools, clear patterns)
- Foundation for future features (real-time updates, background sync)
