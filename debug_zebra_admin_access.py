#!/usr/bin/env python3
"""
Debug Zebra Associates Admin Access Issues

This script will:
1. Test CORS configuration by making actual HTTP requests 
2. Check if matt.lindop@zebra.associates exists and has admin role
3. Test the actual admin endpoints that are failing
4. Provide specific fixes for the issues

CRITICAL: This is for debugging the £925K Zebra Associates opportunity
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    import httpx
    import asyncpg
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text, select
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("   Run: pip install httpx asyncpg sqlalchemy[asyncio]")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZebraAdminDebugger:
    """Debug admin access issues for Zebra Associates"""
    
    def __init__(self):
        # Production URLs
        self.backend_url = "https://marketedge-platform.onrender.com"
        self.frontend_url = "https://app.zebra.associates"
        self.zebra_email = "matt.lindop@zebra.associates"
        
        # Environment-based database URL
        self.database_url = os.getenv("DATABASE_URL", 
            "postgresql+asyncpg://postgres:password@localhost:5432/marketedge")
        
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "issues": [],
            "fixes": []
        }
    
    async def run_all_tests(self):
        """Run all debugging tests"""
        logger.info("🔍 Starting Zebra Associates Admin Access Debug...")
        
        # Test 1: CORS Configuration
        await self.test_cors_configuration()
        
        # Test 2: Database User Verification
        await self.test_database_user_admin()
        
        # Test 3: Admin Endpoints Access
        await self.test_admin_endpoints()
        
        # Test 4: Database Schema Verification
        await self.test_database_schema()
        
        # Generate Report
        await self.generate_debug_report()
        
        return self.results
    
    async def test_cors_configuration(self):
        """Test if CORS is properly configured for app.zebra.associates"""
        logger.info("🌐 Testing CORS configuration...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test OPTIONS preflight request
                response = await client.options(
                    f"{self.backend_url}/api/v1/admin/feature-flags",
                    headers={
                        "Origin": self.frontend_url,
                        "Access-Control-Request-Method": "GET",
                        "Access-Control-Request-Headers": "Authorization, Content-Type"
                    },
                    timeout=10
                )
                
                cors_headers = {
                    "access_control_allow_origin": response.headers.get("access-control-allow-origin"),
                    "access_control_allow_credentials": response.headers.get("access-control-allow-credentials"),
                    "access_control_allow_methods": response.headers.get("access-control-allow-methods"),
                    "access_control_allow_headers": response.headers.get("access-control-allow-headers")
                }
                
                self.results["tests"]["cors"] = {
                    "status": "passed" if response.status_code == 200 else "failed",
                    "status_code": response.status_code,
                    "headers": cors_headers
                }
                
                # Check if zebra.associates is allowed
                if cors_headers["access_control_allow_origin"] != self.frontend_url:
                    self.results["issues"].append({
                        "type": "CORS_ORIGIN_MISMATCH",
                        "description": f"CORS does not allow {self.frontend_url}",
                        "current": cors_headers["access_control_allow_origin"],
                        "expected": self.frontend_url
                    })
                    
                    self.results["fixes"].append({
                        "type": "CORS_FIX",
                        "description": "Update CORS configuration to allow app.zebra.associates",
                        "action": "Already fixed in main.py - check deployment"
                    })
                
                logger.info(f"✅ CORS test completed - Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ CORS test failed: {e}")
            self.results["tests"]["cors"] = {
                "status": "error",
                "error": str(e)
            }
            self.results["issues"].append({
                "type": "CORS_CONNECTION_ERROR",
                "description": f"Failed to connect to backend: {e}"
            })
    
    async def test_database_user_admin(self):
        """Check if matt.lindop@zebra.associates exists and has admin role"""
        logger.info("👤 Testing database user admin status...")
        
        try:
            # Create async engine
            engine = create_async_engine(self.database_url)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with async_session() as session:
                # Check if user exists and has admin role
                result = await session.execute(text("""
                    SELECT u.id, u.email, u.role, u.is_active, o.name as organisation_name
                    FROM users u
                    LEFT JOIN organisations o ON u.organisation_id = o.id
                    WHERE u.email = :email
                """), {"email": self.zebra_email})
                
                user_data = result.fetchone()
                
                if user_data:
                    user_info = {
                        "id": str(user_data.id),
                        "email": user_data.email,
                        "role": user_data.role,
                        "is_active": user_data.is_active,
                        "organisation": user_data.organisation_name
                    }
                    
                    self.results["tests"]["user_admin"] = {
                        "status": "found",
                        "user": user_info,
                        "is_admin": user_data.role == "admin",
                        "is_active": user_data.is_active
                    }
                    
                    if user_data.role != "admin":
                        self.results["issues"].append({
                            "type": "USER_NOT_ADMIN",
                            "description": f"User {self.zebra_email} exists but is not admin",
                            "current_role": user_data.role,
                            "required_role": "admin"
                        })
                        
                        self.results["fixes"].append({
                            "type": "USER_ROLE_UPDATE",
                            "description": f"Update {self.zebra_email} role to admin",
                            "sql": f"UPDATE users SET role = 'admin' WHERE email = '{self.zebra_email}'"
                        })
                    
                    if not user_data.is_active:
                        self.results["issues"].append({
                            "type": "USER_INACTIVE",
                            "description": f"User {self.zebra_email} is inactive"
                        })
                        
                        self.results["fixes"].append({
                            "type": "USER_ACTIVATION",
                            "description": f"Activate user {self.zebra_email}",
                            "sql": f"UPDATE users SET is_active = true WHERE email = '{self.zebra_email}'"
                        })
                    
                    logger.info(f"✅ User found: {user_info}")
                    
                else:
                    self.results["tests"]["user_admin"] = {
                        "status": "not_found",
                        "user": None
                    }
                    
                    self.results["issues"].append({
                        "type": "USER_NOT_FOUND",
                        "description": f"User {self.zebra_email} does not exist in database"
                    })
                    
                    self.results["fixes"].append({
                        "type": "USER_CREATION",
                        "description": f"Create admin user {self.zebra_email}",
                        "action": "Create user through admin endpoint or direct database insert"
                    })
                    
                    logger.warning(f"❌ User {self.zebra_email} not found in database")
            
            await engine.dispose()
            
        except Exception as e:
            logger.error(f"❌ Database user test failed: {e}")
            self.results["tests"]["user_admin"] = {
                "status": "error",
                "error": str(e)
            }
            self.results["issues"].append({
                "type": "DATABASE_CONNECTION_ERROR",
                "description": f"Failed to connect to database: {e}"
            })
    
    async def test_admin_endpoints(self):
        """Test if admin endpoints are accessible (without auth for now)"""
        logger.info("🔐 Testing admin endpoints...")
        
        endpoints_to_test = [
            "/api/v1/admin/feature-flags",
            "/api/v1/admin/dashboard/stats",
            "/api/v1/admin/modules"
        ]
        
        try:
            async with httpx.AsyncClient() as client:
                for endpoint in endpoints_to_test:
                    try:
                        response = await client.get(
                            f"{self.backend_url}{endpoint}",
                            headers={"Origin": self.frontend_url},
                            timeout=10
                        )
                        
                        endpoint_result = {
                            "status_code": response.status_code,
                            "headers": dict(response.headers),
                            "accessible": response.status_code != 404
                        }
                        
                        # 401 is expected (no auth), 500 is the problem
                        if response.status_code == 500:
                            endpoint_result["has_server_error"] = True
                            self.results["issues"].append({
                                "type": "ENDPOINT_SERVER_ERROR",
                                "endpoint": endpoint,
                                "description": f"500 error on {endpoint}"
                            })
                        
                        self.results["tests"][f"endpoint_{endpoint.replace('/', '_')}"] = endpoint_result
                        
                        logger.info(f"📊 {endpoint}: {response.status_code}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to test {endpoint}: {e}")
                        self.results["tests"][f"endpoint_{endpoint.replace('/', '_')}"] = {
                            "status": "error",
                            "error": str(e)
                        }
        
        except Exception as e:
            logger.error(f"❌ Admin endpoints test failed: {e}")
    
    async def test_database_schema(self):
        """Test if required database tables exist"""
        logger.info("🗃️  Testing database schema...")
        
        required_tables = [
            "users", "organisations", "feature_flags", "audit_logs", 
            "admin_actions", "analytics_modules", "organisation_modules"
        ]
        
        try:
            engine = create_async_engine(self.database_url)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with async_session() as session:
                missing_tables = []
                existing_tables = []
                
                for table in required_tables:
                    result = await session.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = :table_name
                        )
                    """), {"table_name": table})
                    
                    exists = result.scalar()
                    if exists:
                        existing_tables.append(table)
                    else:
                        missing_tables.append(table)
                
                self.results["tests"]["database_schema"] = {
                    "existing_tables": existing_tables,
                    "missing_tables": missing_tables,
                    "all_tables_exist": len(missing_tables) == 0
                }
                
                if missing_tables:
                    self.results["issues"].append({
                        "type": "MISSING_DATABASE_TABLES",
                        "description": "Required database tables are missing",
                        "missing_tables": missing_tables
                    })
                    
                    self.results["fixes"].append({
                        "type": "DATABASE_MIGRATION",
                        "description": "Run database migrations to create missing tables",
                        "action": "Run: alembic upgrade head"
                    })
                
                logger.info(f"✅ Schema test - Existing: {len(existing_tables)}, Missing: {len(missing_tables)}")
            
            await engine.dispose()
            
        except Exception as e:
            logger.error(f"❌ Database schema test failed: {e}")
            self.results["tests"]["database_schema"] = {
                "status": "error",
                "error": str(e)
            }
    
    async def generate_debug_report(self):
        """Generate comprehensive debug report"""
        logger.info("📋 Generating debug report...")
        
        # Summary
        total_issues = len(self.results["issues"])
        total_fixes = len(self.results["fixes"])
        
        report = f"""
🔍 ZEBRA ASSOCIATES ADMIN ACCESS DEBUG REPORT
=============================================
Timestamp: {self.results['timestamp']}
Target: {self.zebra_email} accessing {self.backend_url}

📊 SUMMARY
----------
Total Issues Found: {total_issues}
Total Fixes Available: {total_fixes}

🔧 CRITICAL FIXES NEEDED
------------------------
"""
        
        for i, fix in enumerate(self.results["fixes"], 1):
            report += f"{i}. {fix['type']}: {fix['description']}\n"
            if 'sql' in fix:
                report += f"   SQL: {fix['sql']}\n"
            if 'action' in fix:
                report += f"   Action: {fix['action']}\n"
            report += "\n"
        
        report += f"""
🐛 ISSUES IDENTIFIED  
-------------------
"""
        
        for i, issue in enumerate(self.results["issues"], 1):
            report += f"{i}. {issue['type']}: {issue['description']}\n"
        
        # Save report
        report_file = f"/Users/matt/Sites/MarketEdge/zebra_admin_debug_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
            
        print(report)
        logger.info(f"📄 Full report saved to: {report_file}")

async def main():
    """Main debug function"""
    debugger = ZebraAdminDebugger()
    results = await debugger.run_all_tests()
    
    # Output results as JSON for programmatic use
    json_file = f"/Users/matt/Sites/MarketEdge/zebra_admin_debug_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Debug complete. Results saved to: {json_file}")
    return results

if __name__ == "__main__":
    asyncio.run(main())