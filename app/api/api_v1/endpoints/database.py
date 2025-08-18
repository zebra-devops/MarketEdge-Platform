from fastapi import APIRouter, HTTPException, Depends, Request, Response
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
        # Try multiple possible paths for the backend directory
        possible_paths = [
            "/opt/render/project/src/platform-wrapper/backend",  # Original expected path
            "/opt/render/project/src/backend",                   # Alternative render path
            "/opt/render/project/src",                           # Render project root
            "/opt/render/project/platform-wrapper/backend",     # Alternative structure
            os.path.join(os.getcwd(), "platform-wrapper", "backend"),  # Local development
            os.path.join(os.getcwd(), "backend"),                # Alternative local
            os.getcwd()                                          # Current directory fallback
        ]
        
        backend_dir = None
        alembic_cfg_path = None
        
        for path in possible_paths:
            if os.path.exists(path):
                # Check if this directory has alembic.ini
                alembic_ini = os.path.join(path, "alembic.ini")
                if os.path.exists(alembic_ini):
                    backend_dir = path
                    alembic_cfg_path = alembic_ini
                    break
                    
        if not backend_dir:
            # Generate diagnostic info for debugging
            cwd = os.getcwd()
            available_files = []
            try:
                available_files = os.listdir(cwd)[:10]  # Limit to first 10 files
            except:
                available_files = ["Unable to list directory"]
                
            raise HTTPException(
                status_code=500,
                detail=f"Backend directory with alembic.ini not found. CWD: {cwd}, Available files: {available_files}, Tried paths: {possible_paths}"
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
            "backend_dir": backend_dir,
            "alembic_config": alembic_cfg_path
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


@router.get("/diagnostics")
async def diagnostic_check():
    """
    Diagnostic endpoint to check deployment structure
    """
    try:
        cwd = os.getcwd()
        
        # Get environment info
        env_info = {
            "cwd": cwd,
            "render_env": os.getenv("RENDER"),
            "render_url": os.getenv("RENDER_EXTERNAL_URL"),
            "python_path": os.getenv("PYTHONPATH"),
            "path_env": os.getenv("PATH", "").split(":")[:5]  # First 5 PATH entries
        }
        
        # Check for key files in current directory
        files_info = {}
        try:
            files_info["cwd_files"] = os.listdir(cwd)[:20]  # First 20 files
        except:
            files_info["cwd_files"] = ["Unable to list"]
            
        # Check common directories
        check_dirs = [
            "/opt/render/project/src",
            "/opt/render/project",
            "/opt/render",
            os.path.join(cwd, "platform-wrapper"),
            os.path.join(cwd, "backend")
        ]
        
        dir_info = {}
        for dir_path in check_dirs:
            if os.path.exists(dir_path):
                try:
                    dir_info[dir_path] = os.listdir(dir_path)[:10]
                except:
                    dir_info[dir_path] = ["Unable to list"]
            else:
                dir_info[dir_path] = "Does not exist"
        
        return {
            "status": "success",
            "environment": env_info,
            "files": files_info,
            "directories": dir_info
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/emergency-fix")
async def emergency_database_fix(db: Session = Depends(get_db)):
    """
    Emergency fix for missing database columns
    """
    try:
        from sqlalchemy import text
        
        # Add missing columns to organisations table
        missing_columns_sql = """
        DO $$ 
        BEGIN
            -- Add industry_type if missing
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='organisations' AND column_name='industry_type') THEN
                ALTER TABLE organisations ADD COLUMN industry_type VARCHAR(50) DEFAULT 'default';
            END IF;
            
            -- Add rate_limit_per_hour if missing
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='organisations' AND column_name='rate_limit_per_hour') THEN
                ALTER TABLE organisations ADD COLUMN rate_limit_per_hour INTEGER DEFAULT 1000;
            END IF;
            
            -- Add burst_limit if missing
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='organisations' AND column_name='burst_limit') THEN
                ALTER TABLE organisations ADD COLUMN burst_limit INTEGER DEFAULT 100;
            END IF;
            
            -- Add rate_limit_enabled if missing
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='organisations' AND column_name='rate_limit_enabled') THEN
                ALTER TABLE organisations ADD COLUMN rate_limit_enabled BOOLEAN DEFAULT TRUE;
            END IF;
            
            -- Add sic_code if missing
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='organisations' AND column_name='sic_code') THEN
                ALTER TABLE organisations ADD COLUMN sic_code VARCHAR(10);
            END IF;
        END $$;
        """
        
        db.execute(text(missing_columns_sql))
        db.commit()
        
        # Check what columns exist now
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'organisations'
            ORDER BY column_name
        """))
        columns = {row[0]: row[1] for row in result}
        
        return {
            "status": "success",
            "message": "Emergency fix applied",
            "organisation_columns": columns
        }
        
    except Exception as e:
        logger.error(f"Emergency fix error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Emergency fix failed: {str(e)}"
        )


@router.post("/fix-enum-case-issue")
async def fix_enum_case_issue(db: Session = Depends(get_db)):
    """
    CRITICAL FIX: Address enum case sensitivity and foreign key issues preventing auth
    """
    try:
        from sqlalchemy import text
        
        results = {}
        
        # Fix 1: Drop foreign key constraint on sic_code since sic_codes table doesn't exist
        fix_fk_sql = """
        DO $$ 
        BEGIN
            -- Drop foreign key constraint if it exists
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
                      WHERE constraint_name LIKE '%sic_code%' AND table_name = 'organisations') THEN
                ALTER TABLE organisations DROP CONSTRAINT IF EXISTS organisations_sic_code_fkey;
            END IF;
        END $$;
        """
        
        try:
            db.execute(text(fix_fk_sql))
            db.commit()
            results["foreign_key_fix"] = "SUCCESS - Removed sic_code foreign key constraint"
        except Exception as e:
            results["foreign_key_fix"] = f"ERROR: {str(e)}"
            
        # Fix 2: Test enum creation with lowercase values
        test_enum_sql = """
        INSERT INTO organisations (id, name, industry_type, subscription_plan, is_active, rate_limit_per_hour, burst_limit, rate_limit_enabled)
        VALUES (gen_random_uuid(), 'Enum Fix Test Org', 'default', 'basic', true, 1000, 100, true)
        RETURNING id, name, industry_type, subscription_plan;
        """
        
        try:
            test_result = db.execute(text(test_enum_sql))
            test_org = test_result.fetchone()
            if test_org:
                results["enum_test"] = {
                    "success": True,
                    "org": {
                        "id": str(test_org[0]),
                        "name": test_org[1],
                        "industry_type": test_org[2],
                        "subscription_plan": test_org[3]
                    }
                }
                # Clean up test org
                db.execute(text(f"DELETE FROM organisations WHERE id = '{test_org[0]}'"))
            db.commit()
        except Exception as e:
            results["enum_test"] = {"success": False, "error": str(e)}
            
        # Fix 3: Create minimal sic_codes table if needed for future
        create_sic_table_sql = """
        CREATE TABLE IF NOT EXISTS sic_codes (
            code VARCHAR(10) PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            section VARCHAR(1) NOT NULL,
            division VARCHAR(2) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Insert default SIC code
        INSERT INTO sic_codes (code, title, section, division)
        VALUES ('59140', 'Motion picture projection activities', 'J', '59')
        ON CONFLICT (code) DO NOTHING;
        """
        
        try:
            db.execute(text(create_sic_table_sql))
            db.commit()
            results["sic_table_creation"] = "SUCCESS - Created sic_codes table"
        except Exception as e:
            results["sic_table_creation"] = f"ERROR: {str(e)}"
            
        return {
            "status": "success",
            "message": "Enum and foreign key fixes applied",
            "fixes": results
        }
        
    except Exception as e:
        logger.error(f"Enum case fix error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Enum case fix failed: {str(e)}"
        )


@router.post("/fix-enum-sqlalchemy-issue")
async def fix_enum_sqlalchemy_issue(db: Session = Depends(get_db)):
    """
    ULTIMATE FIX: Directly handle enum value conversion in SQLAlchemy
    """
    try:
        from sqlalchemy import text
        from ....models.organisation import Organisation
        from ....core.rate_limit_config import Industry
        from ....models.organisation import SubscriptionPlan
        
        results = {}
        
        # Test 1: Create organisation by directly setting enum values as strings
        try:
            # Create using string values instead of enum objects
            test_org = Organisation(
                name="String Enum Test Org",
                is_active=True,
                rate_limit_per_hour=1000,
                burst_limit=100,
                rate_limit_enabled=True
            )
            
            # Manually set enum fields as strings
            test_org.industry_type = Industry.DEFAULT.value  # Use .value to get 'default'
            test_org.subscription_plan = SubscriptionPlan.basic.value  # Use .value to get 'basic'
            
            db.add(test_org)
            db.commit()
            
            results["string_enum_creation"] = {
                "success": True,
                "org": {
                    "id": str(test_org.id),
                    "name": test_org.name,
                    "industry_type": str(test_org.industry_type),
                    "subscription_plan": str(test_org.subscription_plan)
                }
            }
            
            # Clean up
            db.delete(test_org)
            db.commit()
            
        except Exception as e:
            results["string_enum_creation"] = {"success": False, "error": str(e)}
            db.rollback()
        
        # Test 2: Try direct SQL insert with proper values
        try:
            create_sql = """
            INSERT INTO organisations (id, name, industry_type, subscription_plan, is_active, rate_limit_per_hour, burst_limit, rate_limit_enabled)
            VALUES (gen_random_uuid(), 'SQL Insert Test', 'default', 'basic', true, 1000, 100, true)
            RETURNING id, name, industry_type, subscription_plan;
            """
            
            result = db.execute(text(create_sql))
            org_data = result.fetchone()
            
            if org_data:
                results["direct_sql_insert"] = {
                    "success": True,
                    "org": {
                        "id": str(org_data[0]),
                        "name": org_data[1],
                        "industry_type": org_data[2],
                        "subscription_plan": org_data[3]
                    }
                }
                # Clean up
                db.execute(text(f"DELETE FROM organisations WHERE id = '{org_data[0]}'"))
            
            db.commit()
            
        except Exception as e:
            results["direct_sql_insert"] = {"success": False, "error": str(e)}
            db.rollback()
        
        return {
            "status": "success", 
            "message": "Advanced enum fixes tested",
            "test_results": results
        }
        
    except Exception as e:
        logger.error(f"Enum fix error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Advanced enum fix failed: {str(e)}"
        )


@router.post("/test-user-creation")
async def test_user_creation_realistic(db: Session = Depends(get_db)):
    """Test the exact user creation flow that happens during Auth0 authentication"""
    try:
        from ....models.user import User, UserRole
        from ....models.organisation import Organisation, SubscriptionPlan
        from ....core.rate_limit_config import Industry
        
        # Step 1: Create default organization (same as auth.py lines 297-309)
        default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
        if not default_org:
            default_org = Organisation(
                name="Default", 
                industry="Technology",
                industry_type=Industry.DEFAULT.value,  # This is the critical line
                subscription_plan=SubscriptionPlan.basic.value
            )
            db.add(default_org)
            db.commit()
            db.refresh(default_org)
        
        # Step 2: Create user (same as auth.py lines 312-321)
        import uuid
        user = User(
            email=f"test.auth.user.{uuid.uuid4().hex[:8]}@example.com",
            first_name="Auth",
            last_name="Test",
            organisation_id=default_org.id,
            role=UserRole.viewer
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "status": "success",
            "message": "User creation simulation successful",
            "user_id": str(user.id),
            "org_id": str(default_org.id),
            "enum_values": {
                "industry_type": default_org.industry_type,
                "subscription_plan": default_org.subscription_plan
            }
        }
        
    except Exception as e:
        import traceback
        logger.error(f"User creation test failed: {str(e)}")
        return {
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc(),
            "error_type": type(e).__name__
        }


@router.post("/auth-debug")
async def debug_auth_login(request: Request, response: Response, db: Session = Depends(get_db)):
    """Debug version of auth login with enhanced logging"""
    import json
    import traceback
    from sqlalchemy.exc import SQLAlchemyError
    
    try:
        # Log the incoming request
        body = await request.body()
        logger.info(f"🔍 AUTH DEBUG: Request received - Content-Type: {request.headers.get('content-type')}")
        logger.info(f"🔍 AUTH DEBUG: Request body: {body.decode('utf-8')[:200]}")
        
        # Parse request data
        content_type = request.headers.get("content-type", "")
        if content_type.startswith("application/x-www-form-urlencoded"):
            form = await request.form()
            code = form.get("code")
            redirect_uri = form.get("redirect_uri")
            state = form.get("state")
        else:
            json_data = json.loads(body.decode('utf-8'))
            code = json_data.get("code")
            redirect_uri = json_data.get("redirect_uri")
            state = json_data.get("state")
        
        logger.info(f"🔍 AUTH DEBUG: Parsed data - code: {code[:10] if code else None}..., redirect_uri: {redirect_uri}")
        
        # Step 1: Test Auth0 token exchange
        try:
            from ....auth.auth0 import auth0_client
            logger.info("🔍 AUTH DEBUG: Starting Auth0 token exchange...")
            
            token_data = await auth0_client.exchange_code_for_token(code, redirect_uri, state)
            logger.info(f"🔍 AUTH DEBUG: Token exchange SUCCESS - expires_in: {token_data.get('expires_in')}")
            
            # Step 2: Get user info
            user_info = await auth0_client.get_user_info(token_data["access_token"])
            logger.info(f"🔍 AUTH DEBUG: User info received: {json.dumps(user_info, indent=2)}")
            
        except Exception as auth_error:
            logger.error(f"🔍 AUTH DEBUG: Auth0 operation failed: {str(auth_error)}")
            return {"debug_status": "auth0_failed", "error": str(auth_error)}
        
        # Step 3: Database operations debug
        try:
            from ....models.user import User, UserRole
            from ....models.organisation import Organisation, SubscriptionPlan
            from ....core.rate_limit_config import Industry
            
            # Extract user data
            email = user_info.get("email", "").strip().lower()
            given_name = user_info.get("given_name", "").strip()
            family_name = user_info.get("family_name", "").strip()
            
            logger.info(f"🔍 AUTH DEBUG: Processing user - email: {email}, given_name: '{given_name}', family_name: '{family_name}'")
            
            # Check if user exists
            existing_user = db.query(User).filter(User.email == email).first()
            logger.info(f"🔍 AUTH DEBUG: Existing user found: {existing_user is not None}")
            
            if not existing_user:
                # Test organization creation
                logger.info("🔍 AUTH DEBUG: Creating default organization...")
                default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
                
                if not default_org:
                    logger.info("🔍 AUTH DEBUG: No default org found, creating new one...")
                    default_org = Organisation(
                        name="Default",
                        industry="Technology", 
                        industry_type=Industry.DEFAULT.value,
                        subscription_plan=SubscriptionPlan.basic.value
                    )
                    db.add(default_org)
                    db.commit()
                    logger.info(f"🔍 AUTH DEBUG: Default org created with ID: {default_org.id}")
                else:
                    logger.info(f"🔍 AUTH DEBUG: Using existing default org: {default_org.id}")
                
                # Test user creation
                logger.info("🔍 AUTH DEBUG: Creating new user...")
                user = User(
                    email=email,
                    first_name=given_name or "Unknown",
                    last_name=family_name or "User", 
                    organisation_id=default_org.id,
                    role=UserRole.viewer
                )
                db.add(user)
                db.commit()
                logger.info(f"🔍 AUTH DEBUG: User created successfully with ID: {user.id}")
            else:
                logger.info(f"🔍 AUTH DEBUG: Using existing user: {existing_user.id}")
            
            return {
                "debug_status": "success",
                "message": "Authentication debug completed successfully",
                "user_email": email,
                "auth0_user_info": user_info
            }
            
        except SQLAlchemyError as db_error:
            logger.error(f"🔍 AUTH DEBUG: DATABASE ERROR: {str(db_error)}")
            logger.error(f"🔍 AUTH DEBUG: Database error details: {traceback.format_exc()}")
            db.rollback()
            return {
                "debug_status": "database_error",
                "error": str(db_error),
                "error_type": type(db_error).__name__,
                "traceback": traceback.format_exc()
            }
            
        except Exception as general_error:
            logger.error(f"🔍 AUTH DEBUG: GENERAL ERROR: {str(general_error)}")
            logger.error(f"🔍 AUTH DEBUG: General error details: {traceback.format_exc()}")
            return {
                "debug_status": "general_error", 
                "error": str(general_error),
                "error_type": type(general_error).__name__,
                "traceback": traceback.format_exc()
            }
            
    except Exception as request_error:
        logger.error(f"🔍 AUTH DEBUG: REQUEST ERROR: {str(request_error)}")
        return {
            "debug_status": "request_error",
            "error": str(request_error),
            "traceback": traceback.format_exc()
        }


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


@router.post("/test-enum-creation")
async def test_enum_organisation_creation(db: Session = Depends(get_db)):
    """
    Test organisation creation to diagnose enum issues
    """
    try:
        from sqlalchemy import text
        from ....models.organisation import Organisation
        from ....core.rate_limit_config import Industry
        from ....models.organisation import SubscriptionPlan
        
        results = {}
        
        # Test 1: Check what enum types actually exist in database
        enum_check_sql = """
        SELECT t.typname, e.enumlabel 
        FROM pg_type t 
        JOIN pg_enum e ON t.oid = e.enumtypid 
        WHERE t.typname IN ('industry', 'subscriptionplan')
        ORDER BY t.typname, e.enumsortorder;
        """
        
        try:
            enum_result = db.execute(text(enum_check_sql))
            enum_values = {}
            for row in enum_result:
                type_name, enum_label = row
                if type_name not in enum_values:
                    enum_values[type_name] = []
                enum_values[type_name].append(enum_label)
            results["database_enums"] = enum_values
        except Exception as e:
            results["database_enums"] = {"error": str(e)}
        
        # Test 2: Check what enum values our models expect
        try:
            results["model_enums"] = {
                "Industry": [member.value for member in Industry],
                "SubscriptionPlan": [member.value for member in SubscriptionPlan]
            }
        except Exception as e:
            results["model_enums"] = {"error": str(e)}
        
        # Test 3: Try to create organisation with direct SQL
        direct_sql_test = """
        INSERT INTO organisations (id, name, industry_type, subscription_plan, is_active, rate_limit_per_hour, burst_limit, rate_limit_enabled)
        VALUES (gen_random_uuid(), 'Direct SQL Test Org', 'default', 'basic', true, 1000, 100, true)
        RETURNING id, name, industry_type, subscription_plan;
        """
        
        try:
            direct_result = db.execute(text(direct_sql_test))
            direct_org = direct_result.fetchone()
            if direct_org:
                results["direct_sql_creation"] = {
                    "success": True,
                    "org": {
                        "id": str(direct_org[0]),
                        "name": direct_org[1],
                        "industry_type": direct_org[2],
                        "subscription_plan": direct_org[3]
                    }
                }
                # Clean up
                db.execute(text(f"DELETE FROM organisations WHERE id = '{direct_org[0]}'"))
            db.commit()
        except Exception as e:
            results["direct_sql_creation"] = {"success": False, "error": str(e)}
            db.rollback()
        
        # Test 4: Try to create organisation with SQLAlchemy model
        try:
            test_org = Organisation(
                name="SQLAlchemy Test Org",
                industry_type=Industry.DEFAULT,
                subscription_plan=SubscriptionPlan.basic,
                is_active=True
            )
            db.add(test_org)
            db.commit()
            
            results["sqlalchemy_creation"] = {
                "success": True,
                "org": {
                    "id": str(test_org.id),
                    "name": test_org.name,
                    "industry_type": test_org.industry_type.value if hasattr(test_org.industry_type, 'value') else str(test_org.industry_type),
                    "subscription_plan": test_org.subscription_plan.value if hasattr(test_org.subscription_plan, 'value') else str(test_org.subscription_plan)
                }
            }
            
            # Clean up
            db.delete(test_org)
            db.commit()
            
        except Exception as e:
            results["sqlalchemy_creation"] = {"success": False, "error": str(e)}
            db.rollback()
        
        # Test 5: Check if sic_codes table exists
        sic_check_sql = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'sic_codes'
        );
        """
        
        try:
            sic_result = db.execute(text(sic_check_sql))
            sic_exists = sic_result.scalar()
            results["sic_codes_table_exists"] = sic_exists
            
            if sic_exists:
                sic_count_sql = "SELECT COUNT(*) FROM sic_codes;"
                count_result = db.execute(text(sic_count_sql))
                results["sic_codes_count"] = count_result.scalar()
        except Exception as e:
            results["sic_codes_table_exists"] = False
            results["sic_codes_error"] = str(e)
        
        return {
            "status": "success",
            "test_results": results
        }
        
    except Exception as e:
        logger.error(f"Enum test error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Enum test failed: {str(e)}"
        )