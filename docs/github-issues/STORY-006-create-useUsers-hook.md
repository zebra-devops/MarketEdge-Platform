# Story: Create useUsers Query Hook

**Labels:** `user-story`, `enhancement`, `frontend`, `react-query`, `admin`, `priority-1`
**Milestone:** Q1 2025 - React Query Standardization
**Parent Epic:** #2 (Admin Panel Query Migration)
**Story Points:** 5
**Complexity:** Moderate
**Agent Path:** dev → cr

---

## User Story

**As a** developer building user management features
**I want** reusable `useUsers()` and `useUser()` query hooks
**I want** proper query key factories for cache management
**So that** I can fetch and cache user data efficiently with multi-tenant isolation

---

## Acceptance Criteria

### Functional Requirements
- [ ] Given I call `useUsers()`, when the component mounts, then it fetches all users for the current organization
- [ ] Given I call `useUsers(organizationId)`, when provided an org ID, then it fetches users for that specific organization
- [ ] Given I call `useUser(userId)`, when provided a user ID, then it fetches that specific user's details
- [ ] Given the data is cached, when I navigate back, then it uses cached data
- [ ] Given I switch organizations, when the org context changes, then it fetches users for the new organization
- [ ] Given the API fails, when I retry, then it retries up to 2 times

### Technical Requirements
- [ ] Query key factory: `userKeys` with proper hierarchy
- [ ] Query keys include organization ID for proper multi-tenant isolation
- [ ] TypeScript types defined for `User`, `UserListFilters`
- [ ] Cache configuration: `staleTime: 2 * 60 * 1000` (2 minutes for user data)
- [ ] Hooks properly handle organization context from `useOrganisationContext()`
- [ ] Support for filters (search, role, status)
- [ ] Pagination support (optional for this story)

### Code Quality Requirements
- [ ] TypeScript with no `any` types
- [ ] JSDoc comments for all exports
- [ ] Follows pattern from `useFeatureFlags.ts`
- [ ] ESLint and Prettier pass
- [ ] Unit tests with >80% coverage

---

## Definition of Done

- [ ] Code written and committed
- [ ] Unit tests written and passing
- [ ] Integration tests for multi-tenant scenarios
- [ ] TypeScript types exported
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Merged to main branch

---

## Technical Implementation

### File Location
`/src/hooks/api/useUsers.ts`

### Implementation Example

```typescript
import { useQuery, UseQueryOptions } from 'react-query'
import { apiService } from '@/services/api'
import { useAuth } from '@/hooks/useAuth'
import { useOrganisationContext } from '@/components/providers/OrganisationProvider'
import type { User } from '@/types/auth'

/**
 * User list filters
 */
export interface UserListFilters {
  organizationId?: string
  role?: string
  status?: 'active' | 'inactive'
  search?: string
}

/**
 * Query keys for users
 */
export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (filters: UserListFilters) => [...userKeys.lists(), filters] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
}

/**
 * Fetch list of users
 *
 * @param filters - Optional filters for user list
 * @param options - React Query options
 *
 * @example
 * // Fetch all users for current organization
 * const { data: users } = useUsers()
 *
 * @example
 * // Fetch users for specific organization
 * const { data: users } = useUsers({ organizationId: 'org-123' })
 *
 * @example
 * // Fetch users with search filter
 * const { data: users } = useUsers({ search: 'john' })
 */
export function useUsers(
  filters: UserListFilters = {},
  options?: Omit<UseQueryOptions<User[]>, 'queryKey' | 'queryFn'>
) {
  const { isAuthenticated } = useAuth()
  const { currentOrganisation } = useOrganisationContext()

  // Use current organization if not specified
  const organizationId = filters.organizationId || currentOrganisation?.id

  // Build query params
  const params = new URLSearchParams()
  if (organizationId) params.append('organization_id', organizationId)
  if (filters.role) params.append('role', filters.role)
  if (filters.status) params.append('status', filters.status)
  if (filters.search) params.append('search', filters.search)

  const queryString = params.toString()
  const url = `/users${queryString ? `?${queryString}` : ''}`

  return useQuery<User[]>({
    queryKey: userKeys.list({ ...filters, organizationId }),
    queryFn: () => apiService.get<User[]>(url),
    enabled: isAuthenticated && !!organizationId,
    staleTime: 2 * 60 * 1000, // 2 minutes - user data changes occasionally
    cacheTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
    ...options,
  })
}

/**
 * Fetch a single user by ID
 *
 * @param userId - User ID to fetch
 * @param options - React Query options
 *
 * @example
 * const { data: user } = useUser('user-123')
 */
export function useUser(
  userId: string,
  options?: Omit<UseQueryOptions<User>, 'queryKey' | 'queryFn'>
) {
  const { isAuthenticated } = useAuth()

  return useQuery<User>({
    queryKey: userKeys.detail(userId),
    queryFn: () => apiService.get<User>(`/users/${userId}`),
    enabled: isAuthenticated && !!userId,
    staleTime: 2 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
    retry: 2,
    ...options,
  })
}

/**
 * Get the current authenticated user
 *
 * @example
 * const { data: currentUser } = useCurrentUser()
 */
export function useCurrentUser(
  options?: Omit<UseQueryOptions<User>, 'queryKey' | 'queryFn'>
) {
  const { user, isAuthenticated } = useAuth()

  return useQuery<User>({
    queryKey: userKeys.detail(user?.id || 'current'),
    queryFn: () => apiService.get<User>('/users/me'),
    enabled: isAuthenticated && !!user,
    staleTime: 5 * 60 * 1000, // 5 minutes for current user
    cacheTime: 15 * 60 * 1000,
    retry: 2,
    ...options,
  })
}
```

### Unit Tests

```typescript
// __tests__/hooks/useUsers.test.tsx
import { renderHook, waitFor } from '@testing-library/react'
import { useUsers, useUser } from '@/hooks/api/useUsers'
import { createQueryWrapper } from '@/test-utils/queryWrapper'
import { apiService } from '@/services/api'

jest.mock('@/services/api')
jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: true }),
}))
jest.mock('@/components/providers/OrganisationProvider', () => ({
  useOrganisationContext: () => ({
    currentOrganisation: { id: 'org-123', name: 'Test Org' },
  }),
}))

describe('useUsers', () => {
  const mockUsers = [
    { id: 'user-1', email: 'user1@test.com', name: 'User 1' },
    { id: 'user-2', email: 'user2@test.com', name: 'User 2' },
  ]

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('fetches users for current organization', async () => {
    ;(apiService.get as jest.Mock).mockResolvedValue(mockUsers)

    const { result } = renderHook(() => useUsers(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockUsers)
    expect(apiService.get).toHaveBeenCalledWith('/users?organization_id=org-123')
  })

  it('fetches users with filters', async () => {
    ;(apiService.get as jest.Mock).mockResolvedValue(mockUsers)

    const { result } = renderHook(
      () => useUsers({ role: 'admin', status: 'active', search: 'john' }),
      { wrapper: createQueryWrapper() }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiService.get).toHaveBeenCalledWith(
      '/users?organization_id=org-123&role=admin&status=active&search=john'
    )
  })

  it('uses different cache keys for different filters', () => {
    const { result: result1 } = renderHook(() => useUsers({ role: 'admin' }), {
      wrapper: createQueryWrapper(),
    })

    const { result: result2 } = renderHook(() => useUsers({ role: 'user' }), {
      wrapper: createQueryWrapper(),
    })

    // Query keys should be different
    expect(result1.current).not.toBe(result2.current)
  })

  it('refetches when organization changes', async () => {
    const { rerender } = renderHook(
      ({ orgId }) => useUsers({ organizationId: orgId }),
      {
        wrapper: createQueryWrapper(),
        initialProps: { orgId: 'org-1' },
      }
    )

    await waitFor(() => expect(apiService.get).toHaveBeenCalledTimes(1))

    // Change organization
    rerender({ orgId: 'org-2' })

    await waitFor(() => expect(apiService.get).toHaveBeenCalledTimes(2))
    expect(apiService.get).toHaveBeenLastCalledWith('/users?organization_id=org-2')
  })
})

describe('useUser', () => {
  const mockUser = { id: 'user-1', email: 'user1@test.com', name: 'User 1' }

  it('fetches single user by ID', async () => {
    ;(apiService.get as jest.Mock).mockResolvedValue(mockUser)

    const { result } = renderHook(() => useUser('user-1'), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockUser)
    expect(apiService.get).toHaveBeenCalledWith('/users/user-1')
  })

  it('does not fetch when userId is empty', () => {
    const { result } = renderHook(() => useUser(''), {
      wrapper: createQueryWrapper(),
    })

    expect(result.current.status).toBe('idle')
    expect(apiService.get).not.toHaveBeenCalled()
  })
})
```

---

## Dependencies

**Depends On:**
- QueryProvider configured ✅
- apiService infrastructure ✅
- Auth hook available ✅
- OrganisationProvider available ✅
- User type defined in `/src/types/auth.ts` ✅

**Blocks:**
- Story #10 (Migrate UnifiedUserManagement)
- Story #13 (User mutations)

