# Epic: Admin Panel Query Migration

**Labels:** `epic`, `enhancement`, `frontend`, `admin`, `react-query`, `priority-1`
**Milestone:** Q1 2025 - React Query Standardization
**Parent Epic:** #1 (Standardize Data Fetching with TanStack Query)
**Priority:** P1 - High
**Story Points:** 34
**Timeline:** Weeks 1-2

---

## Epic Overview

**Business Value:**
Migrate all admin panel components from manual state management to React Query patterns. The admin panel has the most duplication and inconsistent patterns, making it the highest ROI target for migration. This will improve admin user experience, reduce maintenance burden, and establish patterns for remaining migrations.

**User Impact:**
- **Admin Users:** Faster page loads, instant navigation with cached data, more responsive UI
- **Developers:** Cleaner code, easier testing, consistent patterns
- **Super Admin (Zebra Associates):** Critical for £925K opportunity - improved dashboard performance

**Current Issues:**
- AdminStats component refetches on every mount (~500ms wasted)
- UnifiedUserManagement has manual state boilerplate (200+ lines)
- OrganizationManagement lacks caching between tab switches
- No request deduplication
- Race conditions in concurrent operations

---

## Stories in this Epic

### Phase 1: Query Hook Creation (Week 1)
- [ ] Story #5: Create useAdminStats query hook - 3 points
- [ ] Story #6: Create useUsers query hook - 5 points
- [ ] Story #7: Create useOrganizations query hook - 5 points
- [ ] Story #8: Create useFeatureFlagsAdmin query hook - 3 points

### Phase 2: Component Migration (Week 2)
- [ ] Story #9: Migrate AdminStats component to useQuery - 5 points
- [ ] Story #10: Migrate UnifiedUserManagement to React Query - 8 points
- [ ] Story #11: Migrate OrganizationManagement to React Query - 5 points

### Documentation
- [ ] Story #12: Document query hook patterns and best practices - 3 points

**Total Story Points:** 37

---

## Success Metrics

**Performance:**
- 60% reduction in API calls to `/admin/dashboard/stats`
- 300ms+ faster admin panel navigation
- Zero race conditions in user/org management

**Code Quality:**
- 40% reduction in state management boilerplate
- 100% TypeScript type coverage
- Zero console errors/warnings

**Developer Experience:**
- Consistent query hook patterns across admin panel
- Easier testing with mockable queries
- Clear documentation for future development

---

## Acceptance Criteria for Epic Completion

### Functional Requirements
- [ ] All admin stats use `useAdminStats()` hook
- [ ] All user operations use `useUsers()` hook
- [ ] All organization operations use `useOrganizations()` hook
- [ ] All feature flag admin operations use `useFeatureFlagsAdmin()` hook
- [ ] Data persists correctly across navigation
- [ ] Loading states display appropriately
- [ ] Error states handled gracefully with retry capability

### Technical Requirements
- [ ] Query key factory pattern implemented for all hooks
- [ ] TypeScript types defined for all query responses
- [ ] Cache configured with appropriate `staleTime` and `cacheTime`
- [ ] Query hooks properly handle organization context
- [ ] Request deduplication verified
- [ ] No memory leaks in async operations

### Testing Requirements
- [ ] Unit tests for all query hooks
- [ ] Integration tests for admin components
- [ ] Multi-tenant isolation verified
- [ ] Performance benchmarks met
- [ ] Error scenarios tested (network failures, 401, 403, 500)

### Documentation Requirements
- [ ] Query hook patterns documented in repo
- [ ] Migration guide for remaining components
- [ ] Code examples in documentation
- [ ] TypeScript types exported and documented

---

## Definition of Done

- [ ] All 7 stories completed and merged
- [ ] Code reviewed and approved by senior developer
- [ ] All tests passing (unit, integration, e2e)
- [ ] Performance benchmarks met and verified
- [ ] Documentation updated and reviewed
- [ ] Deployed to staging and verified
- [ ] Zebra Associates admin user tested and approved
- [ ] Deployed to production
- [ ] No regressions reported within 48 hours

---

## Technical Implementation Plan

### Query Hook Architecture
```typescript
// Pattern to follow (from useFeatureFlags.ts)
export const adminStatsKeys = {
  all: ['admin', 'stats'] as const,
  lists: () => [...adminStatsKeys.all, 'list'] as const,
  details: () => [...adminStatsKeys.all, 'detail'] as const,
}

export function useAdminStats(options?: UseQueryOptions) {
  return useQuery({
    queryKey: adminStatsKeys.all,
    queryFn: () => apiService.get('/admin/dashboard/stats'),
    staleTime: 30_000, // 30 seconds for frequently changing data
    cacheTime: 5 * 60 * 1000,
    retry: 2,
    ...options,
  })
}
```

