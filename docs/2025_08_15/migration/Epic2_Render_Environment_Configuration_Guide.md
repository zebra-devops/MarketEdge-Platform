# Epic 2: Render Environment Configuration Guide

## MIG-007: Render Environment Configuration (5 pts)

### Executive Summary

**Business Context**: Following successful Render account setup (MIG-006), establish staging and production environments with comprehensive environment variable management and security isolation.

**Implementation Objective**: Create enterprise-grade environment configuration supporting multi-tenant business intelligence platform with zero impact on £925K Odeon demo functionality.

**Success Criteria**: Staging and production environments operational with complete environment variable migration, security isolation, and readiness for multi-service Docker deployment.

---

## Environment Architecture Overview

### Environment Strategy

Based on Railway configuration analysis and business requirements:

```yaml
Environment Architecture:
  
  Production Environment:
    Purpose: Live client-facing services (Odeon demo protection)
    Domain: app.zebra.associates (custom domain)
    Resource Tier: Production-grade (2GB RAM, 1+ vCPU)
    Security: Maximum security controls and monitoring
    
  Staging Environment:
    Purpose: Pre-production testing and validation
    Domain: staging.render.app subdomain
    Resource Tier: Development-grade (1GB RAM, 0.5 vCPU)
    Security: Production-equivalent security for testing
```

### Environment Isolation Requirements

```yaml
Isolation Principles:
  Data Isolation:
    - Separate PostgreSQL databases per environment
    - Separate Redis instances per environment
    - No cross-environment data sharing
    
  Security Isolation:
    - Environment-specific secrets and credentials
    - Separate Auth0 application configurations
    - Environment-specific CORS origins
    
  Resource Isolation:
    - Independent resource allocation per environment
    - Separate monitoring and alerting
    - Independent scaling and performance tuning
```

---

## Step 1: Production Environment Setup

### 1.1 Production Web Service Creation

#### Service Configuration
```yaml
Production Service Configuration:
  Service Name: platform-wrapper-production
  Service Type: Web Service
  Environment: production
  
  Runtime Configuration:
    Build Command: docker build .
    Start Command: supervisord -c /etc/supervisor/conf.d/supervisord.conf
    Dockerfile Path: ./Dockerfile
    Build Context: Root directory
    
  Resource Allocation:
    Memory: 2GB (multi-service requirement: Caddy + FastAPI)
    CPU: 1 vCPU (concurrent process support)
    Storage: SSD (application and logs)
    Auto Scaling: Disabled initially (manual control)
    
  Network Configuration:
    Ports: 80 (Caddy proxy), 8000 (FastAPI internal)
    Health Check: /health endpoint on port 8000
    External Access: Port 80 (Caddy handles routing)
```

#### GitHub Integration Setup
```yaml
Source Control Integration:
  Repository: MarketEdge/platform-wrapper
  Branch: main (production deployments only)
  Auto Deploy: Enabled for main branch
  Manual Deploy: Available via dashboard
  
  Build Configuration:
    Context: /backend (Dockerfile location)
    Docker Build Args: Production optimizations
    Build Caching: Enabled for faster deployments
```

### 1.2 Production Environment Variables Configuration

#### Environment Variable Organization Strategy

Based on Railway `.env.railway.template` analysis (58+ variables):

```yaml
Environment Variable Groups:

Group 1: Core Application Configuration
  - PROJECT_NAME="Platform Wrapper"
  - PROJECT_VERSION="1.0.0" 
  - ENVIRONMENT="production"
  - DEBUG="false"
  - LOG_LEVEL="INFO"
  - PORT="8000"
  - FASTAPI_PORT="8000"

Group 2: Database Configuration
  - DATABASE_URL="postgresql://..." (Render PostgreSQL)
  - Database connection pooling settings
  - Database timeout configurations

Group 3: Redis Configuration  
  - REDIS_URL="redis://..." (Render Redis)
  - REDIS_PASSWORD="..." (encrypted)
  - REDIS_SSL_ENABLED="true"
  - REDIS_CONNECTION_POOL_SIZE="50"
  - Rate limiting Redis configuration

Group 4: Authentication (Auth0)
  - AUTH0_DOMAIN="your-tenant.auth0.com"
  - AUTH0_CLIENT_ID="..." (encrypted secret)
  - AUTH0_CLIENT_SECRET="..." (encrypted secret)
  - AUTH0_CALLBACK_URL="https://app.zebra.associates/callback"

Group 5: CORS and Security
  - CORS_ORIGINS="https://app.zebra.associates,http://localhost:3001"
  - CADDY_PROXY_MODE="true"
  - Security headers configuration

Group 6: JWT and Token Management
  - JWT_SECRET_KEY="..." (encrypted secret)
  - JWT_ALGORITHM="HS256"
  - ACCESS_TOKEN_EXPIRE_MINUTES="30"
  - REFRESH_TOKEN_EXPIRE_DAYS="7"

Group 7: Rate Limiting
  - RATE_LIMIT_ENABLED="true"
  - RATE_LIMIT_REQUESTS_PER_MINUTE="60"
  - RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE="1000"

Group 8: External Services
  - DATA_LAYER_SUPABASE__URL="..." (if used)
  - DATA_LAYER_SUPABASE__KEY="..." (encrypted secret)
  - Third-party API configurations
```

