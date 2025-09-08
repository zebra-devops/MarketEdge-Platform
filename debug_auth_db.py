#!/usr/bin/env python3
"""
Database Authentication Diagnostic Script

This script tests the exact database operations that occur during the authentication flow
to identify the root cause of the 500 "Database error during authentication" error.
"""
import os
import sys
import traceback
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models.user import User, UserRole
from app.models.organisation import Organisation, SubscriptionPlan
from app.models.tool import Tool
from app.models.organisation_tool_access import OrganisationToolAccess
from app.core.rate_limit_config import Industry
from app.core.config import settings


def test_database_connection():
    """Test basic database connection"""
    print("🔍 Testing database connection...")
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connected successfully: {version[:50]}...")
            return engine
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None


def test_table_exists(engine, table_name):
    """Check if a table exists"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                );
            """))
            exists = result.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"{status} Table '{table_name}' exists: {exists}")
            return exists
    except Exception as e:
        print(f"❌ Error checking table '{table_name}': {e}")
        return False


def test_enum_exists(engine, enum_name):
    """Check if an enum type exists"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM pg_type 
                    WHERE typname = '{enum_name}'
                );
            """))
            exists = result.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"{status} Enum '{enum_name}' exists: {exists}")
            return exists
    except Exception as e:
        print(f"❌ Error checking enum '{enum_name}': {e}")
        return False


def test_user_lookup(session: Session, test_email: str = "test@example.com"):
    """Test user lookup operation"""
    print(f"\n🔍 Testing user lookup for email: {test_email}")
    try:
        user = session.query(User).filter(User.email == test_email).first()
        if user:
            print(f"✅ User found: {user.id} - {user.email}")
        else:
            print(f"ℹ️  No user found for {test_email} (this is expected for new users)")
        return user
    except Exception as e:
        print(f"❌ User lookup failed: {e}")
        print(traceback.format_exc())
        return None


def test_default_organisation_lookup(session: Session):
    """Test default organization lookup"""
    print(f"\n🔍 Testing default organisation lookup...")
    try:
        default_org = session.query(Organisation).filter(Organisation.name == "Default").first()
        if default_org:
            print(f"✅ Default organisation found: {default_org.id}")
            print(f"   - Name: {default_org.name}")
            print(f"   - Industry: {default_org.industry}")
            print(f"   - Industry Type: {default_org.industry_type}")
            print(f"   - Subscription: {default_org.subscription_plan}")
        else:
            print(f"ℹ️  No default organisation found (will need to create)")
        return default_org
    except Exception as e:
        print(f"❌ Default organisation lookup failed: {e}")
        print(traceback.format_exc())
        return None


def test_organisation_creation(session: Session):
    """Test default organization creation"""
    print(f"\n🔍 Testing default organisation creation...")
    try:
        # Test creating organisation with all required fields
        test_org = Organisation(
            name=f"Test-{datetime.now().strftime('%Y%m%d-%H%M%S')}", 
            industry=Industry.DEFAULT.value,
            industry_type=Industry.DEFAULT,
            subscription_plan=SubscriptionPlan.basic
        )
        session.add(test_org)
        session.commit()
        session.refresh(test_org)
        
        print(f"✅ Test organisation created successfully: {test_org.id}")
        print(f"   - Name: {test_org.name}")
        print(f"   - Industry: {test_org.industry}")
        print(f"   - Industry Type: {test_org.industry_type}")
        print(f"   - Subscription: {test_org.subscription_plan}")
        
        # Clean up test organisation
        session.delete(test_org)
        session.commit()
        print("✅ Test organisation cleaned up")
        
        return True
    except Exception as e:
        print(f"❌ Organisation creation failed: {e}")
        print(traceback.format_exc())
        session.rollback()
        return False


