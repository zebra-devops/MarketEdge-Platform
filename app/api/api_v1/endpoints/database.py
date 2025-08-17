from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....core.config import settings
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/init")
async def initialize_database():
    """
    Initialize database with migrations - EMERGENCY ENDPOINT FOR RENDER DEPLOYMENT
    This endpoint runs Alembic migrations to set up the database schema.
    """
    # EMERGENCY BYPASS: Allow database initialization for Odeon demo deployment
    # Check if we're on Render platform and need emergency database initialization
    is_render_emergency = (
        os.getenv("RENDER") == "true" or 
        "onrender.com" in os.getenv("RENDER_EXTERNAL_URL", "") or
        os.path.exists("/opt/render")  # Render filesystem marker
    )
    
    if not settings.DEBUG and settings.ENVIRONMENT != "development" and not is_render_emergency:
        raise HTTPException(
            status_code=403,
            detail="Database initialization only allowed in development or debug mode"
        )
    
    try:
        # Change to the correct directory for alembic
        backend_dir = "/opt/render/project/src/platform-wrapper/backend"
        if not os.path.exists(backend_dir):
            # Fallback for local development
            backend_dir = os.path.join(os.getcwd(), "platform-wrapper", "backend")
        
        if not os.path.exists(backend_dir):
            raise HTTPException(
                status_code=500,
                detail=f"Backend directory not found. Tried: {backend_dir}"
            )
        
        # Set environment variable for database URL
        env = os.environ.copy()
        env["DATABASE_URL"] = settings.DATABASE_URL
        
        # Run alembic upgrade
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            logger.error(f"Alembic migration failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Migration failed: {result.stderr}"
            )
        
        logger.info("Database migrations completed successfully")
        return {
            "status": "success",
            "message": "Database initialized successfully",
            "migrations_output": result.stdout,
            "backend_dir": backend_dir
        }
        
    except subprocess.TimeoutExpired:
        logger.error("Database migration timeout")
        raise HTTPException(
            status_code=500,
            detail="Migration timeout - database initialization took too long"
        )
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database initialization failed: {str(e)}"
        )


@router.get("/schema-check")
async def check_database_schema(db: Session = Depends(get_db)):
    """
    Check if database tables exist
    """
    try:
        from ....models.user import User
        from ....models.organisation import Organisation
        
        # Try to query tables to see if they exist
        tables_status = {}
        
        try:
            user_count = db.query(User).count()
            tables_status["users"] = {"exists": True, "count": user_count}
        except Exception as e:
            tables_status["users"] = {"exists": False, "error": str(e)}
        
        try:
            org_count = db.query(Organisation).count()
            tables_status["organisations"] = {"exists": True, "count": org_count}
        except Exception as e:
            tables_status["organisations"] = {"exists": False, "error": str(e)}
        
        return {
            "status": "success",
            "tables": tables_status,
            "database_url_host": settings.DATABASE_URL.split("@")[1].split(":")[0] if "@" in settings.DATABASE_URL else "unknown"
        }
        
    except Exception as e:
        logger.error(f"Schema check error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Schema check failed: {str(e)}"
        )