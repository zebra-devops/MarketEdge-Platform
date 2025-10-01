# Authentication Rate Limiting

## Overview

Authentication rate limiting protects the MarketEdge platform from:
- **DoS attacks** on expensive Auth0 endpoints
- **CPU burn** from excessive authentication attempts
- **Auth0 bill spikes** from brute force attacks

## Configuration

### Environment Variables

```bash
# Enable/disable rate limiting (default: true)
RATE_LIMIT_ENABLED=true

# Rate limit for authentication endpoints (default: "10/5minutes")
RATE_LIMIT_AUTH_REQUESTS="10/5minutes"

# Redis URL for distributed rate limiting (default: redis://localhost:6379/1)
RATE_LIMIT_STORAGE_URL="redis://localhost:6379/1"
```

### Rate Limit Format

The rate limit string follows the format: `<requests>/<time_window>`

Examples:
- `"10/5minutes"` - 10 requests per 5 minutes
- `"5/minute"` - 5 requests per minute
- `"100/hour"` - 100 requests per hour

## Protected Endpoints

The following authentication endpoints are rate limited:

1. **POST /api/v1/auth/login** - OAuth2 login with authorization code
2. **POST /api/v1/auth/login-oauth2** - Alternative OAuth2 login endpoint
3. **POST /api/v1/auth/refresh** - Token refresh endpoint
4. **POST /api/v1/auth/user-context** - Auth0 Action callback for user context

## Rate Limiting Behavior

### Per-IP Address Tracking

Rate limits are enforced **per IP address**, preventing distributed attacks while allowing legitimate users across different IPs to authenticate simultaneously.

**Example:**
- IP 192.168.1.1 can make 10 requests in 5 minutes
- IP 192.168.1.2 can make 10 requests in 5 minutes (independently)

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

### Graceful Degradation

If Redis is unavailable:
- Rate limiting **fails open** (allows requests)
- Error is logged for monitoring
- Service remains available

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

**Distributed Attack Mitigation:**
- Per-IP tracking prevents single attacker from overwhelming system
- Multiple IPs required for sustained attack (increases cost)

### Bypass Prevention

**No Bypass Methods:**
- Cannot be disabled per-request
- No special headers to skip rate limiting
- Admin bypass requires code deployment (not runtime configuration)

**Redis Security:**
- Use Redis AUTH password in production
- Enable Redis SSL/TLS for encrypted communication
- Isolate Redis instance on private network

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
- [ ] Rate limits are configured appropriately
- [ ] Monitoring is set up for rate limit violations
- [ ] Alerts configured for excessive 429 responses
- [ ] Rollback plan documented and tested
- [ ] Team trained on troubleshooting
- [ ] Tests passing: `pytest tests/test_auth_rate_limiter.py`

## Future Enhancements

Potential improvements for authentication rate limiting:

1. **Per-User Rate Limiting** - Separate limits per authenticated user
2. **Adaptive Rate Limiting** - Adjust limits based on system load
3. **IP Reputation** - Lower limits for suspicious IPs
4. **Rate Limit Dashboard** - Real-time visualization of rate limits
5. **Custom Bypass** - Admin API to temporarily bypass for specific IPs
6. **Geo-blocking** - Different limits per geographic region

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
**Version:** 1.0.0
**Status:** Production Ready
