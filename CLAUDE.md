# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MarketEdge Platform is a multi-tenant business intelligence SaaS platform providing competitive analysis across diverse industries (Cinema, Hotel, Gym, B2B, Retail). The platform consists of a FastAPI backend and Next.js frontend with Auth0 authentication and tenant-aware data isolation.

## Architecture

### Repository Structure
- **Root**: FastAPI backend (`/app/`, `/database/`, `/tests/`)  
- **Frontend**: Next.js frontend (`/platform-wrapper/frontend/`)
- **Key Business Logic**: £925K Zebra Associates opportunity with super_admin role requirements

### Critical Components
- **Multi-tenant isolation**: PostgreSQL Row Level Security (RLS) policies
- **Authentication**: Auth0 JWT tokens with role-based access control (admin, super_admin, user, analyst)
- **Middleware order**: CORSMiddleware FIRST, then ErrorHandler, then others (critical for error responses)
- **Industry-specific dashboards**: SIC code classification with tailored analytics

## Common Commands

### Backend Development
```bash
# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database operations
alembic upgrade head                    # Apply migrations
alembic revision --autogenerate -m ""  # Create migration
python database/seeds/initial_data.py  # Seed base data
python database/seeds/phase3_data.py   # Seed feature flags & modules

# Testing
pytest                                 # Run all tests
pytest tests/test_auth.py             # Run specific tests
pytest --cov=app                      # Run with coverage
```

### Frontend Development
```bash
cd platform-wrapper/frontend

# Development
npm run dev                           # Start dev server (port 3000)
npm run build                        # Production build
npm run type-check                   # TypeScript validation

# Testing
npm run test                         # Unit tests
npm run test:integration             # Integration tests
npm run test:e2e                     # E2E tests (Playwright)
npm run test:multi-tenant           # Multi-tenant specific tests
```

### Database Management
```bash
# Reset database (destructive)
cd scripts/dev && ./reset-db.sh

# Check migration status
alembic current
alembic history

# Emergency database fixes
python emergency_db_fix.py           # Use cautiously
```

## Authentication & Security

### Critical Auth Flow (Pure Auth0 - Security Enhanced)
1. **Login**: Auth0 provides authorization codes
2. **Token Exchange**: Backend exchanges for Auth0 JWT tokens with tenant context
3. **Token Verification**:
   - Cryptographic JWT signature verification using Auth0 JWKS (public keys)
   - Validates standard claims (exp, iss, aud)
   - Secondary validation with Auth0 userinfo endpoint for freshness
   - JWKS cached for 1 hour with graceful key rotation handling
4. **Token Refresh**:
   - Uses Auth0 refresh token flow (not internal JWTs)
   - Fallback to internal JWT refresh for backwards compatibility
   - Consistent with login flow (Auth0 tokens throughout)
5. **Frontend Storage**:
   - Access tokens: httpOnly: false (accessible to JavaScript)
   - Refresh tokens: httpOnly: true (secure, HTTP-only)
6. **Authorization**: Admin endpoints require `super_admin` or `admin` role

### Key Security Settings
- **Token expiry**: 30 minutes access, 7 days refresh
- **JWT verification**: RS256 algorithm with Auth0 public keys
- **JWKS caching**: 1 hour TTL with stale-if-error fallback
- **Token refresh**: Pure Auth0 flow with internal JWT fallback
- **Cookie security**: Production uses httpOnly for refresh tokens
- **CORS middleware**: MUST be first in middleware stack for error responses
- **RLS policies**: Complete tenant data isolation at database level

### Security Fixes Implemented
- **CRITICAL FIX #2**: Auth0 JWT signature verification using JWKS (addresses code review issue)
- **CRITICAL FIX #3**: Token refresh flow consistency - Auth0 tokens throughout (addresses code review issue)
- **CRITICAL FIX #4**: CSRF protection validation using double-submit cookie pattern (addresses code review issue)

### CSRF Protection (CRITICAL FIX #4)
- **Pattern**: Double-submit cookie
- **Protected Methods**: POST, PUT, PATCH, DELETE
- **Token Header**: X-CSRF-Token
- **Cookie**: csrf_token (httpOnly=false for JS access)
- **Exempt Paths**: /auth/login, /auth/callback, /health, /docs
- **Token Length**: 64 characters (configurable)
- **Validation**: Constant-time comparison to prevent timing attacks

**Frontend Usage**:
1. CSRF token set in cookie on login
2. Frontend reads token from cookie
3. Include in X-CSRF-Token header for state-changing requests (POST/PUT/PATCH/DELETE)
4. Backend validates cookie token matches header token

**Security Benefits**:
- Prevents cross-site logout attacks
- Prevents account lockout via forced failed login attempts
- Protects all state-changing operations
- £925K Zebra Associates opportunity protected from CSRF attacks

## Critical Patterns

### Middleware Ordering (CRITICAL)
```python
# app/main.py - Order matters for response processing
app.add_middleware(CORSMiddleware)          # FIRST (runs last on response)
app.add_middleware(TrustedHostMiddleware)
app.add_middleware(CSRFMiddleware)          # CSRF protection
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
```

### Multi-tenant Context
```python
# Always set tenant context in dependencies
request.state.tenant_context = extract_tenant_context_from_token(payload)

# Use async database sessions consistently
db: AsyncSession = Depends(get_async_db)  # Not Session
```

### Frontend API Integration
```typescript
// Environment-aware token retrieval
const token = process.env.NODE_ENV === 'production' 
  ? Cookies.get('access_token')          // Production: cookies
  : localStorage.getItem('access_token') // Development: localStorage
```

## Testing Approach

### Backend Testing
- **Integration tests**: Full API endpoint testing with real database
- **Multi-tenant tests**: Verify tenant isolation and RLS policies
- **Security tests**: Authentication, authorization, and vulnerability testing
- **Async patterns**: All tests support async/await with proper teardown

### Frontend Testing
- **Component tests**: React Testing Library with user interactions
- **E2E tests**: Playwright for cross-browser testing
- **Multi-tenant tests**: Organization switching and context persistence
- **Accessibility tests**: WCAG 2.1 AA compliance validation

## Common Issues & Solutions

### CORS Errors Masking 500 Errors
**Problem**: Browser shows "No 'Access-Control-Allow-Origin'" instead of actual 500 errors
**Solution**: Ensure CORSMiddleware is added FIRST in middleware stack

### Authentication 403 vs 401 Issues
**Problem**: FastAPI HTTPBearer returns 403 for missing auth instead of 401
**Solution**: Use `HTTPBearer(auto_error=False)` and handle manually

### Database Migration Conflicts
**Problem**: Alembic autogenerate creates conflicting migrations
**Solution**: Review generated SQL, test on separate database first

### Multi-tenant Data Leakage
**Problem**: Data accessed across tenant boundaries
**Solution**: Verify RLS policies active, check `request.state.tenant_context`

## Production Deployment

### Backend (Render)
- **URL**: https://marketedge-platform.onrender.com
- **Health check**: `/health` endpoint
- **Key env vars**: DATABASE_URL, REDIS_URL, AUTH0_* settings
- **Cold start**: 52+ seconds on first request

### Frontend (Vercel - Planned)
- **Build command**: `npm run build`
- **Environment**: Links to production backend API
- **Auth integration**: Auth0 with production callbacks

## Feature Flags & Modules

### JSON-based Feature System
- **Location**: `/app/models/feature_flags.py`
- **Admin endpoints**: `/api/v1/admin/feature-flags`
- **Percentage rollouts**: Target specific user percentages
- **Organization overrides**: Per-tenant feature control

### Analytics Modules
- **SIC code integration**: UK Standard Industrial Classification
- **Industry-specific**: Tailored dashboards per sector
- **Pluggable architecture**: Enable/disable modules per organization

## Emergency Procedures

### Production Issues
1. Check health endpoints: `/health`, `/ready`
2. Review structured logs for error patterns
3. Verify middleware ordering in recent commits
4. Check Auth0 token validation and user roles

### Database Issues
1. Verify RLS policies active: `SHOW row_security;`
2. Check migration status: `alembic current`
3. Test tenant isolation with different organization contexts
4. Monitor slow queries and connection pools

### Authentication Issues
1. Verify Auth0 configuration and callback URLs
2. Check JWT token structure and claims
3. Test role-based access with different user types
4. Monitor token refresh and expiration flows

## Business Context

### Zebra Associates Opportunity (£925K)
- **Key user**: matt.lindop@zebra.associates (super_admin role required)
- **Critical endpoints**: `/admin/feature-flags`, `/admin/dashboard/stats`
- **Industry focus**: Cinema (SIC 59140) competitive intelligence
- **Success metrics**: Admin panel access, feature flag management, multi-tenant switching

This platform serves diverse industries with tenant-aware competitive intelligence, requiring careful attention to security, performance, and multi-tenant isolation patterns.