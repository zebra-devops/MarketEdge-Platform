# Authentication Rate Limiting - SECURITY HARDENED

## Overview

Authentication rate limiting protects the MarketEdge platform from:
- **DoS attacks** on expensive Auth0 endpoints
- **CPU burn** from excessive authentication attempts
- **Auth0 bill spikes** from brute force attacks

## Security Hardening (2025-10-01)

This implementation includes **6 CRITICAL security fixes** from code review:

1. **IP Spoofing Prevention (CRITICAL)** - X-Forwarded-For validation with trusted proxies
2. **Fail-Closed Security (CRITICAL)** - Returns 503 on Redis failure instead of bypass
3. **Redis Namespace Isolation (CRITICAL)** - Environment-specific keys prevent interference
4. **Auth0 URL Protection (HIGH)** - /auth0-url endpoint rate limited
5. **Per-User Rate Limiting (HIGH)** - Higher limits for authenticated users
6. **Environment-Aware Defaults (MEDIUM)** - Development-friendly testing

## Configuration

### Environment Variables

```bash
# Enable/disable rate limiting (default: true)
RATE_LIMIT_ENABLED=true

# Rate limit for unauthenticated requests (per-IP, default: "10/5minutes")
RATE_LIMIT_AUTH_REQUESTS="10/5minutes"

# Rate limit for authenticated users (per-user, default: "50/5minutes")
RATE_LIMIT_AUTH_REQUESTS_USER="50/5minutes"

# Redis URL for distributed rate limiting (default: redis://localhost:6379/1)
RATE_LIMIT_STORAGE_URL="redis://localhost:6379/1"

# SECURITY: Trusted proxy CIDR blocks (CRITICAL for IP spoofing prevention)
TRUSTED_PROXIES="10.0.0.0/8,192.168.0.0/16,172.16.0.0/12"

# Environment namespace for Redis key isolation (auto-detects from RENDER_ENVIRONMENT)
ENV_NAME="development"  # or "staging", "production"
```

### Rate Limit Format

The rate limit string follows the format: `<requests>/<time_window>`

Examples:
- `"10/5minutes"` - 10 requests per 5 minutes
- `"5/minute"` - 5 requests per minute
- `"100/hour"` - 100 requests per hour

## Protected Endpoints

The following authentication endpoints are rate limited:

1. **POST /api/v1/auth/login** - OAuth2 login with authorization code (10/5min per IP)
2. **POST /api/v1/auth/login-oauth2** - Alternative OAuth2 login endpoint (10/5min per IP)
3. **POST /api/v1/auth/refresh** - Token refresh endpoint (50/5min per user)
4. **POST /api/v1/auth/user-context** - Auth0 Action callback for user context (10/5min per IP)
5. **GET /api/v1/auth/auth0-url** - Auth0 authorization URL generation (30/5min per IP) **[NEW]**

## Rate Limiting Behavior

### Per-IP and Per-User Tracking

Rate limits are enforced using two strategies:

1. **Per-IP Tracking (Unauthenticated)**: 10 requests / 5 minutes per IP address
   - Used for login, auth0-url, and other unauthenticated endpoints
   - Prevents distributed attacks
   - Protected against IP spoofing with trusted proxy validation

2. **Per-User Tracking (Authenticated)**: 50 requests / 5 minutes per user
   - Used for token refresh and authenticated endpoints
   - Higher limit to prevent corporate NAT blocking
   - Zebra Associates use case: Multiple users behind same corporate proxy

**Example:**
- **Unauthenticated**: IP 192.168.1.1 can make 10 login requests in 5 minutes
- **Authenticated**: user_123 from any IP can make 50 refresh requests in 5 minutes

### Rate Limit Exceeded Response

When rate limit is exceeded, the API returns:

**Status Code:** `429 Too Many Requests`

**Response Body:**
```json
{
  "detail": "Rate limit exceeded. Try again in 300 seconds.",
  "retry_after": 300,
  "limit": "10/5minutes",
  "message": "Too many authentication attempts from your IP address. Please wait before trying again."
}
```

**Response Headers:**
```
Retry-After: 300
X-RateLimit-Limit: 10/5minutes
X-RateLimit-Reset: 1704123600
```

### Fail-Closed Security (CRITICAL FIX #2)

**BREAKING CHANGE**: Rate limiting now **fails closed** instead of fail-open.

If Redis is unavailable:
- Rate limiting **returns 503 Service Unavailable** (fails closed)
- **Does NOT allow bypass** (prevents DoS vulnerability)
- Error is logged for monitoring
- Client should retry after brief delay

**Why fail-closed?**
- Fail-open allows DoS attacks when Redis is down
- Attacker could intentionally crash Redis to bypass limits
- 503 response provides clear signal that service is degraded

**Rollback procedure**: Set `RATE_LIMIT_ENABLED=false` to disable rate limiting entirely

## Implementation

### Architecture

```
┌─────────────────┐
│  FastAPI App    │
│                 │
│  ┌───────────┐  │
│  │ Auth      │  │
│  │ Endpoints │  │
│  └─────┬─────┘  │
│        │        │
│        v        │
│  ┌───────────┐  │
│  │ slowapi   │  │
│  │ Decorator │  │
│  └─────┬─────┘  │
│        │        │
│        v        │
│  ┌───────────┐  │
│  │  Redis    │◄─┤── Distributed Rate Limit Storage
│  │  Backend  │  │
│  └───────────┘  │
└─────────────────┘
```

### Code Example

```python
from app.middleware.auth_rate_limiter import auth_rate_limiter

@router.post("/login")
@auth_rate_limiter.limit()
async def login(request: Request, ...):
    # Authentication logic
    pass
```

## Monitoring

### Log Events

Rate limit violations are logged with the following event:

```json
{
  "event": "auth_rate_limit_exceeded",
  "client_ip": "192.168.1.1",
  "path": "/api/v1/auth/login",
  "limit": "10/5minutes",
  "retry_after": 300,
  "timestamp": "2025-10-01T12:00:00Z"
}
```

### Metrics to Monitor

1. **Rate limit exceeded count** - Number of 429 responses
2. **Top offending IPs** - IPs with most rate limit violations
3. **Rate limit errors** - Redis connection failures
4. **Average retry_after** - How long users wait

### Alerting Recommendations

**Alert on:**
- More than 100 rate limit violations per hour (possible attack)
- Same IP hitting rate limit repeatedly (brute force attempt)
- Redis connection failures (service degradation)

## Security Considerations

### Defense Against Attacks

**Brute Force Prevention:**
- 10 attempts per 5 minutes makes password guessing impractical
- Each attempt costs attacker ~30 seconds on average
- 1000 password attempts would take ~83 hours

**DoS Protection:**
- Limits Auth0 API calls to prevent bill spikes
- Protects backend CPU from excessive authentication processing
- Distributed Redis ensures consistent limits across instances
- Fail-closed mode prevents Redis-crash bypass attacks

**Distributed Attack Mitigation:**
- Per-IP tracking prevents single attacker from overwhelming system
- Multiple IPs required for sustained attack (increases cost)

