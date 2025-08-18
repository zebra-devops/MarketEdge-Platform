# Epic 2: Render Web Service Configuration Guide

## Render Web Service Setup with Docker Multi-Service Architecture

### Executive Summary

**Business Context**: Configure Render web service supporting Docker multi-service architecture (Caddy proxy + FastAPI backend) with enterprise-grade performance, security, and monitoring for the £925K Odeon opportunity.

**Implementation Objective**: Complete web service configuration enabling seamless deployment of validated Docker multi-service architecture with proper resource allocation, health monitoring, and deployment automation.

**Success Criteria**: Render web service operational with multi-service Docker support, automated deployments, proper resource allocation, comprehensive monitoring, and validated performance meeting enterprise requirements.

---

## Current Docker Architecture Analysis

### Railway Multi-Service Architecture (Validated)

From current Docker configuration analysis:

```yaml
Current Multi-Service Architecture:

Dockerfile Configuration:
  Base Image: python:3.11-slim
  Services: Caddy proxy (port 80) + FastAPI backend (port 8000)
  Process Manager: Supervisord managing both services
  Security: Non-root user (appuser) for service execution
  Health Check: /health endpoint on FastAPI port 8000

Supervisord Configuration:
  Program 1: Caddy reverse proxy (port 80 external)
  Program 2: FastAPI backend (port 8000 internal)
  User: appuser (non-root execution)
  Logging: Structured logging for both services
  Auto-restart: Enabled for service resilience

Service Communication:
  External → Caddy (port 80) → FastAPI (port 8000) → Database/Redis
  CORS: Handled by Caddy proxy with proper header injection
  SSL: Terminated at Caddy level (Railway) or external (Render)
  Load Balancing: Caddy handles request routing and load balancing

Resource Requirements:
  Memory: 2GB minimum (both services + monitoring)
  CPU: 1+ vCPU (concurrent process support)
  Storage: SSD for application logs and temporary files
  Network: Multi-port exposure (80, 8000) with internal communication
```

### Target Render Service Configuration

```yaml
Render Service Requirements:

Service Type: Web Service
Build Method: Docker (using existing validated Dockerfile)
Runtime: Multi-process container with Supervisord
Resource Tier: Production-appropriate (2GB RAM, 1 vCPU minimum)

Port Configuration:
  External Port: 80 (Caddy proxy - public access)
  Internal Port: 8000 (FastAPI - health checks)
  Service Communication: localhost between Caddy and FastAPI

Deployment Configuration:
  Source: GitHub repository (MarketEdge/platform-wrapper)
  Branch: main (production), develop (staging)
  Build Context: /backend (Dockerfile location)
  Auto Deploy: Enabled for continuous deployment

Health Monitoring:
  Health Check: /health endpoint on FastAPI (port 8000)
  Ready Check: /ready endpoint for deployment validation
  Startup Time: 60+ seconds (multi-service initialization)
  Monitoring: Service-level and application-level health checks
```

---

## Step 1: Production Web Service Configuration

### 1.1 Service Creation and Basic Setup

#### Production Web Service Configuration
```yaml
Render Production Service Setup:

Service Details:
  Name: platform-wrapper-production
  Type: Web Service
  Environment: Production
  Region: US East (optimal for target audience)

Source Configuration:
  Repository: https://github.com/MarketEdge/platform-wrapper
  Branch: main
  Root Directory: backend
  Auto Deploy: Yes (on main branch pushes)

Build Configuration:
  Build Command: docker build -t platform-wrapper .
  Dockerfile Path: ./Dockerfile
  Build Context: Current directory (backend)
  Docker Build Args: None (all configuration via environment variables)
```

