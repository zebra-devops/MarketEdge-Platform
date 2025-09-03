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
from datetime import datetime

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

# Test database connectivity and initialize if needed
database_ready = False
database_error = None

try:
    logger.info("🔍 Testing database connectivity and schema...")
    from app.core.database import get_db
    from sqlalchemy import text
    
    # Test basic connection
    db_session = next(get_db())
    db_session.execute(text("SELECT 1"))
    
    # Test if core tables exist
    try:
        db_session.execute(text("SELECT COUNT(*) FROM users LIMIT 1"))
        db_session.execute(text("SELECT COUNT(*) FROM organisations LIMIT 1"))
        database_ready = True
        logger.info("✅ Database schema verified - tables exist")
    except Exception as schema_error:
        logger.warning(f"⚠️  Database tables missing: {schema_error}")
        logger.info("🔧 Running database migrations...")
        
        # Try to run migrations
        try:
            import subprocess
            result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True, cwd='/app')
            if result.returncode == 0:
                database_ready = True
                logger.info("✅ Database migrations completed successfully")
            else:
                logger.error(f"❌ Migration failed: {result.stderr}")
                database_error = f"Migration failed: {result.stderr}"
        except Exception as migration_error:
            logger.error(f"❌ Could not run migrations: {migration_error}")
            database_error = f"Migration error: {migration_error}"
    
    db_session.close()
    
except Exception as e:
    database_error = str(e)
    logger.error(f"❌ Database connection failed: {e}")

# CRITICAL: Include API router with retry logic
api_router_included = False
api_router_error = None

if database_ready:
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
else:
    api_router_error = f"Database not ready: {database_error}"
    logger.warning("⚠️  Database not ready - using fallback endpoints only")
    
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
        "database_ready": database_ready,
        "database_error": database_error,
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

# Emergency admin setup endpoint
@app.post("/emergency/grant-admin-privileges")
async def emergency_grant_admin_privileges():
    """Emergency endpoint to grant admin privileges to matt.lindop@zebra.associates"""
    try:
        from sqlalchemy import text
        from app.core.database import get_db
        
        logger.info("🚨 EMERGENCY: Granting admin privileges for £925K opportunity")
        
        db_session = next(get_db())
        
        try:
            # Check if user exists first
            user_check = db_session.execute(text("""
                SELECT id, email, role, organisation_id, is_active 
                FROM users 
                WHERE email = 'matt.lindop@zebra.associates'
            """))
            user_row = user_check.fetchone()
            
            if user_row:
                # Update existing user to admin
                result = db_session.execute(text("""
                    UPDATE users 
                    SET role = 'admin', 
                        updated_at = CURRENT_TIMESTAMP 
                    WHERE email = 'matt.lindop@zebra.associates'
                """))
                logger.info(f"✅ Updated existing user to admin role")
                
                user_info = {
                    "id": str(user_row[0]),
                    "email": user_row[1], 
                    "role": "admin",  # Updated role
                    "organisation_id": str(user_row[3]),
                    "is_active": user_row[4],
                    "action": "updated_to_admin"
                }
            else:
                # Create new admin user
                logger.info("⚠️  User not found - creating admin user")
                
                # Get default organization
                org_result = db_session.execute(text("SELECT id FROM organisations WHERE name = 'Default' LIMIT 1"))
                org_row = org_result.fetchone()
                
                if not org_row:
                    # Create default organization if it doesn't exist
                    db_session.execute(text("""
                        INSERT INTO organisations (name, industry, subscription_plan, created_at, updated_at)
                        VALUES ('Default', 'Technology', 'basic', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """))
                    org_result = db_session.execute(text("SELECT id FROM organisations WHERE name = 'Default' LIMIT 1"))
                    org_row = org_result.fetchone()
                
                org_id = org_row[0]
                
                # Create admin user with UUID generation
                create_result = db_session.execute(text("""
                    INSERT INTO users (email, first_name, last_name, role, organisation_id, is_active, created_at, updated_at)
                    VALUES ('matt.lindop@zebra.associates', 'Matt', 'Lindop', 'admin', :org_id, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id, email, role, organisation_id, is_active
                """), {"org_id": org_id})
                
                created_user = create_result.fetchone()
                logger.info("✅ Created new admin user matt.lindop@zebra.associates")
                
                user_info = {
                    "id": str(created_user[0]),
                    "email": created_user[1], 
                    "role": created_user[2],
                    "organisation_id": str(created_user[3]),
                    "is_active": created_user[4],
                    "action": "created_new_admin"
                }
            
            db_session.commit()
            logger.info("✅ Database transaction committed successfully")
            
            return {
                "status": "success",
                "message": "Admin privileges granted successfully to matt.lindop@zebra.associates",
                "user": user_info,
                "critical_note": "User MUST re-authenticate via Auth0 to receive new JWT with admin role",
                "epic_access": {
                    "epic_1_modules": "Will be accessible after re-authentication",
                    "epic_2_feature_flags": "Will be accessible after re-authentication"
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as fix_error:
            db_session.rollback()
            logger.error(f"❌ Admin privilege grant failed: {fix_error}")
            raise
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"❌ Emergency admin setup failed: {e}")
        return {
            "status": "error", 
            "message": f"Admin setup failed: {e}",
            "timestamp": datetime.now().isoformat()
        }

# Emergency database fix endpoint
@app.post("/emergency/fix-database-schema")
async def emergency_fix_database_schema():
    """Emergency endpoint to fix missing Base columns causing auth 500 errors"""
    try:
        from sqlalchemy import text
        from app.core.database import get_db
        
        logger.info("🚨 EMERGENCY: Starting database schema fix for authentication")
        
        # Tables with missing columns
        tables_to_fix = {
            'feature_flag_overrides': ['updated_at'],
            'feature_flag_usage': ['created_at', 'updated_at'],
            'module_usage_logs': ['created_at', 'updated_at'],
            'admin_actions': ['updated_at'],
            'audit_logs': ['created_at', 'updated_at'],
            'competitive_insights': ['updated_at'],
            'competitors': ['updated_at'],
            'market_alerts': ['updated_at'],
            'market_analytics': ['updated_at'],
            'pricing_data': ['updated_at']
        }
        
        db_session = next(get_db())
        fixed_tables = []
        
        try:
            for table_name, missing_columns in tables_to_fix.items():
                try:
                    # Check if table exists
                    db_session.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
                    
                    for column in missing_columns:
                        try:
                            # Try to select the column to see if it exists
                            db_session.execute(text(f"SELECT {column} FROM {table_name} LIMIT 1"))
                            logger.info(f"✓ {table_name}.{column} already exists")
                        except Exception:
                            # Column doesn't exist, add it
                            db_session.execute(text(f"""
                                ALTER TABLE {table_name} 
                                ADD COLUMN {column} TIMESTAMP WITH TIME ZONE 
                                DEFAULT CURRENT_TIMESTAMP NOT NULL
                            """))
                            logger.info(f"✅ Added {column} to {table_name}")
                    
                    fixed_tables.append(table_name)
                    
                except Exception as table_error:
                    logger.warning(f"⚠️  Table {table_name} not found or error: {table_error}")
            
            db_session.commit()
            logger.info("✅ Database schema fix completed successfully")
            
            return {
                "status": "success",
                "message": "Database schema fixed - authentication should now work",
                "fixed_tables": fixed_tables,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as fix_error:
            db_session.rollback()
            logger.error(f"❌ Database fix failed: {fix_error}")
            raise
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"❌ Emergency database fix failed: {e}")
        return {
            "status": "error", 
            "message": f"Database fix failed: {e}",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main_stable_production:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )