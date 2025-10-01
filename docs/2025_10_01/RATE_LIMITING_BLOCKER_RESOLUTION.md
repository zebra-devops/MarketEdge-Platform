# Rate Limiting Blocker Resolution Guide

**Date:** 2025-10-01
**Priority:** CRITICAL - Must resolve before production deployment

---

## Blocker 1: Rate Limiting Disabled

### Current State
```bash
# .env
RATE_LIMIT_ENABLED=false  # ❌ DISABLED
```

### Resolution Steps

1. **Update Environment Configuration**
   ```bash
   # Edit .env file
   vim /Users/matt/Sites/MarketEdge/.env

   # Change line:
   RATE_LIMIT_ENABLED=false

   # To:
   RATE_LIMIT_ENABLED=true
   ```

2. **Restart Backend**
   ```bash
   # Kill existing backend process
   pkill -f "uvicorn app.main:app"

   # Start backend (from project root)
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Verify Rate Limiting Enabled**
   ```bash
   # Check backend logs for:
   grep "auth_rate_limiter_init" /tmp/backend_test.log | tail -1

   # Should show:
   # "enabled": true
   ```

4. **Test Rate Limiting Works**
   ```bash
   # Make 11 rapid requests
   for i in {1..11}; do
     curl -s -w "\n%{http_code}\n" \
       -X POST http://localhost:8000/api/v1/auth/login \
       -H "Content-Type: application/json" \
       -d '{"code":"test","redirect_uri":"http://localhost:3000/callback"}'
   done

   # Expected: First 10 succeed, 11th returns 429
   ```

---

## Blocker 2: API Router Import Failure

### Current Error
```
ImportError: cannot import name 'verify_auth0_token'
from 'app.auth.auth0' (/Users/matt/Sites/MarketEdge/app/auth/auth0.py)
```

### Root Cause Analysis

The API router expects a function called `verify_auth0_token` but it's either:
1. Not defined in `app/auth/auth0.py`
2. Not exported properly
3. Named differently

### Resolution Steps

1. **Check Current Auth0 Module**
   ```bash
   # Look for JWT verification functions
   grep -n "def.*verify" /Users/matt/Sites/MarketEdge/app/auth/auth0.py

   # Look for token-related functions
   grep -n "def.*token" /Users/matt/Sites/MarketEdge/app/auth/auth0.py
   ```

2. **Check What's Being Imported**
   ```bash
   # See what the endpoint is trying to import
   grep "from.*auth0 import" /Users/matt/Sites/MarketEdge/app/api/api_v1/endpoints/auth.py
   ```

3. **Possible Solutions**

   **Option A: Function exists but named differently**
   ```python
   # If auth0.py has verify_jwt_token instead of verify_auth0_token

   # In app/api/api_v1/endpoints/auth.py:
   # Change:
   from ....auth.auth0 import auth0_client, verify_auth0_token

   # To:
   from ....auth.auth0 import auth0_client, verify_jwt_token as verify_auth0_token
   ```

   **Option B: Function doesn't exist (create it)**
   ```python
   # Add to app/auth/auth0.py:

   async def verify_auth0_token(token: str) -> dict:
       """Verify Auth0 JWT token and return payload."""
       # Implementation depends on existing auth0_client
       return await auth0_client.verify_token(token)
   ```

   **Option C: Import from different location**
   ```python
   # If verify_auth0_token is in app/auth/jwt.py instead

   # In app/api/api_v1/endpoints/auth.py:
   from ....auth.jwt import verify_auth0_token
   from ....auth.auth0 import auth0_client
   ```

4. **Verify Fix**
   ```bash
   # Try importing in Python
   cd /Users/matt/Sites/MarketEdge
   source venv/bin/activate
   python -c "from app.auth.auth0 import verify_auth0_token; print('SUCCESS')"

   # Should print: SUCCESS
   ```

5. **Restart Backend and Check**
   ```bash
   # Restart backend
   pkill -f uvicorn
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # Check logs - should NOT see import error
   tail -f /tmp/backend_test.log | grep -E "(import|router)"

   # Should see:
   # ✅ API router included successfully
   # ❌ Should NOT see: "API router import failed"
   ```

6. **Test Auth Endpoints Available**
   ```bash
   # Test /auth0-url endpoint
   curl -v "http://localhost:8000/api/v1/auth/auth0-url?redirect_uri=http://localhost:3000/callback"

   # Expected: 200 OK (not 405 Method Not Allowed)
   ```

---

## Verification After Fixes

### Complete Test Suite
```bash
# Run full rate limiting test suite
/Users/matt/Sites/MarketEdge/scripts/security/verify_rate_limiting.sh
```

### Expected Results After Fixes

**Test 1: IP Spoofing Prevention**
- ✅ PASS - Already working

**Test 2: Fail-Closed Security**
- ⏭️ SKIPPED - Manual test required in staging

**Test 3: Redis Namespace Isolation**
- ✅ PASS - Keys should appear: `development:rate_limit:*`

**Test 4: Auth0 URL Protection**
- ✅ PASS - 31st request should return 429

**Test 5: Per-User Rate Limiting**
- ✅ PASS - Unauthenticated limited after 10 requests

**Test 6: Environment-Aware Defaults**
- ✅ PASS - Already working

### Final Validation
```bash
# All tests should pass
echo "Exit code: $?"  # Should be 0

# Check summary
grep -A 3 "Test Results Summary" /tmp/test_output.log
# Should show:
# PASSED: 5
# FAILED: 0
```

---

## Production Deployment Configuration

After resolving blockers, configure for production:

### Environment Variables
```bash
# .env.production
RATE_LIMIT_ENABLED=true
RATE_LIMIT_AUTH_REQUESTS=10/5minutes
RATE_LIMIT_AUTH_REQUESTS_USER=50/5minutes
RATE_LIMIT_STORAGE_URL=redis://production-redis.internal:6379/1
ENV_NAME=production

# Trusted proxies - CRITICAL: Only your load balancer IPs
TRUSTED_PROXIES=["10.0.0.0/8"]  # Update with actual LB CIDR
```

### Monitoring Setup
```bash
# Monitor rate limit violations
# Look for 429 responses in logs
grep '"status_code": 429' /var/log/app/backend.log | wc -l

# Alert on excessive rate limiting (possible attack)
# Set threshold: >100 rate limits per minute
```

### Health Checks
```bash
# Add to deployment health checks
curl -f http://localhost:8000/health || exit 1

# Verify Redis connectivity
redis-cli -h production-redis.internal ping || exit 1
```

---

## Rollback Plan

If rate limiting causes issues in production:

### Immediate Mitigation
```bash
# Disable rate limiting temporarily
export RATE_LIMIT_ENABLED=false

# Restart application
systemctl restart marketedge-backend
```

### Investigate
```bash
# Check for false positives
grep '"status_code": 429' /var/log/app/backend.log | \
  jq -r '.client_ip' | sort | uniq -c | sort -rn

# Look for IP patterns
# High count from single IP = likely attack (rate limit working)
# High count from many IPs = possible false positive
```

### Adjust Limits
```bash
# If limits too strict, increase temporarily
export RATE_LIMIT_AUTH_REQUESTS=20/5minutes  # Double limit

# Restart and monitor
systemctl restart marketedge-backend
```

---

## Support Contacts

- **DevOps Engineer:** Maya (this agent)
- **Backend Developer:** dev agent (for auth0 import issue)
- **Security Review:** cr agent (for security validation)

---

## Timeline

| Step | Priority | Estimated Time | Owner |
|------|----------|----------------|-------|
| Enable rate limiting | CRITICAL | 5 minutes | DevOps |
| Fix API router import | CRITICAL | 30-60 minutes | Backend Dev |
| Re-run test suite | HIGH | 10 minutes | DevOps/QA |
| Staging deployment | HIGH | 1-2 hours | DevOps |
| Production deployment | HIGH | 30 minutes | DevOps |

**Total:** 2-4 hours to production ready

---

**Document Version:** 1.0
**Last Updated:** 2025-10-01 12:40:00 BST
**Status:** Ready for implementation
