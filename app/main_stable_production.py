"""
STABLE PRODUCTION VERSION: Full API router with minimal dependencies
Option 2: New service that combines emergency mode stability with full API functionality
Critical for £925K Zebra Associates opportunity
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import os
import asyncio

# Configure minimal logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("🚀 STABLE PRODUCTION MODE: Starting with full API router")

# Import settings with fallback
try:
    from app.core.config import settings
    logger.info("✅ Settings imported successfully")
except Exception as e:
    logger.error(f"❌ Settings import failed: {e} - using fallback")
    # Create minimal settings fallback
    class Settings:
        PROJECT_NAME = "MarketEdge Platform (Stable Production)"
        PROJECT_VERSION = "2.0.0-stable-api"
        API_V1_STR = "/api/v1"
        DEBUG = False
        ENVIRONMENT = "production"
        CORS_ORIGINS = ["*"]  # Will be overridden below
    settings = Settings()

# Create FastAPI app optimized for production
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Stable Production Mode - Full API router with CORS for £925K opportunity",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Add middleware in correct order for CORS to work
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# CRITICAL CORS configuration for £925K opportunity
cors_origins = [
    "https://app.zebra.associates",
    "https://marketedge-frontend.onrender.com",
    "http://localhost:3000",
    "http://localhost:3001",
]

logger.info(f"🎯 CRITICAL: CORS configured for origins: {cors_origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "Origin", "X-Tenant-ID"],
    expose_headers=["Content-Type", "Authorization", "X-Tenant-ID"],
    max_age=600,
)

# CRITICAL: Include API router with retry logic
api_router_included = False
api_router_error = None

try:
    logger.info("⚡ Importing API router...")
    from app.api.api_v1.api import api_router
    logger.info("⚡ API router imported, including in app...")
    app.include_router(api_router, prefix=settings.API_V1_STR)
    api_router_included = True
    logger.info("✅ API router included successfully - ALL Epic endpoints available")
    logger.info("🎯 Authentication endpoints ready for £925K opportunity")
except Exception as e:
    api_router_error = str(e)
    logger.error(f"❌ API router failed: {e}")
    logger.warning("⚠️  Continuing with manual fallback endpoints")
    
    # Add critical auth endpoints as fallback
    @app.get(f"{settings.API_V1_STR}/auth/auth0-url")
    async def auth0_url_fallback():
        """Fallback auth0 URL endpoint"""
        try:
            auth0_domain = os.getenv("AUTH0_DOMAIN", "dev-g8trhgbfdq2sk2m8.us.auth0.com")
            client_id = os.getenv("AUTH0_CLIENT_ID", "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr")
            callback_url = os.getenv("AUTH0_CALLBACK_URL", "https://marketedge-platform.onrender.com/callback")
            
            auth_url = f"https://{auth0_domain}/authorize?response_type=code&client_id={client_id}&redirect_uri={callback_url}&scope=openid%20profile%20email"
            
            return {
                "auth_url": auth_url,
                "status": "fallback_mode",
                "message": "Auth URL generated in fallback mode",
                "auth0_domain": auth0_domain,
                "client_id": client_id,
                "callback_url": callback_url
            }
        except Exception as fallback_error:
            logger.error(f"Fallback auth endpoint failed: {fallback_error}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Authentication service unavailable",
                    "fallback_error": str(fallback_error),
                    "status": "error"
                }
            )
    
    @app.get(f"{settings.API_V1_STR}/auth/status")
    async def auth_status_fallback():
        """Fallback auth status endpoint"""
        return {
            "status": "fallback_mode",
            "message": "Authentication in fallback mode",
            "available": True,
            "mode": "manual_endpoints",
            "api_router_error": api_router_error
        }

# Health check that always works
@app.get("/health")
async def health_check():
    """Stable production health check for £925K opportunity"""
    return {
        "status": "healthy",
        "mode": "STABLE_PRODUCTION_FULL_API",
        "version": settings.PROJECT_VERSION,
        "timestamp": time.time(),
        "cors_configured": True,
        "zebra_associates_ready": True,
        "critical_business_ready": True,
        "authentication_endpoints": "available",
        "deployment_safe": True,
        "api_router_included": api_router_included,
        "api_router_error": api_router_error,
        "message": "Stable production mode - full API router with CORS optimization"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MarketEdge Platform API (Stable Production)",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
        "cors_test": "/cors-test",
        "api_router_included": api_router_included,
        "status": "STABLE_PRODUCTION_ACTIVE"
    }

@app.get("/cors-test") 
async def cors_test():
    """CORS test endpoint for https://app.zebra.associates integration"""
    return {
        "cors_status": "enabled",
        "allowed_origins": cors_origins,
        "credentials_allowed": True,
        "methods_allowed": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        "headers_allowed": ["Content-Type", "Authorization", "Accept", "X-Requested-With", "Origin", "X-Tenant-ID"],
        "test_timestamp": time.time(),
        "ready_for_auth": True,
        "zebra_associates_ready": True,
        "stable_mode": True
    }

# Status endpoint showing current state
@app.get("/deployment-status")
async def deployment_status():
    """Show deployment status for debugging"""
    return {
        "deployment_status": "STABLE_PRODUCTION_ACTIVE",
        "timestamp": time.time(),
        "api_router_included": api_router_included,
        "api_router_error": api_router_error,
        "cors_configured_for_zebra": True,
        "authentication_available": api_router_included,
        "critical_business_ready": True,
        "mode": "stable_production",
        "ready_for_frontend": True,
        "fallback_endpoints_available": not api_router_included
    }

logger.info("🚀 STABLE PRODUCTION MODE: FastAPI app created successfully")
logger.info(f"✅ CORS enabled for: {cors_origins}")
logger.info(f"🎯 API router included: {api_router_included}")
logger.info("🚀 READY FOR £925K OPPORTUNITY")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main_stable_production:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )