# Railway Operations Guide

## Multi-Tenant FastAPI Backend Operational Procedures

### Overview

This guide provides comprehensive operational procedures for managing the multi-tenant FastAPI backend deployed on Railway. It covers day-to-day operations, maintenance, troubleshooting, and emergency procedures.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Monitoring and Alerting](#monitoring-and-alerting)
3. [Maintenance Procedures](#maintenance-procedures)
4. [Troubleshooting Guide](#troubleshooting-guide)
5. [Emergency Procedures](#emergency-procedures)
6. [Performance Optimization](#performance-optimization)
7. [Security Operations](#security-operations)
8. [Backup and Recovery](#backup-and-recovery)

## Daily Operations

### Morning Health Check Routine

```bash
# 1. Check overall service status
railway status

# 2. Run comprehensive health check
./status-check.sh

# 3. Review overnight logs for errors
railway logs --since 24h | grep -i error

# 4. Check resource usage
railway metrics

# 5. Verify database connectivity
railway connect postgresql -c "SELECT version();"

# 6. Check Redis connectivity
railway connect redis -c "PING"
```

### Service URLs and Endpoints

- **Production API**: `https://your-service.railway.app`
- **Health Check**: `https://your-service.railway.app/health`
- **Readiness Check**: `https://your-service.railway.app/ready`
- **API Documentation**: `https://your-service.railway.app/api/v1/docs` (development only)
- **Railway Dashboard**: `https://railway.app/project/your-project-id`

### Key Metrics to Monitor

1. **Response Time**: < 200ms for 95th percentile
2. **Error Rate**: < 1% of total requests
3. **CPU Usage**: < 70% average
4. **Memory Usage**: < 80% of allocated
5. **Database Connections**: < 80% of pool size
6. **Active Users**: Track concurrent tenant sessions

## Monitoring and Alerting

### Built-in Railway Metrics

Railway automatically monitors:
- CPU and Memory usage
- Request latency and throughput
- Error rates and status codes
- Health check responses
- Service restarts and deployments

Access metrics via Railway dashboard or CLI:
```bash
railway metrics
railway logs --follow
```

### Custom Monitoring Scripts

#### Real-time Service Monitoring
```bash
# Monitor service health every 30 seconds
watch -n 30 './monitor-service.sh $(railway url)'
```

#### Performance Monitoring
```bash
# Weekly performance test
./performance-test.sh $(railway url)
```

#### Database Monitoring
```bash
# Daily database health check
./monitor-database.sh
```

### External Monitoring Setup

#### Uptime Robot Configuration
1. Monitor URL: `https://your-service.railway.app/health`
2. Check interval: 5 minutes
3. Alert contacts: DevOps team email/Slack
4. Expected response: JSON with `"status": "healthy"`

#### Log Aggregation
```bash
# Stream logs to external service (example: Papertrail)
railway logs --follow | logger -h logs.papertrailapp.com -p USER_PORT
```

## Maintenance Procedures

### Weekly Maintenance Tasks

#### 1. Dependency Updates
```bash
# Check for security updates
pip list --outdated

# Update requirements.txt if needed
pip freeze > requirements.txt

# Deploy updates
railway deploy
```

#### 2. Database Maintenance
```bash
# Connect to database
railway connect postgresql

# Check database size and growth
SELECT 
    pg_size_pretty(pg_database_size(current_database())) as db_size,
    count(*) as table_count
FROM pg_tables 
WHERE schemaname = 'public';

# Analyze table statistics
ANALYZE;

# Check for unused indexes
SELECT 
    schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes 
WHERE idx_scan = 0 
    AND indexname NOT LIKE '%_pkey';
```

#### 3. Redis Maintenance
```bash
# Connect to Redis
railway connect redis

# Check memory usage
INFO memory

# Check key statistics
INFO keyspace

# Clean up expired keys (if needed)
FLUSHDB
```

#### 4. Log Rotation and Cleanup
```bash
# Archive old logs (save locally if needed)
railway logs --since 7d > logs_$(date +%Y%m%d).txt

# Check log size and ensure it's manageable
railway logs --lines 1000 | wc -l
```

### Monthly Maintenance Tasks

#### 1. Security Updates
```bash
# Update all Python packages
pip install --upgrade pip
pip install --upgrade -r requirements.txt

# Check for security vulnerabilities
safety check
```

#### 2. Performance Review
```bash
# Run comprehensive performance test
./performance-test.sh $(railway url)

# Analyze results and optimize if needed
# Review slow queries and optimize database
# Check rate limiting effectiveness
```

#### 3. Backup Verification
```bash
# Test database backup restoration
railway connect postgresql -c "\dt"

# Verify backup automation is working
# Check backup retention settings in Railway dashboard
```

### Quarterly Maintenance Tasks

#### 1. Security Audit
```bash
# Rotate JWT secrets
NEW_JWT_SECRET=$(openssl rand -base64 32)
railway variables set JWT_SECRET_KEY="$NEW_JWT_SECRET"
railway deploy

# Review and update CORS origins
railway variables get CORS_ORIGINS

# Review Auth0 configuration
railway variables get AUTH0_DOMAIN
```

#### 2. Capacity Planning
- Review usage trends and growth patterns
- Plan for scaling requirements
- Optimize resource allocation
- Update rate limiting based on usage patterns

#### 3. Disaster Recovery Testing
- Test backup restoration procedures
- Verify monitoring and alerting systems
- Update emergency contact information
- Review and update operational procedures

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Service Not Responding
```bash
# Check service status
railway status

# Check recent deployments
railway deployments

# View recent logs
railway logs --lines 100

# Restart service if needed
railway restart
```

#### 2. Database Connection Issues
```bash
# Check database service status
railway status | grep postgres

# Test database connectivity
railway connect postgresql -c "SELECT 1;"

# Check connection pool usage
railway shell -- python -c "
from app.core.database import engine
print('Database URL:', engine.url)
"

# Reset connections if needed
railway restart
```

#### 3. Redis Connection Issues
```bash
# Check Redis service status
railway status | grep redis

# Test Redis connectivity
railway connect redis -c "PING"

# Check Redis memory usage
railway connect redis -c "INFO memory"

# Clear Redis cache if needed
railway connect redis -c "FLUSHALL"
```

#### 4. High Response Times
```bash
# Check current load
./monitor-service.sh $(railway url)

# Analyze slow queries
./monitor-database.sh

# Check for rate limiting issues
railway logs | grep "rate limit"

# Scale service if needed
# (Configure in Railway dashboard)
```

#### 5. Rate Limiting Issues
```bash
# Check rate limiting configuration
railway variables get RATE_LIMIT_ENABLED
railway variables get RATE_LIMIT_REQUESTS_PER_MINUTE

# Check Redis rate limiting storage
railway connect redis -c "KEYS rate_limit:*"

# Clear rate limiting cache if needed
railway connect redis -c "DEL rate_limit:*"
```

#### 6. Authentication Failures
```bash
# Check Auth0 configuration
railway variables get AUTH0_DOMAIN
railway variables get AUTH0_CLIENT_ID

# Test JWT validation
curl -X POST $(railway url)/api/v1/auth/verify \
  -H "Authorization: Bearer YOUR_TEST_TOKEN"

# Check JWT secret
railway variables get JWT_SECRET_KEY
```

### Emergency Escalation Procedures

#### Severity 1 (Service Down)
1. **Immediate Actions** (0-5 minutes):
   - Check Railway service status
   - Restart service if needed
   - Check recent deployments for issues
   
2. **Investigation** (5-15 minutes):
   - Review logs for errors
   - Check database and Redis connectivity
   - Verify external dependencies (Auth0, Supabase)
   
3. **Resolution** (15-30 minutes):
   - Rollback deployment if recent changes caused issue
   - Scale resources if performance issue
   - Contact Railway support if platform issue

#### Severity 2 (Performance Degradation)
1. **Assessment** (0-10 minutes):
   - Check response times and error rates
   - Review resource usage metrics
   - Identify affected endpoints
   
2. **Mitigation** (10-30 minutes):
   - Scale service resources if needed
   - Clear caches if appropriate
   - Implement temporary rate limiting adjustments

#### Severity 3 (Non-critical Issues)
1. **Documentation** (0-15 minutes):
   - Log issue details and impact
   - Schedule maintenance window if needed
   
2. **Resolution** (within 24 hours):
   - Implement fix during maintenance window
   - Update monitoring to prevent recurrence

## Performance Optimization

### Database Optimization

#### Query Optimization
```sql
-- Enable query statistics (if not enabled)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    stddev_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check index usage
SELECT 
    schemaname, tablename, indexname, 
    idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;
```

#### Connection Pool Optimization
```python
# Adjust connection pool settings based on load
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Increase for high concurrency
    max_overflow=30,     # Allow burst connections
    pool_pre_ping=True,  # Validate connections
    pool_recycle=3600    # Recycle connections hourly
)
```

### Redis Optimization

```bash
# Monitor Redis performance
railway connect redis -c "INFO stats"

# Configure memory optimization
railway connect redis -c "CONFIG SET maxmemory-policy allkeys-lru"

# Monitor key expiration
railway connect redis -c "INFO keyspace"
```

### Application Optimization

#### Rate Limiting Tuning
```bash
# Adjust rate limits based on usage patterns
railway variables set RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE="2000"
railway variables set RATE_LIMIT_BURST_SIZE="20"

# Industry-specific adjustments
# Cinema: High burst during booking windows
# Hotel: Steady load with seasonal peaks
# Gym: Peak hours optimization
```

#### Worker Configuration
```bash
# Adjust worker count based on CPU cores and load
# Railway automatically manages this, but can be overridden in Dockerfile
# CMD ["uvicorn", "app.main:app", "--workers", "4", "--host", "0.0.0.0", "--port", "8000"]
```

## Security Operations

### Security Monitoring

#### Daily Security Checks
```bash
# Check for failed authentication attempts
railway logs | grep -i "unauthorized\|forbidden\|authentication failed"

# Monitor rate limiting events
railway logs | grep -i "rate limit"

# Check for suspicious patterns
railway logs | grep -E "(sql|script|eval|exec)"
```

#### Weekly Security Tasks
```bash
# Review access logs for unusual patterns
railway logs --since 7d | grep -E "POST|PUT|DELETE" | head -100

# Check Auth0 logs for authentication issues
# Review tenant isolation logs
railway logs | grep -i "tenant"
```

### Security Incident Response

#### Suspected Security Breach
1. **Immediate Actions**:
   - Rotate JWT secrets immediately
   - Review recent access logs
   - Check for data exfiltration attempts
   
2. **Investigation**:
   - Analyze authentication patterns
   - Review tenant isolation logs
   - Check database access patterns
   
3. **Containment**:
   - Implement temporary IP restrictions if needed
   - Increase rate limiting
   - Contact affected tenants if necessary

#### Security Configuration Updates
```bash
# Rotate secrets
NEW_JWT_SECRET=$(openssl rand -base64 32)
railway variables set JWT_SECRET_KEY="$NEW_JWT_SECRET"

# Update CORS policies
railway variables set CORS_ORIGINS="https://secure-domain.com"

# Enable additional security headers
# (Configure in application code)
```

## Backup and Recovery

### Automated Backups

Railway automatically backs up PostgreSQL databases with the following retention:
- Hourly snapshots for 24 hours
- Daily snapshots for 7 days
- Weekly snapshots for 4 weeks
- Monthly snapshots for 12 months

### Manual Backup Procedures

#### Database Backup
```bash
# Create manual database backup
railway connect postgresql --command "pg_dump railway > backup_$(date +%Y%m%d_%H%M%S).sql"

# Backup specific tables
railway connect postgresql --command "pg_dump -t organisations -t users railway > tenant_backup_$(date +%Y%m%d).sql"
```

#### Configuration Backup
```bash
# Backup environment variables
railway variables > env_backup_$(date +%Y%m%d).txt

# Backup Railway configuration
cp railway.toml railway_backup_$(date +%Y%m%d).toml
```

### Recovery Procedures

#### Database Recovery
```bash
# List available backups (via Railway dashboard)
# Restore from specific backup timestamp

# Manual restoration from backup file
railway connect postgresql --command "psql railway < backup_file.sql"
```

#### Configuration Recovery
```bash
# Restore environment variables from backup
while IFS='=' read -r key value; do
    railway variables set "$key" "$value"
done < env_backup_file.txt
```

### Disaster Recovery Testing

#### Monthly DR Test
1. Create test environment
2. Restore from backup
3. Verify data integrity
4. Test application functionality
5. Document any issues found

## Contact Information

### Emergency Contacts
- **Primary On-Call**: [Your contact information]
- **Secondary On-Call**: [Backup contact]
- **Railway Support**: support@railway.app
- **Auth0 Support**: [Auth0 support details]

### Escalation Matrix
- **Level 1**: Development team
- **Level 2**: DevOps team
- **Level 3**: External support (Railway, Auth0)
- **Level 4**: Management notification

## Standard Operating Procedures Summary

### Daily
- [ ] Morning health check
- [ ] Review error logs
- [ ] Check resource usage
- [ ] Verify backup completion

### Weekly
- [ ] Performance testing
- [ ] Security log review
- [ ] Database maintenance
- [ ] Dependency updates

### Monthly
- [ ] Security updates
- [ ] Capacity planning review
- [ ] Backup verification
- [ ] Documentation updates

### Quarterly
- [ ] Security audit
- [ ] Disaster recovery testing
- [ ] Performance optimization review
- [ ] Operational procedure review

This operational guide ensures consistent, reliable management of the Railway-deployed multi-tenant FastAPI backend with proper security, monitoring, and maintenance procedures.