#### Production Environment Variables Setup

```yaml
Production Variables (58+ variables from Railway migration):

# Core Application
PROJECT_NAME="Platform Wrapper"
PROJECT_VERSION="1.0.0"
ENVIRONMENT="production"
DEBUG="false"
LOG_LEVEL="INFO"
PORT="8000"
FASTAPI_PORT="8000"

# Multi-Service Configuration
CADDY_PROXY_MODE="true"
CORS_ORIGINS="https://app.zebra.associates,http://localhost:3001"

# Database (will be updated with Render PostgreSQL)
DATABASE_URL="${RENDER_POSTGRESQL_URL}"

# Redis (will be updated with Render Redis)
REDIS_URL="${RENDER_REDIS_URL}"
REDIS_PASSWORD="${RENDER_REDIS_PASSWORD}"
REDIS_SSL_ENABLED="true"
REDIS_CONNECTION_POOL_SIZE="50"
REDIS_HEALTH_CHECK_INTERVAL="30"
REDIS_SOCKET_CONNECT_TIMEOUT="5"
REDIS_SOCKET_TIMEOUT="2"

# Rate Limiting
RATE_LIMIT_STORAGE_URL="${RENDER_REDIS_URL}/1"
RATE_LIMIT_ENABLED="true"
RATE_LIMIT_REQUESTS_PER_MINUTE="60"
RATE_LIMIT_BURST_SIZE="10"
RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE="1000"
RATE_LIMIT_ADMIN_REQUESTS_PER_MINUTE="5000"

# JWT Configuration (secrets encrypted)
JWT_SECRET_KEY="${JWT_SECRET}"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES="30"
REFRESH_TOKEN_EXPIRE_DAYS="7"

# Auth0 Configuration (secrets encrypted)
AUTH0_DOMAIN="${AUTH0_PRODUCTION_DOMAIN}"
AUTH0_CLIENT_ID="${AUTH0_PRODUCTION_CLIENT_ID}"
AUTH0_CLIENT_SECRET="${AUTH0_PRODUCTION_CLIENT_SECRET}"
AUTH0_CALLBACK_URL="https://app.zebra.associates/callback"

# External Services (if applicable)
DATA_LAYER_SUPABASE__URL="${SUPABASE_URL}"
DATA_LAYER_SUPABASE__KEY="${SUPABASE_ANON_KEY}"
```

---

## Step 2: Staging Environment Setup

### 2.1 Staging Web Service Creation

#### Service Configuration
```yaml
Staging Service Configuration:
  Service Name: platform-wrapper-staging
  Service Type: Web Service
  Environment: staging
  
  Runtime Configuration:
    Build Command: docker build .
    Start Command: supervisord -c /etc/supervisor/conf.d/supervisord.conf
    Dockerfile Path: ./Dockerfile
    Build Context: Root directory
    
  Resource Allocation:
    Memory: 1GB (sufficient for testing multi-service)
    CPU: 0.5 vCPU (adequate for staging workload)
    Storage: SSD (application and logs)
    Auto Scaling: Disabled (manual control for testing)
    
  Network Configuration:
    Ports: 80 (Caddy proxy), 8000 (FastAPI internal)
    Health Check: /health endpoint on port 8000
    External Access: Port 80 (staging subdomain)
```

#### GitHub Integration Setup
```yaml
Source Control Integration:
  Repository: MarketEdge/platform-wrapper
  Branch: develop/staging (separate from production)
  Auto Deploy: Disabled (manual deployment for testing)
  Manual Deploy: Primary deployment method
  
  Build Configuration:
    Context: /backend (same Dockerfile as production)
    Docker Build Args: Staging-specific optimizations
    Build Caching: Enabled for faster iteration
```

### 2.2 Staging Environment Variables Configuration

```yaml
Staging Variables (modified from production for testing):

# Core Application (staging-specific)
PROJECT_NAME="Platform Wrapper Staging"
PROJECT_VERSION="1.0.0-staging"
ENVIRONMENT="staging"
DEBUG="true"
LOG_LEVEL="DEBUG"
PORT="8000"
FASTAPI_PORT="8000"

# Multi-Service Configuration
CADDY_PROXY_MODE="true"
CORS_ORIGINS="https://platform-wrapper-staging.render.app,http://localhost:3000,http://localhost:3001"

# Database (staging-specific PostgreSQL)
DATABASE_URL="${RENDER_POSTGRESQL_STAGING_URL}"

# Redis (staging-specific Redis)
REDIS_URL="${RENDER_REDIS_STAGING_URL}"
REDIS_PASSWORD="${RENDER_REDIS_STAGING_PASSWORD}"
REDIS_SSL_ENABLED="true"

# Rate Limiting (relaxed for testing)
RATE_LIMIT_ENABLED="true"
RATE_LIMIT_REQUESTS_PER_MINUTE="120"
RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE="2000"

# JWT Configuration (staging-specific secrets)
JWT_SECRET_KEY="${JWT_SECRET_STAGING}"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES="60"
REFRESH_TOKEN_EXPIRE_DAYS="14"

# Auth0 Configuration (staging Auth0 application)
AUTH0_DOMAIN="${AUTH0_STAGING_DOMAIN}"
AUTH0_CLIENT_ID="${AUTH0_STAGING_CLIENT_ID}"
AUTH0_CLIENT_SECRET="${AUTH0_STAGING_CLIENT_SECRET}"
AUTH0_CALLBACK_URL="https://platform-wrapper-staging.render.app/callback"
```

---

## Step 3: Environment Variable Security and Management

### 3.1 Secrets Management Strategy

#### Secret Classification
```yaml
Secret Classification:

High Sensitivity (Encrypted Secrets):
  - Database credentials and connection strings
  - Redis passwords and connection details
  - JWT secret keys
  - Auth0 client secrets
  - External service API keys
  - Encryption keys and certificates

Medium Sensitivity (Environment Variables):
  - Auth0 client IDs and domains
  - Database and Redis URLs (without credentials)
  - External service URLs
  - Feature flags and configuration

Low Sensitivity (Public Configuration):
  - Application name and version
  - Environment identifier
  - Debug flags
  - Log levels
  - Public API endpoints
```

#### Security Best Practices Implementation
```yaml
Security Controls:

Access Controls:
  - Role-based access to environment variables
  - Audit logging for all variable changes
  - Limited team member access to production secrets
  - Separate staging and production secret access

Encryption and Storage:
  - All secrets encrypted at rest in Render
  - Secrets encrypted in transit
  - No secrets stored in code repository
  - Secret rotation procedures documented

Monitoring and Alerting:
  - Failed authentication alerts
  - Environment variable change notifications
  - Unusual access pattern monitoring
  - Secret expiration monitoring where applicable
```

### 3.2 Environment Variable Groups Organization

#### Production Environment Groups
```yaml
Production Variable Groups:

Core Application Settings:
  - PROJECT_NAME, PROJECT_VERSION, ENVIRONMENT
  - DEBUG, LOG_LEVEL, PORT, FASTAPI_PORT
  - CADDY_PROXY_MODE

Security and CORS:
  - CORS_ORIGINS
  - JWT_SECRET_KEY, JWT_ALGORITHM
  - ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

Database Configuration:
  - DATABASE_URL
  - Connection pool settings
  - Query timeout configurations

Redis Configuration:
  - REDIS_URL, REDIS_PASSWORD
  - Connection pool and timeout settings
  - Rate limiting Redis configuration

Authentication (Auth0):
  - AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET
  - AUTH0_CALLBACK_URL

Rate Limiting:
  - RATE_LIMIT_ENABLED, RATE_LIMIT_REQUESTS_PER_MINUTE
  - RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE
  - RATE_LIMIT_ADMIN_REQUESTS_PER_MINUTE

External Services:
  - DATA_LAYER_SUPABASE__URL, DATA_LAYER_SUPABASE__KEY
  - Third-party service configurations
```

---

## Step 4: Environment-Specific Configuration

### 4.1 Production-Specific Configurations

#### Performance Optimizations
```yaml
Production Performance Settings:

Application Performance:
  - DEBUG="false" (no debug overhead)
  - LOG_LEVEL="INFO" (reduced logging overhead)
  - Connection pooling optimized for production load
  - Caching configurations optimized

Security Hardening:
  - CORS_ORIGINS restricted to production domains only
  - Rate limiting configured for production traffic patterns
  - JWT token expiration appropriate for security
  - All secrets properly encrypted

Resource Optimization:
  - Memory allocation optimized for production workload
  - CPU allocation supporting concurrent multi-service
  - Storage optimization for logs and temporary files
```

