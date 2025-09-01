"""
Emergency Main.py - Minimal version without secret_manager to get service running
This is a temporary bypass to identify if secret_manager is still the issue
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import os

# Configure minimal logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Emergency: Skip secret validation during startup
logger.info("EMERGENCY MODE: Starting without secret validation...")

# Try importing settings with fallback
try:
    from app.core.config import settings
    logger.info("✅ Settings imported successfully")
except Exception as e:
    logger.error(f"❌ Settings import failed: {e}")
    # Create minimal settings fallback
    class Settings:
        PROJECT_NAME = "MarketEdge Platform (Emergency Mode)"
        PROJECT_VERSION = "1.0.0-emergency"
        API_V1_STR = "/api/v1"
        DEBUG = True
        ENVIRONMENT = "emergency"
        CORS_ORIGINS = ["*"]
    settings = Settings()

# Create minimal FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Emergency deployment - bypassing complex startup",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Add minimal CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
async def emergency_health_check():
    """Emergency health check that always works"""
    return {
        "status": "healthy",
        "mode": "EMERGENCY_BYPASS",
        "version": settings.PROJECT_VERSION,
        "timestamp": time.time(),
        "message": "Service running in emergency mode - bypassing complex startup"
    }

@app.get("/")
async def root():
    """Root endpoint for testing"""
    return {
        "message": "MarketEdge Platform API (Emergency Mode)",
        "docs": "/docs",
        "health": "/health"
    }

# Try to include API router with fallback
try:
    from app.api.api_v1.api import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    logger.info("✅ API router included successfully")
except Exception as e:
    logger.error(f"❌ API router failed: {e}")
    logger.info("ℹ️  Running with minimal endpoints only")

logger.info("🚨 EMERGENCY MODE: FastAPI app created successfully")
logger.info(f"Available endpoints: /health, /, {settings.API_V1_STR}/docs")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "emergency_fix_main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )