#!/usr/bin/env python3
"""
Diagnostic test to identify the root cause of authentication failures.

This script tests each component of the authentication flow to identify
where exactly the failure is occurring, bypassing generic error handling.
"""

import os
import sys
import requests
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend path to sys.path
backend_path = os.path.join(os.path.dirname(__file__), 'platform-wrapper', 'backend')
sys.path.insert(0, backend_path)

try:
    from app.core.config import settings
    from app.models.organisation import Organisation, SubscriptionPlan
    from app.models.user import User, UserRole
    from app.core.rate_limit_config import Industry
    from app.core.database import engine
except ImportError as e:
    print(f"Failed to import backend modules: {e}")
    print("Make sure you're running this from the MarketEdge root directory")
    sys.exit(1)

def test_database_connection():
    """Test basic database connectivity"""
    print("=== Testing Database Connection ===")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_database_schema():
    """Test if required tables exist and have correct schema"""
    print("\n=== Testing Database Schema ===")
    try:
        with engine.connect() as conn:
            # Check if organisations table exists
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'organisations'
                ORDER BY ordinal_position;
            """))
            
            org_columns = result.fetchall()
            if not org_columns:
                print("❌ Organisations table does not exist")
                return False
            
            print("✅ Organisations table exists")
            print("Columns:")
            for col in org_columns:
                print(f"  - {col[0]} ({col[1]}) default: {col[2]}")
            
            # Check if users table exists
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """))
            
            user_columns = result.fetchall()
            if not user_columns:
                print("❌ Users table does not exist")
                return False
            
            print("✅ Users table exists")
            print("Columns:")
            for col in user_columns:
                print(f"  - {col[0]} ({col[1]}) default: {col[2]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database schema check failed: {e}")
        return False

def test_enum_constraints():
    """Test enum constraints that might be causing failures"""
    print("\n=== Testing Enum Constraints ===")
    try:
        with engine.connect() as conn:
            # Test Industry enum values
            result = conn.execute(text("""
                SELECT unnest(enum_range(NULL::industry)) as industry_values;
            """))
            industry_values = [row[0] for row in result.fetchall()]
            print(f"✅ Industry enum values: {industry_values}")
            
            # Test SubscriptionPlan enum values  
            result = conn.execute(text("""
                SELECT unnest(enum_range(NULL::subscriptionplan)) as plan_values;
            """))
            plan_values = [row[0] for row in result.fetchall()]
            print(f"✅ SubscriptionPlan enum values: {plan_values}")
            
            # Test UserRole enum values
            result = conn.execute(text("""
                SELECT unnest(enum_range(NULL::userrole)) as role_values;
            """))
            role_values = [row[0] for row in result.fetchall()]
            print(f"✅ UserRole enum values: {role_values}")
            
            return True
            
    except Exception as e:
        print(f"❌ Enum constraint check failed: {e}")
        print("This might be the root cause - enum types may not exist or have wrong values")
        return False

def test_default_organisation_creation():
    """Test creating the default organisation that auth depends on"""
    print("\n=== Testing Default Organisation Creation ===")
    try:
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Check if default org exists
        default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
        if default_org:
            print(f"✅ Default organisation exists: {default_org.id}")
            print(f"  - Industry: {default_org.industry}")
            print(f"  - Industry Type: {default_org.industry_type}")
            print(f"  - Subscription Plan: {default_org.subscription_plan}")
            db.close()
            return True
        
        # Try to create default org
        print("Creating default organisation...")
        default_org = Organisation(
            name="Default",
            industry="Technology",
            industry_type=Industry.DEFAULT,
            subscription_plan=SubscriptionPlan.basic
        )
        
        db.add(default_org)
        db.commit()
        db.refresh(default_org)
        
        print(f"✅ Default organisation created: {default_org.id}")
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Default organisation creation failed: {e}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'orig'):
            print(f"Original error: {e.orig}")
        return False

def test_user_creation():
    """Test creating a user with the default organisation"""
    print("\n=== Testing User Creation ===")
    try:
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Get default org
        default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
        if not default_org:
            print("❌ Default organisation not found")
            db.close()
            return False
        
        # Check if test user exists
        test_email = "diagnostic@test.com"
        existing_user = db.query(User).filter(User.email == test_email).first()
        if existing_user:
            print(f"✅ Test user already exists: {existing_user.id}")
            db.close()
            return True
        
        # Try to create test user
        print("Creating test user...")
        test_user = User(
            email=test_email,
            first_name="Test",
            last_name="User",
            organisation_id=default_org.id,
            role=UserRole.viewer
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✅ Test user created: {test_user.id}")
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'orig'):
            print(f"Original error: {e.orig}")
        return False

def test_backend_health():
    """Test if the backend is responding"""
    print("\n=== Testing Backend Health ===")
    try:
        # Determine backend URL
        backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        if 'render.com' in backend_url:
            # Production backend
            health_url = f"{backend_url}/health"
        else:
            # Local backend
            health_url = "http://localhost:8000/health"
        
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Backend health check passed: {health_url}")
            print(f"Response: {response.text}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False

def test_auth_endpoint_direct():
    """Test the auth endpoint directly with a simulated request"""
    print("\n=== Testing Auth Endpoint Directly ===")
    try:
        # This would require a valid Auth0 code, so we'll just test if the endpoint exists
        backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        if 'render.com' not in backend_url:
            backend_url = "http://localhost:8000"
        
        auth_url = f"{backend_url}/api/v1/auth/login"
        
        # Try with invalid data to see what error we get
        response = requests.post(
            auth_url,
            data={'code': 'test', 'redirect_uri': 'http://test.com'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        print(f"Auth endpoint response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        # A 500 error with our specific message means we're hitting the right endpoint
        # but failing in the database operations
        if response.status_code == 500:
            response_data = response.json()
            if response_data.get('detail') == 'Internal server error':
                print("❌ Getting the same generic 500 error - this confirms the issue")
                return False
            
    except Exception as e:
        print(f"❌ Auth endpoint test failed: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    print("🔍 MarketEdge Authentication Diagnostic Test")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_database_schema,
        test_enum_constraints,
        test_default_organisation_creation,
        test_user_creation,
        test_backend_health,
        test_auth_endpoint_direct
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    print("=" * 50)
    print("🔍 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test.__name__}")
    
    failed_tests = [test.__name__ for test, result in zip(tests, results) if not result]
    
    if failed_tests:
        print(f"\n🚨 FAILED TESTS: {', '.join(failed_tests)}")
        print("\nThe first failed test is likely the root cause of the authentication issues.")
        return False
    else:
        print("\n🎉 All tests passed! The issue might be in Auth0 integration or deployment.")
        return True

if __name__ == "__main__":
    main()