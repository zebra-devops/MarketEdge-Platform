# Epic: Implement Mutations and Optimistic Updates

**Labels:** `epic`, `enhancement`, `frontend`, `react-query`, `ux`, `priority-2`
**Milestone:** Q1 2025 - React Query Standardization
**Parent Epic:** #1 (Standardize Data Fetching with TanStack Query)
**Priority:** P2 - Medium-High
**Story Points:** 34
**Timeline:** Weeks 3-4

---

## Epic Overview

**Business Value:**
Replace all manual CRUD operations with React Query mutations, implementing optimistic updates for instant UI feedback. This will dramatically improve user experience by making the application feel instantaneous, while providing automatic error handling, rollback, and retry capabilities.

**User Impact:**
- **Admin Users:** Instant feedback when creating/updating/deleting users and organizations
- **All Users:** Perceived performance improvement (UI updates before server response)
- **Developers:** Consistent mutation patterns, automatic error recovery

**Current Issues:**
- All mutations use manual `apiService` calls
- No optimistic updates (user waits for server response)
- Manual cache invalidation required
- Inconsistent error handling across operations
- No automatic retry for failed operations
- Race conditions in rapid successive updates

---

## Stories in this Epic

### Phase 1: User Management Mutations (Week 3)
- [ ] Story #13: Implement useCreateUser mutation with optimistic updates - 5 points
- [ ] Story #14: Implement useUpdateUser mutation with optimistic updates - 5 points
- [ ] Story #15: Implement useDeleteUser mutation with optimistic updates - 5 points
- [ ] Story #16: Add bulk user operations mutation - 5 points

### Phase 2: Organization Mutations (Week 4)
- [ ] Story #17: Implement organization CRUD mutations - 5 points
- [ ] Story #18: Implement organization member management mutations - 5 points

### Phase 3: Feature Flag Mutations (Week 4)
- [ ] Story #19: Implement feature flag admin mutations - 3 points

### Error Handling & Polish (Week 4)
- [ ] Story #20: Implement comprehensive error handling and rollback - 3 points
- [ ] Story #21: Add loading states and user feedback for mutations - 3 points

**Total Story Points:** 39

---

## Success Metrics

**User Experience:**
- Perceived instant UI updates (0ms delay for optimistic updates)
- Automatic error rollback (no stale UI state)
- Clear loading indicators during server operations
- Consistent success/error toast notifications

**Technical:**
- 100% of CRUD operations use useMutation
- Automatic cache invalidation after mutations
- Zero manual cache management in components
- Optimistic updates for all user-facing mutations

**Reliability:**
- Automatic retry for transient failures (network errors)
- Rollback on permanent failures (4xx errors)
- No data loss during failed operations
- Proper error reporting to users

---

## Acceptance Criteria for Epic Completion

### Functional Requirements
- [ ] All user CRUD operations use mutations
- [ ] All organization CRUD operations use mutations
- [ ] All feature flag updates use mutations
- [ ] Optimistic updates implemented for all mutations
- [ ] UI updates immediately on mutation trigger
- [ ] Automatic rollback on mutation failure
- [ ] Cache automatically invalidated on success

### Technical Requirements
- [ ] Mutation hooks follow consistent naming pattern (`useCreateX`, `useUpdateX`, `useDeleteX`)
- [ ] Optimistic update implementation for all mutations
- [ ] Error boundaries catch and handle mutation errors
- [ ] Toast notifications for success/failure
- [ ] Retry configuration for transient failures
- [ ] Proper TypeScript typing for all mutations
- [ ] Query cache invalidation strategies documented

### Testing Requirements
- [ ] Unit tests for all mutation hooks
- [ ] Integration tests for optimistic update flows
- [ ] Error scenario testing (network failures, validation errors, server errors)
- [ ] Rollback behavior verified
- [ ] Multi-tenant isolation verified for mutations
- [ ] Concurrent mutation testing (race conditions)

### User Experience Requirements
- [ ] Loading spinners during mutations
- [ ] Success toast notifications
- [ ] Error toast notifications with retry option
- [ ] Disabled state for buttons during mutations
- [ ] Optimistic UI updates feel instant
- [ ] No flickering during optimistic updates

---

## Definition of Done

- [ ] All 9 stories completed and merged
- [ ] Code reviewed and approved
- [ ] All tests passing (unit, integration, e2e)
- [ ] User acceptance testing completed
- [ ] Documentation updated
- [ ] Deployed to staging and verified
- [ ] Performance benchmarks met
- [ ] Deployed to production
- [ ] No regressions within 48 hours
- [ ] User feedback collected and addressed

