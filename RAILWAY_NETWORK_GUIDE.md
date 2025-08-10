# Railway Network Configuration Guide

## Railway Networking Overview

**Key Insight:** Railway uses **automatic private networking** by default. There's no manual "Private vs Public" network configuration needed.

## How Railway Networking Works

### 1. Automatic Private Network
- All services within a Railway project communicate via **private network by default**
- No manual configuration required for service-to-service communication
- Internal traffic is automatically routed through private network

### 2. Service Discovery
Railway provides automatic service discovery through:
- **Environment Variables**: Railway automatically injects connection strings
- **Internal Hostnames**: Services can reference each other by service name
- **DNS Resolution**: Automatic internal DNS for service communication

### 3. Network Access Types

#### Private Network (Default)
- **FastAPI ↔ PostgreSQL**: Automatic private connection
- **FastAPI ↔ Redis**: Automatic private connection
- **Service-to-Service**: All internal communication is private

#### Public Network (Explicit)
- **Web Traffic**: Only services with PORT environment variable exposed
- **Public APIs**: Your FastAPI service exposed on Railway domain
- **External Access**: Only explicitly configured endpoints

## Current Configuration Status

### Your Railway Services Setup
Based on your configuration, you should have:

1. **FastAPI Service** (Public + Private)
   - Public: Exposed via PORT=8000 for web traffic
   - Private: Internal communication with database and Redis

2. **PostgreSQL Service** (Private Only)
   - Private: Only accessible from within Railway project
   - Connection via DATABASE_URL environment variable

3. **Redis Service** (Private Only)
   - Private: Only accessible from within Railway project
   - Connection via REDIS_URL environment variable

## Environment Variables and Networking

### Automatic Variables (Railway Provides)
```bash
# Database connection (private network)
DATABASE_URL=postgresql://postgres:password@postgres.railway.internal:5432/railway

# Redis connection (private network)  
REDIS_URL=redis://default:password@redis.railway.internal:6379

# Rate limiting Redis (private network, different DB)
RATE_LIMIT_STORAGE_URL=redis://default:password@redis.railway.internal:6379/1
```

### Manual Variables (You Configure)
```bash
# Application settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# JWT and Auth0 secrets
JWT_SECRET_KEY=your_secret_key
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret

# CORS for public access
CORS_ORIGINS=https://your-frontend.railway.app
```

## Verification Steps

### 1. Check Service Connectivity
After deployment, verify private network connectivity:

```python
# In your FastAPI application
import asyncpg
import redis

async def test_database_connection():
    """Test private network database connection"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def test_redis_connection():
    """Test private network Redis connection"""
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False
```

### 2. Health Check Implementation
Your railway.toml already includes:

```toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
```

Implement the health endpoint to test all connections:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint that tests all service connections"""
    db_status = await test_database_connection()
    redis_status = test_redis_connection()
    
    return {
        "status": "healthy" if db_status and redis_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "redis": "connected" if redis_status else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Network Security Features

### Railway's Built-in Security
1. **Private Network Isolation**: Services only accessible within project
2. **Encrypted Communication**: All internal traffic encrypted
3. **No Public Database Access**: Database not exposed to internet
4. **Environment Variable Security**: Secrets encrypted at rest

### Additional Security Recommendations
1. **Enable Redis Password**: Use REDIS_PASSWORD environment variable
2. **Enable Redis SSL**: Set REDIS_SSL_ENABLED=true for production
3. **Rotate Secrets Regularly**: Update JWT_SECRET_KEY and Auth0 secrets
4. **Restrict CORS**: Only allow necessary frontend domains

## Next Steps

1. **Authenticate Railway CLI**: `railway login`
2. **Link to Project**: `railway link` or `railway init`
3. **Add Services**: PostgreSQL and Redis if not already added
4. **Set Environment Variables**: Configure all required variables
5. **Deploy Application**: `railway deploy`
6. **Test Connectivity**: Verify all services communicate properly

## Common Network Issues & Solutions

### Issue: Database Connection Refused
**Cause**: DATABASE_URL might be using public hostname
**Solution**: Ensure Railway provides internal connection string

### Issue: Redis Timeout
**Cause**: Redis SSL configuration mismatch
**Solution**: Check REDIS_SSL_ENABLED and certificate settings

### Issue: CORS Errors
**Cause**: Frontend domain not in CORS_ORIGINS
**Solution**: Add Railway frontend URL to CORS_ORIGINS

## Railway Dashboard Network Monitoring

In Railway dashboard, monitor:
1. **Service Logs**: Check connection attempts and errors
2. **Metrics**: Monitor response times and error rates
3. **Environment Variables**: Verify all variables are set correctly
4. **Service Status**: Ensure all services are healthy

---

**Bottom Line**: Railway handles private networking automatically. Your focus should be on configuring environment variables correctly and ensuring your application health checks pass.