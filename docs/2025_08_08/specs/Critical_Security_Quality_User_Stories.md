# Critical Security & Quality User Stories
## Development-Ready Stories for Critical Success Path

**Document Version:** 1.0  
**Created:** 2025-08-08  
**Priority:** Critical  
**Context:** Technical debt resolution and security hardening for multi-tenant platform

---

## Epic Overview

The platform has a solid multi-tenant foundation but lacks critical security enforcement and quality assurance capabilities. These user stories address the four critical path items identified by the technical architect to ensure production readiness and security compliance.

**Critical Success Path Items:**
1. Implement RLS policies (1-2 days) - Critical security fix
2. Add tenant context middleware (2-3 days) - Enforce data isolation
3. Frontend testing framework (3-5 days) - Essential for quality
4. Remove debug code (1 day) - Security cleanup

---

## User Story 1: Row Level Security Implementation

### Story
**As a** Platform Security Administrator  
**I want** Row Level Security (RLS) policies implemented on all multi-tenant tables  
**So that** tenant data is automatically isolated at the database level and cannot be accessed across tenant boundaries

### Priority & Estimation
- **Priority:** P0 - Critical Security Fix
- **Story Points:** 5
- **Duration:** 1-2 days
- **Dependencies:** None (foundational requirement)

### Detailed Acceptance Criteria

#### AC1: RLS Policy Implementation
- **Given** the multi-tenant database schema exists
- **When** RLS policies are implemented
- **Then** all tenant-scoped tables must have RLS enabled
- **And** policies must enforce `organisation_id` filtering for all tenant-scoped operations
- **And** policies must be tested with cross-tenant access attempts

#### AC2: Database Tables Covered
The following tables must have RLS policies implemented:
- `users` (filtered by `organisation_id`)
- `audit_logs` (filtered by `organisation_id`) 
- `feature_flag_usage` (filtered by `organisation_id`)
- `feature_flag_overrides` (filtered by `organisation_id`)
- `organisation_modules` (filtered by `organisation_id`)
- `module_configurations` (filtered by `organisation_id`)
- `module_usage_logs` (filtered by `organisation_id`)
- All Market Edge tool-specific tables (filtered by `organisation_id`)

#### AC3: RLS Policy Rules
- **Given** a user is authenticated with tenant context
- **When** they query any tenant-scoped table
- **Then** only records matching their `organisation_id` are returned
- **And** INSERT operations only succeed with their `organisation_id`
- **And** UPDATE/DELETE operations only affect records within their tenant

#### AC4: Super Admin Access
- **Given** a user has super admin role (zebra user type)
- **When** they access the system with appropriate permissions
- **Then** they can bypass RLS for cross-tenant operations when explicitly required
- **And** all cross-tenant access is logged in audit trails

### Definition of Done
- [ ] RLS policies created for all tenant-scoped tables
- [ ] Database migration script created and tested
- [ ] RLS policies tested with multiple tenant scenarios
- [ ] Cross-tenant access attempts blocked and logged
- [ ] Super admin bypass mechanism implemented and tested
- [ ] Documentation updated with RLS policy details
- [ ] Code review completed and approved
- [ ] Integration tests pass with RLS enabled

### Technical Implementation Notes

#### Database Migration Structure
```sql
-- Enable RLS on tenant-scoped tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
-- ... (continue for all tenant tables)

-- Create policies for regular users
CREATE POLICY tenant_isolation_users ON users 
    FOR ALL TO authenticated 
    USING (organisation_id = current_setting('app.current_tenant_id')::uuid);

-- Create policies for super admins
CREATE POLICY super_admin_access_users ON users 
    FOR ALL TO authenticated 
    USING (
        current_setting('app.current_user_role') = 'super_admin' 
        OR organisation_id = current_setting('app.current_tenant_id')::uuid
    );
```

#### Required Session Context
- Set `app.current_tenant_id` in database session
- Set `app.current_user_role` for role-based policy decisions
- Implement connection pooling considerations for session variables

---

## User Story 2: Tenant Context Enforcement Middleware

### Story
**As a** Platform Developer  
**I want** tenant context middleware that automatically enforces data isolation at the API level  
**So that** all API requests are scoped to the authenticated user's tenant and data leakage is impossible

### Priority & Estimation
- **Priority:** P0 - Critical Security Infrastructure
- **Story Points:** 8
- **Duration:** 2-3 days
- **Dependencies:** User Story 1 (RLS policies)

### Detailed Acceptance Criteria

#### AC1: Middleware Implementation
- **Given** a user makes an authenticated API request
- **When** the request reaches any tenant-scoped endpoint
- **Then** tenant context middleware automatically sets database session variables
- **And** the user's `organisation_id` is extracted from the JWT token
- **And** database session is configured with tenant context before query execution

#### AC2: Automatic Tenant Scoping
- **Given** tenant context middleware is active
- **When** any database query executes
- **Then** the query is automatically scoped to the user's tenant via session variables
- **And** no manual tenant filtering is required in business logic
- **And** all queries respect RLS policies

#### AC3: Error Handling & Security
- **Given** a request lacks proper tenant context
- **When** the middleware processes the request
- **Then** the request is rejected with HTTP 401 Unauthorized
- **And** the security event is logged to audit trail
- **And** no database queries execute without tenant context

#### AC4: Super Admin Context Handling
- **Given** a super admin user makes a request
- **When** they need cross-tenant access
- **Then** middleware supports explicit tenant context override
- **And** all cross-tenant operations are logged with justification
- **And** default behavior still scopes to their primary tenant

#### AC5: Performance Requirements
- **Given** the middleware is processing requests
- **When** measuring performance impact
- **Then** middleware adds < 5ms to request processing time
- **And** database connection pooling works correctly with session variables
- **And** no connection leaks occur between tenant contexts

### Definition of Done
- [ ] Tenant context middleware implemented in FastAPI
- [ ] Middleware extracts tenant ID from JWT automatically
- [ ] Database session variables set correctly for all requests
- [ ] Error handling for missing/invalid tenant context
- [ ] Super admin cross-tenant access mechanism
- [ ] Performance benchmarks meet < 5ms overhead requirement
- [ ] Integration tests cover all tenant scenarios
- [ ] Load testing validates connection pooling behavior
- [ ] Security testing confirms no tenant data leakage
- [ ] Code review and security review completed

### Technical Implementation Notes

#### Middleware Structure
```python
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user

class TenantContextMiddleware:
    async def __call__(self, request: Request, call_next):
        # Extract tenant from authenticated user
        user = await get_current_user(request)
        
        # Set database session variables
        db = get_db()
        db.execute(text(
            "SELECT set_config('app.current_tenant_id', :tenant_id, true)"
        ), {"tenant_id": str(user.organisation_id)})
        
        db.execute(text(
            "SELECT set_config('app.current_user_role', :role, true)"
        ), {"role": user.role.value})
        
        response = await call_next(request)
        return response
```

#### Database Session Configuration
- Implement session variable cleanup between requests
- Handle connection pooling with session-scoped variables
- Optimize for high-concurrency scenarios

---

## User Story 3: Frontend Testing Framework

### Story
**As a** Frontend Developer  
**I want** a comprehensive testing framework for the Next.js frontend  
**So that** I can write reliable tests for components, pages, and user interactions to ensure code quality

### Priority & Estimation
- **Priority:** P1 - Critical Quality Infrastructure
- **Story Points:** 13
- **Duration:** 3-5 days
- **Dependencies:** None (independent implementation)

### Detailed Acceptance Criteria

#### AC1: Testing Framework Setup
- **Given** the Next.js frontend application exists
- **When** the testing framework is implemented
- **Then** Jest and React Testing Library are configured and working
- **And** TypeScript support is fully enabled for tests
- **And** test environment closely mirrors production environment

#### AC2: Component Testing Capabilities
- **Given** the testing framework is set up
- **When** developers write component tests
- **Then** they can test React component rendering and props
- **And** they can simulate user interactions (clicks, form inputs, navigation)
- **And** they can mock API calls and external dependencies
- **And** they can test responsive behavior and accessibility

#### AC3: Integration Testing Support
- **Given** the testing framework supports integration tests
- **When** testing user workflows
- **Then** tests can simulate complete user journeys (login → dashboard → features)
- **And** tests can validate API integration with mocked backends
- **And** tests can verify authentication flows and protected routes

#### AC4: Testing Coverage Requirements
- **Given** the testing framework is implemented
- **When** measuring test coverage
- **Then** coverage reporting is enabled and configured
- **And** CI/CD pipeline enforces minimum coverage thresholds
- **And** critical user paths have 100% test coverage

#### AC5: Test Organization & Performance
- **Given** tests are written using the framework
- **When** the test suite runs
- **Then** tests are organized by feature/component logically
- **And** test execution time is < 30 seconds for unit tests
- **And** tests run reliably in CI/CD environment

### Definition of Done
- [ ] Jest and React Testing Library installed and configured
- [ ] TypeScript test configuration working
- [ ] Test utilities and helpers created
- [ ] Mock setup for API calls and external services
- [ ] Component test examples for key UI components
- [ ] Integration test examples for user workflows
- [ ] Test coverage reporting configured
- [ ] CI/CD integration for automated testing
- [ ] Documentation for writing and running tests
- [ ] Team training materials created

### Technical Implementation Notes

#### Required Dependencies
```json
{
  "devDependencies": {
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/user-event": "^14.4.3",
    "jest": "^29.0.0",
    "jest-environment-jsdom": "^29.0.0",
    "@types/jest": "^29.0.0",
    "msw": "^0.47.0"
  }
}
```

#### Test Configuration Structure
```javascript
// jest.config.js
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    '^@/components/(.*)$': '<rootDir>/src/components/$1',
    '^@/pages/(.*)$': '<rootDir>/src/pages/$1',
    '^@/lib/(.*)$': '<rootDir>/src/lib/$1',
  },
  testEnvironment: 'jest-environment-jsdom',
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
```

#### Priority Test Areas
1. **Authentication Components** - Login, logout, token refresh
2. **Dashboard Components** - Data display, navigation, user interactions
3. **Market Edge Components** - Competitive analysis interface, charts, filters
4. **Admin Components** - User management, feature flags, audit logs
5. **Shared UI Components** - Buttons, modals, forms, loading states

---

## User Story 4: Production Debug Code Cleanup

### Story
**As a** Platform Security Administrator  
**I want** all debug code and console logging removed from production authentication endpoints  
**So that** sensitive authentication data is not exposed in logs and the production system is secure

### Priority & Estimation
- **Priority:** P0 - Critical Security Fix
- **Story Points:** 3
- **Duration:** 1 day
- **Dependencies:** None (cleanup task)

### Detailed Acceptance Criteria

#### AC1: Debug Code Identification
- **Given** the authentication codebase exists
- **When** conducting a security audit
- **Then** all `print()` statements in auth endpoints are identified
- **And** all `console.log()` statements in frontend auth code are identified
- **And** all debug logging that exposes sensitive data is catalogued

#### AC2: Authentication Endpoint Cleanup
- **Given** debug code exists in `/api/auth.py`
- **When** the cleanup is implemented
- **Then** all `print()` statements are removed from login endpoint (lines 37, 45, 51, 53)
- **And** sensitive data logging is replaced with secure logging
- **And** no authentication tokens or codes are logged in production

#### AC3: Structured Logging Implementation
- **Given** debug print statements are removed
- **When** proper logging is implemented
- **Then** authentication events are logged using the configured logger
- **And** log levels are appropriate (INFO for success, ERROR for failures)
- **And** sensitive data is never included in log messages
- **And** logs include sufficient context for debugging without exposing secrets

#### AC4: Frontend Debug Cleanup
- **Given** the frontend authentication components exist
- **When** reviewing for debug code
- **Then** all `console.log()` statements with sensitive data are removed
- **And** production builds exclude development-only debugging code
- **And** error handling maintains user experience without exposing internals