---

## Test Scenarios

### Scenario 1: Fetch Users for Current Organization
1. User logs in to organization "Acme Corp"
2. User navigates to Users page
3. `useUsers()` called without filters
4. Hook fetches `/users?organization_id=acme-123`
5. Users displayed in list

### Scenario 2: Filter Users by Role
1. User is on Users page
2. User selects "Admin" role filter
3. Component calls `useUsers({ role: 'admin' })`
4. Hook fetches `/users?organization_id=acme-123&role=admin`
5. Filtered list displayed

### Scenario 3: Switch Organizations
1. User is viewing users for "Acme Corp"
2. User switches to "Beta Inc" organization
3. Organization context updates
4. `useUsers()` refetches with new org ID
5. Users for "Beta Inc" displayed

### Scenario 4: View User Details
1. User clicks on a user in the list
2. Modal opens showing user details
3. `useUser(userId)` called
4. Hook fetches `/users/user-123`
5. User details displayed

### Scenario 5: Multi-tenant Isolation
1. User A views users for Org A
2. User B views users for Org B
3. Cache keys are different: `['users', 'list', { organizationId: 'org-a' }]` vs `['users', 'list', { organizationId: 'org-b' }]`
4. No data leakage between tenants

---

## Multi-Tenant Testing

**Critical:** This hook must properly isolate data by organization.

```typescript
describe('Multi-tenant isolation', () => {
  it('isolates user data by organization', async () => {
    const queryClient = createTestQueryClient()

    // Fetch users for org-1
    queryClient.setQueryData(
      ['users', 'list', { organizationId: 'org-1' }],
      [{ id: 'user-1', name: 'Org 1 User' }]
    )

    // Fetch users for org-2
    queryClient.setQueryData(
      ['users', 'list', { organizationId: 'org-2' }],
      [{ id: 'user-2', name: 'Org 2 User' }]
    )

    // Verify data is isolated
    const org1Data = queryClient.getQueryData(['users', 'list', { organizationId: 'org-1' }])
    const org2Data = queryClient.getQueryData(['users', 'list', { organizationId: 'org-2' }])

    expect(org1Data).not.toEqual(org2Data)
  })
})
```

---

## Performance Considerations

**Cache Strategy:**
- User lists: 2 minutes stale time (changes occasionally)
- User details: 2 minutes stale time
- Current user: 5 minutes stale time (rarely changes)

**Query Key Design:**
- Includes all filter parameters for proper cache isolation
- Organization ID always included for multi-tenant safety
- Allows invalidation at different granularity levels:
  - `queryClient.invalidateQueries(userKeys.all)` - all user queries
  - `queryClient.invalidateQueries(userKeys.lists())` - all user lists
  - `queryClient.invalidateQueries(userKeys.list({ organizationId: 'org-1' }))` - specific org

---

## Acceptance Testing

**Manual Test Steps:**
1. Log in as admin user
2. Navigate to Users page
3. Verify users load for current organization
4. Apply role filter
5. Verify filtered results
6. Clear filter
7. Verify all users shown again
8. Switch organization
9. Verify new organization's users load
10. Open React Query DevTools
11. Verify query keys include organization ID
12. Navigate away and back
13. Verify cached data used

**Expected Results:**
- Users load in <300ms first time
- Cached users load instantly (<50ms)
- Filters update query key correctly
- Organization switch triggers refetch
- No cross-org data leakage

---

## Related Files

**Reference Implementation:**
- `/src/hooks/useFeatureFlags.ts` - Query pattern
- `/src/types/auth.ts` - User type definition

**Files to Create:**
- `/src/hooks/api/useUsers.ts` - Hook implementation
- `/src/hooks/api/__tests__/useUsers.test.tsx` - Unit tests

**Integration Test:**
- `/src/__tests__/integration/multi-tenant-users.test.tsx` - Multi-tenant isolation test

---

## Estimated Effort

**Development:** 3 hours
**Testing:** 2 hours
**Code Review:** 1 hour
**Total:** 6 hours

---

## Notes

This hook is more complex than `useAdminStats` because it must:
1. Handle multiple filter parameters
2. Properly isolate by organization
3. Support both list and detail queries
4. Include current user query

The query key factory is critical for proper cache management and multi-tenant isolation.

---

## Security Considerations

**Multi-tenant Isolation:**
- Always include organization ID in query keys
- Backend enforces RLS (Row Level Security) policies
- Frontend query keys prevent cache pollution
- Organization context comes from authenticated session

**Authorization:**
- Only admin/super_admin can fetch all users
- Regular users can only fetch their own profile
- Backend validates permissions on every request
