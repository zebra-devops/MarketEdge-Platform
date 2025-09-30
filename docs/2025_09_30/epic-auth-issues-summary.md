# Authentication Epic - GitHub Issues Summary

## Epic Created

**Epic: One Auth to Rule Them All – Zebra-Safe Edition**
- **GitHub Issue**: #35
- **URL**: https://github.com/zebra-devops/MarketEdge-Platform/issues/35
- **Status**: Created successfully
- **Contains**: Full epic context, sprint backlog, and links to all user stories

## User Stories Created

### Critical Path (Must Complete First)

**US-0: Zebra Associates Protection**
- **GitHub Issue**: #36
- **URL**: https://github.com/zebra-devops/MarketEdge-Platform/issues/36
- **Priority**: CRITICAL - Blocks all other work
- **Size**: S (1 dev-day)
- **Purpose**: Protect £925K opportunity with comprehensive smoke test

### Core Authentication Changes

**US-1: Turn off internal JWT issuer**
- **GitHub Issue**: #37
- **URL**: https://github.com/zebra-devops/MarketEdge-Platform/issues/37
- **Size**: S (1 dev-day)
- **Dependencies**: Depends on US-0

**US-2: Add custom claims to Auth0 token**
- **GitHub Issue**: #38
- **URL**: https://github.com/zebra-devops/MarketEdge-Platform/issues/38
- **Size**: M (2 dev-days)
- **Dependencies**: Depends on US-0

**US-3: Swap verifier to Auth0 only (kill fallback)**
- **GitHub Issue**: #39
- **URL**: https://github.com/zebra-devops/MarketEdge-Platform/issues/39
- **Size**: S (1 dev-day)
- **Dependencies**: Depends on US-0, US-1, US-2

**US-4: Delete internal JWT tables & models**
- **GitHub Issue**: #40
- **URL**: https://github.com/zebra-devops/MarketEdge-Platform/issues/40
- **Size**: S (½ dev-day)
- **Dependencies**: Depends on US-0, US-3

### Frontend & Security

**US-5: Cookie-only storage (no localStorage branch)**
- **GitHub Issue**: #41
- **URL**: https://github.com/zebra-devops/MarketEdge-Platform/issues/41
- **Size**: S (1 dev-day)
- **Dependencies**: Depends on US-0

### Database Migration

**US-6A: Enum Migration Safety**
- **GitHub Issue**: #42
- **URL**: https://github.com/zebra-devops/MarketEdge-Platform/issues/42
- **Size**: M (2 dev-days)
- **Dependencies**: Depends on US-0, BLOCKS US-6

**US-6: Uppercase enum everywhere (database & code)**
- **GitHub Issue**: #43
- **URL**: https://github.com/zebra-devops/MarketEdge-Platform/issues/43
- **Size**: M (2 dev-days)
- **Dependencies**: Depends on US-0, US-6A (MUST complete US-6A first)

### Cleanup & Testing

**US-7: Delete conversion & fallback utilities**
- **GitHub Issue**: #44
- **URL**: https://github.com/zebra-devops/MarketEdge-Platform/issues/44
- **Size**: S (½ dev-day)
- **Dependencies**: Depends on US-0, US-6

**US-8: End-to-end auth regression pack**
- **GitHub Issue**: #45
- **URL**: https://github.com/zebra-devops/MarketEdge-Platform/issues/45
- **Size**: M (2 dev-days)
- **Dependencies**: Depends on all other stories (validation)

## Sprint Planning Summary

### Day 1 (Monday)
- **Pair 1**: US-0 (Cypress test + CI gate)
- **Pair 2**: US-6A (backup & staging run)

### Day 2 (Tuesday)
- **Pair 1**: US-1 + US-2
- **Pair 2**: US-5 (start)

### Day 3 (Wednesday)
- **Pair 1**: US-3 + US-4
- **Pair 2**: US-5 (finish) + US-7

### Day 4 (Thursday)
- **Both Pairs**: US-6 (production migration)

### Day 5 (Friday)
- **Both Pairs**: US-8 (full regression + 24-hour monitoring)

## Critical Dependencies

1. **US-0 MUST complete before ANY other work begins** (protects Zebra Associates)
2. **US-6A MUST complete before US-6** (migration safety)
3. **US-1 and US-2 should complete before US-3** (prepare for verifier swap)
4. **US-6 should complete before US-7** (uppercase before cleanup)
5. **US-8 runs last** (validates entire implementation)

## Total Effort Estimate

- **Total Story Points**: 11.5 dev-days
- **Sprint Duration**: 5 days with 2 pairs (10 dev-days capacity)
- **Buffer**: 1.5 days for coordination, testing, and monitoring

## Success Criteria

1. Zero authentication incidents post-deployment
2. Zebra Associates access never broken
3. Token payload < 3.5 KB
4. All regression tests passing
5. No conversion utilities remaining
6. Single Auth0-only authentication flow

## Risk Mitigation

- **Primary Risk**: Breaking Zebra Associates (£925K)
- **Mitigation**: US-0 smoke test runs first and blocks all other work
- **Secondary Risk**: Database migration issues
- **Mitigation**: US-6A creates comprehensive backup and rollback plan

## Next Steps

1. Review and prioritize issues in GitHub project board
2. Assign developers to pair programming teams
3. Set up CI/CD pipeline for US-0 smoke test
4. Schedule maintenance window for US-6 production migration
5. Prepare monitoring dashboards for post-deployment validation