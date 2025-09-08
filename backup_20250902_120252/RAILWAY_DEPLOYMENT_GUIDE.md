# Railway Deployment Guide - Updated CLI Syntax

## Overview
This guide covers the updated Railway deployment process for the multi-tenant FastAPI backend using the latest Railway CLI v4.6.1 syntax.

## Prerequisites

1. **Railway CLI v4.6.1+** - Modern command syntax
2. **Docker** - For containerized deployment
3. **Git** - Version control
4. **Authenticated Railway account** - Run `railway login` if needed

## Updated CLI Syntax Changes

### Key Updates from Legacy Syntax

| Legacy Command | Updated Command |
|----------------|-----------------|
| `railway add postgresql` | `railway add -d postgres` |
| `railway add redis` | `railway add -d redis` |
| `railway variables set KEY=VALUE` | `railway variables --set "KEY=VALUE"` |
| `railway url` | `railway domain` |
| `railway variables get KEY` | `railway variables \| grep KEY` |

## Deployment Process

### 1. Pre-Deployment Validation

```bash
# Run the test script to validate CLI setup
./test-railway-setup.sh
```

### 2. Deploy with Updated Script

```bash
# Make deployment script executable
chmod +x deploy-railway.sh

# Run deployment
./deploy-railway.sh
```

### 3. Service Configuration

The deployment script automatically configures:

#### PostgreSQL Database
- **Connection Pool Size**: 20 connections
- **Max Overflow**: 30 connections  
- **Pool Timeout**: 30 seconds
- **Pool Recycle**: 3600 seconds (1 hour)
- **Pre-ping**: Enabled for connection health

#### Redis Cache
- **Connection Pool Size**: 50 connections
- **Health Check Interval**: 30 seconds
- **Socket Timeout**: 2 seconds
- **Connect Timeout**: 5 seconds

#### Multi-Tenant Configuration
- **Tenant Isolation**: Enabled
- **DB Schema Isolation**: Enabled
- **Max Tenants per Request**: 10

#### Rate Limiting
- **General Rate Limit**: 60 requests/minute
- **Tenant Rate Limit**: 1000 requests/minute
- **Admin Rate Limit**: 5000 requests/minute
- **Burst Size**: 10 requests

## Enhanced Error Handling

The updated script includes:

1. **Service Validation** - Verifies PostgreSQL and Redis services
2. **Deployment Monitoring** - 5-minute deployment wait with status checks
3. **Database Connectivity** - Tests database connection before migrations
4. **Health Check Validation** - Validates service health endpoint
5. **Comprehensive Logging** - Detailed progress and error reporting

## Post-Deployment Configuration

After deployment, configure these environment variables:

### Auth0 Integration
```bash
railway variables --set "AUTH0_DOMAIN=your-tenant.auth0.com"
railway variables --set "AUTH0_CLIENT_ID=your_client_id"
railway variables --set "AUTH0_CLIENT_SECRET=your_client_secret"
```

### CORS Configuration
```bash
railway variables --set "CORS_ORIGINS=https://your-frontend.railway.app"
```

### Supabase Integration (if using)
```bash
railway variables --set "DATA_LAYER_SUPABASE__URL=https://your-project.supabase.co"
railway variables --set "DATA_LAYER_SUPABASE__KEY=your_anon_key"
```

## Monitoring and Troubleshooting

### View Deployment Status
```bash
railway status
```

### Check Logs
```bash
railway logs
```

### Open Railway Dashboard
```bash
railway open
```

### Connect to Database
```bash
railway connect postgres
```

### Connect to Redis
```bash
railway connect redis
```

## Service Health Validation

The deployment includes automatic health checks:

1. **Database Connection Test** - Validates PostgreSQL connectivity
2. **Redis Connection Test** - Validates Redis cache connectivity  
3. **API Health Endpoint** - Tests `/health` endpoint
4. **Service Status Monitoring** - Continuous deployment status checks

## Multi-Tenant Database Setup

### Automatic Configuration
The script configures optimal settings for multi-tenant operations:

- **Connection Pooling** - Efficient database connection management
- **Schema Isolation** - Tenant data separation
- **Performance Optimization** - Pre-ping and connection recycling
- **Rate Limiting Storage** - Redis-backed rate limiting per tenant

### Manual Database Initialization (if needed)
If migrations fail, manually initialize:

```bash
railway shell -- alembic upgrade head
```

## Performance Optimization

### Database Pool Settings
- **Pool Size**: 20 (optimal for typical workloads)
- **Max Overflow**: 30 (handles traffic spikes)
- **Pool Recycle**: 1 hour (prevents connection staleness)

### Redis Configuration  
- **Connection Pool**: 50 connections (high-performance caching)
- **Health Checks**: 30-second intervals
- **Timeout Settings**: Optimized for low latency

## Security Configuration

### Automatic Security Setup
- **JWT Secret**: Auto-generated 32-byte secure key
- **Environment Variable Security**: All secrets use Railway's secure storage
- **Rate Limiting**: Multi-tier protection (general, tenant, admin)

### Manual Security Hardening
After deployment, consider:

1. **Custom Domain with SSL** - `railway domain add your-domain.com`
2. **Environment-Specific Variables** - Use Railway environments for staging/production
3. **Database Encryption** - Enable at-rest encryption in Railway dashboard
4. **Access Control** - Configure team permissions in Railway dashboard

## Troubleshooting Common Issues

### Deployment Fails
```bash
# Check deployment logs
railway logs

# Check service status
railway status

# Redeploy if needed
railway up --detach
```

### Database Connection Issues
```bash
# Check if DATABASE_URL is set
railway variables | grep DATABASE_URL

# Test database connection
railway connect postgres
```

### Redis Connection Issues  
```bash
# Check if REDIS_URL is set
railway variables | grep REDIS_URL

# Test Redis connection
railway connect redis
```

### Service Not Accessible
```bash
# Check if domain is configured
railway domain

# Generate Railway domain if needed
railway domain
```

## Environment Management

### Development Environment
```bash
# Create development environment
railway environment create development

# Switch to development
railway environment development
```

### Production Environment  
```bash
# Switch to production
railway environment production
```

## Cost Optimization

### Resource Monitoring
- Monitor database connection usage in Railway dashboard
- Review Redis memory usage
- Check compute usage and scaling requirements

### Scaling Recommendations
- **Light Traffic**: Current configuration adequate
- **Medium Traffic**: Increase database pool size to 30
- **Heavy Traffic**: Consider horizontal scaling with multiple services

## Support and Documentation

### Railway Documentation
- [Railway Docs](https://docs.railway.app/)
- [Railway CLI Reference](https://docs.railway.app/develop/cli)

### Project-Specific Support
- Check deployment logs: `railway logs`
- Monitor service health: `railway status`  
- Access dashboard: `railway open`

## Version Compatibility

- **Railway CLI**: v4.6.1+
- **PostgreSQL**: Latest available via Railway
- **Redis**: Latest available via Railway
- **FastAPI**: Compatible with Python 3.8+

This deployment configuration ensures optimal performance, security, and scalability for the multi-tenant business intelligence platform.