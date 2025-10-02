# Story: Create useAdminStats Query Hook

**Labels:** `user-story`, `enhancement`, `frontend`, `react-query`, `admin`, `priority-1`
**Milestone:** Q1 2025 - React Query Standardization
**Parent Epic:** #2 (Admin Panel Query Migration)
**Story Points:** 3
**Complexity:** Simple
**Agent Path:** dev → cr

---

## User Story

**As a** developer building admin features
**I want** a reusable `useAdminStats()` query hook
**So that** I can fetch admin dashboard statistics with automatic caching and loading states

---

## Acceptance Criteria

### Functional Requirements
- [ ] Given I call `useAdminStats()`, when the component mounts, then it fetches `/admin/dashboard/stats`
- [ ] Given the data is cached, when I navigate back to the admin page, then it uses cached data instead of refetching
- [ ] Given the data is stale (>30s), when I refocus the window, then it refetches in the background
- [ ] Given the API fails, when I retry, then it attempts the request up to 2 times
- [ ] Given I'm not authenticated, when the hook runs, then it doesn't make API calls

### Technical Requirements
- [ ] Hook exports query states: `data`, `isLoading`, `error`, `refetch`, `isSuccess`
- [ ] Query key factory created: `adminStatsKeys`
- [ ] Cache configuration: `staleTime: 30_000` (30 seconds), `cacheTime: 5 * 60 * 1000` (5 minutes)
- [ ] TypeScript types defined for `AdminStatsData` response
- [ ] Hook properly handles authentication state
- [ ] Retry configuration: `retry: 2`

### Code Quality Requirements
- [ ] TypeScript with no `any` types
- [ ] JSDoc comments for hook and types
- [ ] Follows existing pattern from `useFeatureFlags.ts`
- [ ] ESLint and Prettier pass

---

## Definition of Done

- [ ] Code written and committed
- [ ] Unit tests written and passing
- [ ] TypeScript types exported
- [ ] Code reviewed and approved
- [ ] Merged to main branch
- [ ] No regressions in existing admin dashboard

---

## Technical Implementation

### File Location
`/src/hooks/api/useAdminStats.ts`

### Implementation Example

```typescript
import { useQuery, UseQueryOptions } from 'react-query'
import { apiService } from '@/services/api'
import { useAuth } from '@/hooks/useAuth'

/**
 * Admin dashboard statistics response
 */
export interface AdminStatsData {
  totalUsers: number
  totalOrganizations: number
  activeUsers: number
  totalApplications: number
  recentActivity: Array<{
    id: string
    type: string
    timestamp: string
    user: string
  }>
}

/**
 * Query keys for admin stats
 */
export const adminStatsKeys = {
  all: ['admin', 'stats'] as const,
  dashboard: () => [...adminStatsKeys.all, 'dashboard'] as const,
}

/**
 * Fetch admin dashboard statistics
 *
 * @example
 * const { data, isLoading, error } = useAdminStats()
 *
 * @returns Query result with admin stats data
 */
export function useAdminStats(
  options?: Omit<UseQueryOptions<AdminStatsData>, 'queryKey' | 'queryFn'>
) {
  const { isAuthenticated } = useAuth()

  return useQuery<AdminStatsData>({
    queryKey: adminStatsKeys.dashboard(),
    queryFn: () => apiService.get<AdminStatsData>('/admin/dashboard/stats'),
    enabled: isAuthenticated,
    staleTime: 30_000, // 30 seconds - stats change frequently
    cacheTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
    ...options,
  })
}
```

### Unit Tests

```typescript
// __tests__/hooks/useAdminStats.test.tsx
import { renderHook, waitFor } from '@testing-library/react'
import { useAdminStats } from '@/hooks/api/useAdminStats'
import { createQueryWrapper } from '@/test-utils/queryWrapper'
import { apiService } from '@/services/api'

jest.mock('@/services/api')
jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: true }),
}))

describe('useAdminStats', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('fetches admin stats successfully', async () => {
    const mockStats = {
      totalUsers: 100,
      totalOrganizations: 20,
      activeUsers: 75,
      totalApplications: 5,
      recentActivity: [],
    }

    ;(apiService.get as jest.Mock).mockResolvedValue(mockStats)

    const { result } = renderHook(() => useAdminStats(), {
      wrapper: createQueryWrapper(),
    })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockStats)
    expect(apiService.get).toHaveBeenCalledWith('/admin/dashboard/stats')
  })

  it('handles errors gracefully', async () => {
    const error = new Error('Failed to fetch stats')
    ;(apiService.get as jest.Mock).mockRejectedValue(error)

    const { result } = renderHook(() => useAdminStats(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toEqual(error)
  })

  it('retries on failure', async () => {
    ;(apiService.get as jest.Mock)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ totalUsers: 100 })

    const { result } = renderHook(() => useAdminStats(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Called 3 times total (initial + 2 retries)
    expect(apiService.get).toHaveBeenCalledTimes(3)
  })
})
```

---

## Dependencies

**Depends On:**
- QueryProvider configured ✅
- apiService infrastructure ✅
- Auth hook available ✅

**Blocks:**
- Story #9 (Migrate AdminStats component)

---

## Test Scenarios

### Scenario 1: First Load
1. User navigates to admin dashboard
2. `useAdminStats()` called
3. Loading spinner displays
4. API request sent to `/admin/dashboard/stats`
5. Data returned and cached
6. Stats displayed

### Scenario 2: Cached Load
1. User navigated to admin dashboard previously
2. User navigates away then back
3. `useAdminStats()` called
4. Cached data displayed immediately (no spinner)
5. Background refetch if data is stale (>30s)

### Scenario 3: Error Handling
1. User navigates to admin dashboard
2. API returns 500 error
3. Hook retries 2 times
4. Error state returned to component
5. Error message displayed to user

### Scenario 4: Authentication
1. User is not authenticated
2. `useAdminStats()` called with `enabled: false`
3. No API request made
4. Hook returns idle state

---

## Acceptance Testing

**Manual Test Steps:**
1. Log in as super_admin user
2. Navigate to `/admin` dashboard
3. Verify stats load and display
4. Open React Query DevTools
5. Verify query key is `['admin', 'stats', 'dashboard']`
6. Verify cache time is 5 minutes
7. Navigate away and back
8. Verify cached data used (no spinner)
9. Disconnect network
10. Refresh page
11. Verify error state displayed

**Expected Results:**
- Stats load in <500ms on first visit
- Stats load instantly (<50ms) on subsequent visits
- No console errors
- No TypeScript errors
- Query visible in DevTools

---

## Related Files

**Reference Implementation:**
- `/src/hooks/useFeatureFlags.ts` - Follow this pattern

**Files to Create:**
- `/src/hooks/api/useAdminStats.ts` - Hook implementation
- `/src/hooks/api/__tests__/useAdminStats.test.tsx` - Unit tests

**Files to Update:**
- None (new hook)

---

## Estimated Effort

**Development:** 2 hours
**Testing:** 1 hour
**Code Review:** 0.5 hours
**Total:** 3.5 hours

---

## Notes

This is the first query hook in the migration and will establish the pattern for all subsequent hooks. Pay special attention to:
- Query key factory structure
- TypeScript type definitions
- Cache configuration rationale
- Test coverage

This hook will be used by Story #9 to migrate the AdminStats component.

---

## Comments Section

<!-- GitHub will populate this with discussion -->