#### Resource Allocation Configuration
```yaml
Resource Configuration:

Memory Allocation:
  Production: 2GB (multi-service requirement)
  Justification: Caddy (200MB) + FastAPI (800MB) + System (1GB)
  Monitoring: Memory usage alerts at 80% and 90%

CPU Allocation:
  Production: 1 vCPU (minimum for multi-process)
  Scaling: Auto-scaling enabled based on CPU utilization
  Target: 70% CPU utilization for scaling triggers

Storage Configuration:
  Disk Space: 1GB (application + logs + temporary files)
  Type: SSD storage for optimal performance
  Monitoring: Disk usage alerts at 80% capacity

Network Configuration:
  External Port: 80 (Caddy proxy)
  Health Check Port: 8000 (FastAPI)
  Internal Communication: localhost between services
  Bandwidth: Unlimited (included in plan)
```

### 1.2 Docker Multi-Service Configuration

#### Dockerfile Validation for Render
```dockerfile
# Current Dockerfile (validated for multi-service)
FROM python:3.11-slim

# Security: Create non-root user early
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

WORKDIR /app

# Install system dependencies including Caddy and Supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl supervisor \
    debian-keyring debian-archive-keyring apt-transport-https ca-certificates \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list \
    && apt-get update && apt-get install -y --no-install-recommends caddy \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /var/log/supervisor /var/log/caddy /var/run \
    && chmod 755 /var/log/supervisor /var/log/caddy \
    && chown appuser:appuser /var/log/supervisor /var/log/caddy

# Copy configuration files
COPY --chown=root:root supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY --chown=appuser:appuser Caddyfile /app/Caddyfile

# Set permissions
RUN chmod 755 start.sh && chmod 644 /etc/supervisor/conf.d/supervisord.conf && chmod 644 /app/Caddyfile

# Expose necessary ports
EXPOSE 80 8000

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run supervisord as root (services run as appuser)
USER root
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

#### Supervisord Configuration for Multi-Service
```ini
# supervisord.conf - Multi-service configuration
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
childlogdir=/var/log/supervisor

