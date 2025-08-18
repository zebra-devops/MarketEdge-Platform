#!/usr/bin/env python3
"""
Emergency SQLAlchemy Error Debug Script
Captures the exact SQLAlchemy error during authentication flow
"""
import sys
import os
import traceback
import logging
from contextlib import contextmanager

# Add app to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db, engine
from app.models.user import User, UserRole
from app.models.organisation import Organisation, SubscriptionPlan
from app.core.rate_limit_config import Industry

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@contextmanager
def capture_sqlalchemy_errors():
    """Context manager to capture detailed SQLAlchemy errors"""
    try:
        yield
    except SQLAlchemyError as e:
        logger.error("=== DETAILED SQLALCHEMY ERROR ANALYSIS ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Error args: {e.args}")
        
        # Get the original exception if available
        if hasattr(e, 'orig'):
            logger.error(f"Original exception: {e.orig}")
            logger.error(f"Original exception type: {type(e.orig).__name__}")
        
        # Get statement details if available
        if hasattr(e, 'statement'):
            logger.error(f"SQL statement: {e.statement}")
        
        if hasattr(e, 'params'):
            logger.error(f"SQL parameters: {e.params}")
            
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise

def test_enum_creation():
    """Test the exact enum operations that fail in auth flow"""
    logger.info("=== TESTING ENUM CREATION OPERATIONS ===")
    
    with capture_sqlalchemy_errors():
        db = next(get_db())
        
        try:
            # Test 1: Check if Industry enum values are correct
            logger.info("Testing Industry enum values...")
            logger.info(f"Industry.DEFAULT = {Industry.DEFAULT}")
            logger.info(f"Industry.DEFAULT.value = {Industry.DEFAULT.value}")
            
            # Test 2: Check if SubscriptionPlan enum values are correct
            logger.info("Testing SubscriptionPlan enum values...")
            logger.info(f"SubscriptionPlan.basic = {SubscriptionPlan.basic}")
            logger.info(f"SubscriptionPlan.basic.value = {SubscriptionPlan.basic.value}")
            
            # Test 3: Try to create organization with enum values (this is where it fails)
            logger.info("Testing organization creation with enum values...")
            test_org = Organisation(
                name="Test_Debug_Org_" + str(os.getpid()),
                industry="Technology",
                industry_type=Industry.DEFAULT.value,  # This line might fail
                subscription_plan=SubscriptionPlan.basic.value  # This line might fail
            )
            
            logger.info("Organization object created successfully")
            logger.info(f"Org industry_type: {test_org.industry_type}")
            logger.info(f"Org subscription_plan: {test_org.subscription_plan}")
            
            # Test 4: Try to add and commit to database
            logger.info("Adding organization to database...")
            db.add(test_org)
            
            logger.info("Flushing to database...")
            db.flush()  # This will show SQL without committing
            
            logger.info("Committing to database...")
            db.commit()
            
            logger.info("✅ Organization creation successful!")
            
            # Clean up
            db.delete(test_org)
            db.commit()
            
        except Exception as e:
            logger.error("❌ Organization creation failed!")
            db.rollback()
            raise
        finally:
            db.close()

def test_user_creation():
    """Test the exact user creation that happens in auth flow"""
    logger.info("=== TESTING USER CREATION OPERATIONS ===")
    
    with capture_sqlalchemy_errors():
        db = next(get_db())
        
        try:
            # First ensure we have a default organization
            default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
            if not default_org:
                logger.info("Creating default organization...")
                default_org = Organisation(
                    name="Default", 
                    industry="Technology",
                    industry_type=Industry.DEFAULT.value,
                    subscription_plan=SubscriptionPlan.basic.value
                )
                db.add(default_org)
                db.commit()
                db.refresh(default_org)
                logger.info("✅ Default organization created")
            else:
                logger.info("✅ Default organization exists")
            
            # Test user creation (this is the exact code from auth.py)
            logger.info("Testing user creation...")
            test_user = User(
                email=f"test_debug_{os.getpid()}@example.com",
                first_name="Test",
                last_name="User",
                organisation_id=default_org.id,
                role=UserRole.viewer
            )
            
            logger.info("User object created successfully")
            logger.info(f"User email: {test_user.email}")
            logger.info(f"User role: {test_user.role}")
            logger.info(f"User organisation_id: {test_user.organisation_id}")
            
            db.add(test_user)
            db.flush()
            db.commit()
            
            logger.info("✅ User creation successful!")
            
            # Clean up
            db.delete(test_user)
            db.commit()
            
        except Exception as e:
            logger.error("❌ User creation failed!")
            db.rollback()
            raise
        finally:
            db.close()

def check_database_schema():
    """Check if database schema matches model definitions"""
    logger.info("=== CHECKING DATABASE SCHEMA ===")
    
    try:
        from sqlalchemy import inspect, text
        
        inspector = inspect(engine)
        
        # Check organisations table
        logger.info("Checking organisations table...")
        if 'organisations' in inspector.get_table_names():
            columns = inspector.get_columns('organisations')
            for col in columns:
                logger.info(f"Column: {col['name']}, Type: {col['type']}, Nullable: {col['nullable']}")
        else:
            logger.error("organisations table not found!")
        
        # Check users table
        logger.info("Checking users table...")
        if 'users' in inspector.get_table_names():
            columns = inspector.get_columns('users')
            for col in columns:
                logger.info(f"Column: {col['name']}, Type: {col['type']}, Nullable: {col['nullable']}")
        else:
            logger.error("users table not found!")
            
        # Check for enum constraints
        with engine.connect() as conn:
            logger.info("Checking enum constraints...")
            
            # Check industry enum
            result = conn.execute(text("""
                SELECT constraint_name, check_clause 
                FROM information_schema.check_constraints 
                WHERE constraint_schema = current_schema()
                AND constraint_name LIKE '%industry%'
            """))
            
            for row in result:
                logger.info(f"Industry constraint: {row}")
                
            # Check subscription plan enum  
            result = conn.execute(text("""
                SELECT constraint_name, check_clause 
                FROM information_schema.check_constraints 
                WHERE constraint_schema = current_schema()
                AND constraint_name LIKE '%subscription%'
            """))
            
            for row in result:
                logger.info(f"Subscription constraint: {row}")
                
    except Exception as e:
        logger.error(f"Schema check failed: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    print("🔍 Starting SQLAlchemy Error Debug Analysis...")
    
    try:
        check_database_schema()
        print("\n" + "="*50)
        test_enum_creation()
        print("\n" + "="*50)
        test_user_creation()
        
        print("\n✅ All tests passed! Database operations working correctly.")
        print("The issue might be environment-specific or in production deployment.")
        
    except Exception as e:
        print(f"\n❌ Error found: {e}")
        print("This is likely the root cause of the authentication failures.")
        sys.exit(1)