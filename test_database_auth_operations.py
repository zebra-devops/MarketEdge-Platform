#!/usr/bin/env python3
"""
Database Authentication Operations Test
Tests the specific database operations that occur during authentication
to identify the exact failure point.
"""

import asyncio
import sys
import os
import traceback
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy.exc import SQLAlchemyError

# Add the app directory to Python path
sys.path.insert(0, '/Users/matt/Sites/MarketEdge')

from app.core.config import settings
from app.core.database import get_database_url
from app.models.user import User, UserRole
from app.models.organisation import Organisation, SubscriptionPlan
from app.core.rate_limit_config import Industry

def test_database_connection():
    """Test basic database connectivity"""
    print("=" * 60)
    print("DATABASE AUTHENTICATION OPERATIONS DIAGNOSTIC")
    print("=" * 60)
    
    try:
        # Get database URL
        db_url = get_database_url()
        print(f"Database URL: {db_url[:50]}...")
        
        # Test basic connection
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            echo=False,  # Disable SQL echo for cleaner output
            connect_args={
                "connect_timeout": 30,
                "application_name": "auth_diagnostic"
            }
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            print(f"✅ Basic connection: SUCCESS - {result.fetchone()}")
            
        return engine
        
    except Exception as e:
        print(f"❌ Basic connection: FAILED - {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return None

def test_table_existence(engine):
    """Test if required tables exist"""
    print("\n" + "=" * 40)
    print("TABLE EXISTENCE CHECK")
    print("=" * 40)
    
    tables_to_check = [
        "users",
        "organisations", 
        "alembic_version"
    ]
    
    try:
        with engine.connect() as conn:
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"✅ Table '{table}': EXISTS - {count} rows")
                except Exception as e:
                    print(f"❌ Table '{table}': MISSING or ERROR - {e}")
                    
    except Exception as e:
        print(f"❌ Table check failed: {e}")

def test_user_operations(engine):
    """Test user-related database operations that occur during auth"""
    print("\n" + "=" * 40)
    print("USER OPERATIONS TEST")
    print("=" * 40)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with SessionLocal() as db:
            # Test 1: Query existing user (simulates user lookup)
            print("\n1. Testing user lookup by email...")
            try:
                test_email = "test@example.com"
                user = db.query(User).filter(User.email == test_email).first()
                if user:
                    print(f"✅ User lookup: Found user {user.email}")
                else:
                    print(f"✅ User lookup: No user found for {test_email} (expected)")
            except Exception as e:
                print(f"❌ User lookup: FAILED - {e}")
                traceback.print_exc()
            
            # Test 2: Query organisations (simulates default org lookup)
            print("\n2. Testing organisation lookup...")
            try:
                default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
                if default_org:
                    print(f"✅ Organisation lookup: Found Default org (ID: {default_org.id})")
                else:
                    print("⚠️ Organisation lookup: No Default org found")
                    
                # Check if any organisations exist
                org_count = db.query(Organisation).count()
                print(f"✅ Total organisations: {org_count}")
                
            except Exception as e:
                print(f"❌ Organisation lookup: FAILED - {e}")
                traceback.print_exc()
            
            # Test 3: Create organisation (simulates org creation)
            print("\n3. Testing organisation creation...")
            try:
                test_org_name = f"Test Org {os.getpid()}"
                test_org = Organisation(
                    name=test_org_name,
                    industry="Technology",
                    industry_type=Industry.DEFAULT,
                    subscription_plan=SubscriptionPlan.basic
                )
                db.add(test_org)
                db.commit()
                db.refresh(test_org)
                print(f"✅ Organisation creation: SUCCESS (ID: {test_org.id})")
                
                # Clean up
                db.delete(test_org)
                db.commit()
                print(f"✅ Organisation cleanup: SUCCESS")
                
            except Exception as e:
                print(f"❌ Organisation creation: FAILED - {e}")
                traceback.print_exc()
                try:
                    db.rollback()
                except:
                    pass
            
            # Test 4: Create user (simulates user creation)
            print("\n4. Testing user creation...")
            try:
                # First ensure we have a default org
                default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
                if not default_org:
                    print("   Creating Default organisation for test...")
                    default_org = Organisation(
                        name="Default",
                        industry="Technology", 
                        industry_type=Industry.DEFAULT,
                        subscription_plan=SubscriptionPlan.basic
                    )
                    db.add(default_org)
                    db.commit()
                    db.refresh(default_org)
                    print(f"   ✅ Default org created (ID: {default_org.id})")
                
                test_user_email = f"test_{os.getpid()}@example.com"
                test_user = User(
                    email=test_user_email,
                    first_name="Test",
                    last_name="User",
                    organisation_id=default_org.id,
                    role=UserRole.viewer
                )
                db.add(test_user)
                db.commit()
                db.refresh(test_user)
                print(f"✅ User creation: SUCCESS (ID: {test_user.id})")
                
                # Test relationship loading
                if not test_user.organisation:
                    test_user = db.query(User).options(joinedload(User.organisation)).filter(User.id == test_user.id).first()
                
                if test_user.organisation:
                    print(f"✅ User-Organisation relationship: SUCCESS")
                else:
                    print(f"❌ User-Organisation relationship: FAILED")
                
                # Clean up
                db.delete(test_user)
                db.commit()
                print(f"✅ User cleanup: SUCCESS")
                
            except Exception as e:
                print(f"❌ User creation: FAILED - {e}")
                traceback.print_exc()
                try:
                    db.rollback()
                except:
                    pass
                    
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        traceback.print_exc()

