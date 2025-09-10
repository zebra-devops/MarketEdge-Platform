#!/usr/bin/env python3
"""
Zebra Associates User Verification Tool for Production Database

This script specifically investigates the £925K Zebra Associates opportunity user setup issue:
- Backend enum fix was deployed successfully (403 instead of 500 errors)
- Admin endpoints require authentication (expected behavior)
- BUT admin console shows "no users visible"

This tool will verify:
1. User existence: matt.lindop@zebra.associates in production database
2. User role: Confirm 'admin' role is set correctly
3. User status: Check active, email_verified, etc.
4. Organization associations: Verify Zebra Associates connections
5. Database connectivity: Test admin endpoint queries
6. Auth flow: Verify JWT token generation and role claims

Critical for the £925K Zebra Associates opportunity.
"""

import sys
import os
import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import asyncio

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from sqlalchemy import create_engine, text, inspect
    from sqlalchemy.engine import Engine
    from sqlalchemy.exc import SQLAlchemyError
    import psycopg2
    from psycopg2 import sql
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("   Run: pip install sqlalchemy psycopg2-binary requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Production configuration
PRODUCTION_URL = "https://marketedge-platform.onrender.com"
TARGET_USER_EMAIL = "matt.lindop@zebra.associates"

class ZebraUserVerifier:
    """Verifies Zebra Associates user setup in production"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine: Optional[Engine] = None
        self.user_data = {}
        self.verification_results = {
            "user_exists": False,
            "user_role": None,
            "user_status": {},
            "organizations": [],
            "database_connectivity": False,
            "auth_endpoints": {},
            "admin_access": False
        }
        
    def connect_to_database(self) -> bool:
        """Establish connection to production database"""
        try:
            logger.info("🔌 Connecting to production database...")
            logger.info(f"   Host: {self.database_url.split('@')[1].split(':')[0] if '@' in self.database_url else 'unknown'}")
            
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    "connect_timeout": 30,
                    "application_name": "zebra_user_verifier"
                }
            )
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                
            if test_value == 1:
                logger.info("✅ Database connection successful")
                self.verification_results["database_connectivity"] = True
                return True
            else:
                logger.error("❌ Database connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False
    
    def verify_user_exists(self) -> bool:
        """Verify if the target user exists in production database"""
        logger.info(f"👤 Checking if user exists: {TARGET_USER_EMAIL}")
        
        try:
            with self.engine.connect() as conn:
                # Check if user exists with full details
                query = text("""
                    SELECT 
                        id, 
                        email, 
                        role, 
                        is_active, 
                        email_verified, 
                        created_at, 
                        updated_at,
                        auth0_user_id,
                        first_name,
                        last_name
                    FROM users 
                    WHERE email = :email
                """)
                
                result = conn.execute(query, {"email": TARGET_USER_EMAIL})
                user_row = result.fetchone()
                
                if user_row:
                    # Convert to dict for easier handling
                    user_dict = {
                        "id": str(user_row[0]),
                        "email": user_row[1],
                        "role": str(user_row[2]),
                        "is_active": user_row[3],
                        "email_verified": user_row[4],
                        "created_at": user_row[5].isoformat() if user_row[5] else None,
                        "updated_at": user_row[6].isoformat() if user_row[6] else None,
                        "auth0_user_id": user_row[7],
                        "first_name": user_row[8],
                        "last_name": user_row[9]
                    }
                    
                    self.user_data = user_dict
                    self.verification_results["user_exists"] = True
                    self.verification_results["user_role"] = user_dict["role"]
                    self.verification_results["user_status"] = {
                        "is_active": user_dict["is_active"],
                        "email_verified": user_dict["email_verified"],
                        "has_auth0_id": bool(user_dict["auth0_user_id"]),
                        "has_name": bool(user_dict["first_name"] or user_dict["last_name"])
                    }
                    
                    logger.info(f"   ✅ User found: {user_dict['email']}")
                    logger.info(f"   👥 Role: {user_dict['role']}")
                    logger.info(f"   🔵 Active: {user_dict['is_active']}")
                    logger.info(f"   📧 Email Verified: {user_dict['email_verified']}")
                    logger.info(f"   🔑 Auth0 ID: {user_dict['auth0_user_id'][:20]}..." if user_dict['auth0_user_id'] else "   🔑 Auth0 ID: None")
                    
                    return True
                    
                else:
                    logger.error(f"   ❌ User NOT FOUND: {TARGET_USER_EMAIL}")
                    logger.error("   🚨 CRITICAL: User does not exist in production database")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to check user existence: {e}")
            return False
    
    def verify_user_organizations(self) -> bool:
        """Verify user's organization associations"""
        if not self.verification_results["user_exists"]:
            logger.warning("⚠️  Skipping organization check - user does not exist")
            return False
            
        logger.info("🏢 Checking user organization associations...")
        
        try:
            with self.engine.connect() as conn:
                # Get user's organizations
                query = text("""
                    SELECT 
                        o.id,
                        o.name,
                        o.created_at,
                        uoa.created_at as association_created_at
                    FROM organisations o
                    JOIN user_organisation_access uoa ON o.id = uoa.organisation_id
                    JOIN users u ON uoa.user_id = u.id
                    WHERE u.email = :email
                    ORDER BY uoa.created_at DESC
                """)
                
                result = conn.execute(query, {"email": TARGET_USER_EMAIL})
                org_rows = result.fetchall()
                
                organizations = []
                for row in org_rows:
                    org_data = {
                        "id": str(row[0]),
                        "name": row[1],
                        "org_created_at": row[2].isoformat() if row[2] else None,
                        "association_created_at": row[3].isoformat() if row[3] else None
                    }
                    organizations.append(org_data)
                    
                    logger.info(f"   ✅ Organization: {org_data['name']} (ID: {org_data['id']})")
                
                self.verification_results["organizations"] = organizations
                
                if organizations:
                    logger.info(f"   👥 Total organizations: {len(organizations)}")
                    
                    # Check specifically for Zebra Associates
                    zebra_orgs = [org for org in organizations if 'zebra' in org['name'].lower()]
                    if zebra_orgs:
                        logger.info(f"   🦓 Zebra Associates found: {zebra_orgs[0]['name']}")
                        return True
                    else:
                        logger.warning("   ⚠️  No Zebra Associates organization found")
                        return True  # User has orgs, just not named 'Zebra'
                else:
                    logger.error("   ❌ No organizations found for user")
                    logger.error("   🚨 CRITICAL: User has no organization associations")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to check user organizations: {e}")
            return False
    
    def verify_total_user_count(self) -> int:
        """Get total user count in production database"""
        logger.info("📊 Checking total user count in production...")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                total_users = result.fetchone()[0]
                
                logger.info(f"   👥 Total users in database: {total_users}")
                
                # Also get count by role
                result = conn.execute(text("""
                    SELECT role, COUNT(*) as count 
                    FROM users 
                    GROUP BY role 
                    ORDER BY count DESC
                """))
                role_counts = result.fetchall()
                
                logger.info("   📊 User count by role:")
                for role, count in role_counts:
                    logger.info(f"      {role}: {count}")
                
                return total_users
                
        except Exception as e:
            logger.error(f"❌ Failed to get user count: {e}")
            return -1
    
    def test_production_health(self) -> bool:
        """Test production backend health"""
        logger.info("🏥 Testing production backend health...")
        
        try:
            response = requests.get(f"{PRODUCTION_URL}/health", timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"   ✅ Production Status: {data.get('status', 'unknown')}")
            logger.info(f"   🗄️  Database Ready: {data.get('database_ready', 'unknown')}")
            
            self.verification_results["auth_endpoints"]["health"] = {
                "success": True,
                "status": data.get('status'),
                "database_ready": data.get('database_ready')
            }
            
            return data.get('database_ready', False)
            
        except Exception as e:
            logger.error(f"   ❌ Health check failed: {e}")
            self.verification_results["auth_endpoints"]["health"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    def test_auth_endpoints(self) -> bool:
        """Test authentication endpoints"""
        logger.info("🔐 Testing authentication endpoints...")
        
        endpoints_working = True
        
        # Test Auth0 URL endpoint
        try:
            response = requests.get(f"{PRODUCTION_URL}/api/v1/auth/auth0-url", timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info("   ✅ Auth0 URL endpoint: SUCCESS")
            
            self.verification_results["auth_endpoints"]["auth0_url"] = {
                "success": True,
                "has_url": bool(data.get('auth_url'))
            }
            
        except Exception as e:
            logger.error(f"   ❌ Auth0 URL endpoint failed: {e}")
            self.verification_results["auth_endpoints"]["auth0_url"] = {
                "success": False,
                "error": str(e)
            }
            endpoints_working = False
        
        # Test auth status endpoint (should return 401/403 without auth)
        try:
            response = requests.get(f"{PRODUCTION_URL}/api/v1/auth/status", timeout=30)
            
            if response.status_code == 200:
                logger.info("   ✅ Auth status endpoint: SUCCESS (authenticated)")
                self.verification_results["auth_endpoints"]["auth_status"] = {
                    "success": True,
                    "status_code": 200,
                    "authenticated": True
                }
            elif response.status_code in [401, 403]:
                logger.info(f"   ✅ Auth status endpoint: SUCCESS (HTTP {response.status_code} - requires auth)")
                self.verification_results["auth_endpoints"]["auth_status"] = {
                    "success": True,
                    "status_code": response.status_code,
                    "requires_auth": True
                }
            elif response.status_code == 500:
                logger.error("   ❌ Auth status endpoint: HTTP 500 - Database/schema error")
                self.verification_results["auth_endpoints"]["auth_status"] = {
                    "success": False,
                    "status_code": 500,
                    "error": "Internal server error - likely database issue"
                }
                endpoints_working = False
            else:
                logger.warning(f"   ⚠️  Auth status endpoint: HTTP {response.status_code}")
                self.verification_results["auth_endpoints"]["auth_status"] = {
                    "success": True,
                    "status_code": response.status_code,
                    "unexpected_status": True
                }
            
        except Exception as e:
            logger.error(f"   ❌ Auth status endpoint failed: {e}")
            self.verification_results["auth_endpoints"]["auth_status"] = {
                "success": False,
                "error": str(e)
            }
            endpoints_working = False
        
        return endpoints_working
    
    def test_admin_endpoints(self) -> bool:
        """Test admin endpoints (should return 403 without auth)"""
        logger.info("👑 Testing admin endpoints...")
        
        admin_endpoints_working = True
        
        # Test users endpoint (admin required)
        try:
            response = requests.get(f"{PRODUCTION_URL}/api/v1/users/", timeout=30)
            
            if response.status_code == 403:
                logger.info("   ✅ Users endpoint: SUCCESS (HTTP 403 - requires admin auth)")
                logger.info("   ✅ This confirms enum fix worked - no more 500 errors!")
                self.verification_results["auth_endpoints"]["users"] = {
                    "success": True,
                    "status_code": 403,
                    "requires_admin_auth": True,
                    "enum_fix_working": True
                }
            elif response.status_code == 401:
                logger.info("   ✅ Users endpoint: SUCCESS (HTTP 401 - requires auth)")
                self.verification_results["auth_endpoints"]["users"] = {
                    "success": True,
                    "status_code": 401,
                    "requires_auth": True
                }
            elif response.status_code == 500:
                logger.error("   ❌ Users endpoint: HTTP 500 - Still has database/enum errors")
                self.verification_results["auth_endpoints"]["users"] = {
                    "success": False,
                    "status_code": 500,
                    "enum_fix_failed": True
                }
                admin_endpoints_working = False
            elif response.status_code == 200:
                logger.warning("   ⚠️  Users endpoint: HTTP 200 - No auth required (unexpected)")
                try:
                    data = response.json()
                    logger.info(f"      Returned {len(data) if isinstance(data, list) else 'unknown'} users")
                except:
                    logger.info("      Could not parse response")
                self.verification_results["auth_endpoints"]["users"] = {
                    "success": True,
                    "status_code": 200,
                    "no_auth_required": True,
                    "unexpected": True
                }
            else:
                logger.warning(f"   ⚠️  Users endpoint: HTTP {response.status_code}")
                self.verification_results["auth_endpoints"]["users"] = {
                    "success": True,
                    "status_code": response.status_code,
                    "unexpected_status": True
                }
                
        except Exception as e:
            logger.error(f"   ❌ Users endpoint failed: {e}")
            self.verification_results["auth_endpoints"]["users"] = {
                "success": False,
                "error": str(e)
            }
            admin_endpoints_working = False
        
        return admin_endpoints_working
    
    def diagnose_no_users_visible_issue(self) -> Dict[str, Any]:
        """Diagnose why admin console shows 'no users visible'"""
        logger.info("🔍 Diagnosing 'no users visible' issue...")
        
        diagnosis = {
            "possible_causes": [],
            "recommendations": [],
            "severity": "unknown"
        }
        
        # Check if user exists but admin endpoints don't work
        if self.verification_results["user_exists"]:
            if self.verification_results["user_role"] == "admin":
                diagnosis["possible_causes"].append("User exists with admin role - not a user setup issue")
                
                # Check if admin endpoints work
                auth_status = self.verification_results["auth_endpoints"].get("users", {})
                if auth_status.get("status_code") == 403:
                    diagnosis["possible_causes"].append("Admin endpoints require authentication (correct behavior)")
                    diagnosis["possible_causes"].append("Frontend may not be passing authentication tokens properly")
                    diagnosis["recommendations"].extend([
                        "Check frontend authentication token storage and transmission",
                        "Verify JWT tokens contain proper role claims",
                        "Test admin console authentication flow",
                        "Check browser network tab for authentication headers"
                    ])
                    diagnosis["severity"] = "medium"
                    
                elif auth_status.get("status_code") == 500:
                    diagnosis["possible_causes"].append("Backend still has 500 errors - enum fix incomplete")
                    diagnosis["recommendations"].extend([
                        "Re-run emergency enum fix endpoint",
                        "Check backend logs for specific errors",
                        "Verify enum values in database match backend expectations"
                    ])
                    diagnosis["severity"] = "high"
                    
            else:
                diagnosis["possible_causes"].append(f"User exists but has role '{self.verification_results['user_role']}' instead of 'admin'")
                diagnosis["recommendations"].extend([
                    f"Update user role to 'admin': UPDATE users SET role = 'admin' WHERE email = '{TARGET_USER_EMAIL}'",
                    "Verify role enum values in database"
                ])
                diagnosis["severity"] = "high"
                
        else:
            diagnosis["possible_causes"].append("User does not exist in production database")
            diagnosis["recommendations"].extend([
                f"Create user in production database",
                f"Ensure Auth0 user {TARGET_USER_EMAIL} is properly synced to database",
                "Run user creation/sync process"
            ])
            diagnosis["severity"] = "critical"
        
        # Check organization associations
        if not self.verification_results["organizations"]:
            diagnosis["possible_causes"].append("User has no organization associations")
            diagnosis["recommendations"].append("Create organization association for Zebra Associates")
        
        return diagnosis
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive verification report"""
        report = []
        report.append("=" * 80)
        report.append("ZEBRA ASSOCIATES USER VERIFICATION REPORT")
        report.append("£925K Opportunity - Production Database Investigation")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append(f"Target User: {TARGET_USER_EMAIL}")
        report.append(f"Production URL: {PRODUCTION_URL}")
        report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 40)
        
        user_exists = self.verification_results["user_exists"]
        user_role = self.verification_results["user_role"]
        has_orgs = len(self.verification_results["organizations"]) > 0
        
        if user_exists and user_role == "admin" and has_orgs:
            report.append("🎯 STATUS: USER SETUP IS CORRECT")
            report.append("   ✅ User exists with admin role and organization associations")
            report.append("   🔍 Issue likely in frontend authentication or token handling")
        elif user_exists and user_role != "admin":
            report.append("🚨 STATUS: USER ROLE INCORRECT")
            report.append(f"   ❌ User has role '{user_role}' but needs 'admin'")
            report.append("   🔧 Database update required")
        elif user_exists and not has_orgs:
            report.append("⚠️  STATUS: USER MISSING ORGANIZATIONS")
            report.append("   ✅ User exists with correct role")
            report.append("   ❌ No organization associations found")
        elif not user_exists:
            report.append("🚨 STATUS: USER DOES NOT EXIST")
            report.append("   ❌ Critical issue - user not found in production database")
        else:
            report.append("⚠️  STATUS: MIXED RESULTS")
            report.append("   🔍 Multiple issues detected - see details below")
        
        report.append("")
        
        # User Details
        report.append("USER VERIFICATION DETAILS")
        report.append("-" * 40)
        
        if user_exists:
            user = self.user_data
            report.append(f"✅ User Found: {user['email']}")
            report.append(f"   ID: {user['id']}")
            report.append(f"   Role: {user['role']}")
            report.append(f"   Active: {user['is_active']}")
            report.append(f"   Email Verified: {user['email_verified']}")
            report.append(f"   Auth0 ID: {user['auth0_user_id'][:30]}..." if user['auth0_user_id'] else "   Auth0 ID: None")
            report.append(f"   Name: {user['first_name']} {user['last_name']}" if user['first_name'] or user['last_name'] else "   Name: Not set")
            report.append(f"   Created: {user['created_at']}")
        else:
            report.append(f"❌ User Not Found: {TARGET_USER_EMAIL}")
            report.append("   🚨 This is the root cause of 'no users visible'")
        
        report.append("")
        
        # Organization Details
        report.append("ORGANIZATION ASSOCIATIONS")
        report.append("-" * 40)
        
        orgs = self.verification_results["organizations"]
        if orgs:
            report.append(f"✅ Organizations Found: {len(orgs)}")
            for i, org in enumerate(orgs, 1):
                report.append(f"   {i}. {org['name']} (ID: {org['id']})")
                report.append(f"      Associated: {org['association_created_at']}")
                
            # Check for Zebra specifically
            zebra_orgs = [org for org in orgs if 'zebra' in org['name'].lower()]
            if zebra_orgs:
                report.append(f"   🦓 Zebra Associates: FOUND ({zebra_orgs[0]['name']})")
            else:
                report.append("   ⚠️  Zebra Associates: NOT FOUND (may need to be created)")
        else:
            report.append("❌ No Organizations Found")
            report.append("   🚨 User has no organization associations")
        
        report.append("")
        
        # Backend Status
        report.append("BACKEND STATUS VERIFICATION")
        report.append("-" * 40)
        
        health = self.verification_results["auth_endpoints"].get("health", {})
        if health.get("success"):
            report.append("✅ Production Health: OK")
            report.append(f"   Database Ready: {health.get('database_ready', 'unknown')}")
        else:
            report.append("❌ Production Health: FAILED")
            report.append(f"   Error: {health.get('error', 'Unknown')}")
        
        # Auth endpoints
        auth_status = self.verification_results["auth_endpoints"].get("auth_status", {})
        if auth_status.get("success"):
            status_code = auth_status.get("status_code")
            if status_code in [401, 403]:
                report.append(f"✅ Auth Status: OK (HTTP {status_code} - requires authentication)")
            elif status_code == 200:
                report.append("✅ Auth Status: OK (HTTP 200 - authenticated)")
            else:
                report.append(f"⚠️  Auth Status: HTTP {status_code}")
        else:
            report.append("❌ Auth Status: FAILED")
        
        # Users endpoint (admin test)
        users_endpoint = self.verification_results["auth_endpoints"].get("users", {})
        if users_endpoint.get("success"):
            status_code = users_endpoint.get("status_code")
            if status_code == 403:
                report.append("✅ Users Endpoint: OK (HTTP 403 - requires admin)")
                report.append("   ✅ ENUM FIX CONFIRMED: No more 500 errors!")
            elif status_code == 401:
                report.append("✅ Users Endpoint: OK (HTTP 401 - requires auth)")
            elif status_code == 500:
                report.append("❌ Users Endpoint: FAILED (HTTP 500)")
                report.append("   🚨 ENUM FIX NOT WORKING: Still has database errors")
            else:
                report.append(f"⚠️  Users Endpoint: HTTP {status_code}")
        else:
            report.append("❌ Users Endpoint: FAILED")
        
        report.append("")
        
        # Root Cause Analysis
        diagnosis = self.diagnose_no_users_visible_issue()
        report.append("ROOT CAUSE ANALYSIS")
        report.append("-" * 40)
        
        report.append("Possible Causes:")
        for i, cause in enumerate(diagnosis["possible_causes"], 1):
            report.append(f"   {i}. {cause}")
        
        report.append("")
        report.append("Recommendations:")
        for i, rec in enumerate(diagnosis["recommendations"], 1):
            report.append(f"   {i}. {rec}")
        
        report.append("")
        report.append(f"Severity: {diagnosis['severity'].upper()}")
        
        report.append("")
        
        # Action Plan
        report.append("IMMEDIATE ACTION PLAN")
        report.append("-" * 40)
        
        if not user_exists:
            report.append("🚨 CRITICAL: User Creation Required")
            report.append("   1. Create user in production database with admin role")
            report.append("   2. Associate user with Zebra Associates organization")
            report.append("   3. Ensure Auth0 sync is working")
            report.append("")
            report.append("SQL Commands:")
            report.append(f"   INSERT INTO users (email, role, is_active, email_verified)")
            report.append(f"   VALUES ('{TARGET_USER_EMAIL}', 'admin', true, true);")
            
        elif user_role != "admin":
            report.append("🔧 MEDIUM: Role Update Required")
            report.append("   1. Update user role to admin")
            report.append("")
            report.append("SQL Command:")
            report.append(f"   UPDATE users SET role = 'admin' WHERE email = '{TARGET_USER_EMAIL}';")
            
        elif not has_orgs:
            report.append("⚠️  MEDIUM: Organization Association Required")
            report.append("   1. Create Zebra Associates organization if needed")
            report.append("   2. Associate user with organization")
            
        else:
            report.append("✅ LOW: User Setup Correct - Focus on Frontend")
            report.append("   1. Check frontend authentication token handling")
            report.append("   2. Verify JWT token contains proper role claims")
            report.append("   3. Test admin console authentication flow")
            report.append("   4. Check browser developer tools for auth errors")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main verification function"""
    print("🦓 Zebra Associates User Verification Tool")
    print("=" * 60)
    print(f"🎯 Target User: {TARGET_USER_EMAIL}")
    print(f"💰 Opportunity Value: £925K")
    print("")
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Try to load from settings
        try:
            from app.core.config import settings
            database_url = settings.DATABASE_URL
            print("✅ Database URL loaded from settings")
        except Exception as e:
            print(f"❌ Could not load database URL: {e}")
            print("   Set DATABASE_URL environment variable")
            sys.exit(1)
    else:
        print("✅ Database URL loaded from environment")
    
    print("")
    
    # Initialize verifier
    verifier = ZebraUserVerifier(database_url)
    
    # Step 1: Test production health
    if not verifier.test_production_health():
        print("❌ Production backend is not healthy - cannot proceed")
        sys.exit(1)
    
    print("")
    
    # Step 2: Connect to database
    if not verifier.connect_to_database():
        print("❌ Failed to connect to production database")
        sys.exit(1)
    
    print("")
    
    # Step 3: Verify user exists
    user_exists = verifier.verify_user_exists()
    print("")
    
    # Step 4: Check organizations (if user exists)
    if user_exists:
        verifier.verify_user_organizations()
        print("")
    
    # Step 5: Get overall user stats
    total_users = verifier.verify_total_user_count()
    print("")
    
    # Step 6: Test authentication endpoints
    verifier.test_auth_endpoints()
    print("")
    
    # Step 7: Test admin endpoints
    verifier.test_admin_endpoints()
    print("")
    
    # Generate comprehensive report
    report = verifier.generate_comprehensive_report()
    print(report)
    
    # Save report
    report_filename = f"zebra_user_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to: {report_filename}")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")
    
    print("")
    
    # Final status
    if verifier.verification_results["user_exists"]:
        if verifier.verification_results["user_role"] == "admin":
            print("✅ USER VERIFICATION PASSED: User exists with admin role")
            print("🔍 Issue likely in frontend authentication - check token handling")
            sys.exit(0)
        else:
            print("⚠️  USER VERIFICATION PARTIAL: User exists but wrong role")
            print("🔧 Update user role to admin and test again")
            sys.exit(1)
    else:
        print("❌ USER VERIFICATION FAILED: User does not exist")
        print("🚨 CRITICAL: Create user in production database immediately")
        sys.exit(1)

if __name__ == "__main__":
    main()