#### Production Monitoring Configuration
```yaml
Production Monitoring:

Health Checks:
  - Endpoint: /health
  - Interval: 30 seconds
  - Timeout: 10 seconds
  - Retries: 3
  - Start period: 60 seconds (multi-service startup)

Logging Configuration:
  - Structured logging for analysis
  - Log retention appropriate for compliance
  - Error tracking and alerting
  - Performance monitoring integration

Alerting Thresholds:
  - Response time > 2 seconds
  - Error rate > 1%
  - Memory usage > 80%
  - CPU usage > 70%
  - Database connection failures
```

### 4.2 Staging-Specific Configurations

#### Development and Testing Optimizations
```yaml
Staging Development Settings:

Application Development:
  - DEBUG="true" (detailed error information)
  - LOG_LEVEL="DEBUG" (comprehensive logging)
  - Relaxed rate limiting for testing
  - Extended token expiration for testing convenience

Testing Configurations:
  - CORS_ORIGINS including localhost for local testing
  - Database configured for test data isolation
  - Redis configured for test caching scenarios
  - Auth0 configured for test user scenarios

Resource Allocation:
  - Memory allocation adequate for testing scenarios
  - CPU allocation supporting development workflows
  - Storage adequate for test data and logs
```

---

## Step 5: Environment Validation and Testing

### 5.1 Environment Configuration Validation

#### Production Environment Validation Checklist
```yaml
Production Validation:

Service Configuration:
  - [ ] Web service created and configured correctly
  - [ ] GitHub integration working with main branch
  - [ ] Docker multi-service build successful
  - [ ] Health checks passing consistently

Environment Variables:
  - [ ] All 58+ variables migrated from Railway
  - [ ] Secrets properly encrypted and access-controlled
  - [ ] Environment-specific values correctly set
  - [ ] No sensitive data exposed in logs

Network and Security:
  - [ ] CORS origins correctly configured
  - [ ] Authentication flow working through environment
  - [ ] Rate limiting functioning as configured
  - [ ] SSL/TLS configuration appropriate

Resource and Performance:
  - [ ] Memory and CPU allocation appropriate
  - [ ] Health checks responding within timeouts
  - [ ] Service startup time acceptable
  - [ ] No resource constraint warnings
```

#### Staging Environment Validation Checklist
```yaml
Staging Validation:

Service Configuration:
  - [ ] Staging web service created and configured
  - [ ] Manual deployment capability working
  - [ ] Docker build process identical to production
  - [ ] Health checks configured and passing

Environment Variables:
  - [ ] Staging-specific variables correctly configured
  - [ ] Debug and development features enabled
  - [ ] Test-appropriate CORS origins configured
  - [ ] Staging Auth0 application working

Testing Capabilities:
  - [ ] Local development integration working
  - [ ] Test data isolation verified
  - [ ] Development workflow optimization validated
  - [ ] Team access for testing confirmed
```

### 5.2 Cross-Environment Isolation Testing

#### Data Isolation Verification
```yaml
Isolation Testing:

Database Isolation:
  - [ ] Production and staging databases completely separate
  - [ ] No cross-environment data access possible
  - [ ] Connection string isolation verified
  - [ ] Backup procedures environment-specific

Authentication Isolation:
  - [ ] Separate Auth0 applications per environment
  - [ ] No cross-environment token acceptance
  - [ ] Environment-specific callback URLs working
  - [ ] User session isolation verified

Security Isolation:
  - [ ] Environment-specific secrets properly isolated
  - [ ] No secret sharing between environments
  - [ ] Access controls environment-specific
  - [ ] Audit logging environment-separated
```

---

## Step 6: Documentation and Procedures

### 6.1 Environment Management Documentation

#### Environment Configuration Guide
```yaml
Documentation Requirements:

Environment Setup Procedures:
  - Step-by-step environment creation process
  - Environment variable configuration procedures
  - Secret management and rotation procedures
  - Environment validation and testing procedures

Team Access and Management:
  - Environment-specific access controls
  - Deployment procedures per environment
  - Monitoring and troubleshooting procedures
  - Emergency procedures and escalation

Configuration Management:
  - Environment variable change procedures
  - Configuration drift detection and resolution
  - Environment synchronization procedures
  - Backup and recovery procedures
```

