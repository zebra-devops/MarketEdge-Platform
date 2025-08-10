# Railway Manual Setup Instructions

## Project Information
- **Project Name**: platform-wrapper-backend
- **Project URL**: https://railway.com/project/e6f51f81-f649-4529-90fe-d491a578591d
- **Environment**: production

## Required Services

### 1. PostgreSQL Database
- Service Type: Database → PostgreSQL
- Will automatically provide: `DATABASE_URL`

### 2. Redis Cache
- Service Type: Database → Redis
- Will automatically provide: `REDIS_URL`

### 3. FastAPI Application
- Service Type: GitHub Repo
- Repository: Your current repository
- Build Command: Uses Dockerfile
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Environment Variables to Set

### Application Configuration
```
PROJECT_NAME=Platform Wrapper
PROJECT_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
PORT=8000
```

### JWT Configuration
```
JWT_SECRET_KEY=<generate-32-char-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Rate Limiting Configuration
```
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10
RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE=1000
RATE_LIMIT_ADMIN_REQUESTS_PER_MINUTE=5000
```

### Database Configuration
```
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_PRE_PING=true
```

### Redis Configuration
```
REDIS_CONNECTION_POOL_SIZE=50
REDIS_HEALTH_CHECK_INTERVAL=30
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_SOCKET_TIMEOUT=2
```

### Multi-Tenant Configuration
```
TENANT_ISOLATION_ENABLED=true
TENANT_DB_SCHEMA_ISOLATION=true
MAX_TENANTS_PER_REQUEST=10
```

## After Services Are Added

### 1. Configure Rate Limiting Storage
Once Redis is added and `REDIS_URL` is available, add:
```
RATE_LIMIT_STORAGE_URL=${REDIS_URL}/1
```

### 2. Run Database Migrations
In the Railway service shell or during deployment:
```bash
alembic upgrade head
```

### 3. Configure Auth0 (Required for Authentication)
```
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your_auth0_client_id
AUTH0_CLIENT_SECRET=your_auth0_client_secret
AUTH0_CALLBACK_URL=https://your-app-domain.railway.app/callback
```

### 4. Configure CORS Origins
```
CORS_ORIGINS=https://your-frontend-domain.railway.app,https://your-custom-domain.com
```

### 5. Optional: Supabase Data Layer
```
DATA_LAYER_SUPABASE__URL=https://your-project.supabase.co
DATA_LAYER_SUPABASE__KEY=your_supabase_anon_key
```

## Deployment Verification

After setup, verify:
1. Health endpoint: `https://your-app.railway.app/health`
2. API documentation: `https://your-app.railway.app/api/v1/docs`
3. Database connectivity via health checks
4. Redis connectivity for rate limiting

## Monitoring

- View logs: Railway dashboard → Your service → Logs
- Monitor metrics: Railway dashboard → Your service → Metrics
- Check deployments: Railway dashboard → Your service → Deployments

## Security Notes

- JWT_SECRET_KEY must be at least 32 characters long
- All secrets should be set as environment variables, never in code
- Enable HTTPS only in production (Railway handles this automatically)
- Regularly rotate JWT secrets and API keys

## Next Steps After Manual Setup

1. Test all API endpoints
2. Verify multi-tenant functionality
3. Run integration tests
4. Configure custom domain if needed
5. Set up monitoring alerts