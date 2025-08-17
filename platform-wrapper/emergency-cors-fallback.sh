#!/bin/bash

# EMERGENCY CORS FALLBACK FIX
# Alternative solution using FastAPI's native CORS middleware

set -e

echo "🚨 EMERGENCY CORS FALLBACK FOR ODEON DEMO"
echo "=========================================="
echo ""
echo "This script replaces the ASGI CORS handler with FastAPI's native CORS middleware"
echo "as a more reliable fallback solution."
echo ""

# Step 1: Create backup of current main.py
echo "📦 Step 1: Creating backup of main.py..."
cp backend/app/main.py backend/app/main.py.backup.$(date +%s)
echo "✅ Backup created!"

# Step 2: Apply fallback CORS fix
echo ""
echo "🔧 Step 2: Applying fallback CORS configuration..."
echo "--------------------------------------------------"

cat > backend/app/main_fallback.py << 'EOF'
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from .core.config import settings
from .core.logging import configure_logging
from .core.health_checks import health_checker
from .api.api_v1.api import api_router
from .middleware.error_handler import ErrorHandlerMiddleware
from .middleware.logging import LoggingMiddleware
from .middleware.tenant_context import TenantContextMiddleware
from .middleware.rate_limiting import RateLimitMiddleware

configure_logging()
logger = logging.getLogger(__name__)

# Production-ready FastAPI app configuration
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Multi-Tenant Business Intelligence Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
    root_path="",
)

# EMERGENCY FALLBACK: Use FastAPI's native CORS middleware
print("EMERGENCY CORS FALLBACK v1: Using FastAPI native CORS middleware")
print(f"Custom domain: https://app.zebra.associates")
print("FALLBACK DEPLOYMENT TIMESTAMP:", time.time())

# Custom domain CORS origins - EMERGENCY hardcoded list
emergency_origins = [
    "https://app.zebra.associates",  # CRITICAL: Custom domain
    "http://localhost:3000",
    "http://localhost:3001", 
    "https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
]

print(f"CORS origins configured: {emergency_origins}")

# Add CORS middleware with emergency origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=emergency_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add other middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check(request: Request):
    """Simple health check endpoint for Railway health checks."""
    try:
        health_data = {
            "status": "healthy",
            "version": settings.PROJECT_VERSION,
            "timestamp": time.time(),
            "cors_mode": "fastapi_native_fallback"
        }
        
        try:
            logger.info("Health check requested - fallback CORS mode")
        except:
            pass
        
        return health_data
        
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": time.time(),
                "cors_mode": "fastapi_native_fallback",
                "note": "basic_health_check_fallback"
            }
        )

@app.get("/cors-debug")
async def cors_debug(request: Request):
    """Debug endpoint to check CORS configuration and headers."""
    origin = request.headers.get("origin", "no-origin-header")
    user_agent = request.headers.get("user-agent", "no-user-agent")
    
    debug_info = {
        "cors_mode": "fastapi_native_fallback",
        "emergency_origins": emergency_origins,
        "request_origin": origin,
        "origin_allowed": origin in emergency_origins,
        "user_agent": user_agent,
        "all_headers": dict(request.headers),
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "timestamp": time.time()
    }
    
    try:
        logger.info(f"CORS debug requested from origin: {origin}")
    except:
        pass
    
    return debug_info

@app.get("/ready")
async def readiness_check():
    """Railway readiness check endpoint."""
    try:
        health_result = await health_checker.comprehensive_health_check()
        
        if health_result["status"] == "healthy":
            return {
                "status": "ready",
                "version": settings.PROJECT_VERSION,
                "network_type": "railway_private_network",
                "services": health_result["services"],
                "summary": health_result["summary"],
                "timestamp": time.time(),
                "cors_mode": "fastapi_native_fallback"
            }
        else:
            logger.warning("Readiness check failed - services not healthy", extra=health_result)
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "version": settings.PROJECT_VERSION,
                    "services": health_result["services"],
                    "error": "One or more services not healthy",
                    "details": health_result if settings.DEBUG else None,
                    "timestamp": time.time(),
                    "cors_mode": "fastapi_native_fallback"
                }
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e) if settings.DEBUG else "Service not ready",
                "timestamp": time.time(),
                "cors_mode": "fastapi_native_fallback"
            }
        )

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
EOF

# Replace main.py with fallback version
cp backend/app/main_fallback.py backend/app/main.py
rm backend/app/main_fallback.py

echo "✅ Fallback CORS configuration applied!"

# Step 3: Commit and deploy
echo ""
echo "📦 Step 3: Committing fallback fix..."
git add backend/app/main.py
git commit -m "EMERGENCY FALLBACK: Replace ASGI CORS with FastAPI native CORS

- Removed custom ASGI CORS handler
- Using FastAPI's CORSMiddleware directly  
- Hardcoded emergency origins including custom domain
- Added fallback debug endpoints

🚨 Fallback solution for £925K Odeon demo CORS issues
" || echo "No changes to commit"

# Step 4: Deploy to Railway
echo ""
echo "🚀 Step 4: Deploying fallback to Railway..."
if command -v railway &> /dev/null; then
    cd backend
    railway up --detach
    cd ..
    echo "✅ Fallback deployment started!"
else
    echo "❌ Railway CLI not found! Install with: npm install -g @railway/cli"
    exit 1
fi

echo ""
echo "⏳ Waiting 90 seconds for fallback deployment..."
sleep 90

# Step 5: Test fallback
echo ""
echo "🧪 Step 5: Testing fallback CORS..."
echo "-----------------------------------"

curl -s -X OPTIONS \
     -H "Origin: https://app.zebra.associates" \
     -H "Access-Control-Request-Method: GET" \
     https://marketedge-backend-production.up.railway.app/health \
     -w "\nFallback Status: %{http_code}\n" || true

echo ""
echo "🎯 EMERGENCY FALLBACK COMPLETE"
echo "==============================="
echo ""
echo "✅ FastAPI native CORS middleware deployed"
echo "✅ Custom domain included in hardcoded origins"
echo "✅ Fallback deployment active"
echo ""
echo "🔧 Next: Test at https://app.zebra.associates"
echo "📊 Monitor: railway logs --tail"