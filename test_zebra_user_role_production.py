#!/usr/bin/env python3
"""
Test to verify Zebra user role in production database
Diagnoses why admin console access is failing
"""

import os
import asyncio
import sys
import logging
from datetime import datetime
import json
import httpx
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZebraUserRoleTest:
    """Test Zebra user role and admin access"""
    
    def __init__(self):
        self.backend_url = "https://marketedge-platform.onrender.com"
        self.zebra_email = "matt.lindop@zebra.associates"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "zebra_email": self.zebra_email,
            "tests": {},
            "issues": [],
            "fixes": []
        }
    
    async def test_database_direct_connection(self) -> Dict[str, Any]:
        """Test direct database connection to verify user role"""
        try:
            # Import database dependencies
            sys.path.append('/Users/matt/Sites/MarketEdge')
            
            # Use production database URL if available
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                # Try to construct from environment
                db_user = os.getenv('POSTGRES_USER', 'postgres')
                db_pass = os.getenv('POSTGRES_PASSWORD', '')
                db_host = os.getenv('POSTGRES_HOST', 'localhost')
                db_port = os.getenv('POSTGRES_PORT', '5432')
                db_name = os.getenv('POSTGRES_DB', 'marketedge')
                
                if db_pass:
                    database_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
                else:
                    database_url = f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
            
            logger.info(f"🔍 Testing database connection...")
            logger.info(f"Database URL pattern: {database_url.split('://')[0]}://[USER]@{database_url.split('@')[1] if '@' in database_url else 'localhost'}")
            
            # Try to connect and query user
            import asyncpg
            
            conn = await asyncpg.connect(database_url)
            
            # Query user details
            user_query = """
                SELECT id, email, first_name, last_name, role, is_active, organisation_id, created_at
                FROM users 
                WHERE email = $1
            """
            
            user_result = await conn.fetchrow(user_query, self.zebra_email)
            
            if user_result:
                user_data = dict(user_result)
                logger.info(f"✅ Found user: {user_data['email']}")
                logger.info(f"   Role: {user_data['role']}")
                logger.info(f"   Active: {user_data['is_active']}")
                logger.info(f"   Organisation: {user_data['organisation_id']}")
                
                # Check if role is admin
                is_admin = user_data['role'] == 'admin'
                logger.info(f"   Is Admin: {is_admin}")
                
                if not is_admin:
                    self.results["issues"].append({
                        "type": "USER_ROLE_NOT_ADMIN",
                        "description": f"User {self.zebra_email} has role '{user_data['role']}' but needs 'admin' role",
                        "severity": "CRITICAL",
                        "blocking_admin_access": True
                    })
                    
                    self.results["fixes"].append({
                        "type": "UPDATE_USER_ROLE",
                        "description": "Update user role to admin",
                        "sql": f"UPDATE users SET role = 'admin' WHERE email = '{self.zebra_email}'"
                    })
                
                return {
                    "success": True,
                    "user_found": True,
                    "user_data": user_data,
                    "is_admin": is_admin,
                    "needs_role_fix": not is_admin
                }
            else:
                logger.error(f"❌ User not found: {self.zebra_email}")
                self.results["issues"].append({
                    "type": "USER_NOT_FOUND",
                    "description": f"User {self.zebra_email} not found in database",
                    "severity": "CRITICAL"
                })
                return {
                    "success": True,
                    "user_found": False,
                    "needs_user_creation": True
                }
                
        except Exception as e:
            logger.error(f"❌ Database test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_auth_endpoints(self) -> Dict[str, Any]:
        """Test authentication endpoints to verify login process"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test login endpoint exists
                login_response = await client.post(
                    f"{self.backend_url}/api/v1/auth/login",
                    json={"email": self.zebra_email, "password": "test"},
                    headers={"Origin": "https://app.zebra.associates"}
                )
                
                logger.info(f"🔐 Login endpoint test: {login_response.status_code}")
                
                # Test token verification endpoint
                token_response = await client.post(
                    f"{self.backend_url}/api/v1/auth/verify-token",
                    json={"token": "test-token"},
                    headers={"Origin": "https://app.zebra.associates"}
                )
                
                logger.info(f"🎫 Token verify endpoint test: {token_response.status_code}")
                
                return {
                    "login_endpoint_status": login_response.status_code,
                    "token_verify_status": token_response.status_code,
                    "auth_endpoints_available": True
                }
                
        except Exception as e:
            logger.error(f"❌ Auth endpoints test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_admin_endpoints_without_auth(self) -> Dict[str, Any]:
        """Test admin endpoints without authentication to verify they exist"""
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/users/",
            "/api/v1/admin/dashboard/stats",
            "/api/v1/admin/feature-flags",
        ]
        
        results = {}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for endpoint in admin_endpoints:
                    try:
                        response = await client.get(
                            f"{self.backend_url}{endpoint}",
                            headers={"Origin": "https://app.zebra.associates"}
                        )
                        
                        results[endpoint] = {
                            "status_code": response.status_code,
                            "exists": response.status_code != 404,
                            "requires_auth": response.status_code in [401, 403],
                            "cors_working": response.headers.get("access-control-allow-origin") is not None
                        }
                        
                        logger.info(f"📊 {endpoint}: {response.status_code} (exists: {results[endpoint]['exists']}, cors: {results[endpoint]['cors_working']})")
                        
                    except Exception as e:
                        logger.error(f"❌ Error testing {endpoint}: {e}")
                        results[endpoint] = {"error": str(e)}
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Admin endpoints test failed: {e}")
            return {"error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all diagnostic tests"""
        logger.info("🚀 Starting Zebra user role and admin access tests...")
        
        # Test database connection
        logger.info("\n📊 Testing database connection...")
        db_test = await self.test_database_direct_connection()
        self.results["tests"]["database"] = db_test
        
        # Test auth endpoints
        logger.info("\n🔐 Testing authentication endpoints...")
        auth_test = await self.test_auth_endpoints()
        self.results["tests"]["auth_endpoints"] = auth_test
        
        # Test admin endpoints
        logger.info("\n👑 Testing admin endpoints...")
        admin_test = await self.test_admin_endpoints_without_auth()
        self.results["tests"]["admin_endpoints"] = admin_test
        
        # Generate summary
        self.results["summary"] = {
            "total_issues": len(self.results["issues"]),
            "total_fixes": len(self.results["fixes"]),
            "critical_issues": len([i for i in self.results["issues"] if i.get("severity") == "CRITICAL"]),
            "admin_access_blocked": any(i.get("blocking_admin_access") for i in self.results["issues"])
        }
        
        return self.results
    
    def print_report(self):
        """Print comprehensive diagnostic report"""
        print("\n" + "="*60)
        print("🔍 ZEBRA USER ROLE & ADMIN ACCESS DIAGNOSTIC REPORT")
        print("="*60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Target User: {self.zebra_email}")
        print(f"Backend URL: {self.backend_url}")
        
        # Print summary
        summary = self.results.get("summary", {})
        print(f"\n📊 SUMMARY")
        print("-" * 20)
        print(f"Total Issues Found: {summary.get('total_issues', 0)}")
        print(f"Critical Issues: {summary.get('critical_issues', 0)}")
        print(f"Admin Access Blocked: {summary.get('admin_access_blocked', False)}")
        print(f"Fixes Available: {summary.get('total_fixes', 0)}")
        
        # Print database test results
        db_test = self.results.get("tests", {}).get("database", {})
        if db_test:
            print(f"\n🗄️ DATABASE CONNECTION")
            print("-" * 25)
            if db_test.get("success"):
                if db_test.get("user_found"):
                    user_data = db_test.get("user_data", {})
                    print(f"✅ User Found: {user_data.get('email')}")
                    print(f"   Role: {user_data.get('role')}")
                    print(f"   Active: {user_data.get('is_active')}")
                    print(f"   Is Admin: {db_test.get('is_admin')}")
                    
                    if db_test.get("needs_role_fix"):
                        print(f"⚠️  ISSUE: User role is '{user_data.get('role')}' but needs 'admin'")
                else:
                    print(f"❌ User not found in database")
            else:
                print(f"❌ Database connection failed: {db_test.get('error')}")
        
        # Print admin endpoints results
        admin_test = self.results.get("tests", {}).get("admin_endpoints", {})
        if admin_test and not admin_test.get("error"):
            print(f"\n👑 ADMIN ENDPOINTS")
            print("-" * 20)
            for endpoint, result in admin_test.items():
                if isinstance(result, dict):
                    status = result.get("status_code", "N/A")
                    exists = "✅" if result.get("exists") else "❌"
                    cors = "✅" if result.get("cors_working") else "❌"
                    print(f"{exists} {endpoint} - Status: {status}, CORS: {cors}")
        
        # Print issues
        if self.results.get("issues"):
            print(f"\n🐛 ISSUES IDENTIFIED")
            print("-" * 20)
            for i, issue in enumerate(self.results["issues"], 1):
                severity = issue.get("severity", "UNKNOWN")
                print(f"{i}. {severity}: {issue.get('description')}")
        
        # Print fixes
        if self.results.get("fixes"):
            print(f"\n🔧 RECOMMENDED FIXES")
            print("-" * 20)
            for i, fix in enumerate(self.results["fixes"], 1):
                print(f"{i}. {fix.get('type')}: {fix.get('description')}")
                if fix.get("sql"):
                    print(f"   SQL: {fix.get('sql')}")


async def main():
    """Main test runner"""
    tester = ZebraUserRoleTest()
    
    try:
        results = await tester.run_all_tests()
        
        # Print report
        tester.print_report()
        
        # Save results
        results_file = f"/Users/matt/Sites/MarketEdge/zebra_user_role_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"✅ Results saved to: {results_file}")
        
        # Return appropriate exit code
        critical_issues = results.get("summary", {}).get("critical_issues", 0)
        return 1 if critical_issues > 0 else 0
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)