def test_user_creation(session: Session, org_id: uuid.UUID):
    """Test user creation"""
    print(f"\n🔍 Testing user creation with org_id: {org_id}...")
    try:
        test_user = User(
            email=f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}@example.com",
            first_name="Test",
            last_name="User",
            organisation_id=org_id,
            role=UserRole.viewer
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        
        print(f"✅ Test user created successfully: {test_user.id}")
        print(f"   - Email: {test_user.email}")
        print(f"   - Role: {test_user.role}")
        print(f"   - Organisation ID: {test_user.organisation_id}")
        
        # Clean up test user
        session.delete(test_user)
        session.commit()
        print("✅ Test user cleaned up")
        
        return True
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        print(traceback.format_exc())
        session.rollback()
        return False


def test_tool_access_setup(session: Session, org_id: uuid.UUID):
    """Test tool access setup"""
    print(f"\n🔍 Testing tool access setup for org_id: {org_id}...")
    try:
        # Check if tools exist
        tools = session.query(Tool).filter(Tool.is_active == True).all()
        print(f"ℹ️  Found {len(tools)} active tools")
        
        if not tools:
            print("⚠️  No active tools found - this might be the issue!")
            return False
            
        # Test creating tool access record
        test_tool = tools[0] if tools else None
        if test_tool:
            test_access = OrganisationToolAccess(
                organisation_id=org_id,
                tool_id=test_tool.id,
                subscription_tier="basic",
                features_enabled=[],
                usage_limits={}
            )
            session.add(test_access)
            session.commit()
            session.refresh(test_access)
            
            print(f"✅ Tool access created successfully: {test_access.id}")
            
            # Clean up
            session.delete(test_access)
            session.commit()
            print("✅ Tool access cleaned up")
            
        return True
    except Exception as e:
        print(f"❌ Tool access setup failed: {e}")
        print(traceback.format_exc())
        session.rollback()
        return False


def main():
    """Main diagnostic function"""
    print("🚀 MarketEdge Authentication Database Diagnostic")
    print("=" * 50)
    
    # Test 1: Database connection
    engine = test_database_connection()
    if not engine:
        print("❌ Cannot proceed without database connection")
        return
    
    # Test 2: Check required tables exist
    print("\n📋 Checking required tables...")
    required_tables = ['users', 'organisations', 'tools', 'organisation_tool_access']
    missing_tables = []
    
    for table in required_tables:
        if not test_table_exists(engine, table):
            missing_tables.append(table)
    
    if missing_tables:
        print(f"❌ Missing tables: {missing_tables}")
        print("💡 Run database migrations: python -m alembic upgrade head")
        return
    
    # Test 3: Check required enums exist
    print("\n📋 Checking required enums...")
    required_enums = ['userrole', 'subscriptionplan', 'industry']
    missing_enums = []
    
    for enum in required_enums:
        if not test_enum_exists(engine, enum):
            missing_enums.append(enum)
    
    if missing_enums:
        print(f"❌ Missing enums: {missing_enums}")
        print("💡 Run database migrations: python -m alembic upgrade head")
        return
    
    # Test 4: Test actual database operations
    print("\n🔧 Testing database operations...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Test user lookup
        test_user_lookup(session, "diagnostic@test.com")
        
        # Test default org lookup
        default_org = test_default_organisation_lookup(session)
        
        # Test organisation creation if needed
        if not default_org:
            if not test_organisation_creation(session):
                print("❌ Cannot proceed - organisation creation failed")
                return
            # Create actual default org for testing
            default_org = Organisation(
                name="Default", 
                industry=Industry.DEFAULT.value,
                industry_type=Industry.DEFAULT,
                subscription_plan=SubscriptionPlan.basic
            )
            session.add(default_org)
            session.commit()
            session.refresh(default_org)
            print(f"✅ Default organisation created: {default_org.id}")
        
        # Test user creation
        test_user_creation(session, default_org.id)
        
        # Test tool access setup
        test_tool_access_setup(session, default_org.id)
        
        print("\n🎉 All database operations completed successfully!")
        print("💡 If authentication is still failing, the issue might be:")
        print("   1. Environment variables (DATABASE_URL, AUTH0_CLIENT_SECRET)")
        print("   2. Network connectivity to database from Render")
        print("   3. Database user permissions")
        print("   4. Connection pooling issues")
        
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        print(traceback.format_exc())
    finally:
        session.close()


if __name__ == "__main__":
    main()