#### AC5: Security Validation
- **Given** debug code cleanup is complete
- **When** testing authentication flows
- **Then** no sensitive data appears in application logs
- **And** no authentication details are exposed to client-side logging
- **And** error messages are user-friendly without revealing system internals

### Definition of Done
- [ ] All debug `print()` statements removed from auth endpoints
- [ ] Structured logging implemented for auth events
- [ ] Frontend console logging cleaned up
- [ ] Production log review shows no sensitive data exposure
- [ ] Authentication flows tested and working correctly
- [ ] Security review confirms no information leakage
- [ ] Error handling maintains user experience
- [ ] Code review completed and approved

### Technical Implementation Notes

#### Current Debug Code Locations
```python
# File: /app/api/api_v1/endpoints/auth.py
# Lines to replace:

# Line 37: print(f"Login attempt with code: {login_data.code[:10]}... and redirect_uri: {login_data.redirect_uri}")
# Line 45: print("Failed to exchange authorization code")
# Line 51: print(f"Token exchange successful, got token: {token_data.get('access_token', 'N/A')[:10]}...")
# Line 53: print(f"Error in login endpoint: {str(e)}")
```

#### Secure Logging Replacement
```python
import logging
from app.core.logging import get_logger

logger = get_logger(__name__)

# Replace debug prints with:
logger.info("Authentication attempt initiated", extra={
    "event": "auth_attempt",
    "redirect_uri_domain": extract_domain(login_data.redirect_uri)
})

logger.error("Token exchange failed", extra={
    "event": "auth_failure",
    "error_type": "token_exchange"
})

logger.info("Authentication successful", extra={
    "event": "auth_success", 
    "user_id": str(user.id)
})
```

#### Security Guidelines
- Never log full tokens, codes, or passwords
- Use structured logging with appropriate context
- Log security events for monitoring and alerting
- Ensure log aggregation systems handle sensitive data properly

---

## Implementation Sequence & Dependencies

### Phase 1: Security Foundation (Days 1-2)
1. **User Story 4** - Debug code cleanup (1 day)
2. **User Story 1** - RLS policies implementation (1-2 days)

### Phase 2: Security Enforcement (Days 3-5)
3. **User Story 2** - Tenant context middleware (2-3 days)
   - Depends on: User Story 1 (RLS policies)

### Phase 3: Quality Infrastructure (Days 6-10)
4. **User Story 3** - Frontend testing framework (3-5 days)
   - Independent implementation, can run in parallel

### Total Timeline
- **Minimum:** 7 days (if all estimates are met)
- **Maximum:** 10 days (accounting for complexity)
- **Critical path:** Stories 1 → 2 (security foundation)
- **Parallel track:** Story 3 (quality infrastructure)

---

## Risk Mitigation

### Technical Risks
1. **RLS Performance Impact** - Monitor query performance after RLS implementation
2. **Middleware Complexity** - Validate session variable handling in connection pooling
3. **Testing Framework Compatibility** - Ensure Next.js 14 compatibility with testing tools

### Security Risks
1. **Data Exposure During Migration** - Test RLS policies in staging environment first
2. **Authentication Disruption** - Deploy debug cleanup during low-traffic window
3. **Cross-Tenant Data Leakage** - Comprehensive testing of tenant isolation

### Quality Risks
1. **Test Framework Adoption** - Provide training and documentation for team
2. **Coverage Enforcement** - Gradually increase coverage requirements
3. **CI/CD Integration** - Ensure stable test execution in automated pipelines

---

## Success Metrics

### Security Metrics
- Zero cross-tenant data access attempts succeed
- Authentication logs contain no sensitive data
- All security events properly logged and monitored

### Quality Metrics
- Frontend test coverage > 80% for critical paths
- Test suite execution time < 30 seconds
- Zero test failures in CI/CD pipeline

### Performance Metrics
- API response time increase < 5ms with middleware
- Database query performance maintained with RLS
- Frontend build and test times remain acceptable

---

**Document Owner:** Sarah (Technical Product Owner)  
**Review Status:** Ready for Development  
**Next Review:** After Phase 1 completion