---

## Technical Implementation Plan

### Mutation Hook Pattern

```typescript
// Example: useCreateUser mutation with optimistic update
export function useCreateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (userData: Partial<User>) =>
      apiService.post<User>('/users', userData),

    // Optimistic update
    onMutate: async (newUser) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries(userKeys.lists())

      // Snapshot previous value for rollback
      const previousUsers = queryClient.getQueryData(userKeys.lists())

      // Optimistically update cache
      queryClient.setQueryData(userKeys.lists(), (old: User[] | undefined) =>
        old ? [...old, { ...newUser, id: `temp-${Date.now()}` }] : [newUser]
      )

      // Return context for rollback
      return { previousUsers }
    },

    // Rollback on error
    onError: (err, newUser, context) => {
      // Restore previous state
      queryClient.setQueryData(userKeys.lists(), context?.previousUsers)

      // Show error notification
      toast.error(`Failed to create user: ${err.message}`)
    },

    // Refetch on success
    onSuccess: (data) => {
      // Invalidate to trigger refetch with real data
      queryClient.invalidateQueries(userKeys.lists())

      // Show success notification
      toast.success('User created successfully')
    },
  })
}
```

### Component Usage Pattern

```typescript
export function UserManagement() {
  const { data: users } = useUsers()
  const createUser = useCreateUser()
  const updateUser = useUpdateUser()
  const deleteUser = useDeleteUser()

  const handleCreateUser = async (userData: Partial<User>) => {
    try {
      await createUser.mutateAsync(userData)
      // UI already updated optimistically!
    } catch (error) {
      // Error already handled in mutation hook
    }
  }

  return (
    <div>
      <button
        onClick={() => handleCreateUser(newUserData)}
        disabled={createUser.isLoading}
      >
        {createUser.isLoading ? 'Creating...' : 'Create User'}
      </button>

      {users?.map(user => (
        <UserCard
          key={user.id}
          user={user}
          onUpdate={(updates) => updateUser.mutate({ id: user.id, ...updates })}
          onDelete={() => deleteUser.mutate(user.id)}
          isUpdating={updateUser.isLoading}
          isDeleting={deleteUser.isLoading}
        />
      ))}
    </div>
  )
}
```

---

## Files to Modify/Create

### New Mutation Hooks
- `/src/hooks/api/useUsers.ts` - Add mutation exports
- `/src/hooks/api/useOrganizations.ts` - Add mutation exports
- `/src/hooks/api/useFeatureFlagsAdmin.ts` - Add mutation exports

### Components to Update
- `/src/components/admin/UnifiedUserManagement.tsx` - Replace manual mutations
- `/src/components/admin/OrganizationManagement.tsx` - Replace manual mutations
- `/src/components/admin/FeatureFlagManager.tsx` - Replace manual mutations
- `/src/components/admin/BulkUserImport.tsx` - Use bulk mutation

### Utilities to Create
- `/src/utils/queryHelpers.ts` - Optimistic update helpers
- `/src/utils/mutationErrorHandler.ts` - Centralized error handling

---

## Dependencies

**Depends On:**
- Epic #2 (Admin Panel Migration) - Query hooks must exist first ✅
- Query key factories established ✅
- Toast notification system (`react-hot-toast`) ✅

**Blocks:**
- Epic #4 (Optimization) - Mutations enable advanced caching strategies
- Future features requiring CRUD operations

---

## Risk Assessment

**Technical Risks:**
- **Medium:** Optimistic update complexity - Mitigated by following established patterns
- **Medium:** Race conditions in concurrent mutations - Mitigated by proper query key invalidation
- **Low:** Cache synchronization issues - Mitigated by testing

**User Experience Risks:**
- **Low:** Confusing optimistic updates - Mitigated by clear loading indicators
- **Low:** Failed rollback scenarios - Mitigated by comprehensive error testing

**Mitigation Strategy:**
- Extensive testing of optimistic update flows
- Clear user feedback during mutations
- Proper error boundaries to catch unexpected failures
- Rollback plan: Can disable optimistic updates temporarily if issues arise

---

## Performance Impact

### Current State (Baseline)
- User creation: 500ms perceived delay (wait for server response)
- User update: 400ms perceived delay
- User deletion: 300ms perceived delay
- **User waits for every operation**

### Target State (After Mutations)
- User creation: **0ms perceived delay** (optimistic update), 500ms actual
- User update: **0ms perceived delay** (optimistic update), 400ms actual
- User deletion: **0ms perceived delay** (optimistic update), 300ms actual
- **UI feels instant, server processes in background**

