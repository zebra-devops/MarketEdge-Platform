#!/usr/bin/env python3
"""
Render PostgreSQL Direct Connection Test
=======================================

This script tests direct connectivity to the Render PostgreSQL database
and attempts to create the Matt Lindop admin user automatically.

Database URL: postgresql://marketedge_user:Qra5HBKofZqoQwQgKNyVnOOwKVRbRPAW@dpg-d2gch862dbo4c73b0kl80-a.oregon-postgres.render.com/marketedge_production

Tests performed:
1. Basic connectivity test
2. Permission assessment 
3. Schema validation
4. Admin user creation
5. User verification

Usage:
    python test_render_postgresql_direct.py
"""

import os
import sys
import traceback
from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional

# Database imports
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Define the exact database URL provided
RENDER_DB_URL = "postgresql://marketedge_user:Qra5HBKofZqoQwQgKNyVnOOwKVRbRPAW@dpg-d2gch862dbo4c73b0kl80-a.oregon-postgres.render.com/marketedge_production"

class RenderPostgreSQLTester:
    """Comprehensive tester for Render PostgreSQL database operations"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = None
        self.connection = None
        self.test_results = {
            'connectivity': False,
            'permissions': {},
            'schema_validation': False,
            'user_creation': False,
            'verification': False,
            'errors': [],
            'warnings': []
        }
    
    def safe_connect(self) -> bool:
        """Safely establish database connection with comprehensive error handling"""
        try:
            print("🔌 Attempting connection to Render PostgreSQL...")
            
            # Create engine with production-appropriate settings
            # Render PostgreSQL requires SSL for external connections
            self.engine = create_engine(
                self.db_url,
                pool_pre_ping=True,
                pool_recycle=300,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                echo=False,  # Set to True for SQL debugging
                connect_args={
                    "connect_timeout": 30,
                    "application_name": "MarketEdge_Admin_Setup",
                    "sslmode": "require",  # Render requires SSL
                    "sslcert": None,
                    "sslkey": None,
                    "sslrootcert": None
                }
            )
            
            # Test connection
            self.connection = self.engine.connect()
            
            # Basic connectivity test
            result = self.connection.execute(text("SELECT version(), current_database(), current_user"))
            version_info, db_name, current_user = result.fetchone()
            
            print(f"✅ Successfully connected to Render PostgreSQL!")
            print(f"   Database: {db_name}")
            print(f"   User: {current_user}")
            print(f"   Version: {version_info.split(',')[0]}")
            
            self.test_results['connectivity'] = True
            return True
            
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results['errors'].append(error_msg)
            return False
    
    def test_permissions(self) -> Dict[str, bool]:
        """Test database permissions for the marketedge_user"""
        permissions = {}
        
        if not self.connection:
            return permissions
            
        try:
            print("\n🔐 Testing database permissions...")
            
            # Test SELECT permissions
            try:
                self.connection.execute(text("SELECT 1"))
                permissions['select'] = True
                print("   ✅ SELECT: Allowed")
            except Exception as e:
                permissions['select'] = False
                print(f"   ❌ SELECT: Denied - {e}")
            
            # Test INSERT permissions (create a test table first)
            try:
                # Try to create a test table
                self.connection.execute(text("""
                    CREATE TEMPORARY TABLE perm_test_insert (id SERIAL, test_data TEXT)
                """))
                self.connection.execute(text("INSERT INTO perm_test_insert (test_data) VALUES ('test')"))
                permissions['insert'] = True
                print("   ✅ INSERT: Allowed")
            except Exception as e:
                permissions['insert'] = False
                print(f"   ❌ INSERT: Denied - {e}")
            
            # Test UPDATE permissions
            try:
                self.connection.execute(text("UPDATE perm_test_insert SET test_data = 'updated' WHERE id = 1"))
                permissions['update'] = True
                print("   ✅ UPDATE: Allowed")
            except Exception as e:
                permissions['update'] = False
                print(f"   ❌ UPDATE: Denied - {e}")
            
            # Test DELETE permissions
            try:
                self.connection.execute(text("DELETE FROM perm_test_insert WHERE id = 1"))
                permissions['delete'] = True
                print("   ✅ DELETE: Allowed")
            except Exception as e:
                permissions['delete'] = False
                print(f"   ❌ DELETE: Denied - {e}")
            
            # Test CREATE permissions
            try:
                self.connection.execute(text("""
                    CREATE TEMPORARY TABLE perm_test_create (
                        id SERIAL PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                permissions['create'] = True
                print("   ✅ CREATE: Allowed")
            except Exception as e:
                permissions['create'] = False
                print(f"   ❌ CREATE: Denied - {e}")
            
            # Test schema introspection
            try:
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                permissions['introspection'] = True
                print(f"   ✅ INTROSPECTION: Allowed ({len(tables)} tables visible)")
            except Exception as e:
                permissions['introspection'] = False
                print(f"   ❌ INTROSPECTION: Denied - {e}")
            
            self.test_results['permissions'] = permissions
            
        except Exception as e:
            error_msg = f"Permission testing failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results['errors'].append(error_msg)
        
        return permissions
    
    def validate_schema(self) -> bool:
        """Validate that required tables and columns exist"""
        
        if not self.connection:
            return False
            
        try:
            print("\n📋 Validating database schema...")
            
            # Required tables and their key columns
            required_schema = {
                'users': ['id', 'email', 'auth0_id', 'name', 'created_at'],
                'organisations': ['id', 'name', 'created_at'],
                'organization_hierarchy': ['id', 'parent_id', 'child_id'],
                'user_hierarchy_assignments': ['id', 'user_id', 'organization_id']
            }
            
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            schema_valid = True
            
            for table_name, required_columns in required_schema.items():
                if table_name not in existing_tables:
                    print(f"   ❌ Table missing: {table_name}")
                    schema_valid = False
                    continue
                
                print(f"   ✅ Table exists: {table_name}")
                
                # Check columns
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                
                for col in required_columns:
                    if col in columns:
                        print(f"      ✅ Column: {col}")
                    else:
                        print(f"      ❌ Missing column: {col}")
                        schema_valid = False
            
            # Check for any existing users
            try:
                result = self.connection.execute(text("SELECT COUNT(*) as count FROM users"))
                user_count = result.fetchone()[0]
                print(f"   📊 Current users in database: {user_count}")
                
                # Check if Matt Lindop already exists
                result = self.connection.execute(text(
                    "SELECT COUNT(*) as count FROM users WHERE email = 'matt.lindop@zebra.associates'"
                ))
                matt_exists = result.fetchone()[0] > 0
                
                if matt_exists:
                    print(f"   ⚠️  Matt Lindop user already exists!")
                    self.test_results['warnings'].append("Matt Lindop user already exists in database")
                else:
                    print(f"   ✅ Matt Lindop user does not exist - ready for creation")
                    
            except Exception as e:
                print(f"   ⚠️  Could not check existing users: {e}")
            
            self.test_results['schema_validation'] = schema_valid
            return schema_valid
            
        except Exception as e:
            error_msg = f"Schema validation failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results['errors'].append(error_msg)
            return False
    
    def create_matt_admin_user(self) -> bool:
        """Create Matt Lindop's admin user in the production database"""
        
        if not self.connection:
            return False
            
        try:
            print("\n👤 Creating Matt Lindop admin user...")
            
            # Begin transaction
            trans = self.connection.begin()
            
            try:
                # Check if user already exists
                result = self.connection.execute(text(
                    "SELECT id FROM users WHERE email = 'matt.lindop@zebra.associates'"
                ))
                existing_user = result.fetchone()
                
                if existing_user:
                    print("   ⚠️  Matt Lindop user already exists, skipping creation")
                    trans.rollback()
                    return True
                
                # Check if Zebra Associates organization exists
                result = self.connection.execute(text(
                    "SELECT id FROM organisations WHERE name = 'Zebra Associates'"
                ))
                zebra_org = result.fetchone()
                
                zebra_org_id = None
                
                if not zebra_org:
                    print("   📢 Creating Zebra Associates organization...")
                    
                    # Create organization
                    org_result = self.connection.execute(text("""
                        INSERT INTO organisations (id, name, created_at, updated_at)
                        VALUES (gen_random_uuid(), 'Zebra Associates', NOW(), NOW())
                        RETURNING id
                    """))
                    zebra_org_id = org_result.fetchone()[0]
                    print(f"   ✅ Created organization with ID: {zebra_org_id}")
                else:
                    zebra_org_id = zebra_org[0]
                    print(f"   ✅ Found existing organization with ID: {zebra_org_id}")
                
                # Create Matt's user account
                print("   👤 Creating Matt Lindop user account...")
                
                user_result = self.connection.execute(text("""
                    INSERT INTO users (
                        id, email, auth0_id, name, role, 
                        is_active, created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(), 
                        'matt.lindop@zebra.associates',
                        'auth0|placeholder-will-be-updated-on-first-login',
                        'Matt Lindop',
                        'SUPER_ADMIN',
                        true,
                        NOW(),
                        NOW()
                    )
                    RETURNING id, email, name, role
                """))
                
                user_data = user_result.fetchone()
                user_id = user_data[0]
                
                print(f"   ✅ Created user:")
                print(f"      ID: {user_id}")
                print(f"      Email: {user_data[1]}")
                print(f"      Name: {user_data[2]}")
                print(f"      Role: {user_data[3]}")
                
                # Create hierarchy assignment
                print("   🔗 Creating user-organization hierarchy assignment...")
                
                self.connection.execute(text("""
                    INSERT INTO user_hierarchy_assignments (
                        id, user_id, organization_id, created_at
                    ) VALUES (
                        gen_random_uuid(), :user_id, :org_id, NOW()
                    )
                """), {"user_id": user_id, "org_id": zebra_org_id})
                
                print("   ✅ Created hierarchy assignment")
                
                # Commit transaction
                trans.commit()
                
                print("   🎉 Matt Lindop admin user created successfully!")
                
                self.test_results['user_creation'] = True
                return True
                
            except Exception as e:
                trans.rollback()
                raise e
                
        except Exception as e:
            error_msg = f"User creation failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results['errors'].append(error_msg)
            return False
    
    def verify_admin_user(self) -> bool:
        """Verify the admin user was created correctly and is functional"""
        
        if not self.connection:
            return False
            
        try:
            print("\n🔍 Verifying Matt Lindop admin user creation...")
            
            # Check user exists with correct details
            result = self.connection.execute(text("""
                SELECT u.id, u.email, u.name, u.role, u.is_active,
                       u.created_at, o.name as org_name
                FROM users u
                LEFT JOIN user_hierarchy_assignments uha ON u.id = uha.user_id
                LEFT JOIN organisations o ON uha.organization_id = o.id
                WHERE u.email = 'matt.lindop@zebra.associates'
            """))
            
            user_data = result.fetchone()
            
            if not user_data:
                print("   ❌ User not found!")
                return False
            
            print("   ✅ User verification successful:")
            print(f"      ID: {user_data[0]}")
            print(f"      Email: {user_data[1]}")
            print(f"      Name: {user_data[2]}")
            print(f"      Role: {user_data[3]}")
            print(f"      Active: {user_data[4]}")
            print(f"      Created: {user_data[5]}")
            print(f"      Organization: {user_data[6]}")
            
            # Verify role is SUPER_ADMIN
            if user_data[3] != 'SUPER_ADMIN':
                print(f"   ❌ Incorrect role: {user_data[3]} (expected: SUPER_ADMIN)")
                return False
            
            # Verify user is active
            if not user_data[4]:
                print("   ❌ User is not active!")
                return False
            
            print("   🎉 All verifications passed!")
            
            self.test_results['verification'] = True
            return True
            
        except Exception as e:
            error_msg = f"User verification failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results['errors'].append(error_msg)
            return False
    
    def test_production_safety(self) -> bool:
        """Test that we can safely operate in production environment"""
        
        if not self.connection:
            return False
            
        try:
            print("\n🛡️  Testing production safety measures...")
            
            # Check current database name to confirm we're in production
            result = self.connection.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            
            if db_name != 'marketedge_production':
                print(f"   ⚠️  Unexpected database name: {db_name}")
                self.test_results['warnings'].append(f"Connected to {db_name}, expected marketedge_production")
            else:
                print(f"   ✅ Confirmed production database: {db_name}")
            
            # Check for backup/recovery capabilities (if available)
            try:
                result = self.connection.execute(text(
                    "SELECT setting FROM pg_settings WHERE name = 'archive_mode'"
                ))
                archive_mode = result.fetchone()
                if archive_mode:
                    print(f"   📦 Archive mode: {archive_mode[0]}")
                    
            except Exception:
                print("   ⚠️  Could not check backup settings (permissions)")
            
            # Test transaction rollback capability
            test_trans = self.connection.begin()
            try:
                # Create a test record that we'll roll back
                self.connection.execute(text("""
                    CREATE TEMPORARY TABLE safety_test (id SERIAL, data TEXT)
                """))
                self.connection.execute(text("INSERT INTO safety_test (data) VALUES ('rollback_test')"))
                test_trans.rollback()
                print("   ✅ Transaction rollback test passed")
            except Exception as e:
                print(f"   ❌ Transaction rollback test failed: {e}")
                return False
            
            return True
            
        except Exception as e:
            error_msg = f"Production safety test failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results['errors'].append(error_msg)
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database_url': self.db_url.replace(self.db_url.split('@')[0].split(':')[-1], '****'),
            'test_results': self.test_results,
            'summary': {
                'total_tests': 6,
                'passed': 0,
                'failed': 0,
                'warnings': len(self.test_results['warnings'])
            }
        }
        
        # Count passed/failed tests
        test_status = [
            self.test_results['connectivity'],
            bool(self.test_results['permissions'].get('select', False)),
            self.test_results['schema_validation'],
            self.test_results['user_creation'],
            self.test_results['verification']
        ]
        
        report['summary']['passed'] = sum(test_status)
        report['summary']['failed'] = len(test_status) - sum(test_status)
        
        return report
    
    def cleanup(self):
        """Clean up database connections"""
        try:
            if self.connection:
                self.connection.close()
            if self.engine:
                self.engine.dispose()
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


