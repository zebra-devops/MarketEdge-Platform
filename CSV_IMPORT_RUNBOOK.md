# CSV Import Production Runbook

**Service**: MarketEdge Platform - CSV User Import  
**Platform**: Render  
**Last Updated**: 2025-08-20  
**Oncall Contact**: DevOps Team

## Overview

The CSV Import feature allows admin users to bulk import users into their organizations. This runbook covers monitoring, troubleshooting, and maintenance procedures.

## Architecture

```
Frontend (React) → Backend API → Background Tasks → Database
                ↓
            Rate Limiter (Redis) → Import Processing
```

### Key Components
- **API Endpoints**: `/api/v1/organizations/{org_id}/users/import/*`
- **Database Tables**: `import_batches`, `import_errors`, `users`
- **Background Processing**: FastAPI BackgroundTasks
- **Rate Limiting**: Redis-based upload limits
- **File Storage**: Temporary in-memory processing

## Monitoring & Alerts

### Key Metrics
- Import success/failure rates
- Processing time per user
- Rate limit violations
- Background task health
- File upload errors

### Alert Thresholds
- **CRITICAL**: Import failure rate > 10%
- **WARNING**: Processing time > 30 seconds per user
- **WARNING**: Rate limit violations > 20/hour

### Dashboards
- Grafana: "CSV Import Monitoring Dashboard"
- Render: Service logs and metrics

## Common Issues & Resolution

### 1. Import Stalled/Stuck

**Symptoms:**
- Import batch stuck in "processing" status
- No progress updates for >10 minutes
- Users report imports never completing

**Diagnosis:**
```bash
# Check active imports
SELECT id, filename, status, created_at, started_at, processed_rows, total_rows 
FROM import_batches 
WHERE status = 'processing' 
  AND created_at < NOW() - INTERVAL '10 minutes';

# Check background task errors
SELECT * FROM import_errors 
WHERE import_batch_id = 'batch-id-here' 
ORDER BY created_at DESC LIMIT 10;
```

**Resolution:**
1. Check Render service logs for background task errors
2. Verify database connectivity and locks
3. If database deadlock, restart the service
4. Manually mark stuck imports as failed:
   ```sql
   UPDATE import_batches 
   SET status = 'failed', 
       error_message = 'Manual intervention - stuck import',
       completed_at = NOW()
   WHERE id = 'stuck-batch-id';
   ```

### 2. High Failure Rate

**Symptoms:**
- Alert: "CSVImportHighFailureRate"
- Multiple imports failing validation or processing

**Diagnosis:**
```bash
# Check recent failure patterns
SELECT error_message, COUNT(*) as error_count
FROM import_batches 
WHERE status = 'failed' 
  AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY error_message;

# Check validation errors
SELECT field_name, error_message, COUNT(*) as occurrence_count
FROM import_errors 
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY field_name, error_message;
```

**Resolution:**
1. **Database Issues**: Check database connectivity and locks
2. **Validation Errors**: Review common validation patterns
3. **Service Errors**: Check Render logs for application errors
4. **Resource Exhaustion**: Monitor CPU/memory usage

### 3. Rate Limiting Issues

**Symptoms:**
- Users getting 429 errors too frequently
- Alert: "CSVRateLimitViolations"

**Diagnosis:**
```bash
# Check Redis rate limit keys
redis-cli --scan --pattern "upload_rate:*" | head -20

# Check user-specific rate limits
redis-cli get "upload_rate:csv_import:user-id:hour:current-hour"
```

**Resolution:**
1. **Reset user limits** (if legitimate):
   ```python
   from app.middleware.upload_rate_limiter import upload_rate_limiter
   upload_rate_limiter.reset_limits("user_id", "csv_import")
   ```
2. **Adjust limits** (if needed):
   - Modify `UPLOAD_RATE_LIMITS` in `upload_rate_limiter.py`
   - Deploy updated configuration
3. **Block abusive users**: Add IP/user to rate limit blacklist

### 4. File Upload Failures

**Symptoms:**
- 400 errors on file upload
- Files not being processed
- "File too large" or "Invalid format" errors

**Diagnosis:**
- Check Render service logs for upload errors
- Verify file size limits (10MB max)
- Check CSV format validation

**Resolution:**
1. **File Size**: Confirm 10MB limit is appropriate
2. **Format Issues**: Validate CSV headers and encoding
3. **Network Issues**: Check Render ingress configuration
4. **Storage Issues**: Monitor disk space (unlikely on Render)

### 5. Database Connection Issues

**Symptoms:**
- Imports fail with database errors
- Connection timeout errors

**Diagnosis:**
```bash
# Check database connections
SELECT count(*) FROM pg_stat_activity;

# Check for locks
SELECT * FROM pg_locks WHERE NOT granted;
```

**Resolution:**
1. **Connection Pool**: Restart the application service
2. **Database Locks**: Identify and resolve blocking queries
3. **Resource Limits**: Check PostgreSQL connection limits
4. **Network Issues**: Verify Render network configuration

## Maintenance Procedures

### Daily Checks
- [ ] Review import success rates (should be >95%)
- [ ] Check for stuck imports (>10 minutes in processing)
- [ ] Verify Redis connectivity for rate limiting
- [ ] Monitor error patterns in logs

### Weekly Maintenance
- [ ] Clean up old import batches (>30 days)
  ```sql
  DELETE FROM import_batches WHERE created_at < NOW() - INTERVAL '30 days';
  ```
- [ ] Review and rotate logs if needed
- [ ] Check database table growth and performance
- [ ] Update rate limit configurations if needed

### Monthly Reviews
- [ ] Analyze usage patterns and performance trends
- [ ] Review and update alert thresholds
- [ ] Performance optimization based on metrics
- [ ] Security review of file upload handling

## Emergency Procedures

### Complete Service Outage
1. **Check Render service status**
2. **Review recent deployments**
3. **Check database connectivity**
4. **Verify Redis availability**
5. **Rollback if necessary**

### Data Corruption
1. **Stop import processing immediately**
2. **Backup current database state**
3. **Identify affected imports**
4. **Restore from backup if needed**
5. **Reprocess affected imports**

### Security Incident
1. **Disable CSV import feature**:
   ```python
   # Set environment variable
   FEATURE_USER_MANAGEMENT=false
   ```
2. **Review suspicious uploads**
3. **Check for CSV injection attempts**
4. **Review user access logs**
5. **Implement additional security measures**

## Performance Optimization

### Current Benchmarks
- **File Upload**: <2 seconds for 10MB files
- **Validation**: <5 seconds for 1000 users
- **Processing**: 10-20 users per second
- **Progress Updates**: 2-second polling

### Optimization Strategies
1. **Batch Processing**: Increase batch sizes for large imports
2. **Parallel Processing**: Process multiple imports simultaneously
3. **Database Indexing**: Optimize query performance
4. **Caching**: Cache validation results where appropriate

## Configuration Management

### Environment Variables
```bash
# Feature flags
FEATURE_USER_MANAGEMENT=true
FEATURE_ADMIN_PANEL=true

# Rate limiting
RATE_LIMIT_ENABLED=true
REDIS_URL=redis://...

# File upload limits
MAX_FILE_SIZE=10485760  # 10MB
MAX_ROWS_PER_IMPORT=5000
```

### Database Schema
- Tables: `import_batches`, `import_errors`, `users`
- Indexes: Optimized for query performance
- Retention: 30 days for import history

## Escalation Procedures

### Level 1: Warning Alerts
- Monitor for 15 minutes
- Check basic health indicators
- Document patterns

### Level 2: Critical Alerts
- Immediate investigation required
- Check all components
- Prepare for potential service restart

### Level 3: Service Outage
- Immediately disable feature if needed
- Engage senior DevOps team
- Prepare communications for users

## Contact Information

- **Primary Oncall**: DevOps Team
- **Secondary**: Platform Engineering
- **Product Owner**: For feature-related decisions
- **Database Admin**: For complex database issues

## Related Documentation

- [CSV Import API Documentation](./api_documentation.md)
- [User Management System Overview](./user_management.md)
- [Rate Limiting Configuration](./rate_limiting.md)
- [Render Deployment Guide](./render_deployment.md)

---
**Remember**: When in doubt, disable the feature and investigate. User data integrity is paramount.