### Migration Approach
1. Create query hook in `/src/hooks/api/` directory
2. Add query key factory for cache management
3. Replace manual state in component with query hook
4. Remove `useState`, `useEffect`, manual error handling
5. Add loading and error UI using query states
6. Test in development environment
7. Verify multi-tenant isolation
8. Code review and merge

### Files to Modify
- `/src/components/admin/AdminStats.tsx` (remove manual state)
- `/src/components/admin/UnifiedUserManagement.tsx` (remove manual state)
- `/src/components/admin/OrganizationManagement.tsx` (remove manual state)
- Create `/src/hooks/api/useAdminStats.ts` (new)
- Create `/src/hooks/api/useUsers.ts` (new)
- Create `/src/hooks/api/useOrganizations.ts` (new)
- Update `/docs/DEVELOPER_GUIDE.md` (add query patterns)

---

## Dependencies

**Blockers:** None (all infrastructure in place)

**Depends On:**
- QueryProvider already configured ✅
- apiService infrastructure exists ✅
- Auth0 authentication working ✅
- Multi-tenant context available ✅

**Blocks:**
- Epic #3 (Mutations) - needs query hooks established
- Epic #4 (Optimization) - needs base implementation

---

## Risk Assessment

**Technical Risks:**
- **Low:** Query key conflicts - Mitigated by factory pattern
- **Low:** Cache invalidation issues - Mitigated by testing
- **Medium:** Multi-tenant data leakage - Mitigated by RLS policies + testing

**Business Risks:**
- **Low:** Admin panel downtime - Mitigated by incremental rollout
- **Critical:** Zebra Associates user impact - Mitigated by UAT testing

**Mitigation Strategy:**
- Feature branch development
- Comprehensive testing before merge
- Staged rollout (dev → staging → production)
- Rollback plan: Keep manual patterns in Git history

---

## Performance Benchmarks

### Current State (Baseline)
- Admin stats: 500ms first load, 500ms every navigation
- User list: 300ms first load, 300ms every navigation
- Organization list: 250ms first load, 250ms every navigation
- **Total API calls per session:** ~15 redundant calls

### Target State (After Migration)
- Admin stats: 500ms first load, **0ms cached navigation** (instant)
- User list: 300ms first load, **0ms cached navigation** (instant)
- Organization list: 250ms first load, **0ms cached navigation** (instant)
- **Total API calls per session:** ~5 calls (60% reduction)

---

## Testing Strategy

### Unit Tests
```typescript
// Test query hooks
describe('useAdminStats', () => {
  it('fetches admin stats successfully', async () => {
    const { result, waitFor } = renderHook(() => useAdminStats(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toBeDefined()
  })
})
```

### Integration Tests
- Test full admin panel flow with React Query
- Verify cache persistence across navigation
- Test multi-tenant data isolation
- Test error scenarios and retry logic

### Performance Tests
- Measure API call reduction
- Measure navigation speed improvement
- Verify no memory leaks

---

## Rollout Plan

**Week 1:**
- Day 1-2: Create query hooks (Stories #5, #6, #7, #8)
- Day 3: Code review and testing
- Day 4-5: Merge to main branch

**Week 2:**
- Day 1-2: Migrate AdminStats (Story #9)
- Day 3-4: Migrate UnifiedUserManagement (Story #10)
- Day 5: Migrate OrganizationManagement (Story #11)

**Week 3:**
- Day 1: Documentation (Story #12)
- Day 2: Staging deployment and testing
- Day 3: UAT with Zebra Associates user
- Day 4: Production deployment
- Day 5: Monitor and verify

---

## Reference Implementation

**Best Practice Example:**
`/src/hooks/useFeatureFlags.ts` - Follow this pattern for all query hooks

**Key Patterns to Replicate:**
- Query key factory for cache management
- Proper TypeScript typing
- Loading and error state handling
- Offline fallback support
- Consistent naming conventions

---

## Comments

This epic is the foundation for the entire React Query migration. Getting admin panel patterns right will make subsequent migrations faster and easier. The admin panel is high-visibility (Zebra Associates opportunity) and high-duplication (most technical debt), making it the perfect starting point.

**Zebra Associates Impact:**
The super_admin user (matt.lindop@zebra.associates) relies heavily on the admin dashboard. Improving performance here directly supports the £925K opportunity.
