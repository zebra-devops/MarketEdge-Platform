# Railway Backend Deployment Guide

## Multi-Tenant FastAPI Platform Production Deployment

### Overview

This guide covers the complete deployment of the multi-tenant business intelligence platform FastAPI backend to Railway with production-ready configuration supporting 10-30 clients with a $25-75/month infrastructure budget.

### Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Railway CLI**: Installed and authenticated
3. **Git Repository**: Backend code committed to git
4. **Auth0 Account**: For authentication configuration
5. **Domain** (optional): For custom domain setup

### Phase 1: Initial Railway Setup

#### 1.1 Railway CLI Authentication

```bash
# Install Railway CLI (if not installed)
curl -fsSL https://railway.app/install.sh | sh

# Add to PATH
export PATH="$HOME/.railway/bin:$PATH"

# Login to Railway
railway login
```

#### 1.2 Initialize Railway Project

```bash
# Navigate to backend directory
cd /Users/matt/sites/marketedge/platform-wrapper/backend

# Initialize Railway project
railway init

# Link to existing project (if creating new one)
railway link

# Or create new project
railway create platform-wrapper-backend
```

### Phase 2: Database and Cache Provisioning

#### 2.1 Provision PostgreSQL Database

```bash
# Add PostgreSQL service
railway add postgresql

# Get database connection details
railway variables
```

#### 2.2 Provision Redis Cache

```bash
# Add Redis service
railway add redis

# Verify services
railway status
```

#### 2.3 Configure Database Connection

The PostgreSQL service automatically provides these environment variables:
- `DATABASE_URL`: Full connection string
- `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`: Individual components

### Phase 3: Environment Variables Configuration

#### 3.1 Set Production Environment Variables

```bash
# Application Configuration
railway variables set PROJECT_NAME="Platform Wrapper"
railway variables set PROJECT_VERSION="1.0.0"
railway variables set ENVIRONMENT="production"
railway variables set DEBUG="false"
railway variables set LOG_LEVEL="INFO"

# JWT Configuration (generate secure keys)
railway variables set JWT_SECRET_KEY="$(openssl rand -base64 32)"
railway variables set JWT_ALGORITHM="HS256"
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES="30"
railway variables set REFRESH_TOKEN_EXPIRE_DAYS="7"

# Auth0 Configuration
railway variables set AUTH0_DOMAIN="your-tenant.auth0.com"
railway variables set AUTH0_CLIENT_ID="your_auth0_client_id"
railway variables set AUTH0_CLIENT_SECRET="your_auth0_client_secret"
railway variables set AUTH0_CALLBACK_URL="https://your-frontend.railway.app/callback"

# CORS Configuration
railway variables set CORS_ORIGINS="https://your-frontend.railway.app"

# Rate Limiting Configuration
railway variables set RATE_LIMIT_ENABLED="true"
railway variables set RATE_LIMIT_REQUESTS_PER_MINUTE="60"
railway variables set RATE_LIMIT_BURST_SIZE="10"
railway variables set RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE="1000"
railway variables set RATE_LIMIT_ADMIN_REQUESTS_PER_MINUTE="5000"

# Redis Configuration (use Railway Redis URL)
railway variables set REDIS_CONNECTION_POOL_SIZE="50"
railway variables set REDIS_HEALTH_CHECK_INTERVAL="30"
railway variables set REDIS_SOCKET_CONNECT_TIMEOUT="5"
railway variables set REDIS_SOCKET_TIMEOUT="2"

# Supabase Configuration
railway variables set DATA_LAYER_SUPABASE__URL="https://your-project.supabase.co"
railway variables set DATA_LAYER_SUPABASE__KEY="your_supabase_anon_key"
```

#### 3.2 Redis URL Configuration

```bash
# Set Redis URL for rate limiting storage (using Redis DB 1)
# Get the Redis URL first
REDIS_URL=$(railway variables get REDIS_URL)
RATE_LIMIT_STORAGE_URL="${REDIS_URL}/1"
railway variables set RATE_LIMIT_STORAGE_URL="$RATE_LIMIT_STORAGE_URL"
```

### Phase 4: Database Migration and Setup

#### 4.1 Run Database Migrations

