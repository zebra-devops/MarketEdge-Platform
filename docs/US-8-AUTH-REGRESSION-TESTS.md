# US-8: Auth Regression Test Suite

## Overview

Comprehensive end-to-end authentication testing suite for the MarketEdge platform, designed for:
- Regression detection during development
- Sales demo validation (Zebra Associates)
- CI/CD pipeline integration
- Production deployment verification

## Test Components

### 1. Playwright E2E Test Suite

**Location**: `platform-wrapper/frontend/e2e/auth-regression.spec.ts`

**Test Scenarios**:

1. **Login Success Flow**
   - Navigate to login page
   - Auth0 redirect and authentication
   - Callback handling
   - Dashboard access verification
   - User menu presence

2. **Application Access Navigation**
   - Market Edge route accessibility
   - Causal Edge route accessibility
   - Value Edge route accessibility
   - No authentication errors

3. **Token Refresh Flow**
   - Clear cookies/storage
   - Protected route access
   - Redirect to login verification

4. **401 Handling**
   - API request without auth
   - Proper 401 response
   - Error message validation

5. **Backend Health Check**
   - Backend availability
   - Health endpoint response

6. **Application Enum Verification**
   - Uppercase enum validation (MARKET_EDGE, CAUSAL_EDGE, VALUE_EDGE)

**Smoke Tests**:
- Frontend loads without errors
- Backend API responds

### 2. Standalone Smoke Test Script

**Location**: `scripts/zebra-smoke.js`

**Purpose**: Quick validation for sales demos and pre-deployment checks

**Tests**:
1. Backend health check
2. Frontend load verification
3. Login UI presence
4. Application route accessibility
5. Console error detection
6. Screenshot capture

**Usage**:
```bash
# From project root
node scripts/zebra-smoke.js

# From frontend directory
npm run smoke-test

# With visible browser
HEADLESS=false npm run smoke-test
```

**Output**:
- Console summary report
- `smoke-test-screenshot.png` (success)
- `smoke-test-failure.png` (failure)

### 3. CI/CD Integration

**Location**: `.github/workflows/auth-regression.yml`

**Triggers**:
- Pull requests to `main` or `test/*` branches
- Direct pushes to those branches
- Manual workflow dispatch

**Services**:
- PostgreSQL 15 (test database)
- Redis 7 (caching)

**Steps**:
1. Setup Python + backend dependencies
2. Run database migrations
3. Start backend server (port 8000)
4. Setup Node.js + frontend dependencies
5. Install Playwright browsers
6. Build and start frontend (port 3000)
7. Run auth regression tests
8. Upload test results and screenshots
9. Comment PR with results

**Required Secrets**:
- `AUTH0_DOMAIN`
- `AUTH0_CLIENT_ID`
- `AUTH0_CLIENT_SECRET`
- `AUTH0_AUDIENCE`
- `TEST_USER_PASSWORD` (optional, for full login tests)

## Running Tests Locally

### Prerequisites
```bash
# Install dependencies
cd platform-wrapper/frontend
npm install

# Install Playwright browsers
npx playwright install chromium
```

### Backend Setup
```bash
# Terminal 1: Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
# Terminal 2: Start frontend
cd platform-wrapper/frontend
npm run dev
```

### Run Tests

**Full auth regression suite**:
```bash
cd platform-wrapper/frontend
npm run test:auth-regression
```

**With UI mode** (interactive):
```bash
npx playwright test e2e/auth-regression.spec.ts --ui
```

**Headed mode** (visible browser):
```bash
npx playwright test e2e/auth-regression.spec.ts --headed
```

**Smoke test only**:
```bash
npm run smoke-test
```

## Test Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:3000` | Frontend URL |
| `API_URL` | `http://localhost:8000` | Backend API URL |
| `TEST_PASSWORD` | (none) | Test user password for full login tests |
| `HEADLESS` | `true` | Run smoke test in headless mode |

## Interpreting Results

### Success Indicators
- ✅ All scenarios pass
- ✅ No critical console errors
- ✅ Screenshots show proper UI rendering
- ✅ Backend health check passes

### Common Failures

**Scenario 1 (Login) fails**:
- Check Auth0 configuration
- Verify `TEST_PASSWORD` is set
- Review Auth0 callback URLs

**Scenario 2 (Navigation) fails**:
- Check token storage (cookies/localStorage)
- Verify application routes exist
- Review user application access permissions

**Scenario 3 (Token Refresh) fails**:
- Check token expiry handling
- Verify redirect logic
- Review refresh token flow

**Scenario 4 (401 Handling) fails**:
- Check backend authentication middleware
- Verify 401 response format
- Review error handling

## Sales Demo Checklist

Before Zebra Associates demo:

1. **Run smoke test**:
   ```bash
   npm run smoke-test
   ```

2. **Verify screenshot**:
   - Check `smoke-test-screenshot.png`
   - Confirm UI renders correctly
   - No error messages visible

3. **Test login flow manually**:
   - Visit frontend URL
   - Click "Login"
   - Authenticate with matt.lindop@zebra.associates
   - Verify dashboard access
   - Switch between applications

4. **Check super_admin features**:
   - Access admin panel
   - Verify feature flag management
   - Test organization switcher

5. **Review logs**:
   ```bash
   # Check backend logs
   tail -f backend.log
   
   # Check for errors
   grep ERROR backend.log
   ```

## Maintenance

### Adding New Test Scenarios

1. Edit `e2e/auth-regression.spec.ts`
2. Add new `test()` block in appropriate `describe()` group
3. Follow existing patterns for:
   - Auth state management
   - Error handling
   - Screenshot capture
4. Update this documentation

### Updating Smoke Test

1. Edit `scripts/zebra-smoke.js`
2. Add test to `try` block
3. Update success summary
4. Test locally before committing

### CI/CD Updates

1. Edit `.github/workflows/auth-regression.yml`
2. Test workflow with:
   ```bash
   act -j auth-regression  # Using nektos/act for local testing
   ```
3. Monitor first run in GitHub Actions
4. Review artifacts and logs

## Troubleshooting

### Playwright Installation Issues
```bash
# Reinstall browsers
npx playwright install --force chromium

# With system dependencies
npx playwright install --with-deps chromium
```

### CI Timeouts
- Increase `timeout-minutes` in workflow
- Check service health checks
- Review server startup logs

### Screenshot Comparison Failures
- Update baseline screenshots
- Review visual regression tolerance
- Check viewport sizes

### Backend Connection Issues
```bash
# Check backend health
curl http://localhost:8000/health

# Check logs
uvicorn app.main:app --log-level debug
```

## Related Documentation

- [CLAUDE.md](/CLAUDE.md) - Project overview and commands
- [US-2-IMPLEMENTATION-SUMMARY.md](/docs/US-2-IMPLEMENTATION-SUMMARY.md) - Multi-tenant architecture
- [US-6 Migration Guide] - Uppercase enum migration
- [AUTH0_SECURITY_FIXES.md](/AUTH0_SECURITY_FIXES.md) - Auth security implementation

## Success Metrics

- ✅ All tests passing in CI
- ✅ < 5 minute test execution time
- ✅ Zero false positives in smoke tests
- ✅ Successful sales demos with Zebra Associates

## Support

For issues or questions:
1. Check test output and screenshots
2. Review backend/frontend logs
3. Consult this documentation
4. Contact development team
