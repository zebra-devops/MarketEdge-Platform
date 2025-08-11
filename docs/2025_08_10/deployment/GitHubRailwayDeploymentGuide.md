# GitHub to Railway Deployment Guide

## Current Situation
- **Project**: platform-wrapper-backend
- **PostgreSQL**: Empty database (needs migrations)
- **Backend Service**: Partially deployed (needs GitHub integration)
- **GitHub Repository**: https://github.com/zebra-devops/marketedge-backend

## Step-by-Step Deployment Process

### Phase 1: Identify Current Services

1. **Access Railway Dashboard**:
   ```bash
   # Open Railway dashboard
   open https://railway.app/dashboard
   ```

2. **Navigate to Project**: Go to `platform-wrapper-backend` project

3. **Document Current Services**: List all existing services (likely includes):
   - PostgreSQL service
   - Backend service (may be manually created)
   - Redis service (if exists)
   - Any redundant services

### Phase 2: Database Setup

1. **Check Database Connection**:
   ```bash
   # Test PostgreSQL connection
   psql "postgresql://postgres:XCxvJPLTYlcPgwOzrDgjfSNPiTLnYVTd@shinkansen.proxy.rlwy.net:48826/railway" -c "\\l"
   ```

2. **Run Database Migrations**:
   ```bash
   # Set environment variables locally for testing
   export DATABASE_URL="postgresql://postgres:XCxvJPLTYlcPgwOzrDgjfSNPiTLnYVTd@shinkansen.proxy.rlwy.net:48826/railway"
   
   # Install dependencies locally (if not done)
   pip install -r requirements.txt
   
   # Run migrations
   alembic upgrade head
   ```

3. **Verify Tables Created**:
   ```bash
   psql "$DATABASE_URL" -c "\\dt"
   ```

### Phase 3: GitHub Service Deployment

#### Option A: Create New Service from GitHub (Recommended)

1. **Via Railway Dashboard**:
   - Go to Railway Dashboard → New Service
   - Select "Deploy from GitHub"
   - Choose `zebra-devops/marketedge-backend` repository
   - Select `main` branch
   - Configure build settings

2. **Via CLI** (if repository access is fixed):
   ```bash
   railway add --repo https://github.com/zebra-devops/marketedge-backend
   ```

#### Option B: Connect Existing Service to GitHub

If you have an existing backend service:

1. **In Railway Dashboard**:
   - Go to existing backend service
   - Settings → Source → Connect Repository
   - Select `zebra-devops/marketedge-backend`
   - Configure branch and build settings

### Phase 4: Environment Variable Configuration

1. **Required Environment Variables**:
   ```bash
   # For the GitHub-deployed backend service
   railway variables --service YourBackendServiceName --set "DATABASE_URL=\${{Postgres.DATABASE_URL}}"
   railway variables --service YourBackendServiceName --set "REDIS_URL=\${{Redis.REDIS_URL}}"
   railway variables --service YourBackendServiceName --set "ENVIRONMENT=production"
   railway variables --service YourBackendServiceName --set "DEBUG=false"
   railway variables --service YourBackendServiceName --set "LOG_LEVEL=INFO"
   railway variables --service YourBackendServiceName --set "PORT=8000"
   
   # Add any additional required variables
   railway variables --service YourBackendServiceName --set "DATA_LAYER_ENABLED=false"
   ```

2. **Verify Variables Set**:
   ```bash
   railway variables --service YourBackendServiceName
   ```

### Phase 5: Build Configuration

Ensure your `railway.toml` is properly configured:

```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
startCommand = "./start.sh"

[env]
ENVIRONMENT = "production"
DEBUG = "false"
LOG_LEVEL = "INFO"
PORT = "8000"
```

### Phase 6: Deploy and Test

1. **Trigger Deployment**:
   - Push code changes to GitHub `main` branch
   - Or manually trigger deployment in Railway dashboard

2. **Monitor Deployment**:
   ```bash
   railway logs --service YourBackendServiceName
   ```

3. **Test Health Endpoint**:
   ```bash
   curl https://your-backend-service-url.railway.app/health
   ```

### Phase 7: Service Cleanup

After successful GitHub deployment:

1. **Identify Redundant Services**:
   - Any manually created backend services
   - Duplicate PostgreSQL services
   - Unused services

2. **Remove Redundant Services**:
   ```bash
   # In Railway Dashboard
   # Go to redundant service → Settings → Delete Service
   ```

## Final Architecture

### Recommended Service Structure:
```
Project: platform-wrapper-backend
├── PostgreSQL Service (with data)
├── Redis Service (for caching)
└── Backend Service (deployed from GitHub)
```

### Automatic Deployment Flow:
```
GitHub Commit → Railway Build → Docker Image → Deploy → Health Check
```

## Verification Commands

### Database Verification:
```bash
# Check tables exist
psql "$DATABASE_URL" -c "\\dt"

# Check migrations applied
psql "$DATABASE_URL" -c "SELECT * FROM alembic_version;"
```

### Service Health Verification:
```bash
# Check backend health
curl https://your-backend-url.railway.app/health

# Check backend logs
railway logs --service YourBackendServiceName
```

### Environment Verification:
```bash
# Check all variables set
railway variables --service YourBackendServiceName
```

## Troubleshooting

### Common Issues:

1. **Repository Access Error**:
   - Ensure GitHub repository is public or Railway has access
   - Check repository permissions in GitHub settings

2. **Build Failures**:
   - Check `Dockerfile` is in root directory
   - Verify all dependencies in `requirements.txt`
   - Check Railway build logs

3. **Database Connection Issues**:
   - Verify `DATABASE_URL` environment variable
   - Check PostgreSQL service is running
   - Ensure migrations are applied

4. **Health Check Failures**:
   - Verify `/health` endpoint is available
   - Check application startup logs
   - Ensure correct port configuration

## Next Steps

1. **Complete the deployment following phases 1-7**
2. **Set up monitoring and alerting**
3. **Configure custom domain (if needed)**
4. **Set up CI/CD pipeline for automated testing**

## Security Notes

- Never commit secrets to repository
- Use Railway environment variables for sensitive data
- Ensure PostgreSQL is only accessible via Railway internal network
- Regular security updates and dependency scanning