def test_auth_simulation(engine):
    """Simulate the exact auth flow operations"""
    print("\n" + "=" * 40)
    print("AUTH FLOW SIMULATION")
    print("=" * 40)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with SessionLocal() as db:
            print("\nSimulating auth flow for test@marketedge.com...")
            
            # Step 1: User lookup
            sanitized_email = "test@marketedge.com"
            user = db.query(User).filter(User.email == sanitized_email).first()
            
            if not user:
                print("   User not found, creating new user...")
                
                # Step 2: Default org lookup/creation
                default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
                if not default_org:
                    print("   Default org not found, creating...")
                    default_org = Organisation(
                        name="Default", 
                        industry="Technology",
                        industry_type=Industry.DEFAULT,
                        subscription_plan=SubscriptionPlan.basic
                    )
                    db.add(default_org)
                    db.commit()
                    db.refresh(default_org)
                    print(f"   ✅ Default org created: {default_org.id}")
                
                # Step 3: User creation
                user = User(
                    email=sanitized_email,
                    first_name="Test",
                    last_name="User",
                    organisation_id=default_org.id,
                    role=UserRole.viewer
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"   ✅ User created: {user.id}")
            else:
                print(f"   ✅ User found: {user.id}")
            
            # Step 4: Organization relationship check
            if not user.organisation:
                user = db.query(User).options(joinedload(User.organisation)).filter(User.id == user.id).first()
            
            if user.organisation:
                print(f"   ✅ Organisation loaded: {user.organisation.name}")
                print(f"   ✅ Industry: {user.organisation.industry}")
                print(f"   ✅ Subscription: {user.organisation.subscription_plan}")
            else:
                print("   ❌ Organisation relationship failed")
            
            print("\n✅ AUTH FLOW SIMULATION: SUCCESS")
            print("   All database operations completed successfully")
            
    except Exception as e:
        print(f"\n❌ AUTH FLOW SIMULATION: FAILED")
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()

def main():
    """Run all database tests"""
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Rate limiting: {settings.RATE_LIMIT_ENABLED}")
    
    # Test 1: Basic connection
    engine = test_database_connection()
    if not engine:
        print("\n❌ CRITICAL: Cannot connect to database")
        return False
    
    # Test 2: Table existence
    test_table_existence(engine)
    
    # Test 3: User operations
    test_user_operations(engine)
    
    # Test 4: Auth simulation
    test_auth_simulation(engine)
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)
    
    engine.dispose()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)