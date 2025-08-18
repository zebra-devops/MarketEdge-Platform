# Epic 2: Database and Redis Infrastructure Setup Guide

## MIG-008: Database and Redis Infrastructure Setup (8 pts)

### Executive Summary

**Business Context**: Following successful Render account and environment setup (MIG-006, MIG-007), establish PostgreSQL database and Redis infrastructure with zero-data-loss migration from Railway and enterprise-grade performance optimization.

**Implementation Objective**: Complete database and Redis migration maintaining 100% data integrity while establishing performance baselines exceeding current Railway capabilities for the £925K Odeon opportunity.

**Success Criteria**: PostgreSQL and Redis fully operational on Render with complete data migration, optimized performance, comprehensive monitoring, and validated backup/recovery procedures.

---

## Infrastructure Requirements Analysis

### Current Railway Database Analysis

From Railway configuration analysis and current environment:

```yaml
Current Railway Infrastructure:

PostgreSQL Database:
  - Version: PostgreSQL 14+ (Railway managed)
  - Connection: DATABASE_URL environment variable
  - Usage Pattern: Multi-tenant business intelligence data
  - Performance Requirements: <100ms query response times
  - Data Volume: Production client data (Odeon demo critical)
  - Backup: Railway automated backups

Redis Cache:
  - Version: Redis 6+ (Railway managed)
  - Connection: REDIS_URL with authentication
  - Usage Pattern: Session management, API rate limiting, caching
  - Performance Requirements: <5ms response times
  - Configuration: SSL enabled, connection pooling
  - Rate Limiting Storage: Separate Redis database (DB 1)
```

### Target Render Infrastructure Requirements

```yaml
Target Render Infrastructure:

PostgreSQL Requirements:
  - Version: PostgreSQL 14+ (compatibility maintained)
  - Plan: Starter or Standard (based on data volume)
  - Performance: Equal or better query performance
  - Security: Encryption at rest and in transit
  - Backup: Automated daily backups with point-in-time recovery
  - Monitoring: Query performance and connection monitoring

Redis Requirements:
  - Version: Redis 6+ (compatibility maintained)
  - Plan: Starter or Standard (based on memory requirements)
  - Performance: Sub-5ms response times maintained
  - Security: TLS encryption, password authentication
  - Configuration: Connection pooling, multiple databases
  - Monitoring: Performance metrics and connection monitoring
```

---

## Step 1: PostgreSQL Database Infrastructure Setup

### 1.1 Database Instance Creation

#### Database Service Configuration
```yaml
PostgreSQL Configuration:

Service Setup:
  Name: platform-wrapper-production-db
  PostgreSQL Version: 14 (latest stable)
  Plan: Starter ($7/month) or Standard ($25/month)
  Region: US East (same as web service for latency)
  
Resource Specifications:
  Storage: 1GB (Starter) or 10GB (Standard)
  Memory: 1GB (Starter) or 4GB (Standard)  
  CPU: Shared (Starter) or Dedicated (Standard)
  Connections: 97 (Starter) or 197 (Standard)
  
Security Configuration:
  Encryption: At rest and in transit (TLS 1.2+)
  Authentication: Password-based with strong credentials
  Network Access: Render services only (internal network)
  Backup Encryption: Encrypted backup storage
```

#### Database Selection Criteria
```yaml
Plan Selection Analysis:

For Starter Plan ($7/month):
  - Suitable for: Development, staging, small production
  - Storage: 1GB (sufficient for current data volume)
  - Connections: 97 (adequate for multi-service architecture)
  - Memory: 1GB (sufficient for current query patterns)
  
For Standard Plan ($25/month):  
  - Suitable for: Production with growth expectations
  - Storage: 10GB (future-proofed for expansion)
  - Connections: 197 (supports increased concurrent load)
  - Memory: 4GB (better performance for complex queries)

Recommendation: Start with Starter, upgrade to Standard when needed
```

### 1.2 Database Migration Strategy

#### Data Migration Planning
```yaml
Migration Strategy:

Pre-Migration Assessment:
  - Current database size analysis
  - Table structure and relationship mapping
  - Index and constraint documentation
  - Current performance baseline establishment
  
Migration Approach:
  - Dump and restore method for initial migration
  - Incremental sync for minimal downtime (if required)
  - Validation procedures for data integrity
  - Rollback procedures for emergency recovery

Data Integrity Validation:
  - Row count verification for all tables
  - Checksum validation for data consistency
  - Referential integrity verification
  - Application functionality testing post-migration
```

#### Migration Procedures

```yaml
Database Migration Steps:

Phase 1: Pre-Migration Preparation
  1. Create full backup of Railway PostgreSQL database
  2. Document current database schema and constraints  
  3. Establish baseline performance metrics
  4. Plan migration window for minimal business impact
  
Phase 2: Database Setup and Migration
  1. Create PostgreSQL database instance on Render
  2. Configure security settings and access controls
  3. Perform database dump from Railway
  4. Restore data to Render PostgreSQL instance
  5. Verify data integrity and completeness
  
Phase 3: Configuration and Optimization
  1. Apply database optimizations and indexing
  2. Configure connection pooling and performance settings
  3. Update application DATABASE_URL configuration
  4. Test application connectivity and functionality
  
Phase 4: Validation and Monitoring
  1. Validate all application database operations
  2. Establish monitoring and alerting
  3. Configure backup and recovery procedures
  4. Document final configuration and procedures
```

### 1.3 Database Performance Optimization

#### Performance Configuration
```yaml
PostgreSQL Performance Tuning:

Connection Management:
  - Connection pooling: 50 connections max
  - Idle timeout: 300 seconds
  - Statement timeout: 30 seconds
  - Connection retry logic: 3 attempts with backoff

Query Performance:
  - Shared buffers: 25% of available memory
  - Work memory: Optimized for query complexity
  - Effective cache size: 75% of available memory
  - Random page cost: 1.1 (SSD optimization)

Monitoring Configuration:
  - Query performance tracking enabled
  - Slow query logging: >1 second
  - Connection monitoring and alerting
  - Lock monitoring and deadlock detection
```

#### Database Security Configuration
```yaml
Security Settings:

Access Controls:
  - SSL/TLS encryption required for all connections
  - Strong password policy enforcement
  - Database user permissions (principle of least privilege)
  - Network access restricted to Render services

Backup Security:
  - Automated daily backups encrypted
  - Point-in-time recovery capability
  - Backup retention: 7 days (adjustable)
  - Backup access controls and audit logging

Monitoring and Auditing:
  - Connection attempt logging
  - Query execution monitoring
  - Failed authentication alerts
  - Database modification audit trail
```

---

## Step 2: Redis Cache Infrastructure Setup

### 2.1 Redis Instance Creation

#### Redis Service Configuration
```yaml
Redis Configuration:

Service Setup:
  Name: platform-wrapper-production-redis
  Redis Version: 6.2 (latest stable)
  Plan: Starter ($7/month) or Standard ($25/month)
  Region: US East (same as web service for latency)
  
Resource Specifications:
  Memory: 256MB (Starter) or 1GB (Standard)
  CPU: Shared (Starter) or Dedicated (Standard)
  Connections: 250 (Starter) or 500 (Standard)
  Persistence: RDB snapshots + AOF logging

Security Configuration:
  Encryption: TLS 1.2+ for all connections
  Authentication: AUTH password required
  Network Access: Render services only
  Access Controls: User-based permissions
```

#### Redis Plan Selection
```yaml
Plan Selection Analysis:

For Starter Plan ($7/month):
  - Memory: 256MB (adequate for sessions + caching)
  - Connections: 250 (sufficient for multi-service)
  - Suitable for: Current usage patterns
  - Cost-effective for initial deployment

For Standard Plan ($25/month):
  - Memory: 1GB (future-proofed for growth)
  - Connections: 500 (supports increased load)
  - Suitable for: High-performance requirements
  - Better for enterprise client expansion

Recommendation: Start with Starter, monitor usage patterns
```

### 2.2 Redis Configuration and Migration

#### Redis Database Configuration
```yaml
Redis Database Organization:

Database 0 (Default):
  - User sessions and authentication data
  - Application caching (API responses, computed data)
  - Configuration cache

Database 1:
  - Rate limiting counters and tracking
  - API quota management
  - Temporary rate limit storage

Database 2 (Future):
  - Analytics and metrics caching
  - Temporary computation storage
  - Background job queues (if implemented)

Connection Configuration:
  - SSL/TLS required
  - Password authentication
  - Connection pooling: 50 connections
  - Connection timeout: 5 seconds
  - Socket timeout: 2 seconds
```

#### Redis Migration Strategy
```yaml
Redis Migration Approach:

Data Migration:
  - Session data: Allow natural expiration (no migration needed)
  - Rate limiting data: Reset counters (fresh start acceptable)
  - Cache data: Rebuild from source (cache warming)
  - Configuration cache: Export/import critical configurations

Migration Steps:
  1. Create Redis instance on Render
  2. Configure databases and security settings
  3. Update application REDIS_URL configuration
  4. Test connectivity and basic operations
  5. Migrate critical cached configurations
  6. Validate all Redis-dependent functionality
  7. Monitor performance and tune as needed
```

### 2.3 Redis Performance Optimization

#### Performance Configuration
```yaml
Redis Performance Settings:

Memory Management:
  - Max memory policy: allkeys-lru (least recently used eviction)
  - Memory usage monitoring and alerting
  - Key expiration optimization
  - Memory fragmentation monitoring

Persistence Configuration:
  - RDB snapshots: Every 15 minutes if >=1 change
  - AOF (Append Only File): Every second for durability
  - AOF rewrite optimization for file size management
  - Backup frequency aligned with data criticality

Connection Optimization:
  - Keep alive: 300 seconds
  - TCP timeout: 0 (disabled for persistent connections)
  - Connection pooling optimization
  - Connection health monitoring
```

#### Redis Security and Monitoring
```yaml
Security Configuration:

Access Security:
  - AUTH password required (strong password)
  - TLS encryption for all connections
  - User-based access controls where supported
  - Network access restricted to Render services

Data Security:
  - Sensitive data encryption before storage
  - Key naming conventions for data classification
  - TTL (Time To Live) for sensitive data
  - Regular security audits and access reviews

Monitoring Setup:
  - Memory usage monitoring and alerts
  - Connection count monitoring
  - Command statistics and performance tracking
  - Error rate monitoring and alerting
```

---

## Step 3: Environment Integration

### 3.1 Production Environment Database Integration

#### Production Database Configuration
```yaml
Production Database Integration:

Environment Variables:
  # PostgreSQL Configuration
  DATABASE_URL="postgresql://username:password@host:port/dbname"
  DATABASE_POOL_SIZE="20"
  DATABASE_TIMEOUT="30"
  DATABASE_SSL_MODE="require"
  
  # Redis Configuration  
  REDIS_URL="rediss://default:password@host:port"
  REDIS_PASSWORD="strong_redis_password"
  REDIS_SSL_ENABLED="true"
  REDIS_CONNECTION_POOL_SIZE="50"
  REDIS_HEALTH_CHECK_INTERVAL="30"
  REDIS_SOCKET_CONNECT_TIMEOUT="5"
  REDIS_SOCKET_TIMEOUT="2"
  
  # Rate Limiting Redis (Database 1)
  RATE_LIMIT_STORAGE_URL="rediss://default:password@host:port/1"

Application Configuration Updates:
  - Update database connection strings
  - Verify SSL/TLS certificate validation
  - Update connection pooling settings
  - Configure retry logic and error handling
```

#### Connection Validation Procedures
```yaml
Connection Validation:

Database Connectivity:
  - [ ] Application can connect to PostgreSQL
  - [ ] All database queries execute successfully
  - [ ] Connection pooling working properly
  - [ ] SSL/TLS encryption verified
  - [ ] Transaction isolation functioning
  - [ ] Error handling and retry logic tested

Redis Connectivity:
  - [ ] Application can connect to Redis
  - [ ] All Redis operations working (GET, SET, DEL)
  - [ ] Multiple database access functioning
  - [ ] Connection pooling optimized
  - [ ] SSL/TLS encryption verified
  - [ ] Rate limiting operations validated
```

### 3.2 Staging Environment Database Integration

#### Staging Database Configuration
```yaml
Staging Database Setup:

Database Configuration:
  # Separate staging database instance
  DATABASE_URL="postgresql://staging_user:password@staging_host:port/staging_db"
  
  # Staging Redis instance
  REDIS_URL="rediss://default:staging_password@staging_host:port"
  
Configuration Differences:
  - Separate database instances for isolation
  - Smaller resource allocation for cost optimization
  - Debug logging enabled for development
  - Relaxed connection timeouts for testing
  - Test data seeding capabilities

Data Management:
  - Test data sets for validation
  - Data reset procedures for testing
  - Backup and restore procedures tested
  - Cross-environment isolation verified
```

---

## Step 4: Data Migration Execution

### 4.1 Database Migration Implementation

#### Pre-Migration Checklist
```yaml
Migration Readiness:

Railway Database Assessment:
  - [ ] Current database size documented
  - [ ] Table structure and constraints mapped
  - [ ] Performance baselines established
  - [ ] Full backup created and verified
  - [ ] Migration window planned and approved

Render Database Preparation:
  - [ ] PostgreSQL instance created and configured
  - [ ] Security settings implemented
  - [ ] Performance tuning applied
  - [ ] Monitoring and alerting configured
  - [ ] Backup procedures established

Team Preparation:
  - [ ] Migration procedures documented
  - [ ] Team roles and responsibilities assigned
  - [ ] Emergency rollback procedures tested
  - [ ] Communication plan activated
  - [ ] Go/No-Go criteria established
```

#### Migration Execution Steps
```bash
# Database Migration Execution Script

# Step 1: Create database dump from Railway
pg_dump $RAILWAY_DATABASE_URL > railway_database_backup.sql

# Step 2: Verify dump file integrity
psql $RAILWAY_DATABASE_URL -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Step 3: Restore to Render PostgreSQL
psql $RENDER_DATABASE_URL < railway_database_backup.sql

# Step 4: Verify data integrity
psql $RENDER_DATABASE_URL -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Step 5: Run application-specific validation queries
# (Application-specific validation scripts)

# Step 6: Update application configuration
# Update environment variables in Render dashboard

# Step 7: Test application connectivity
curl -f http://localhost:8000/health/database || exit 1
```

### 4.2 Redis Migration Implementation

#### Redis Migration Steps
```yaml
Redis Migration Process:

Session Data Migration:
  - Decision: Allow natural session expiration (no migration)
  - Impact: Users will need to re-authenticate
  - Timeline: Gradual over 24-48 hours
  - Mitigation: Communication to users about brief re-login requirement

Rate Limiting Data:
  - Decision: Reset all rate limiting counters
  - Impact: Fresh start for all rate limits
  - Timeline: Immediate reset
  - Benefit: Clean slate for new platform

Cache Data Migration:
  - Critical configuration data: Export and import
  - API response cache: Allow natural expiration and rebuild
  - Computed data cache: Rebuild from source systems
  - Timeline: Gradual rebuild over 1-2 hours
```

#### Redis Configuration Update
```bash
# Redis Migration Configuration Script

# Step 1: Update Redis connection configuration
export REDIS_URL="rediss://default:new_password@render_redis_host:port"
export REDIS_PASSWORD="new_strong_password"

# Step 2: Test Redis connectivity
redis-cli -u $REDIS_URL ping

# Step 3: Configure Redis databases
redis-cli -u $REDIS_URL config set save "900 1 300 10 60 10000"

# Step 4: Test multi-database access
redis-cli -u $REDIS_URL -n 0 ping  # Default database
redis-cli -u $REDIS_URL -n 1 ping  # Rate limiting database

# Step 5: Update application configuration
# Update environment variables in Render dashboard

# Step 6: Test application Redis operations
curl -f http://localhost:8000/health/redis || exit 1
```

---

## Step 5: Performance Monitoring and Optimization

### 5.1 Database Performance Monitoring

#### Monitoring Configuration
```yaml
PostgreSQL Monitoring:

Performance Metrics:
  - Query execution time monitoring
  - Connection count and utilization
  - Database size and growth tracking
  - Index usage and optimization opportunities
  - Lock contention and deadlock detection

Alerting Thresholds:
  - Query time > 1 second (warning)
  - Query time > 5 seconds (critical)
  - Connection utilization > 80% (warning)
  - Connection utilization > 95% (critical)
  - Database size > 80% of allocated storage (warning)

Performance Optimization:
  - Slow query analysis and optimization
  - Index creation and maintenance
  - Connection pool tuning
  - Query plan analysis and optimization
```

