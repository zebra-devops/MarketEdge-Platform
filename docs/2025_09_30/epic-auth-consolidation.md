# Epic: One Auth to Rule Them All – Zebra-Safe Edition

## Epic Overview

**Epic Title:** One Auth to Rule Them All – Zebra-Safe Edition

**Goal:** Replace dual JWT + internal fallback with single Auth0-only flow, uniform uppercase enums, secure-cookie-only storage, and no conversion utilities.

**Business Context:** This epic addresses critical technical debt identified by the technical architect while protecting the £925K Zebra Associates opportunity. It simplifies authentication architecture, improves security, and eliminates format conversion complexity.

## Technical Context

This epic implements the authentication consolidation strategy outlined in the TA assessment, focusing on:
- Single source of truth (Auth0 only)
- Elimination of dual-token complexity
- Standardization of enum formats
- Enhanced security through cookie-only storage
- Protection of critical business relationships

## Risk Mitigation

**Primary Risk:** Breaking Zebra Associates access (£925K opportunity)
**Mitigation:** US-0 creates comprehensive smoke test that runs before any other changes

## Success Metrics

- Zero authentication-related incidents post-deployment
- Token payload size < 3.5 KB
- All regression tests passing
- No conversion utilities remaining in codebase
- Single authentication flow with no fallbacks

## Sprint Backlog (5 days, 2 pairs)

| Day | Stories | Focus |
|-----|---------|-------|
| Mon | US-0 Cypress test + CI gate (pair 1), US-6A backup & staging run (pair 2) | Safety First |
| Tue | US-1 + US-2 (pair 1), US-5 start (pair 2) | Core Changes |
| Wed | US-3 + US-4 (pair 1), US-5 finish + US-7 (pair 2) | Cleanup |
| Thu | US-6 production migration (both pairs) | Critical Migration |
| Fri | US-8 full regression + 24-h monitoring setup | Validation |

## Enhanced Definition of Done

**Applies to every story:**

- [ ] Code peer-reviewed & merged to main
- [ ] Unit test coverage ≥ 80% of diff
- [ ] Zebra Associates smoke test passes (matt.lindop login)
- [ ] Token payload size < 3.5 KB (measured in Auth0 dashboard)
- [ ] Database backup verified restorable (for any DB-changing story)
- [ ] Rollback procedure documented & tested (link in PR)
- [ ] Auth0 dashboard shows zero "Invalid Signature" or "Invalid Token" spikes 24h post-deploy
- [ ] Cypress auth regression pack green
- [ ] No new Sentry errors 30 min after deploy

## Output Artifacts

1. `docs/auth/rollback-enum-migration.md` – exact commands + timing
2. `scripts/zebra-smoke.js` – standalone test runner for sales demos
3. Auth0 Rule version tag v1.3-claims pinned in dashboard
4. Run-book page "Auth0 Token Size Monitoring" with 3.5 KB alert

## Dependencies

- US-0 MUST complete before any other story begins
- US-6A MUST complete before US-6 can execute
- All stories depend on maintaining Zebra Associates access

## Related Documentation

- Technical Architecture assessment: `/docs/2025_09_24/design/AuthenticationStrategy.md`
- Current auth architecture: `/docs/authentication-architecture.md`
- Database migration safety: `/docs/database/migration-safety.md`