[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

# FastAPI Backend Service
[program:fastapi]
command=uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
directory=/app
user=appuser
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/fastapi.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
priority=100

# Caddy Proxy Service
[program:caddy]
command=caddy run --config /app/Caddyfile --adapter caddyfile
directory=/app
user=appuser
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/caddy.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
priority=200
```

#### Caddyfile Configuration for CORS and Proxy
```caddyfile
# Caddyfile - Caddy proxy configuration for Render
:80 {
    # Disable automatic HTTPS (handled by Render)
    auto_https off
    
    # CORS headers for authentication and API access
    header {
        Access-Control-Allow-Origin "https://app.zebra.associates"
        Access-Control-Allow-Credentials true
        Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With, X-API-Key"
        Access-Control-Max-Age "86400"
        
        # Security headers
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
    
    # Handle preflight requests
    @options {
        method OPTIONS
    }
    respond @options 204
    
    # Reverse proxy to FastAPI backend
    reverse_proxy localhost:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
    
    # Logging
    log {
        output file /var/log/caddy/access.log
        format json
        level INFO
    }
}
```

---

## Step 2: Health Check and Monitoring Configuration

### 2.1 Health Check Configuration

#### Render Health Check Setup
```yaml
Health Check Configuration:

Primary Health Check:
  Path: /health
  Port: 8000 (FastAPI backend)
  Method: GET
  Expected Status: 200
  Timeout: 10 seconds
  Interval: 30 seconds
  Retries: 3
  
Startup Configuration:
  Initial Delay: 60 seconds (multi-service startup time)
  Startup Timeout: 300 seconds (5 minutes maximum)
  Failure Threshold: 3 consecutive failures
  
Health Check Response:
  Format: JSON with service status
  Content: Database connectivity, Redis connectivity, service status
  Performance: Response time <1 second
```

#### Application Health Check Implementation
```python
# Health check endpoint implementation
from fastapi import FastAPI, HTTPException
from datetime import datetime
import redis
import asyncpg
import asyncio

app = FastAPI()

@app.get("/health")
async def health_check():
    """Comprehensive health check for multi-service architecture"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "fastapi": "healthy",
            "database": "unknown",
            "redis": "unknown",
            "caddy": "unknown"
        },
        "version": "1.0.0"
    }
    
    # Check database connectivity
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        await conn.execute('SELECT 1')
        await conn.close()
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Redis connectivity
    try:
        r = redis.from_url(os.getenv('REDIS_URL'))
        r.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Caddy proxy (attempt connection to port 80)
    try:
        # Simple check if Caddy is responding
        import requests
        response = requests.get('http://localhost:80/health', timeout=5)
        if response.status_code == 200:
            health_status["services"]["caddy"] = "healthy"
        else:
            health_status["services"]["caddy"] = "degraded"
    except Exception:
        health_status["services"]["caddy"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Determine overall status
    unhealthy_services = [k for k, v in health_status["services"].items() if v == "unhealthy"]
    if unhealthy_services:
        if len(unhealthy_services) > 1:
            health_status["status"] = "unhealthy"
        else:
            health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=health_status)
    
    return health_status

@app.get("/ready")
async def readiness_check():
    """Simple readiness check for deployment validation"""
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "platform-wrapper",
        "version": "1.0.0"
    }
```

### 2.2 Service Monitoring Configuration

#### Service-Level Monitoring
```yaml
Render Service Monitoring:

Resource Monitoring:
  - CPU utilization (target: <70%)
  - Memory utilization (target: <80%)
  - Disk utilization (target: <80%)
  - Network throughput and latency
  
Application Monitoring:
  - Response time monitoring (target: <2 seconds)
  - Error rate monitoring (target: <1%)
  - Request throughput tracking
  - Health check success rate (target: >99%)
  
Service Availability:
  - Uptime monitoring (target: >99.9%)
  - Service restart frequency tracking
  - Deployment success rate monitoring
  - Rollback frequency tracking

Alert Configuration:
  - Critical: Service down, health check failures
  - Warning: High resource utilization, slow response times
  - Info: Deployments, scaling events
```

---

## Step 3: Deployment Configuration and Automation

### 3.1 GitHub Integration and Deployment

#### Repository Configuration
```yaml
GitHub Integration Setup:

Repository Configuration:
  Repository: MarketEdge/platform-wrapper
  Access: Deploy key or GitHub integration
  Branch Strategy: main (production), develop (staging)
  Webhook Configuration: Automatic on push to main

Build Configuration:
  Build Command: None (Docker build handled automatically)
  Build Context: /backend directory
  Docker Build: Automatic detection of Dockerfile
  Build Caching: Enabled for faster builds
  
Environment Configuration:
  Production Branch: main
  Staging Branch: develop  
  Auto Deploy: Enabled for both branches
  Manual Deploy: Available via Render dashboard

Security Configuration:
  Deploy Key: Read-only access to repository
  Environment Secrets: Not stored in repository
  Build Logs: Available in Render dashboard
  Source Code: Protected in private repository
```

#### Deployment Pipeline Configuration
```yaml
Deployment Pipeline:

Trigger Events:
  - Push to main branch (production deployment)
  - Push to develop branch (staging deployment)
  - Manual deployment via Render dashboard
  - API-triggered deployment for CI/CD integration

Build Process:
  1. Source code checkout from GitHub
  2. Docker image build with multi-stage optimization
  3. Environment variable injection
  4. Container startup with health check validation
  5. Traffic routing to new deployment
  6. Old container shutdown after health validation

Rollback Configuration:
  - Automatic rollback on health check failures
  - Manual rollback via Render dashboard  
  - Previous deployment preservation (3 versions)
  - Instant rollback capability (<2 minutes)

Deployment Validation:
  - Health check validation (60 seconds timeout)
  - Performance validation (response time testing)
  - Integration testing (database and Redis connectivity)
  - Traffic validation (sample request processing)
```

### 3.2 Environment-Specific Deployment Configuration

#### Production Deployment Configuration
```yaml
Production Deployment:

Service Configuration:
  Name: platform-wrapper-production
  Branch: main
  Auto Deploy: Yes
  Health Check: Strict (3 retries maximum)
  
Resource Configuration:
  Memory: 2GB (fixed allocation)
  CPU: 1 vCPU (minimum, auto-scaling available)
  Instances: 1 (can be scaled based on load)
  
Environment Variables:
  Source: Render environment variable configuration
  Secrets: Encrypted secrets management
  Configuration: Production-optimized settings
  
Monitoring Configuration:
  Health Checks: Every 30 seconds
  Performance Monitoring: Enabled
  Alerting: Configured for all critical metrics
  Logging: Structured JSON logging
```

#### Staging Deployment Configuration
```yaml
Staging Deployment:

Service Configuration:
  Name: platform-wrapper-staging
  Branch: develop
  Auto Deploy: No (manual deployment for testing)
  Health Check: Relaxed (5 retries for testing)
  
Resource Configuration:
  Memory: 1GB (cost-optimized for testing)
  CPU: 0.5 vCPU (adequate for testing load)
  Instances: 1 (fixed for testing consistency)
  
Environment Variables:
  Source: Staging-specific environment configuration
  Secrets: Separate staging secrets
  Configuration: Debug-enabled settings
  
Monitoring Configuration:
  Health Checks: Every 60 seconds
  Performance Monitoring: Basic monitoring
  Alerting: Reduced alerting for testing environment
  Logging: Debug-level logging enabled
```

---

## Step 4: Performance Optimization and Scaling

### 4.1 Performance Configuration

#### Service Performance Optimization
```yaml
Performance Optimization Strategy:

Docker Image Optimization:
  - Multi-stage builds for smaller image size
  - Dependency caching for faster builds
  - Security scanning integration
  - Base image optimization (python:3.11-slim)

Application Performance:
  - FastAPI worker optimization (2 workers for 1 vCPU)
  - Connection pooling for database and Redis
  - Caching strategy implementation
  - Request/response optimization

Network Performance:
  - Caddy proxy optimization for request routing
  - Compression enabled for response optimization
  - Keep-alive connections for reduced latency
  - CDN integration for static content (future)

Resource Utilization:
  - Memory allocation optimization
  - CPU utilization monitoring and tuning
  - Disk I/O optimization for logging
  - Network bandwidth optimization
```

#### Auto-Scaling Configuration
```yaml
Auto-Scaling Strategy:

Scaling Triggers:
  - CPU utilization >70% (scale up)
  - CPU utilization <30% (scale down)
  - Memory utilization >80% (scale up)
  - Response time >2 seconds (scale up)
  
Scaling Limits:
  - Minimum Instances: 1
  - Maximum Instances: 3 (cost-controlled scaling)
  - Scale-up Cooldown: 5 minutes
  - Scale-down Cooldown: 10 minutes
  
Performance Targets:
  - Response Time: <2 seconds (95th percentile)
  - Throughput: 100+ requests per second
  - Error Rate: <1%
  - CPU Utilization: 50-70% (optimal range)
```

---

## Step 5: Security and Compliance Configuration

### 5.1 Service Security Configuration

#### Container Security
```yaml
Container Security Configuration:

User Security:
  - Non-root user execution (appuser)
  - Minimal privileges for service processes
  - Secure file permissions (644/755)
  - No privileged container execution

Network Security:
  - Port exposure limited to necessary ports (80, 8000)
  - Internal service communication (localhost)
  - No unnecessary network access
  - Firewall rules via Render network policies

Image Security:
  - Base image security scanning
  - Dependency vulnerability scanning
  - Regular security updates
  - Minimal attack surface (slim base image)

Runtime Security:
  - Process isolation via supervisord
  - Log security and audit trails
  - Secret management via environment variables
  - No hardcoded credentials in container
```

#### Application Security Configuration
```yaml
Application Security:

CORS Security:
  - Restricted origins (app.zebra.associates only)
  - Credentials handling secure
  - Preflight request validation
  - Security headers implementation

Authentication Security:
  - JWT token validation
  - Auth0 integration security
  - Session management security
  - Token expiration management

API Security:
  - Rate limiting implementation
  - Input validation and sanitization
  - SQL injection prevention
  - XSS protection headers

Data Security:
  - Database connection encryption (SSL)
  - Redis connection security (TLS)
  - Environment variable encryption
  - Audit logging for security events
```

---

## Step 6: Validation and Testing

### 6.1 Service Configuration Validation

#### Pre-Deployment Validation
```yaml
Service Configuration Validation:

Docker Configuration:
  - [ ] Dockerfile builds successfully
  - [ ] Multi-service architecture functional
  - [ ] Supervisord configuration valid
  - [ ] Health check endpoints responsive

Render Service Configuration:
  - [ ] Service created with correct settings
  - [ ] Resource allocation appropriate
  - [ ] Environment variables configured
  - [ ] GitHub integration functional

Deployment Configuration:
  - [ ] Auto-deployment triggers working
  - [ ] Build process completing successfully
  - [ ] Health checks passing
  - [ ] Service startup within timeout limits

Network Configuration:
  - [ ] Port 80 accessible externally
  - [ ] Port 8000 accessible for health checks
  - [ ] CORS headers delivering correctly
  - [ ] SSL termination working properly
```

#### Post-Deployment Validation
```yaml
Post-Deployment Validation:

Service Health:
  - [ ] All services (Caddy + FastAPI) running
  - [ ] Health check endpoint returning 200
  - [ ] Ready check endpoint functional
  - [ ] Service logs showing normal operation

Performance Validation:
  - [ ] Response times <2 seconds
  - [ ] Memory utilization within limits
  - [ ] CPU utilization within targets
  - [ ] No service restarts or failures

Integration Validation:
  - [ ] Database connectivity working
  - [ ] Redis connectivity functional
  - [ ] Auth0 authentication flows working
  - [ ] CORS headers enabling client access

Security Validation:
  - [ ] Services running as non-root user
  - [ ] CORS origins properly restricted
  - [ ] Security headers implemented
  - [ ] No security vulnerabilities exposed
```

---

## Success Criteria and Completion

### 6.1 Render Web Service Configuration Complete

```yaml
Service Configuration Success Criteria:

Infrastructure Complete:
  - [ ] Production web service configured and operational
  - [ ] Staging web service configured for testing
  - [ ] Multi-service Docker architecture functional
  - [ ] Resource allocation optimized for performance

Deployment Automation:
  - [ ] GitHub integration configured and tested
  - [ ] Auto-deployment working for main branch
  - [ ] Manual deployment capability validated
  - [ ] Rollback procedures tested and functional

Performance and Monitoring:
  - [ ] Health checks configured and passing
  - [ ] Performance monitoring operational
  - [ ] Alerting configured for critical metrics
  - [ ] Auto-scaling configured and tested

Security and Compliance:
  - [ ] Container security best practices implemented
  - [ ] Network security configured properly
  - [ ] Application security validated
  - [ ] Compliance requirements met
```

### 6.2 Ready for Epic 3 Application Deployment

```yaml
Epic 3 Prerequisites Met:

Service Foundation:
  - [ ] Web service infrastructure provides reliable deployment platform
  - [ ] Multi-service architecture enables Caddy + FastAPI deployment
  - [ ] Resource allocation supports enterprise performance requirements
  - [ ] Monitoring enables production-grade operational visibility

Deployment Readiness:
  - [ ] Automated deployment pipeline operational
  - [ ] Health check validation ensures deployment success
  - [ ] Rollback capability provides deployment safety net
  - [ ] Performance monitoring enables optimization and scaling

Integration Readiness:
  - [ ] Service configuration supports database and Redis integration
  - [ ] CORS configuration enables authentication and API access
  - [ ] Security configuration protects enterprise client data
  - [ ] Monitoring configuration enables operational excellence
```

This comprehensive Render web service configuration guide ensures successful multi-service Docker deployment supporting the Railway to Render migration while maintaining enterprise-grade performance and security for the £925K Odeon opportunity.