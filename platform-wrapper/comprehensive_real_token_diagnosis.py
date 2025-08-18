#!/usr/bin/env python3
"""
Comprehensive Real Auth0 Token Diagnosis
========================================

This script performs a complete end-to-end diagnosis of the authentication failure
with real Auth0 tokens, combining Auth0 API analysis with database testing.

CRITICAL SITUATION ANALYSIS:
- Real Auth0 tokens: Pass token exchange → Get user info → FAIL at database (500)
- Test codes: Fail at token exchange → Never reach database (400)

This script will:
1. Test Auth0 API with real tokens to capture user info structure
2. Test database operations with realistic user data
3. Identify the exact failure point in the authentication flow
4. Provide specific recommendations for fixing the issue
"""

import asyncio
import httpx
import json
import os
import sys
import traceback
from typing import Dict, Any, Optional

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


class ComprehensiveAuthDiagnosis:
    """Complete diagnosis of Auth0 + Database authentication failures"""
    
    def __init__(self):
        # Auth0 Configuration
        self.domain = os.getenv('AUTH0_DOMAIN', 'dev-ph7m31mc6y5yxsw2.us.auth0.com')
        self.client_id = os.getenv('AUTH0_CLIENT_ID')
        self.client_secret = os.getenv('AUTH0_CLIENT_SECRET')
        self.base_url = f"https://{self.domain}"
        
        # Database Configuration  
        self.database_url = os.getenv(
            'DATABASE_URL', 
            'postgresql://postgres:password@localhost:5432/marketedge'
        )
        
        if not self.client_id or not self.client_secret:
            print("❌ ERROR: AUTH0_CLIENT_ID and AUTH0_CLIENT_SECRET must be set")
            exit(1)
    
    async def diagnose_auth0_flow(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Diagnose Auth0 API flow and capture user info"""
        print("\n🔍 PHASE 1: Auth0 Flow Diagnosis")
        print("-" * 40)
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                print("📡 Testing Auth0 userinfo endpoint...")
                response = await client.get(
                    f"{self.base_url}/userinfo",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                print(f"   Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    user_info = response.json()
                    print(f"   ✅ Auth0 API Success")
                    print(f"   📊 User Info Fields: {list(user_info.keys())}")
                    
                    # Analyze critical fields
                    print(f"\n📋 Critical Field Analysis:")
                    print(f"   Email: {user_info.get('email', 'MISSING')}")
                    print(f"   Sub (ID): {user_info.get('sub', 'MISSING')}")
                    print(f"   Given Name: '{user_info.get('given_name', 'MISSING')}'")
                    print(f"   Family Name: '{user_info.get('family_name', 'MISSING')}'")
                    print(f"   Email Verified: {user_info.get('email_verified', 'MISSING')}")
                    
                    return user_info
                else:
                    print(f"   ❌ Auth0 API Failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return None
                    
            except Exception as e:
                print(f"   ❌ Auth0 API Exception: {type(e).__name__}: {str(e)}")
                return None
    
    def diagnose_database_compatibility(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnose database compatibility issues"""
        print(f"\n🔍 PHASE 2: Database Compatibility Analysis")
        print("-" * 40)
        
        # Extract and sanitize data exactly like the auth endpoint
        email = user_info.get('email', '').strip() if user_info.get('email') else ''
        given_name = user_info.get('given_name', '').strip() if user_info.get('given_name') else ''
        family_name = user_info.get('family_name', '').strip() if user_info.get('family_name') else ''
        
        print(f"📊 Sanitized Data Analysis:")
        print(f"   Email: '{email}' (length: {len(email)})")
        print(f"   Given Name: '{given_name}' (length: {len(given_name)})")  
        print(f"   Family Name: '{family_name}' (length: {len(family_name)})")
        
        # Identify potential issues
        issues = []
        warnings = []
        
        # Email validation
        if not email:
            issues.append("CRITICAL: Empty email after sanitization")
        elif len(email) > 254:
            issues.append(f"CRITICAL: Email too long ({len(email)} chars, max 254)")
        elif '@' not in email:
            issues.append("CRITICAL: Invalid email format")
        
        # Name validation
        if not given_name and not family_name:
            warnings.append("WARNING: Both names are empty")
        
        if len(given_name) > 100:
            issues.append(f"CRITICAL: Given name too long ({len(given_name)} chars, max 100)")
        
        if len(family_name) > 100:
            issues.append(f"CRITICAL: Family name too long ({len(family_name)} chars, max 100)")
        
        # Character encoding issues
        try:
            email.encode('utf-8')
            given_name.encode('utf-8')
            family_name.encode('utf-8')
        except UnicodeEncodeError:
            issues.append("CRITICAL: Non-UTF8 characters in user data")
        
        # Report findings
        if issues:
            print(f"🚨 CRITICAL ISSUES FOUND ({len(issues)}):")
            for issue in issues:
                print(f"   ❌ {issue}")
        
        if warnings:
            print(f"⚠️ WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"   ⚠️ {warning}")
        
        if not issues and not warnings:
            print(f"✅ No obvious data compatibility issues found")
        
        return {
            "sanitized_data": {
                "email": email,
                "given_name": given_name,
                "family_name": family_name
            },
            "issues": issues,
            "warnings": warnings,
            "compatible": len(issues) == 0
        }
    
    def test_database_operations(self, sanitized_data: Dict[str, str]) -> Dict[str, Any]:
        """Test actual database operations"""
        print(f"\n🔍 PHASE 3: Database Operations Testing")
        print("-" * 40)
        
        try:
            # Import database components
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import sessionmaker
            from backend.app.models.user import User, UserRole
            from backend.app.models.organisation import Organisation, SubscriptionPlan
            from backend.app.core.rate_limit_config import Industry
            
            print(f"📡 Testing database connection...")
            engine = create_engine(self.database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"   ✅ Database connection successful")
            
            # Test user operations
            db = SessionLocal()
            try:
                email = sanitized_data["email"]
                given_name = sanitized_data["given_name"]
                family_name = sanitized_data["family_name"]
                
                print(f"🔍 Testing user lookup...")
                existing_user = db.query(User).filter(User.email == email).first()
                if existing_user:
                    print(f"   ℹ️ User already exists: {existing_user.id}")
                    return {
                        "success": True,
                        "operation": "user_exists",
                        "user_id": str(existing_user.id)
                    }
                
                print(f"🔍 Testing organization lookup/creation...")
                default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
                if not default_org:
                    print(f"   Creating default organization...")
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
                else:
                    print(f"   ✅ Default org exists: {default_org.id}")
                
                print(f"🔍 Testing user creation...")
                test_user = User(
                    email=email,
                    first_name=given_name,
                    last_name=family_name,
                    organisation_id=default_org.id,
                    role=UserRole.viewer
                )
                
                db.add(test_user)
                db.commit()
                db.refresh(test_user)
                print(f"   ✅ User created successfully: {test_user.id}")
                
                # Clean up test user
                db.delete(test_user)
                db.commit()
                print(f"   🧹 Test user cleaned up")
                
                return {
                    "success": True,
                    "operation": "user_created_and_cleaned",
                    "user_id": str(test_user.id)
                }
                
            except Exception as db_error:
                db.rollback()
                print(f"   ❌ Database operation failed: {type(db_error).__name__}")
                print(f"   Error details: {str(db_error)}")
                
                # Capture specific SQLAlchemy error details
                error_details = {
                    "error_type": type(db_error).__name__,
                    "error_message": str(db_error),
                    "error_code": getattr(db_error, 'code', None),
                    "error_orig": str(getattr(db_error, 'orig', None))
                }
                
                return {
                    "success": False,
                    "operation": "database_error",
                    "error_details": error_details
                }
            finally:
                db.close()
                
        except ImportError as e:
            print(f"   ❌ Import Error: {str(e)}")
            return {
                "success": False,
                "operation": "import_error", 
                "error_details": str(e)
            }
        except Exception as e:
            print(f"   ❌ Unexpected Error: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "operation": "unexpected_error",
                "error_details": str(e)
            }
    
    async def run_comprehensive_diagnosis(self, access_token: str) -> Dict[str, Any]:
        """Run complete diagnosis"""
        print("🚀 COMPREHENSIVE REAL TOKEN DIAGNOSIS")
        print("=" * 60)
        
        results = {
            "auth0_success": False,
            "database_compatible": False,
            "database_operations_success": False,
            "root_cause": None,
            "recommendations": []
        }
        
        # Phase 1: Auth0 Flow
        user_info = await self.diagnose_auth0_flow(access_token)
        if not user_info:
            results["root_cause"] = "Auth0 API failure"
            results["recommendations"] = ["Check Auth0 token validity", "Verify Auth0 configuration"]
            return results
        
        results["auth0_success"] = True
        
        # Phase 2: Database Compatibility
        compatibility = self.diagnose_database_compatibility(user_info)
        results["database_compatible"] = compatibility["compatible"]
        
        if not compatibility["compatible"]:
            results["root_cause"] = "User data incompatible with database schema"
            results["recommendations"] = [
                "Fix data validation in authentication endpoint",
                "Handle edge cases in user data processing",
                f"Address issues: {', '.join(compatibility['issues'])}"
            ]
            return results
        
        # Phase 3: Database Operations
        db_test = self.test_database_operations(compatibility["sanitized_data"])
        results["database_operations_success"] = db_test["success"]
        
        if not db_test["success"]:
            results["root_cause"] = f"Database operation failure: {db_test.get('operation', 'unknown')}"
            results["recommendations"] = [
                "Check database connection and permissions",
                "Review SQLAlchemy model constraints",
                "Investigate specific database error",
                f"Error details: {db_test.get('error_details', 'No details')}"
            ]
        else:
            results["root_cause"] = "No issues found in isolated testing"
            results["recommendations"] = [
                "Issue may be environment-specific",
                "Check production database constraints", 
                "Investigate concurrent user creation",
                "Review transaction isolation settings"
            ]
        
        return results
    
    def print_final_report(self, results: Dict[str, Any]) -> None:
        """Print comprehensive final report"""
        print(f"\n📊 FINAL DIAGNOSIS REPORT")
        print("=" * 60)
        
        print(f"🔍 Test Results:")
        print(f"   Auth0 API: {'✅ Success' if results['auth0_success'] else '❌ Failed'}")
        print(f"   Data Compatibility: {'✅ Compatible' if results['database_compatible'] else '❌ Incompatible'}")  
        print(f"   Database Operations: {'✅ Success' if results['database_operations_success'] else '❌ Failed'}")
        
        print(f"\n🎯 Root Cause: {results['root_cause']}")
        
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n🔧 Next Steps:")
        if results['database_operations_success']:
            print("   1. Issue is likely environment-specific (production vs local)")
            print("   2. Check production logs for exact SQLAlchemy error") 
            print("   3. Compare production and local database schemas")
            print("   4. Test with actual production environment variables")
        else:
            print("   1. Fix the identified database issue")
            print("   2. Test locally with the same data")
            print("   3. Deploy fix to production")
            print("   4. Verify with real Auth0 token")


async def main():
    """Main diagnosis function"""
    print("📝 INSTRUCTIONS:")
    print("1. Get a fresh Auth0 access token")
    print("2. Use Auth0 dashboard or 'clear session and get fresh code'")
    print("3. Paste the access token below for comprehensive analysis")
    
    access_token = input("\n🔐 Enter Auth0 access token: ").strip()
    
    if not access_token:
        print("❌ No access token provided")
        return
    
    diagnosis = ComprehensiveAuthDiagnosis()
    results = await diagnosis.run_comprehensive_diagnosis(access_token)
    diagnosis.print_final_report(results)


if __name__ == "__main__":
    asyncio.run(main())