### Additional Benefits
- Automatic retry for network failures
- Proper loading states during mutations
- Consistent error handling across all operations
- Better error recovery (automatic rollback)

---

## Testing Strategy

### Unit Tests
```typescript
describe('useCreateUser', () => {
  it('performs optimistic update', async () => {
    const { result } = renderHook(() => useCreateUser(), {
      wrapper: createQueryWrapper(),
    })

    // Trigger mutation
    result.current.mutate({ email: 'test@example.com', name: 'Test User' })

    // Verify optimistic update
    const cachedUsers = queryClient.getQueryData(userKeys.lists())
    expect(cachedUsers).toContainEqual(expect.objectContaining({
      email: 'test@example.com',
      name: 'Test User',
    }))
  })

  it('rolls back on error', async () => {
    // Mock API failure
    apiService.post.mockRejectedValue(new Error('Server error'))

    const { result } = renderHook(() => useCreateUser(), {
      wrapper: createQueryWrapper(),
    })

    // Get initial state
    const initialUsers = queryClient.getQueryData(userKeys.lists())

    // Trigger mutation
    await result.current.mutateAsync({ email: 'test@example.com' })
      .catch(() => {}) // Expected to fail

    // Verify rollback
    const finalUsers = queryClient.getQueryData(userKeys.lists())
    expect(finalUsers).toEqual(initialUsers)
  })
})
```

### Integration Tests
- Test full CRUD flow with optimistic updates
- Verify cache invalidation after success
- Test concurrent mutations (create + update)
- Test error scenarios (network, validation, server errors)
- Verify multi-tenant isolation

### E2E Tests
- Create user → verify optimistic update → verify server persistence
- Update user → verify optimistic update → verify rollback on error
- Delete user → verify optimistic removal → verify refetch

---

## Rollout Plan

**Week 3:**
- Day 1-2: Implement user mutations (Stories #13, #14, #15)
- Day 3: Implement bulk operations (Story #16)
- Day 4-5: Testing and code review

**Week 4:**
- Day 1-2: Implement organization mutations (Stories #17, #18)
- Day 3: Implement feature flag mutations (Story #19)
- Day 4: Error handling and polish (Stories #20, #21)
- Day 5: Integration testing

**Week 5:**
- Day 1-2: Staging deployment and UAT
- Day 3: Production deployment
- Day 4-5: Monitor and verify

---

## Error Handling Strategy

### Error Categories

**Transient Errors (Retry):**
- Network timeouts
- 502/503 server errors
- Connection failures
→ Retry 2 times with exponential backoff

**Validation Errors (Don't Retry):**
- 400 Bad Request
- 422 Validation errors
→ Show error to user, don't rollback optimistic update until user dismisses

**Authorization Errors (Don't Retry):**
- 401 Unauthorized
- 403 Forbidden
→ Rollback immediately, redirect to login if needed

**Server Errors (Don't Retry):**
- 500 Internal Server Error
- 409 Conflict
→ Rollback immediately, show error to user

### Error Notification Pattern

```typescript
onError: (err, variables, context) => {
  // Rollback optimistic update
  queryClient.setQueryData(userKeys.lists(), context?.previousUsers)

  // Categorize error
  if (err.status === 401) {
    toast.error('Session expired. Please log in again.')
    router.push('/login')
  } else if (err.status === 403) {
    toast.error('You do not have permission to perform this action.')
  } else if (err.status === 422) {
    toast.error(`Validation error: ${err.message}`)
  } else if (err.status >= 500) {
    toast.error('Server error. Please try again later.')
  } else {
    toast.error(`Failed to create user: ${err.message}`)
  }

  // Log error for monitoring
  console.error('Mutation error:', err)
}
```

---

## Reference Implementation

**Best Practice Example:**
Feature flag mutations (if implemented) or create from scratch following TanStack Query docs

**TanStack Query Mutation Docs:**
- https://tanstack.com/query/latest/docs/react/guides/mutations
- https://tanstack.com/query/latest/docs/react/guides/optimistic-updates

---

## Comments

Mutations are the second pillar of React Query (after queries). Implementing optimistic updates will make the application feel significantly faster, improving user satisfaction and reducing perceived latency. This is especially important for admin operations where users perform many CRUD operations in succession.

**Critical Success Factor:**
Proper error handling and rollback. Users must never see stale or incorrect data due to failed optimistic updates.