```bash
# Deploy the application first to get a running instance
railway up -d

# Run migrations using Railway shell
railway shell

# Inside the shell, run migrations
alembic upgrade head

# Exit shell
exit
```

#### 4.2 Apply Row Level Security Policies

The migrations include RLS policies, but verify they're applied:

```bash
# Connect to database using Railway
railway connect postgresql

# Verify RLS is enabled
\d+ organisations
\d+ users
\d+ audit_logs

# Check RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE schemaname = 'public';

# Exit database connection
\q
```

### Phase 5: Production Deployment

#### 5.1 Deploy Application

```bash
# Deploy from current directory
railway up

# Or deploy with specific configuration
railway up --detach

# Monitor deployment
railway logs
```

#### 5.2 Configure Custom Domain (Optional)

```bash
# Add custom domain
railway domain add your-api-domain.com

# Configure DNS (add CNAME record pointing to Railway)
# your-api-domain.com -> your-service-name.up.railway.app
```

#### 5.3 SSL Configuration

Railway automatically provides SSL certificates for custom domains. No additional configuration needed.

### Phase 6: Validation and Testing

#### 6.1 Health Check Validation

```bash
# Get service URL
SERVICE_URL=$(railway url)

# Test health endpoint
curl $SERVICE_URL/health

# Expected response:
# {"status": "healthy", "version": "1.0.0"}
```

#### 6.2 API Documentation Access

Access the automatic API documentation:
- Swagger UI: `https://your-service.railway.app/api/v1/docs`
- ReDoc: `https://your-service.railway.app/api/v1/redoc`

#### 6.3 Authentication Testing

```bash
# Test Auth0 integration
curl -X POST $SERVICE_URL/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TEST_JWT_TOKEN"
```

#### 6.4 Rate Limiting Testing

```bash
# Test rate limiting (should get rate limited after configured threshold)
for i in {1..100}; do
  curl -X GET $SERVICE_URL/api/v1/organisations \
    -H "Authorization: Bearer YOUR_TEST_JWT_TOKEN"
  echo "Request $i"
done
```

#### 6.5 Multi-Tenant Testing

```bash
# Test tenant isolation with different JWT tokens containing tenant_id claims
curl -X GET $SERVICE_URL/api/v1/organisations \
  -H "Authorization: Bearer TENANT_A_JWT_TOKEN"

curl -X GET $SERVICE_URL/api/v1/organisations \
  -H "Authorization: Bearer TENANT_B_JWT_TOKEN"
```

### Phase 7: Monitoring and Alerting Setup

#### 7.1 Railway Monitoring

Railway provides built-in monitoring for:
- CPU and Memory usage
- Request latency and throughput
- Error rates
- Health check status

Access monitoring dashboard at: https://railway.app/project/your-project

#### 7.2 Application Logging

```bash
# View application logs
railway logs

# Follow logs in real-time
railway logs --follow

# Filter logs by service
railway logs --service backend
```

#### 7.3 Database Monitoring

```bash
# Check database performance
railway connect postgresql

# Monitor active connections
SELECT count(*) FROM pg_stat_activity;

# Check database size
SELECT pg_size_pretty(pg_database_size('railway'));

# Monitor slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### Phase 8: Production Optimizations

#### 8.1 Database Connection Pooling

The application uses SQLAlchemy's connection pooling. Monitor and adjust if needed:

```python
# In app/core/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,  # Adjust based on concurrent users
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### 8.2 Redis Configuration Optimization

```bash
# Set Redis-specific optimizations
railway variables set REDIS_MAXMEMORY_POLICY="allkeys-lru"
railway variables set REDIS_TIMEOUT="300"
```

#### 8.3 Auto-scaling Configuration

Railway automatically scales based on traffic. Configure scaling settings:

```bash
# Check current scaling settings
railway settings

# Configure auto-scaling (via dashboard)
# - Min instances: 1
# - Max instances: 5
# - Scale up threshold: 80% CPU
# - Scale down threshold: 30% CPU
```

### Phase 9: Security Hardening

#### 9.1 Environment Security