#### Database Backup and Recovery
```yaml
Backup Configuration:

Automated Backups:
  - Daily full backups at 2 AM UTC
  - Point-in-time recovery capability
  - Backup retention: 7 days
  - Backup encryption and security
  - Backup validation and integrity checks

Recovery Procedures:
  - Point-in-time recovery testing
  - Full database restore procedures
  - Partial data recovery procedures
  - Recovery time objectives (RTO): <1 hour
  - Recovery point objectives (RPO): <24 hours

Backup Monitoring:
  - Backup success/failure alerts
  - Backup size and duration monitoring
  - Recovery procedure validation
  - Backup storage utilization tracking
```

### 5.2 Redis Performance Monitoring

#### Redis Monitoring Configuration
```yaml
Redis Performance Monitoring:

Key Metrics:
  - Memory usage and fragmentation
  - Connection count and utilization
  - Command execution statistics
  - Cache hit/miss ratios
  - Key expiration and eviction rates

Alerting Configuration:
  - Memory usage > 80% (warning)
  - Memory usage > 95% (critical)
  - Connection count > 200 (warning)
  - Cache hit ratio < 90% (warning)
  - High eviction rate (warning)

Performance Optimization:
  - Memory usage analysis and optimization
  - Key expiration strategy optimization
  - Connection pooling tuning
  - Cache warming strategies
  - Redis configuration tuning
```

---

## Step 6: Security Implementation and Validation

### 6.1 Database Security Implementation

#### Security Controls
```yaml
PostgreSQL Security:

Access Controls:
  - Role-based database user permissions
  - Application-specific database user (limited permissions)
  - Administrative access restricted and monitored
  - Connection source IP restrictions (Render network only)

Encryption and Data Protection:
  - SSL/TLS encryption for all connections
  - Data encryption at rest
  - Backup encryption
  - Connection certificate validation

Security Monitoring:
  - Failed authentication attempt monitoring
  - Unusual access pattern detection
  - Database modification audit logging
  - Security alert escalation procedures
```

### 6.2 Redis Security Implementation

#### Redis Security Configuration
```yaml
Redis Security Controls:

Authentication and Access:
  - Strong password authentication (AUTH command)
  - TLS encryption for all connections
  - Network access restricted to Render services
  - User-based access controls where supported

Data Protection:
  - Sensitive data encryption before Redis storage
  - Appropriate TTL for all cached sensitive data
  - Regular security audit of stored data
  - Key naming conventions for data classification

Security Monitoring:
  - Authentication failure monitoring
  - Unusual command pattern detection
  - Memory usage and access pattern monitoring
  - Security incident response procedures
```

---

## Step 7: Documentation and Team Handoff

### 7.1 Infrastructure Documentation

#### Database and Redis Documentation
```yaml
Documentation Requirements:

Technical Documentation:
  - Database and Redis configuration documentation
  - Connection string and security configuration
  - Performance tuning and optimization procedures
  - Backup and recovery procedures
  - Monitoring and alerting configuration

Operational Procedures:
  - Daily monitoring and maintenance procedures
  - Performance optimization procedures
  - Security audit and validation procedures
  - Incident response and troubleshooting procedures
  - Emergency escalation procedures

Migration Documentation:
  - Migration procedures and validation steps
  - Data integrity validation procedures
  - Rollback procedures and emergency recovery
  - Lessons learned and optimization recommendations
```

### 7.2 Team Training and Knowledge Transfer

#### Training Requirements
```yaml
Team Training:

Database Management Training:
  - PostgreSQL administration on Render
  - Performance monitoring and optimization
  - Backup and recovery procedures
  - Security management and compliance
  - Troubleshooting and emergency procedures

Redis Management Training:
  - Redis administration and configuration
  - Performance monitoring and tuning
  - Memory management and optimization
  - Security best practices
  - Cache strategy optimization

Operations Training:
  - Daily monitoring procedures
  - Performance analysis and optimization
  - Security validation and auditing
  - Incident response and escalation
  - Emergency procedures and recovery
```

