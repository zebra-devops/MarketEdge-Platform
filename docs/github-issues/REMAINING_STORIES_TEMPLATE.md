# Remaining User Stories Template

This document provides templates for creating the remaining 23 user stories (#7-#29). Each follows the same detailed pattern established in Stories #5 and #6.

---

## Priority 1 Stories (Epic #2: Admin Panel Migration)

### Story #7: Create useOrganizations Query Hook
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As a developer building organization management features
I want reusable `useOrganizations()` and `useOrganization()` query hooks
So that I can fetch and cache organization data efficiently

**Key Requirements:**
- Query key factory: `organizationKeys`
- Fetch organizations list with filters
- Fetch single organization details
- Multi-tenant aware (current user's accessible orgs)
- Cache: `staleTime: 5 * 60 * 1000` (5 minutes)

**Files to Create:**
- `/src/hooks/api/useOrganizations.ts`
- `/src/hooks/api/__tests__/useOrganizations.test.tsx`

**Blocks:** Story #11, #17, #18

---

### Story #8: Create useFeatureFlagsAdmin Query Hook
**Points:** 3 | **Complexity:** Simple | **Agent:** dev → cr

**User Story:**
As a developer building feature flag admin features
I want a `useFeatureFlagsAdmin()` query hook for admin operations
So that I can manage feature flags with proper caching

**Key Requirements:**
- Extend existing `useFeatureFlags` for admin operations
- Fetch all feature flags (admin-only)
- Fetch feature flag by key (admin details)
- Cache: `staleTime: 2 * 60 * 1000` (2 minutes)

**Files to Modify:**
- `/src/hooks/useFeatureFlags.ts` (add admin hooks)

**Files to Create:**
- `/src/hooks/api/__tests__/useFeatureFlagsAdmin.test.tsx`

**Blocks:** Story #19

---

### Story #9: Migrate AdminStats Component to useQuery
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As an admin user
I want the admin dashboard to load faster with cached data
So that I can quickly access key metrics

**Key Requirements:**
- Replace manual state management in `AdminStats.tsx`
- Use `useAdminStats()` hook
- Remove `useState`, `useEffect`, manual fetch logic
- Add proper loading and error UI
- Verify performance improvement (cached navigation)

**Files to Modify:**
- `/src/components/admin/AdminStats.tsx`

**Depends On:** Story #5

---

### Story #10: Migrate UnifiedUserManagement to React Query
**Points:** 8 | **Complexity:** Complex | **Agent:** dev → cr → qa

**User Story:**
As an admin user
I want user management operations to be fast and reliable
So that I can efficiently manage users across my organization

**Key Requirements:**
- Replace manual state in `UnifiedUserManagement.tsx`
- Use `useUsers()` hook for fetching
- Use `useUser()` for user details
- Remove 200+ lines of manual state boilerplate
- Add proper loading states
- Maintain all existing functionality (search, filter, pagination)
- Verify multi-tenant isolation

**Files to Modify:**
- `/src/components/admin/UnifiedUserManagement.tsx`

**Files to Test:**
- Multi-tenant isolation integration tests

**Depends On:** Story #6

---

### Story #11: Migrate OrganizationManagement to React Query
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As an admin user
I want organization management to use cached data
So that I can quickly switch between organizations without waiting

**Key Requirements:**
- Replace manual state in `OrganizationManagement.tsx`
- Use `useOrganizations()` hook
- Cache organization data (5 minutes)
- Proper loading states
- Error handling

**Files to Modify:**
- `/src/components/admin/OrganizationManagement.tsx`

**Depends On:** Story #7

---

### Story #12: Document Query Hook Patterns and Best Practices
**Points:** 3 | **Complexity:** Simple | **Agent:** dev → cr

**User Story:**
As a developer
I want clear documentation on query hook patterns
So that I can follow best practices when creating new hooks

**Key Requirements:**
- Create developer guide document
- Document query key factory pattern
- Document cache configuration guidelines
- Document multi-tenant considerations
- Provide code examples
- Document testing patterns

**Files to Create:**
- `/docs/QUERY_HOOK_PATTERNS.md`

**Files to Update:**
- `/docs/DEVELOPER_GUIDE.md`

**Can Run In Parallel:** Yes (alongside Stories #9-#11)

---

## Priority 2 Stories (Epic #3: Mutations)

### Story #13: Implement useCreateUser Mutation with Optimistic Updates
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As an admin user
I want user creation to feel instant
So that I can efficiently add multiple users without waiting

**Key Requirements:**
- Create `useCreateUser()` mutation hook
- Implement optimistic update (add to cache immediately)
- Rollback on error
- Cache invalidation on success
- Toast notifications (success/error)
- Loading state management

**Files to Modify:**
- `/src/hooks/api/useUsers.ts` (add mutation export)

**Depends On:** Story #6

---

### Story #14: Implement useUpdateUser Mutation with Optimistic Updates
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As an admin user
I want user updates to reflect immediately in the UI
So that I see changes instantly without waiting for server confirmation

**Key Requirements:**
- Create `useUpdateUser()` mutation hook
- Optimistic update (update cache immediately)
- Rollback on error
- Update both list cache and detail cache
- Toast notifications

**Files to Modify:**
- `/src/hooks/api/useUsers.ts`

**Depends On:** Story #6

---

### Story #15: Implement useDeleteUser Mutation with Optimistic Updates
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As an admin user
I want deleted users to be removed from the UI immediately
So that I can confirm my deletion action was successful

**Key Requirements:**
- Create `useDeleteUser()` mutation hook
- Optimistic removal from cache
- Rollback on error
- Confirmation dialog before deletion
- Toast notifications

**Files to Modify:**
- `/src/hooks/api/useUsers.ts`

**Depends On:** Story #6

---

### Story #16: Add Bulk User Operations Mutation
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As an admin user
I want to perform bulk operations on users (import, delete, update)
So that I can manage large user sets efficiently

**Key Requirements:**
- Create `useBulkUserOperation()` mutation
- Support bulk import (CSV)
- Support bulk delete
- Support bulk role updates
- Progress indicator for long operations
- Partial success handling

**Files to Modify:**
- `/src/hooks/api/useUsers.ts`
- `/src/components/admin/BulkUserImport.tsx`

**Depends On:** Story #6

---

### Story #17: Implement Organization CRUD Mutations
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As a super admin user
I want organization management operations to be instant
So that I can efficiently manage multiple organizations

**Key Requirements:**
- Create `useCreateOrganization()` mutation
- Create `useUpdateOrganization()` mutation
- Create `useDeleteOrganization()` mutation
- Optimistic updates for all operations
- Proper cache invalidation

**Files to Modify:**
- `/src/hooks/api/useOrganizations.ts`

**Depends On:** Story #7

---

### Story #18: Implement Organization Member Management Mutations
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As an admin user
I want to add/remove users from organizations instantly
So that I can manage team membership efficiently

**Key Requirements:**
- Create `useAddOrganizationMember()` mutation
- Create `useRemoveOrganizationMember()` mutation
- Create `useUpdateMemberRole()` mutation
- Optimistic updates
- Invalidate both user and org caches

**Files to Modify:**
- `/src/hooks/api/useOrganizations.ts`

**Depends On:** Story #7

---

### Story #19: Implement Feature Flag Admin Mutations
**Points:** 3 | **Complexity:** Simple | **Agent:** dev → cr

**User Story:**
As a super admin user
I want feature flag updates to be instant
So that I can quickly enable/disable features

**Key Requirements:**
- Create `useUpdateFeatureFlag()` mutation
- Create `useToggleFeatureFlag()` mutation
- Optimistic updates
- Cache invalidation for affected users

**Files to Modify:**
- `/src/hooks/useFeatureFlags.ts`

**Depends On:** Story #8

---

### Story #20: Implement Comprehensive Error Handling and Rollback
**Points:** 3 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As a user
I want clear error messages and automatic recovery
So that I understand what went wrong and can retry easily

**Key Requirements:**
- Centralized error handler for mutations
- Categorize errors (transient, validation, auth, server)
- Retry logic for transient errors (exponential backoff)
- Rollback for permanent errors
- Clear error messages to users
- Logging for debugging

**Files to Create:**
- `/src/utils/mutationErrorHandler.ts`

**Files to Modify:**
- All mutation hooks (apply error handler)

---

### Story #21: Add Loading States and User Feedback for Mutations
**Points:** 3 | **Complexity:** Simple | **Agent:** dev → cr

**User Story:**
As a user
I want clear feedback during operations
So that I know the system is working and when operations complete

**Key Requirements:**
- Loading spinners during mutations
- Disabled buttons during mutations
- Success toast notifications
- Error toast notifications with retry option
- Progress indicators for long operations
- Consistent UI patterns across all mutations

**Files to Modify:**
- All components using mutations

---

## Priority 3 Stories (Epic #4: Optimization)

### Story #22: Implement Query Key Factory Patterns for All Domains
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As a developer
I want a centralized query key factory
So that cache management is consistent and predictable

**Key Requirements:**
- Create centralized `queryKeys` object
- Include all domains (users, orgs, stats, feature flags, etc.)
- Hierarchical key structure
- TypeScript types for keys
- Documentation

**Files to Create:**
- `/src/utils/queryKeys.ts`

**Files to Modify:**
- All query hooks (use centralized keys)

---

### Story #23: Configure Data-Type-Specific Cache Strategies
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As a developer
I want clear cache configuration for different data types
So that I can optimize performance for each use case

**Key Requirements:**
- Define cache config for static data (infinite)
- Define cache config for user data (5 min)
- Define cache config for stats (30 sec)
- Define cache config for real-time data (0 sec, polling)
- Document cache strategy
- Apply to all query hooks

**Files to Create:**
- `/src/utils/cacheConfig.ts`
- `/docs/QUERY_CACHING_STRATEGY.md`

**Files to Modify:**
- All query hooks (apply cache config)

---

### Story #24: Implement Smart Cache Invalidation Strategies
**Points:** 3 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As a developer
I want intelligent cache invalidation
So that data stays fresh without unnecessary refetches

**Key Requirements:**
- Invalidation after mutations
- Invalidation after organization switch
- Invalidation after user logout
- Selective invalidation (don't clear everything)
- Background refetch for stale data
- Document invalidation patterns

**Files to Modify:**
- All mutation hooks (add invalidation logic)
- `/src/components/providers/OrganisationProvider.tsx`
- `/src/hooks/useAuth.ts`

---

### Story #25: Add Prefetching for Navigation and Common Paths
**Points:** 5 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As a user
I want pages to load instantly when I navigate
So that the application feels fast and responsive

**Key Requirements:**
- Prefetch on hover (200ms delay)
- Prefetch common paths on login
- Prefetch next page in pagination
- Prefetch related data (e.g., users when viewing org)
- Don't prefetch unnecessarily (waste bandwidth)

**Files to Create:**
- `/src/components/shared/PrefetchLink.tsx`
- `/src/hooks/usePrefetchCommonData.ts`

**Files to Modify:**
- `/src/components/layout/Navigation.tsx`

---

### Story #26: Implement Suspense Boundaries for Loading States
**Points:** 3 | **Complexity:** Simple | **Agent:** dev → cr

**User Story:**
As a user
I want smooth loading transitions
So that the UI doesn't flash or feel janky

**Key Requirements:**
- Add Suspense boundaries for query-heavy components
- Skeleton loaders for predictable content
- Error boundaries for failed queries
- No loading flashes for cached data
- Graceful degradation for slow networks

**Files to Modify:**
- `/src/app/admin/layout.tsx`
- Admin components (wrap in Suspense)

**Files to Create:**
- `/src/components/shared/SkeletonLoaders.tsx`

---

### Story #27: Configure Cache Persistence with localStorage
**Points:** 3 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As a user
I want my data to persist across browser sessions
So that I don't wait for data to reload every time I visit

**Key Requirements:**
- Install `@tanstack/react-query-persist-client`
- Configure localStorage persister
- Selective persistence (critical data only)
- 24-hour max age
- Size limits (don't exceed localStorage quota)

**Files to Modify:**
- `/src/components/providers/QueryProvider.tsx`

**Files to Create:**
- `/src/utils/queryPersistence.ts`

---

### Story #28: Add Offline Support for Critical Data
**Points:** 3 | **Complexity:** Moderate | **Agent:** dev → cr

**User Story:**
As a user
I want to access previously loaded data when offline
So that I can continue working without network connectivity

**Key Requirements:**
- Detect online/offline status
- Display offline indicator
- Serve cached data when offline
- Show "offline - cached data" message
- Background sync on reconnection
- Prioritize critical data (user, org, feature flags)

**Files to Create:**
- `/src/hooks/useOnlineStatus.ts`
- `/src/components/shared/OfflineIndicator.tsx`

**Files to Modify:**
- Query hooks (configure for offline)

---

### Story #29: Integrate React Query DevTools for Development
**Points:** 2 | **Complexity:** Simple | **Agent:** dev → cr

**User Story:**
As a developer
I want visual debugging tools for queries
So that I can inspect cache, debug issues, and monitor performance

**Key Requirements:**
- Install `@tanstack/react-query-devtools`
- Add DevTools to QueryProvider (dev only)
- Configure position and display
- Document usage in developer guide

**Files to Modify:**
- `/src/components/providers/QueryProvider.tsx`

**Files to Update:**
- `/docs/DEVELOPER_GUIDE.md`

---

## Story Creation Checklist

For each story, ensure:
- [ ] User story format: "As a [persona], I want [goal], so that [benefit]"
- [ ] Acceptance criteria with Given/When/Then format
- [ ] Technical implementation details
- [ ] Test scenarios
- [ ] Definition of Done
- [ ] Dependencies clearly stated
- [ ] Story points estimated (Fibonacci)
- [ ] Complexity label (Simple/Moderate/Complex)
- [ ] Agent path defined
- [ ] Files to create/modify listed
- [ ] Estimated effort breakdown
- [ ] Related to parent epic

---

## Next Steps

1. **Copy Templates:** Use this template to create individual markdown files for Stories #7-#29
2. **Create GitHub Issues:** Create issues in GitHub from markdown files
3. **Link to Epics:** Link each story to its parent epic
4. **Apply Labels:** Add appropriate labels (priority, complexity, domain)
5. **Assign Points:** Ensure story points match
6. **Set Milestone:** Assign to Q1 2025 milestone
7. **Order Backlog:** Order by dependencies and priority

---

**Template Version:** 1.0
**Created:** 2025-10-02
**Stories Covered:** #7-#29 (23 stories)