```bash
# Rotate JWT secret key periodically
railway variables set JWT_SECRET_KEY="$(openssl rand -base64 32)"

# Update CORS origins to specific domains only
railway variables set CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Enable Redis SSL
railway variables set REDIS_SSL_ENABLED="true"
```

#### 9.2 Database Security

```bash
# Connect to database and verify RLS
railway connect postgresql

# Ensure RLS is enabled on all tables
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' AND rowsecurity = true;

# Verify no public access
\dp organisations
\dp users
\dp audit_logs
```

### Phase 10: Backup and Disaster Recovery

#### 10.1 Database Backups

Railway automatically backs up PostgreSQL databases. Configure retention:

1. Access Railway dashboard
2. Go to PostgreSQL service
3. Configure backup retention (7-30 days recommended)
4. Set up automated backups

#### 10.2 Manual Backup

```bash
# Create manual backup
railway connect postgresql --command "pg_dump railway > backup_$(date +%Y%m%d_%H%M%S).sql"

# Restore from backup
railway connect postgresql --command "psql railway < backup_file.sql"
```

### Performance and Cost Optimization

#### Expected Performance Metrics

- **Response Time**: < 200ms for most API calls
- **Throughput**: 1000+ requests/minute per instance
- **Memory Usage**: 256-512MB per instance
- **CPU Usage**: < 50% under normal load

#### Cost Optimization Strategies

1. **Resource Scaling**: Start with 1 instance, scale as needed
2. **Database Optimization**: Regular query optimization and indexing
3. **Redis Optimization**: Efficient caching and expiration policies
4. **Connection Pooling**: Minimize database connections

#### Target Cost Breakdown (Monthly)

- **Application Instance**: $5-15
- **PostgreSQL Database**: $5-20
- **Redis Cache**: $5-10
- **Bandwidth**: $5-15
- **Total**: $20-60/month

### Troubleshooting Guide

#### Common Issues and Solutions

1. **Database Connection Errors**
   ```bash
   # Check DATABASE_URL format
   railway variables get DATABASE_URL
   
   # Test connection
   railway connect postgresql
   ```

2. **Redis Connection Issues**
   ```bash
   # Verify Redis URL
   railway variables get REDIS_URL
   
   # Test Redis connection
   railway connect redis
   ```

3. **Migration Failures**
   ```bash
   # Check migration status
   railway shell
   alembic current
   alembic history
   
   # Force migration to specific version
   alembic stamp head
   ```

4. **Rate Limiting Not Working**
   ```bash
   # Check Redis connection for rate limiting
   railway variables get RATE_LIMIT_STORAGE_URL
   
   # Verify rate limiting is enabled
   railway variables get RATE_LIMIT_ENABLED
   ```

5. **Authentication Issues**
   ```bash
   # Verify Auth0 configuration
   railway variables get AUTH0_DOMAIN
   railway variables get AUTH0_CLIENT_ID
   
   # Check JWT secret
   railway variables get JWT_SECRET_KEY
   ```

### Maintenance Procedures

#### Regular Maintenance Tasks

1. **Weekly**:
   - Review application logs for errors
   - Monitor resource usage
   - Check database performance

2. **Monthly**:
   - Update dependencies
   - Rotate JWT secrets
   - Review and optimize database queries
   - Backup verification

3. **Quarterly**:
   - Security audit
   - Performance optimization
   - Cost analysis and optimization

### Support and Documentation

#### Railway Resources

- **Documentation**: https://docs.railway.app/
- **Community**: https://railway.app/discord
- **Status Page**: https://status.railway.app/

#### Application Resources

- **Health Check**: `GET /health`
- **API Docs**: `/api/v1/docs`
- **Application Logs**: `railway logs`

### Next Steps

1. **Frontend Deployment**: Deploy Next.js frontend to Railway or Vercel
2. **CI/CD Pipeline**: Set up GitHub Actions for automated deployments
3. **Monitoring**: Implement application-level monitoring and alerting
4. **Load Testing**: Conduct load testing to validate performance
5. **Security Audit**: Regular security assessments and penetration testing

This deployment guide ensures a production-ready, secure, and scalable FastAPI backend deployment on Railway that can support 10-30 clients with proper multi-tenant isolation, rate limiting, and monitoring capabilities.