---

## Success Criteria and Validation

### 8.1 MIG-008 Success Criteria

#### Database Infrastructure Success Criteria
```yaml
PostgreSQL Infrastructure Complete:
  - [ ] PostgreSQL database instance operational on Render
  - [ ] Complete data migration with zero data loss
  - [ ] Performance meeting or exceeding Railway baselines
  - [ ] Security controls implemented and validated
  - [ ] Backup and recovery procedures operational
  - [ ] Monitoring and alerting configured
  - [ ] Application connectivity validated
  - [ ] Team training completed and documented

Redis Infrastructure Complete:
  - [ ] Redis instance operational on Render
  - [ ] Multi-database configuration functional
  - [ ] Performance meeting or exceeding Railway baselines
  - [ ] Security controls implemented and validated
  - [ ] Connection pooling and optimization configured
  - [ ] Monitoring and alerting operational
  - [ ] Rate limiting functionality validated
  - [ ] Session management working correctly
```

### 8.2 Performance Validation

#### Performance Benchmark Validation
```yaml
Performance Requirements Met:

Database Performance:
  - [ ] Query response times <100ms for standard operations
  - [ ] Connection establishment <200ms
  - [ ] Transaction throughput meeting requirements
  - [ ] Concurrent connection handling validated
  - [ ] Performance monitoring baseline established

Redis Performance:
  - [ ] Cache operations <5ms response time
  - [ ] Connection establishment <100ms  
  - [ ] Cache hit ratios >90% for cached data
  - [ ] Memory utilization optimized
  - [ ] Rate limiting performance validated

Integration Performance:
  - [ ] Application startup time <60 seconds
  - [ ] Health check response time <1 second
  - [ ] End-to-end request processing <2 seconds
  - [ ] Multi-service architecture performance validated
```

---

## Risk Mitigation and Emergency Procedures

### 8.1 Migration Risk Management

#### Data Migration Risks
```yaml
Risk Assessment:

Data Loss Risk:
  - Mitigation: Multiple backup validation, checksum verification
  - Recovery: Immediate rollback to Railway with data restore
  - Testing: Pre-migration validation on staging environment

Performance Degradation Risk:
  - Mitigation: Performance baseline establishment, optimization
  - Recovery: Performance tuning, resource scaling
  - Testing: Load testing and performance validation

Application Connectivity Risk:
  - Mitigation: Connection testing, retry logic validation
  - Recovery: Configuration rollback, connection troubleshooting
  - Testing: End-to-end connectivity testing
```

### 8.2 Emergency Response Procedures

#### Emergency Recovery Procedures
```yaml
Emergency Response:

Database Issues:
  1. Immediate health check validation
  2. Connection troubleshooting and restoration
  3. Performance analysis and optimization
  4. Rollback procedures if critical issues
  5. Stakeholder communication and status updates

Redis Issues:
  1. Redis connectivity and performance validation
  2. Cache warming and data restoration
  3. Rate limiting functionality verification
  4. Configuration adjustment and optimization  
  5. Application functionality validation

Critical System Failure:
  1. Immediate assessment of impact and scope
  2. Emergency rollback to Railway if necessary
  3. Stakeholder notification and communication
  4. Emergency team activation and coordination
  5. Resolution timeline communication and updates
```

---

## Next Steps and Epic Integration

### 8.3 Completion and Handoff

#### Epic 2 Integration Status
```yaml
MIG-008 Integration with Other Epic 2 Tasks:

Completed Dependencies:
  - MIG-006: Account setup provides infrastructure foundation
  - MIG-007: Environment configuration provides deployment context

Ready to Enable:
  - MIG-009: Domain configuration can proceed with database connectivity
  - Environment variable mapping can include database/Redis URLs
  - Service configuration can include database health checks

Epic 3 Prerequisites:
  - Database infrastructure ready for application deployment
  - Redis infrastructure ready for session/cache management
  - Performance baselines established for deployment validation
  - Team training completed for operational support
```

This comprehensive database and Redis infrastructure setup guide ensures successful completion of MIG-008 while establishing enterprise-grade data infrastructure supporting the Railway to Render migration and protecting the £925K Odeon opportunity through zero-data-loss migration and optimized performance.