#### Environment Operations Runbook
```yaml
Operations Procedures:

Daily Operations:
  - Environment health monitoring procedures
  - Performance monitoring and analysis
  - Log analysis and issue identification
  - Security monitoring and validation

Incident Response:
  - Environment-specific troubleshooting procedures
  - Emergency rollback procedures
  - Cross-environment impact assessment
  - Stakeholder communication procedures

Maintenance Procedures:
  - Environment variable updates and rotation
  - Service configuration updates
  - Security patch and update procedures
  - Performance optimization procedures
```

---

## Step 7: Team Training and Handoff

### 7.1 Team Training Requirements

#### Environment Management Training
```yaml
Training Materials:

Render Platform Training:
  - Environment creation and management
  - Environment variable configuration and security
  - Service deployment and monitoring
  - Troubleshooting and emergency procedures

Security Training:
  - Secret management best practices
  - Environment isolation principles
  - Access control and audit procedures
  - Incident response and escalation

Operations Training:
  - Daily monitoring and maintenance procedures
  - Performance optimization and tuning
  - Cross-environment management
  - Documentation and knowledge sharing
```

### 7.2 Environment Handoff Procedures

#### Production Environment Handoff
```yaml
Production Handoff Checklist:

Environment Readiness:
  - [ ] Production environment fully configured and validated
  - [ ] All environment variables migrated and tested
  - [ ] Security controls implemented and verified
  - [ ] Performance benchmarks established

Team Readiness:
  - [ ] All team members trained on environment management
  - [ ] Access controls and permissions validated
  - [ ] Emergency procedures tested and verified
  - [ ] Documentation complete and accessible

Operational Readiness:
  - [ ] Monitoring and alerting configured
  - [ ] Backup and recovery procedures tested
  - [ ] Incident response procedures validated
  - [ ] Stakeholder communication procedures established
```

---

## Success Criteria and Completion Validation

### MIG-007 Success Criteria

```yaml
Environment Configuration Complete:

Infrastructure:
  - [ ] Production environment operational with proper configuration
  - [ ] Staging environment operational with testing-optimized configuration
  - [ ] Environment isolation verified and tested
  - [ ] Resource allocation appropriate for requirements

Security:
  - [ ] All environment variables securely migrated and organized
  - [ ] Secrets properly encrypted and access-controlled
  - [ ] Environment-specific security controls implemented
  - [ ] Access controls and audit logging operational

Operations:
  - [ ] Environment validation and testing completed successfully
  - [ ] Team training completed and competency verified
  - [ ] Documentation complete and procedures validated
  - [ ] Handoff procedures completed and signed off
```

### Readiness for Next Epic

```yaml
Epic 3 Prerequisites Met:
  - [ ] Both production and staging environments ready for application deployment
  - [ ] All environment variables configured and tested
  - [ ] Multi-service architecture configuration validated
  - [ ] Team trained and ready for application migration
  
Dependencies for MIG-008:
  - Database infrastructure setup can proceed with environment foundation
  - Redis configuration can proceed with environment foundation
  - Domain and SSL configuration ready for environment integration
```

---

## Risk Mitigation and Emergency Procedures

### Environment Configuration Risks

```yaml
Risk Assessment and Mitigation:

Configuration Errors:
  - Risk: Incorrect environment variable configuration
  - Mitigation: Comprehensive validation checklist and testing
  - Recovery: Environment variable rollback procedures

Security Vulnerabilities:
  - Risk: Exposed secrets or improper access controls
  - Mitigation: Security validation procedures and audit logging
  - Recovery: Immediate secret rotation and access review

Performance Issues:
  - Risk: Inadequate resource allocation or configuration
  - Mitigation: Performance testing and monitoring
  - Recovery: Resource scaling and configuration adjustment

Cross-Environment Issues:
  - Risk: Environment isolation failures or configuration drift
  - Mitigation: Isolation testing and configuration management
  - Recovery: Environment reset and reconfiguration procedures
```

### Emergency Response Procedures

```yaml
Emergency Procedures:

Environment Access Issues:
  1. Verify team member access and permissions
  2. Use backup admin access for emergency recovery
  3. Contact Render support for platform issues
  4. Implement temporary workarounds if possible
  5. Communicate status to stakeholders immediately

Configuration Issues:
  1. Identify scope and impact of configuration problem
  2. Implement immediate rollback if possible
  3. Use staging environment for testing fixes
  4. Validate fixes before applying to production
  5. Document issue and resolution for future reference
```

This comprehensive environment configuration guide ensures successful completion of MIG-007 while establishing enterprise-grade environment management supporting the Railway to Render migration and protecting the £925K Odeon opportunity.