def main():
    """Main execution function"""
    
    print("=" * 80)
    print("RENDER POSTGRESQL DIRECT CONNECTION TEST")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing direct connection to Render PostgreSQL production database")
    print("=" * 80)
    
    # Initialize tester
    tester = RenderPostgreSQLTester(RENDER_DB_URL)
    
    try:
        # Test 1: Basic connectivity
        if not tester.safe_connect():
            print("\n❌ CRITICAL: Cannot establish database connection")
            print("   Check network connectivity and database credentials")
            return False
        
        # Test 2: Permissions assessment
        permissions = tester.test_permissions()
        required_perms = ['select', 'insert', 'update', 'create']
        
        if not all(permissions.get(perm, False) for perm in required_perms):
            print(f"\n⚠️  WARNING: Missing required permissions")
            print(f"   Required: {required_perms}")
            print(f"   Available: {[k for k, v in permissions.items() if v]}")
        
        # Test 3: Schema validation
        if not tester.validate_schema():
            print("\n❌ CRITICAL: Database schema validation failed")
            print("   Required tables or columns are missing")
            return False
        
        # Test 4: Production safety check
        tester.test_production_safety()
        
        # Test 5: Create admin user
        if not tester.create_matt_admin_user():
            print("\n❌ CRITICAL: Admin user creation failed")
            return False
        
        # Test 6: Verify admin user
        if not tester.verify_admin_user():
            print("\n❌ CRITICAL: Admin user verification failed")
            return False
        
        # Generate final report
        report = tester.generate_report()
        
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"✅ Tests Passed: {report['summary']['passed']}")
        print(f"❌ Tests Failed: {report['summary']['failed']}")
        print(f"⚠️  Warnings: {report['summary']['warnings']}")
        
        if report['summary']['failed'] == 0:
            print("\n🎉 SUCCESS: Direct database administration is fully functional!")
            print("   ✅ Can connect to Render PostgreSQL")
            print("   ✅ Have sufficient permissions")
            print("   ✅ Schema is valid")
            print("   ✅ Matt Lindop admin user created/verified")
            print("   ✅ Production database operations work correctly")
            
            print("\n📋 RECOMMENDATIONS:")
            print("   • Direct database operations are viable for admin tasks")
            print("   • Consider creating additional admin management scripts")
            print("   • Implement monitoring for database connection health")
            print("   • Set up automated backup verification")
            
        else:
            print("\n❌ FAILED: Some database operations are not working")
            print("\n🔧 ISSUES FOUND:")
            for error in report['test_results']['errors']:
                print(f"   • {error}")
        
        if report['summary']['warnings'] > 0:
            print("\n⚠️  WARNINGS:")
            for warning in report['test_results']['warnings']:
                print(f"   • {warning}")
        
        print("=" * 80)
        
        return report['summary']['failed'] == 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False
        
    finally:
        tester.cleanup()


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 FATAL ERROR: {e}")
        sys.exit(1)