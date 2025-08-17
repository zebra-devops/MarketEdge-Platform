# CRITICAL DEPLOYMENT COMMANDS - Epic 2 Migration

## IMMEDIATE ACTIONS REQUIRED

### 1. Deploy to Render (CRITICAL)
**Repository**: `zebra-devops/MarketEdge-Platform`

**Manual Deployment Steps**:
1. Go to https://render.com
2. Connect GitHub repository: `zebra-devops/MarketEdge-Platform`
3. Create new Web Service
4. Use blueprint from `render.yaml` OR manual configuration:
   - **Runtime**: Docker
   - **Dockerfile Path**: `./Dockerfile`
   - **Build Command**: [AUTOMATIC]
   - **Start Command**: [FROM DOCKERFILE]

### 2. Verify Deployment Success
```bash
# Run validation script immediately after deployment
cd /Users/matt/Sites/MarketEdge
./render-deployment-validation.sh
```

### 3. Update Frontend Environment
```bash
# Update Vercel environment variable
NEXT_PUBLIC_API_URL=https://marketedge-platform.onrender.com
```

## CRITICAL FILES READY FOR DEPLOYMENT ✅

- `Dockerfile` - ✅ Fixed and tested locally
- `render.yaml` - ✅ Updated with AUTH0_CLIENT_SECRET
- `platform-wrapper/backend/` - ✅ All files verified

## EXPECTED DEPLOYMENT TIME
- **Docker Build**: ~3-5 minutes
- **Service Start**: ~1-2 minutes  
- **Total**: ~5-7 minutes to platform restoration

## VALIDATION ENDPOINTS
- Health: `https://marketedge-platform.onrender.com/health`
- Docs: `https://marketedge-platform.onrender.com/docs`
- CORS Test: Origin validation for Vercel frontend

**DEPLOY IMMEDIATELY TO RESTORE PLATFORM**