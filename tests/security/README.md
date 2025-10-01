# Security Tests

This directory contains security-specific test scripts and utilities.

## CSRF Timing Attack Test

**Script**: `test_csrf_timing.sh`

### Purpose

Verifies that CSRF token validation uses constant-time comparison to prevent timing attack vulnerabilities.

### Requirements

- Backend running at `http://localhost:8000`
- CSRF protection enabled (`CSRF_ENABLED=True`)
- `curl` command available
- `bc` command for calculations

### Usage

```bash
# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run timing test
./tests/security/test_csrf_timing.sh
```

### Expected Output

```
🔒 CSRF Timing Attack Stress Test
==================================
Backend: http://localhost:8000
Endpoint: http://localhost:8000/api/v1/auth/logout
Requests: 50 (parallel: 50)

✅ Backend is running

Running timing attack test...
Testing with wrong CSRF tokens (should be rejected in constant time)

📊 Timing Statistics (seconds):
  Min:    0.005
  Max:    0.007
  Avg:    0.006
  Median: 0.006

📈 Timing Variance: 1.40x

✅ PASS: Constant-time comparison verified
   Variance < 1.5x indicates no timing leak
   max ≈ min → no O(n) timing leak ✅
```

### Interpretation

- **Variance < 1.5x**: PASS - Constant-time comparison working correctly
- **Variance 1.5x-2.0x**: WARNING - Review implementation
- **Variance > 2.0x**: FAIL - Potential timing leak detected

### Integration with Pytest

The timing test is also integrated into the pytest suite:

```bash
# Run as part of test suite (requires backend running)
pytest tests/test_csrf_protection.py::TestCSRFTimingAttack::test_csrf_timing_attack_resistance -v

# Backend must be running at http://localhost:8000
```

### Environment Variables

- `BACKEND_URL`: Backend URL (default: `http://localhost:8000`)
- `NUM_REQUESTS`: Number of requests to send (default: 50)
- `PARALLEL_WORKERS`: Number of parallel workers (default: 50)

Example:
```bash
BACKEND_URL=https://api.example.com ./tests/security/test_csrf_timing.sh
```

## Security Best Practices

1. **Run before production deployment**: Always verify timing attack resistance
2. **Check variance**: Ensure variance < 1.5x
3. **Monitor in CI/CD**: Include in automated security tests
4. **Document results**: Save timing test output for security audits

## Troubleshooting

### Backend not running

```
❌ Backend not running at http://localhost:8000
Start backend: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Solution**: Start the backend server before running the test.

### High timing variance

```
⚠️  WARNING: High timing variance detected
   Variance 2.5x may indicate timing leak
   Review constant-time comparison implementation
```

**Solution**: Review the `_constant_time_compare` method in `app/middleware/csrf.py` to ensure:
- No early exit on mismatch
- XOR comparison used
- Equal-length strings compared byte-by-byte

### bc command not found

**Solution**: Install bc:
- macOS: `brew install bc`
- Ubuntu/Debian: `apt-get install bc`
- RHEL/CentOS: `yum install bc`

## References

- [OWASP Timing Attack Prevention](https://owasp.org/www-community/attacks/Timing_attack)
- [Constant-Time Comparison Best Practices](https://codahale.com/a-lesson-in-timing-attacks/)
- [CSRF Protection Implementation](../../docs/CSRF_SECURITY_IMPLEMENTATION.md)
