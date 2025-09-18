#!/usr/bin/env python3
"""
Selective Admin Endpoint Failure Analysis
Critical Issue: User can login successfully but admin endpoints return 403/500 errors

BUSINESS CONTEXT:
- £925K Zebra Associates opportunity
- Matt Lindop can login but cannot access admin features
- Specific endpoints failing: statistics, modules, feature flags
- Basic auth works, admin endpoints fail - indicates authorization issue

ANALYSIS FOCUS:
This selective failure pattern suggests:
1. Core Auth0 authentication works (user can login)
2. Basic JWT token validation works 
3. Admin role authorization is failing
4. Different code paths between basic auth and admin auth
"""

import sys
import os
import asyncio
import traceback
from datetime import datetime
import json

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

try:
    from app.models.user import User, UserRole
    from app.auth.dependencies import get_current_user, require_admin, require_super_admin
    from app.core.database import get_async_db
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select, text
    from fastapi import HTTPException, Depends
    import logging
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SelectiveEndpointFailureDiagnostic:
    """Diagnose why admin endpoints fail while basic auth works"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'business_context': '£925K Zebra Associates - Admin endpoint access failure',
            'user_email': 'matt.lindop@zebra.associates',
            'issue_pattern': 'Selective failure - login works, admin endpoints fail',
            'tests': {},
            'analysis': {},
            'recommendations': []
        }
    
    async def connect_to_database(self):
        """Establish database connection"""
        print("🔌 Connecting to database...")
        
        # Use production database URL 
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            DATABASE_URL = "postgresql+asyncpg://marketedge_dev_user:1sEJF6bVbk48xUr@ep-empty-recipe-a2nwdxp3.eu-central-1.aws.neon.tech/marketedge_dev"
        
        try:
            self.engine = create_async_engine(DATABASE_URL, echo=False)
            self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
            
            # Test connection
            async with self.async_session() as session:
                await session.execute(text("SELECT 1"))
                
            print("✅ Database connection successful")
            self.results['database_connection'] = True
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.results['database_connection'] = False
            self.results['database_error'] = str(e)
            return False
    
    async def verify_user_status(self):
        """Verify Matt Lindop's current database status"""
        print("\n👤 Verifying user database status...")
        
        try:
            async with self.async_session() as session:
                # Find Matt Lindop
                result = await session.execute(
                    select(User).where(User.email == 'matt.lindop@zebra.associates')
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    print("❌ CRITICAL: User not found in database")
                    self.results['tests']['user_found'] = False
                    return None
                
                print(f"✅ User found: {user.email}")
                print(f"   👤 Role: {user.role} (type: {type(user.role)})")
                print(f"   🆔 User ID: {user.id}")
                print(f"   📧 Auth0 ID: {user.auth0_id}")
                print(f"   🏢 Organisation ID: {user.organisation_id}")
                print(f"   ✅ Active: {user.is_active}")
                print(f"   📅 Updated: {user.updated_at}")
                
                # Analyze role compatibility
                role_analysis = {
                    'current_role': str(user.role),
                    'role_type': str(type(user.role)),
                    'is_admin_compatible': user.role in [UserRole.admin, UserRole.super_admin],
                    'is_super_admin': user.role == UserRole.super_admin,
                    'is_active': user.is_active
                }
                
                print(f"\n🔍 Role Analysis:")
                print(f"   Expected for require_admin: {[UserRole.admin, UserRole.super_admin]}")
                print(f"   User role matches admin requirement: {role_analysis['is_admin_compatible']}")
                print(f"   User role matches super_admin requirement: {role_analysis['is_super_admin']}")
                
                self.results['tests']['user_status'] = {
                    'found': True,
                    'email': user.email,
                    'role': str(user.role),
                    'active': user.is_active,
                    'role_analysis': role_analysis
                }
                
                return user
                
        except Exception as e:
            print(f"❌ Error verifying user: {e}")
            self.results['tests']['user_status'] = {'error': str(e)}
            return None
    
    async def test_auth_dependencies(self, user: User):
        """Test the auth dependency functions directly"""
        print("\n🔐 Testing authentication dependencies...")
        
        try:
            # Test require_admin function
            print("Testing require_admin dependency...")
            try:
                admin_result = await require_admin(current_user=user)
                print(f"✅ require_admin succeeded: {admin_result.email}")
                self.results['tests']['require_admin'] = {
                    'success': True,
                    'user_email': admin_result.email,
                    'user_role': str(admin_result.role)
                }
            except HTTPException as e:
                print(f"❌ require_admin failed: {e.status_code} - {e.detail}")
                self.results['tests']['require_admin'] = {
                    'success': False,
                    'status_code': e.status_code,
                    'detail': e.detail
                }
            except Exception as e:
                print(f"❌ require_admin error: {e}")
                self.results['tests']['require_admin'] = {
                    'success': False,
                    'error': str(e)
                }
            
            # Test require_super_admin function
            print("Testing require_super_admin dependency...")
            try:
                super_admin_result = await require_super_admin(current_user=user)
                print(f"✅ require_super_admin succeeded: {super_admin_result.email}")
                self.results['tests']['require_super_admin'] = {
                    'success': True,
                    'user_email': super_admin_result.email,
                    'user_role': str(super_admin_result.role)
                }
            except HTTPException as e:
                print(f"❌ require_super_admin failed: {e.status_code} - {e.detail}")
                self.results['tests']['require_super_admin'] = {
                    'success': False,
                    'status_code': e.status_code,
                    'detail': e.detail
                }
            except Exception as e:
                print(f"❌ require_super_admin error: {e}")
                self.results['tests']['require_super_admin'] = {
                    'success': False,
                    'error': str(e)
                }
                
        except Exception as e:
            print(f"❌ Error testing auth dependencies: {e}")
            self.results['tests']['auth_dependencies'] = {'error': str(e)}
    
    async def analyze_enum_consistency(self):
        """Check for UserRole enum consistency issues"""
        print("\n🔍 Analyzing UserRole enum consistency...")
        
        try:
            # Check database enum values
            async with self.async_session() as session:
                result = await session.execute(text("""
                    SELECT enumlabel 
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid 
                    WHERE t.typname = 'userrole'
                    ORDER BY e.enumsortorder;
                """))
                db_enum_values = [row[0] for row in result.fetchall()]
            
            # Check Python enum values
            python_enum_values = [role.value for role in UserRole]
            
            print(f"📊 Database enum values: {db_enum_values}")
            print(f"🐍 Python enum values: {python_enum_values}")
            
            enum_analysis = {
                'database_values': db_enum_values,
                'python_values': python_enum_values,
                'consistent': set(db_enum_values) == set(python_enum_values),
                'missing_in_db': list(set(python_enum_values) - set(db_enum_values)),
                'missing_in_python': list(set(db_enum_values) - set(python_enum_values))
            }
            
            if enum_analysis['consistent']:
                print("✅ UserRole enum values are consistent")
            else:
                print("❌ UserRole enum inconsistency detected!")
                if enum_analysis['missing_in_db']:
                    print(f"   Missing in database: {enum_analysis['missing_in_db']}")
                if enum_analysis['missing_in_python']:
                    print(f"   Missing in Python: {enum_analysis['missing_in_python']}")
            
            self.results['tests']['enum_consistency'] = enum_analysis
            
        except Exception as e:
            print(f"❌ Error analyzing enum consistency: {e}")
            self.results['tests']['enum_consistency'] = {'error': str(e)}
    
    async def check_endpoint_code_paths(self):
        """Analyze the failing endpoint code paths"""
        print("\n🛣️  Analyzing failing endpoint code paths...")
        
        failing_endpoints = [
            '/api/v1/admin/feature-flags',
            '/api/v1/admin/modules', 
            '/api/v1/admin/dashboard/stats'
        ]
        
        # Read the admin.py file to analyze dependencies
        try:
            admin_file_path = "/Users/matt/Sites/MarketEdge/app/api/api_v1/endpoints/admin.py"
            if os.path.exists(admin_file_path):
                with open(admin_file_path, 'r') as f:
                    admin_content = f.read()
                
                endpoint_analysis = {}
                
                # Check each failing endpoint
                for endpoint in failing_endpoints:
                    endpoint_name = endpoint.split('/')[-1]
                    if 'dashboard' in endpoint:
                        endpoint_name = 'dashboard/stats'
                    
                    # Look for the endpoint definition
                    if f'@router.get("/{endpoint_name}")' in admin_content or f'@router.get("/dashboard/stats")' in admin_content:
                        endpoint_analysis[endpoint] = {
                            'found': True,
                            'uses_require_admin': 'Depends(require_admin)' in admin_content,
                            'uses_require_super_admin': 'Depends(require_super_admin)' in admin_content
                        }
                    else:
                        endpoint_analysis[endpoint] = {'found': False}
                
                print("📊 Endpoint dependency analysis:")
                for endpoint, analysis in endpoint_analysis.items():
                    print(f"   {endpoint}: {analysis}")
                
                self.results['tests']['endpoint_analysis'] = endpoint_analysis
                
            else:
                print("❌ Admin endpoint file not found")
                self.results['tests']['endpoint_analysis'] = {'error': 'File not found'}
                
        except Exception as e:
            print(f"❌ Error analyzing endpoint code paths: {e}")
            self.results['tests']['endpoint_analysis'] = {'error': str(e)}
    
    async def generate_analysis_and_recommendations(self):
        """Generate analysis and recommendations based on test results"""
        print("\n📝 Generating analysis and recommendations...")
        
        analysis = {
            'issue_category': 'Authorization Failure',
            'root_cause': 'Unknown - requires investigation',
            'authentication_status': 'Working (user can login)',
            'authorization_status': 'Failing (admin endpoints return 403/500)',
            'critical_findings': []
        }
        
        # Analyze user status
        if 'user_status' in self.results['tests']:
            user_test = self.results['tests']['user_status']
            if user_test.get('found'):
                if user_test.get('role_analysis', {}).get('is_admin_compatible'):
                    analysis['critical_findings'].append("✅ User has admin-compatible role in database")
                else:
                    analysis['critical_findings'].append("❌ User lacks admin role in database")
                    analysis['root_cause'] = "User role insufficient for admin endpoints"
            else:
                analysis['critical_findings'].append("❌ User not found in database")
                analysis['root_cause'] = "User authentication/database sync issue"
        
        # Analyze dependency tests
        if 'require_admin' in self.results['tests']:
            admin_test = self.results['tests']['require_admin']
            if admin_test.get('success'):
                analysis['critical_findings'].append("✅ require_admin dependency works correctly")
            else:
                analysis['critical_findings'].append("❌ require_admin dependency failing")
                analysis['root_cause'] = "Admin authorization logic broken"
        
        # Generate recommendations
        recommendations = []
        
        if analysis['root_cause'] == 'User role insufficient for admin endpoints':
            recommendations.append({
                'priority': 'CRITICAL',
                'action': 'Verify user role promotion completed successfully',
                'command': 'Check database for matt.lindop@zebra.associates role'
            })
        
        elif analysis['root_cause'] == 'Admin authorization logic broken':
            recommendations.append({
                'priority': 'CRITICAL', 
                'action': 'Debug require_admin dependency implementation',
                'command': 'Review app/auth/dependencies.py require_admin function'
            })
        
        else:
            recommendations.extend([
                {
                    'priority': 'HIGH',
                    'action': 'Test admin endpoints with direct authentication',
                    'command': 'Create test script to call admin endpoints with valid JWT token'
                },
                {
                    'priority': 'HIGH',
                    'action': 'Check JWT token structure and claims',
                    'command': 'Decode JWT token to verify role and permissions are correct'
                },
                {
                    'priority': 'MEDIUM',
                    'action': 'Verify Auth0 role mapping configuration',
                    'command': 'Check Auth0 tenant configuration for role assignment'
                }
            ])
        
        self.results['analysis'] = analysis
        self.results['recommendations'] = recommendations
        
        print("🔍 Analysis Summary:")
        print(f"   Root Cause: {analysis['root_cause']}")
        print(f"   Critical Findings: {len(analysis['critical_findings'])}")
        
        print("📋 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. [{rec['priority']}] {rec['action']}")
    
    async def run_full_diagnostic(self):
        """Run complete diagnostic analysis"""
        print("🚀 Starting Selective Admin Endpoint Failure Diagnostic")
        print("=" * 80)
        print(f"Business Context: {self.results['business_context']}")
        print(f"Issue Pattern: {self.results['issue_pattern']}")
        print("=" * 80)
        
        try:
            # Step 1: Database connection
            if not await self.connect_to_database():
                print("❌ Cannot proceed without database connection")
                return False
            
            # Step 2: User verification
            user = await self.verify_user_status()
            if not user:
                print("❌ Cannot proceed without user verification")
                return False
            
            # Step 3: Test auth dependencies
            await self.test_auth_dependencies(user)
            
            # Step 4: Check enum consistency
            await self.analyze_enum_consistency()
            
            # Step 5: Analyze endpoint code paths  
            await self.check_endpoint_code_paths()
            
            # Step 6: Generate analysis
            await self.generate_analysis_and_recommendations()
            
            print("\n✅ Diagnostic completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Diagnostic failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            self.results['diagnostic_error'] = str(e)
            return False
        
        finally:
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"/Users/matt/Sites/MarketEdge/docs/2025_09_18/selective_admin_endpoint_diagnostic_{timestamp}.json"
            
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {results_file}")

async def main():
    """Main execution function"""
    diagnostic = SelectiveEndpointFailureDiagnostic()
    success = await diagnostic.run_full_diagnostic()
    
    if success:
        print("\n🎯 DIAGNOSTIC SUMMARY")
        print("=" * 50)
        
        analysis = diagnostic.results.get('analysis', {})
        print(f"Issue Category: {analysis.get('issue_category', 'Unknown')}")
        print(f"Root Cause: {analysis.get('root_cause', 'Unknown')}")
        
        recommendations = diagnostic.results.get('recommendations', [])
        print(f"\nNext Actions ({len(recommendations)} recommendations):")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. [{rec['priority']}] {rec['action']}")
        
        return True
    else:
        print("\n❌ Diagnostic failed - manual investigation required")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Diagnostic interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)