**IP Spoofing Prevention (CRITICAL FIX #1):**
- X-Forwarded-For validated against TRUSTED_PROXIES
- Only accepts headers from RFC1918 private ranges by default
- Uses last IP in chain (closest to server, hardest to spoof)
- Untrusted proxies fall back to direct connection IP

### Bypass Prevention

**No Bypass Methods:**
- Cannot be disabled per-request
- No special headers to skip rate limiting
- Admin bypass requires code deployment (not runtime configuration)
- Fail-closed on Redis failure (no automatic bypass)

**Redis Security:**
- Use Redis AUTH password in production
- Enable Redis SSL/TLS for encrypted communication
- Isolate Redis instance on private network
- Environment namespace isolation (staging/production separated)

**Trusted Proxy Configuration:**
- Default: RFC1918 private ranges (10.0.0.0/8, 192.168.0.0/16, 172.16.0.0/12)
- Production: Configure TRUSTED_PROXIES for your infrastructure
- Render.com: Add Render's proxy IPs if using X-Forwarded-For
- Verify with: `curl -H "X-Forwarded-For: spoofed.ip" your-api.com/endpoint`

## Testing

### Unit Tests

```bash
# Run rate limiter tests
pytest tests/test_auth_rate_limiter.py -v
```

### Manual Testing

**Test rate limit enforcement:**
```bash
# Make 12 requests rapidly (exceeds 10 request limit)
for i in {1..12}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"code":"test","redirect_uri":"http://localhost:3000"}' \
    -w "\nStatus: %{http_code}\n"
done
```

**Expected:**
- First 10 requests: Status 200/400 (depending on valid auth)
- Requests 11-12: Status 429 (rate limit exceeded)

**Test rate limit reset:**
```bash
# Wait 5 minutes, then retry
sleep 300
curl -X POST http://localhost:8000/api/v1/auth/login ...
# Should succeed
```

## Troubleshooting

### Issue: Rate limiting not working

**Symptoms:**
- More than 10 requests succeed from same IP
- No 429 responses

**Solutions:**
1. Verify `RATE_LIMIT_ENABLED=true` in environment
2. Check Redis connection: `redis-cli ping`
3. Review logs for rate limiter initialization errors
4. Ensure slowapi is installed: `pip install slowapi`

### Issue: Legitimate users blocked

**Symptoms:**
- Users report authentication failures
- 429 errors for normal usage

**Solutions:**
1. Increase rate limit: `RATE_LIMIT_AUTH_REQUESTS="20/5minutes"`
2. Check for shared IP addresses (NAT, proxy)
3. Review logs for repeated failures from same IP
4. Consider per-user rate limiting (future enhancement)

### Issue: Redis connection failures

**Symptoms:**
- Rate limiting not enforcing limits
- Logs show Redis errors

**Solutions:**
1. Verify Redis is running: `redis-cli ping`
2. Check Redis URL in environment: `RATE_LIMIT_STORAGE_URL`
3. Verify network connectivity to Redis
4. Check Redis AUTH credentials if configured

## Rollback Plan

If rate limiting causes issues in production:

### Immediate Rollback (< 5 minutes)

**Option 1: Disable via environment variable**
```bash
# Set in environment
RATE_LIMIT_ENABLED=false

# Restart application
sudo systemctl restart marketedge-backend
```

**Option 2: Increase limits temporarily**
```bash
# Set very high limit
RATE_LIMIT_AUTH_REQUESTS="1000/minute"

# Restart application
sudo systemctl restart marketedge-backend
```

### Code Rollback

If environment changes don't work, rollback the code:

```bash
# Revert to previous commit
git revert <commit-hash>

# Deploy previous version
git push origin main
```

## Production Checklist

Before deploying rate limiting to production:

- [ ] Redis is configured and accessible
- [ ] `RATE_LIMIT_STORAGE_URL` points to production Redis
- [ ] Rate limits are configured appropriately (RATE_LIMIT_AUTH_REQUESTS, RATE_LIMIT_AUTH_REQUESTS_USER)
- [ ] `TRUSTED_PROXIES` configured for your infrastructure (CRITICAL)
- [ ] `ENV_NAME` set to "production" or auto-detected from RENDER_ENVIRONMENT
- [ ] Monitoring is set up for rate limit violations
- [ ] Alerts configured for excessive 429 responses
- [ ] Alerts configured for Redis failures (503 responses)
- [ ] Rollback plan documented and tested
- [ ] Team trained on troubleshooting
- [ ] Tests passing: `pytest tests/test_auth_rate_limiter.py -v`
- [ ] Verify fail-closed behavior: Stop Redis, expect 503 responses
- [ ] Verify IP spoofing protection: Test X-Forwarded-For from untrusted IPs
- [ ] Verify namespace isolation: Check Redis keys include environment prefix

## Future Enhancements

Potential improvements for authentication rate limiting:

1. ~~**Per-User Rate Limiting**~~ - ✅ **IMPLEMENTED** (HIGH FIX #5)
2. **Adaptive Rate Limiting** - Adjust limits based on system load
3. **IP Reputation** - Lower limits for suspicious IPs
4. **Rate Limit Dashboard** - Real-time visualization of rate limits
5. **Custom Bypass** - Admin API to temporarily bypass for specific IPs
6. **Geo-blocking** - Different limits per geographic region
7. **In-Memory Fallback** - Short-term memory cache when Redis is down (fail-degraded instead of fail-closed)

## References

- [slowapi Documentation](https://slowapi.readthedocs.io/)
- [Redis Rate Limiting Patterns](https://redis.io/docs/manual/patterns/rate-limiter/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Auth0 Rate Limiting Best Practices](https://auth0.com/docs/troubleshoot/customer-support/operational-policies/rate-limit-policy)

## Support

For issues or questions about authentication rate limiting:

1. Check this documentation first
2. Review logs: `tail -f /var/log/marketedge/backend.log`
3. Test Redis connectivity: `redis-cli -u $RATE_LIMIT_STORAGE_URL ping`
4. Contact DevOps team if Redis infrastructure issues
5. File bug report if code defect suspected

---

**Last Updated:** 2025-10-01
**Version:** 2.0.0 (SECURITY HARDENED)
**Status:** Production Ready

## Changelog

### Version 2.0.0 (2025-10-01) - SECURITY HARDENING

**CRITICAL SECURITY FIXES:**
1. ✅ IP Spoofing Prevention - X-Forwarded-For validation with TRUSTED_PROXIES
2. ✅ Fail-Closed Security - Redis failure returns 503 instead of bypass
3. ✅ Redis Namespace Isolation - Environment-specific keys (ENV_NAME)
4. ✅ Auth0 URL Protection - /auth0-url endpoint now rate limited (30/5min)

**HIGH PRIORITY IMPROVEMENTS:**
5. ✅ Per-User Rate Limiting - Authenticated users get 50/5min (vs 10/5min for IPs)
6. ✅ Environment-Aware Defaults - Development: 100/min, Staging: 20/5min, Production: 10/5min

**BREAKING CHANGES:**
- Fail-closed behavior: Redis failures now return 503 (previously allowed requests)
- TRUSTED_PROXIES validation: X-Forwarded-For from untrusted sources ignored
- Environment namespacing: Redis keys now include ENV_NAME prefix

**Migration:**
- Add `TRUSTED_PROXIES` to production environment variables
- Verify `ENV_NAME` is set correctly (or use RENDER_ENVIRONMENT)
- Test Redis failure scenario (should return 503)
- Update monitoring to alert on 503 responses

### Version 1.0.0 (2025-09-01) - INITIAL RELEASE

- Basic rate limiting for authentication endpoints
- Redis-backed distributed limiting
- Per-IP tracking
- Graceful degradation (fail-open)
