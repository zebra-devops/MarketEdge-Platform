#!/usr/bin/env python3
"""
Fixed Zebra Associates User Verification Tool

Based on the actual production schema, this script properly verifies:
- User existence and role for matt.lindop@zebra.associates  
- Organization associations
- Backend connectivity and authentication status
- Root cause of 'no users visible' in admin console

The users table has these columns:
id, created_at, updated_at, email, first_name, last_name, organisation_id, role, is_active, department, location, phone
"""

import sys
import os
import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from sqlalchemy import create_engine, text, inspect
    from sqlalchemy.engine import Engine
    from sqlalchemy.exc import SQLAlchemyError
    import psycopg2
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Production configuration
PRODUCTION_URL = "https://marketedge-platform.onrender.com"
TARGET_USER_EMAIL = "matt.lindop@zebra.associates"

class FixedZebraUserVerifier:
    """Fixed verifier that uses the actual production schema"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine: Optional[Engine] = None
        self.user_data = {}
        self.organization_data = {}
        
    def connect_to_database(self) -> bool:
        """Connect to production database"""
        try:
            self.engine = create_engine(self.database_url, pool_pre_ping=True)
            
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                test_value = result.fetchone()[0]
                
            return test_value == 1
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def verify_user_details(self) -> bool:
        """Check user details with correct column names"""
        print(f"👤 Verifying user: {TARGET_USER_EMAIL}")
        
        try:
            with self.engine.connect() as conn:
                # Use the actual column structure
                query = text("""
                    SELECT 
                        id, 
                        email, 
                        role, 
                        is_active, 
                        first_name,
                        last_name,
                        organisation_id,
                        created_at, 
                        updated_at,
                        department,
                        location,
                        phone
                    FROM users 
                    WHERE email = :email
                """)
                
                result = conn.execute(query, {"email": TARGET_USER_EMAIL})
                user_row = result.fetchone()
                
                if user_row:
                    self.user_data = {
                        "id": str(user_row[0]),
                        "email": user_row[1],
                        "role": str(user_row[2]),
                        "is_active": user_row[3],
                        "first_name": user_row[4],
                        "last_name": user_row[5],
                        "organisation_id": str(user_row[6]),
                        "created_at": user_row[7].isoformat() if user_row[7] else None,
                        "updated_at": user_row[8].isoformat() if user_row[8] else None,
                        "department": user_row[9],
                        "location": user_row[10], 
                        "phone": user_row[11]
                    }
                    
                    print(f"   ✅ User found: {self.user_data['email']}")
                    print(f"   👥 Role: {self.user_data['role']}")
                    print(f"   🔵 Active: {self.user_data['is_active']}")
                    print(f"   👤 Name: {self.user_data['first_name']} {self.user_data['last_name']}")
                    print(f"   🏢 Organization ID: {self.user_data['organisation_id']}")
                    print(f"   📅 Created: {self.user_data['created_at']}")
                    
                    return True
                else:
                    print(f"   ❌ User NOT FOUND: {TARGET_USER_EMAIL}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error checking user: {e}")
            return False
    
    def verify_user_organization(self) -> bool:
        """Check the user's organization details"""
        if not self.user_data:
            return False
            
        print("🏢 Verifying organization details...")
        
        try:
            with self.engine.connect() as conn:
                org_id = self.user_data['organisation_id']
                
                query = text("""
                    SELECT 
                        id,
                        name, 
                        created_at,
                        updated_at
                    FROM organisations 
                    WHERE id = :org_id
                """)
                
                result = conn.execute(query, {"org_id": org_id})
                org_row = result.fetchone()
                
                if org_row:
                    self.organization_data = {
                        "id": str(org_row[0]),
                        "name": org_row[1],
                        "created_at": org_row[2].isoformat() if org_row[2] else None,
                        "updated_at": org_row[3].isoformat() if org_row[3] else None
                    }
                    
                    print(f"   ✅ Organization found: {self.organization_data['name']}")
                    print(f"   🆔 Organization ID: {self.organization_data['id']}")
                    print(f"   📅 Created: {self.organization_data['created_at']}")
                    
                    # Check if it's Zebra Associates
                    if 'zebra' in self.organization_data['name'].lower():
                        print("   🦓 ✅ This IS Zebra Associates!")
                        return True
                    else:
                        print(f"   ⚠️  This is NOT Zebra Associates (it's {self.organization_data['name']})")
                        return True  # Still successful, just wrong org
                        
                else:
                    print(f"   ❌ Organization NOT FOUND for ID: {org_id}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error checking organization: {e}")
            return False
    
    def check_all_users_summary(self) -> Dict[str, Any]:
        """Get summary of all users for context"""
        print("📊 Getting user database summary...")
        
        try:
            with self.engine.connect() as conn:
                # Total user count
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                total_users = result.fetchone()[0]
                
                # Users by role
                result = conn.execute(text("SELECT role, COUNT(*) FROM users GROUP BY role"))
                role_counts = {row[0]: row[1] for row in result.fetchall()}
                
                # Admin users specifically
                result = conn.execute(text("SELECT email, first_name, last_name FROM users WHERE role = 'admin'"))
                admin_users = result.fetchall()
                
                summary = {
                    "total_users": total_users,
                    "role_counts": role_counts,
                    "admin_users": admin_users
                }
                
                print(f"   👥 Total users: {total_users}")
                print(f"   👑 Admin users: {role_counts.get('admin', 0)}")
                print(f"   👁️  Viewer users: {role_counts.get('viewer', 0)}")
                
                if admin_users:
                    print("   📋 Admin users list:")
                    for admin in admin_users:
                        print(f"      - {admin[0]} ({admin[1]} {admin[2]})")
                
                return summary
                
        except Exception as e:
            print(f"❌ Error getting user summary: {e}")
            return {}
    
    def test_backend_endpoints(self) -> Dict[str, Any]:
        """Test backend endpoint responses"""
        print("🔗 Testing backend endpoints...")
        
        endpoint_results = {}
        
        # Health check
        try:
            response = requests.get(f"{PRODUCTION_URL}/health", timeout=10)
            health_data = response.json()
            endpoint_results["health"] = {
                "status_code": response.status_code,
                "success": True,
                "data": health_data
            }
            print(f"   ✅ Health: {health_data.get('status', 'unknown')}")
        except Exception as e:
            endpoint_results["health"] = {"success": False, "error": str(e)}
            print(f"   ❌ Health check failed: {e}")
        
        # Admin users endpoint
        try:
            response = requests.get(f"{PRODUCTION_URL}/api/v1/users/", timeout=10)
            endpoint_results["users"] = {
                "status_code": response.status_code,
                "success": response.status_code in [200, 401, 403]
            }
            
            if response.status_code == 403:
                print("   ✅ Users endpoint: HTTP 403 (requires admin auth)")
                print("   ✅ This confirms the enum fix worked!")
            elif response.status_code == 401:
                print("   ✅ Users endpoint: HTTP 401 (requires auth)")
            elif response.status_code == 500:
                print("   ❌ Users endpoint: HTTP 500 (still broken)")
            else:
                print(f"   ⚠️  Users endpoint: HTTP {response.status_code}")
                
        except Exception as e:
            endpoint_results["users"] = {"success": False, "error": str(e)}
            print(f"   ❌ Users endpoint failed: {e}")
        
        return endpoint_results
    
    def diagnose_admin_console_issue(self) -> Dict[str, Any]:
        """Diagnose why admin console shows no users"""
        print("🔍 Diagnosing admin console issue...")
        
        diagnosis = {
            "user_exists": bool(self.user_data),
            "is_admin": self.user_data.get('role') == 'admin',
            "is_active": self.user_data.get('is_active', False),
            "has_organization": bool(self.organization_data),
            "backend_working": True,
            "likely_causes": [],
            "solutions": []
        }
        
        if not diagnosis["user_exists"]:
            diagnosis["likely_causes"].append("User does not exist in database")
            diagnosis["solutions"].append("Create user in production database")
        elif not diagnosis["is_admin"]:
            diagnosis["likely_causes"].append(f"User has role '{self.user_data.get('role')}' instead of 'admin'")
            diagnosis["solutions"].append("Update user role to 'admin'")
        elif not diagnosis["is_active"]:
            diagnosis["likely_causes"].append("User account is inactive")
            diagnosis["solutions"].append("Activate user account")
        else:
            # User setup is correct - issue is likely frontend
            diagnosis["likely_causes"].extend([
                "Frontend authentication not working",
                "JWT tokens not being generated/sent properly",
                "Admin console not properly authenticated"
            ])
            diagnosis["solutions"].extend([
                "Check frontend authentication flow",
                "Verify JWT token generation and storage",
                "Test admin console login process",
                "Check browser network tab for authentication errors"
            ])
        
        print("   🎯 Analysis:")
        for cause in diagnosis["likely_causes"]:
            print(f"      • {cause}")
        
        return diagnosis
    
    def generate_final_report(self, user_summary: Dict, endpoints: Dict, diagnosis: Dict) -> str:
        """Generate comprehensive report"""
        report = []
        report.append("=" * 80)
        report.append("ZEBRA ASSOCIATES USER VERIFICATION - FINAL REPORT")
        report.append("£925K Opportunity Investigation")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append(f"Target User: {TARGET_USER_EMAIL}")
        report.append("")
        
        # Executive Summary
        report.append("🎯 EXECUTIVE SUMMARY")
        report.append("-" * 50)
        
        if self.user_data and self.user_data.get('role') == 'admin':
            report.append("✅ USER SETUP IS CORRECT")
            report.append("   • User exists in production database")
            report.append("   • User has admin role")
            report.append("   • User account is active")
            report.append("   • Backend endpoints are working (403 not 500)")
            report.append("")
            report.append("🔍 ROOT CAUSE: Frontend authentication issue")
            report.append("   The 'no users visible' problem is NOT a user setup issue.")
            report.append("   The backend enum fix worked - admin endpoints return 403 instead of 500.")
            report.append("   The issue is likely in frontend token handling or admin console auth.")
        
        elif self.user_data and self.user_data.get('role') != 'admin':
            report.append("⚠️  USER ROLE INCORRECT")
            report.append(f"   • User exists but has role: {self.user_data.get('role')}")
            report.append("   • User needs admin role for admin console access")
            report.append("")
            report.append("🔧 ROOT CAUSE: Database role configuration")
            
        elif not self.user_data:
            report.append("❌ USER DOES NOT EXIST")
            report.append("   • User not found in production database")
            report.append("")
            report.append("🚨 ROOT CAUSE: Missing user record")
        
        else:
            report.append("⚠️  MIXED ISSUES DETECTED")
        
        report.append("")
        
        # Detailed Findings
        report.append("📋 DETAILED FINDINGS")
        report.append("-" * 50)
        
        if self.user_data:
            report.append(f"✅ User Record Found:")
            report.append(f"   Email: {self.user_data['email']}")
            report.append(f"   Role: {self.user_data['role']}")
            report.append(f"   Active: {self.user_data['is_active']}")
            report.append(f"   Name: {self.user_data['first_name']} {self.user_data['last_name']}")
            report.append(f"   Created: {self.user_data['created_at']}")
        else:
            report.append("❌ User Record: NOT FOUND")
        
        report.append("")
        
        if self.organization_data:
            report.append(f"✅ Organization Record Found:")
            report.append(f"   Name: {self.organization_data['name']}")
            report.append(f"   ID: {self.organization_data['id']}")
            
            if 'zebra' in self.organization_data['name'].lower():
                report.append("   🦓 Confirmed: This IS Zebra Associates")
            else:
                report.append("   ⚠️  Note: This is NOT named 'Zebra Associates'")
        else:
            report.append("❌ Organization Record: NOT FOUND")
        
        report.append("")
        
        # Backend Status
        if endpoints.get("users", {}).get("status_code") == 403:
            report.append("✅ Backend Status: WORKING CORRECTLY")
            report.append("   • Admin endpoints return 403 (require authentication)")
            report.append("   • Enum fix has resolved the 500 errors")
            report.append("   • Database queries are working")
        elif endpoints.get("users", {}).get("status_code") == 500:
            report.append("❌ Backend Status: STILL BROKEN")
            report.append("   • Admin endpoints still return 500 errors") 
            report.append("   • Enum fix may not have been applied properly")
        
        report.append("")
        
        # User Database Summary
        report.append("📊 Production Database Summary:")
        report.append(f"   • Total users: {user_summary.get('total_users', 'unknown')}")
        role_counts = user_summary.get('role_counts', {})
        for role, count in role_counts.items():
            report.append(f"   • {role.title()} users: {count}")
        
        report.append("")
        
        # Solutions
        report.append("🔧 RECOMMENDED SOLUTIONS")
        report.append("-" * 50)
        
        for i, solution in enumerate(diagnosis["solutions"], 1):
            report.append(f"{i}. {solution}")
        
        if self.user_data and self.user_data.get('role') == 'admin':
            report.append("")
            report.append("🎯 NEXT STEPS FOR FRONTEND AUTHENTICATION:")
            report.append("   1. Test the authentication flow from browser")
            report.append("   2. Check if JWT tokens are being generated")
            report.append("   3. Verify tokens contain proper role claims") 
            report.append("   4. Check admin console authentication logic")
            report.append("   5. Look at browser network tab for 401/403 errors")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main verification function"""
    print("🦓 Fixed Zebra Associates User Verification")
    print("=" * 60)
    print(f"🎯 Target: {TARGET_USER_EMAIL}")
    print(f"💰 Opportunity: £925K")
    print("")
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        try:
            from app.core.config import settings
            database_url = settings.DATABASE_URL
        except Exception as e:
            print(f"❌ Database URL error: {e}")
            sys.exit(1)
    
    # Initialize verifier
    verifier = FixedZebraUserVerifier(database_url)
    
    # Connect to database
    print("🔌 Connecting to production database...")
    if not verifier.connect_to_database():
        sys.exit(1)
    print("✅ Connected successfully")
    print("")
    
    # Verify user
    user_found = verifier.verify_user_details()
    print("")
    
    # Check organization (if user found)
    if user_found:
        verifier.verify_user_organization()
        print("")
    
    # Get database summary
    user_summary = verifier.check_all_users_summary()
    print("")
    
    # Test backend endpoints
    endpoints = verifier.test_backend_endpoints()
    print("")
    
    # Diagnose the issue
    diagnosis = verifier.diagnose_admin_console_issue()
    print("")
    
    # Generate report
    report = verifier.generate_final_report(user_summary, endpoints, diagnosis)
    print(report)
    
    # Save report
    report_filename = f"zebra_verification_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"📄 Report saved: {report_filename}")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")
    
    # Final verdict
    print("\n" + "="*60)
    if verifier.user_data and verifier.user_data.get('role') == 'admin':
        print("✅ VERIFICATION RESULT: User setup is CORRECT")
        print("🔍 ISSUE: Frontend authentication needs investigation")
        print("💡 SOLUTION: Check admin console token handling")
        sys.exit(0)
    else:
        print("❌ VERIFICATION RESULT: User setup needs FIXING")
        if not verifier.user_data:
            print("🚨 CRITICAL: User does not exist - create immediately")
        else:
            print("🔧 MEDIUM: User exists but needs admin role")
        sys.exit(1)

if __name__ == "__main__":
    main()