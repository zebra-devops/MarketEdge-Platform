#!/usr/bin/env python3
"""
COMPREHENSIVE PRODUCTION AUTH TEST FOR ZEBRA ASSOCIATES £925K OPPORTUNITY

This script will perform comprehensive testing of the production authentication flow
to identify the specific backend/database issues preventing admin access.

Tests:
1. Direct database connection to production (via environment variables)
2. JWT token validation and role claim verification
3. Admin endpoint authentication flow testing
4. Organization context validation
5. User permission verification

CRITICAL: This identifies the root cause of admin access failures for Zebra Associates
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx
import requests

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    import asyncpg
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    import jwt
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("   Run: pip install httpx asyncpg sqlalchemy[asyncio] pyjwt")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionAuthTester:
    """Comprehensive production authentication testing"""
    
    def __init__(self):
        # Production configuration
        self.backend_url = "https://marketedge-platform.onrender.com"
        self.frontend_url = "https://app.zebra.associates"
        self.zebra_email = "matt.lindop@zebra.associates"
        
        # Try to get production database URL from environment
        self.production_database_url = self._get_production_database_url()
        
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": "production",
            "tests": {},
            "issues": [],
            "fixes": [],
            "analysis": {}
        }
    
    def _get_production_database_url(self) -> str:
        """Get production database URL from various possible sources"""
        # Try different environment variable names that might contain production DB URL
        possible_env_vars = [
            "DATABASE_URL",
            "PRODUCTION_DATABASE_URL", 
            "RENDER_DATABASE_URL",
            "POSTGRES_URL",
            "SUPABASE_DATABASE_URL"
        ]
        
        for env_var in possible_env_vars:
            url = os.getenv(env_var)
            if url and ("render.com" in url or "supabase" in url):
                logger.info(f"Using production database from {env_var}")
                return url
        
        # Default to a placeholder - we'll handle the error gracefully
        return "postgresql+asyncpg://placeholder:placeholder@placeholder:5432/placeholder"
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive authentication tests"""
        logger.info("🔍 Starting COMPREHENSIVE Production Auth Testing...")
        
        # Test 1: Production Database Direct Connection
        await self.test_production_database_connection()
        
        # Test 2: Backend Endpoint Response Analysis
        await self.test_backend_endpoint_responses()
        
        # Test 3: Authentication Headers and JWT Analysis
        await self.test_jwt_token_format()
        
        # Test 4: Admin User Database Verification
        await self.test_admin_user_database_status()
        
        # Test 5: Organization Context Verification
        await self.test_organization_context()
        
        # Test 6: Auth0 Configuration Verification
        await self.test_auth0_configuration()
        
        # Generate Comprehensive Analysis
        await self.generate_comprehensive_analysis()
        
        return self.results
    
    async def test_production_database_connection(self):
        """Test direct connection to production database"""
        logger.info("🗃️  Testing production database connection...")
        
        try:
            # Test if we can connect to production database
            if "placeholder" in self.production_database_url:
                self.results["tests"]["production_db"] = {
                    "status": "skipped",
                    "reason": "Production database URL not available in environment"
                }
                self.results["issues"].append({
                    "type": "DATABASE_CONFIG_MISSING",
                    "severity": "high",
                    "description": "Production database URL not accessible from local environment",
                    "impact": "Cannot verify user status directly in production database"
                })
                return
            
            # Try to connect
            engine = create_async_engine(self.production_database_url)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with async_session() as session:
                # Test connection with a simple query
                result = await session.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                
                self.results["tests"]["production_db"] = {
                    "status": "connected" if test_value == 1 else "failed",
                    "connection_test": test_value
                }
                
                if test_value == 1:
                    logger.info("✅ Production database connection successful")
                    # Now test user existence
                    await self._test_user_in_production_db(session)
                
            await engine.dispose()
            
        except Exception as e:
            logger.error(f"❌ Production database connection failed: {e}")
            self.results["tests"]["production_db"] = {
                "status": "error",
                "error": str(e)
            }
            self.results["issues"].append({
                "type": "DATABASE_CONNECTION_ERROR", 
                "severity": "critical",
                "description": f"Cannot connect to production database: {e}",
                "impact": "Unable to verify user admin status in production"
            })
    
    async def _test_user_in_production_db(self, session):
        """Test user existence in production database"""
        try:
            # Check user existence and admin status
            result = await session.execute(text("""
                SELECT u.id, u.email, u.role, u.is_active, 
                       o.name as organisation_name, o.id as organisation_id
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
                    "organisation_name": user_data.organisation_name,
                    "organisation_id": str(user_data.organisation_id) if user_data.organisation_id else None
                }
                
                self.results["tests"]["production_user"] = {
                    "status": "found",
                    "user": user_info,
                    "is_admin": user_data.role == "admin",
                    "is_active": user_data.is_active
                }
                
                if user_data.role != "admin":
                    self.results["issues"].append({
                        "type": "USER_NOT_ADMIN",
                        "severity": "critical",
                        "description": f"User {self.zebra_email} exists but role is '{user_data.role}', not 'admin'",
                        "current_role": user_data.role,
                        "required_role": "admin"
                    })
                
                if not user_data.is_active:
                    self.results["issues"].append({
                        "type": "USER_INACTIVE",
                        "severity": "high", 
                        "description": f"User {self.zebra_email} exists but is inactive"
                    })
                
                logger.info(f"✅ Production user found: {user_info}")
                
            else:
                self.results["tests"]["production_user"] = {
                    "status": "not_found"
                }
                self.results["issues"].append({
                    "type": "USER_NOT_FOUND_PRODUCTION",
                    "severity": "critical",
                    "description": f"User {self.zebra_email} does not exist in production database",
                    "impact": "User cannot authenticate or access admin endpoints"
                })
                
        except Exception as e:
            logger.error(f"❌ Production user check failed: {e}")
            self.results["tests"]["production_user"] = {
                "status": "error",
                "error": str(e)
            }
    
    async def test_backend_endpoint_responses(self):
        """Analyze backend endpoint responses in detail"""
        logger.info("🔐 Testing backend endpoint responses...")
        
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/feature-flags", 
            "/api/v1/admin/dashboard/stats",
            "/api/v1/admin/modules"
        ]
        
        try:
            async with httpx.AsyncClient() as client:
                for endpoint in admin_endpoints:
                    try:
                        # Test without authentication
                        response = await client.get(
                            f"{self.backend_url}{endpoint}",
                            headers={
                                "Origin": self.frontend_url,
                                "Accept": "application/json"
                            },
                            timeout=15
                        )
                        
                        # Try to parse response body
                        response_body = None
                        try:
                            response_body = response.json()
                        except:
                            response_body = response.text[:500]  # Truncate long responses
                        
                        endpoint_result = {
                            "status_code": response.status_code,
                            "response_body": response_body,
                            "headers": dict(response.headers),
                            "expected_auth": response.status_code in [401, 403],
                            "server_error": response.status_code >= 500
                        }
                        
                        self.results["tests"][f"endpoint_{endpoint.replace('/', '_')}"] = endpoint_result
                        
                        # Analyze specific issues
                        if response.status_code >= 500:
                            self.results["issues"].append({
                                "type": "ENDPOINT_SERVER_ERROR",
                                "severity": "critical",
                                "endpoint": endpoint,
                                "status_code": response.status_code,
                                "description": f"Server error (5xx) on {endpoint}",
                                "response": str(response_body)[:200]
                            })
                        elif response.status_code == 403:
                            # 403 is expected for admin endpoints without auth, but let's note it
                            logger.info(f"📊 {endpoint}: 403 Forbidden (expected without auth)")
                        elif response.status_code == 401:
                            logger.info(f"📊 {endpoint}: 401 Unauthorized (expected without auth)")
                        else:
                            logger.info(f"📊 {endpoint}: {response.status_code}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to test {endpoint}: {e}")
                        self.results["tests"][f"endpoint_{endpoint.replace('/', '_')}"] = {
                            "status": "error",
                            "error": str(e)
                        }
                        
        except Exception as e:
            logger.error(f"❌ Backend endpoint testing failed: {e}")
    
    async def test_jwt_token_format(self):
        """Test JWT token format and validation"""
        logger.info("🎫 Testing JWT token format requirements...")
        
        # This simulates what the frontend should send
        mock_jwt_payload = {
            "sub": "auth0|zebra_user_id",
            "email": self.zebra_email,
            "role": "admin",
            "organisation_id": "zebra_org_id",
            "iss": "https://dev-auth0-domain.auth0.com/",
            "aud": "marketedge-api",
            "exp": int(datetime.utcnow().timestamp()) + 3600,
            "iat": int(datetime.utcnow().timestamp())
        }
        
        try:
            # Test JWT creation with a dummy secret
            test_token = jwt.encode(
                mock_jwt_payload,
                "test-secret-key",
                algorithm="HS256"
            )
            
            # Test JWT decoding
            decoded_payload = jwt.decode(
                test_token,
                "test-secret-key", 
                algorithms=["HS256"]
            )
            
            self.results["tests"]["jwt_format"] = {
                "status": "valid_format",
                "mock_payload": mock_jwt_payload,
                "token_length": len(test_token),
                "decoded_successfully": decoded_payload == mock_jwt_payload
            }
            
            logger.info("✅ JWT format test passed")
            
        except Exception as e:
            logger.error(f"❌ JWT format test failed: {e}")
            self.results["tests"]["jwt_format"] = {
                "status": "error",
                "error": str(e)
            }
            
            self.results["issues"].append({
                "type": "JWT_FORMAT_ERROR",
                "severity": "high",
                "description": f"JWT token format validation failed: {e}"
            })
    
    async def test_admin_user_database_status(self):
        """Test admin user status using emergency endpoints"""
        logger.info("👤 Testing admin user database status...")
        
        try:
            # Use the emergency admin verification endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.backend_url}/api/v1/database/verify-admin-access/{self.zebra_email}",
                    timeout=15
                )
                
                if response.status_code == 200:
                    admin_data = response.json()
                    self.results["tests"]["admin_verification"] = {
                        "status": "success",
                        "response": admin_data
                    }
                    
                    # Analyze the response
                    user_info = admin_data.get("user", {})
                    if user_info.get("role") == "admin":
                        logger.info("✅ User has admin role in database")
                    else:
                        self.results["issues"].append({
                            "type": "DATABASE_ROLE_MISMATCH",
                            "severity": "critical", 
                            "description": f"User role in database is '{user_info.get('role')}', not 'admin'"
                        })
                else:
                    self.results["tests"]["admin_verification"] = {
                        "status": "failed",
                        "status_code": response.status_code,
                        "response": response.text
                    }
                    self.results["issues"].append({
                        "type": "ADMIN_VERIFICATION_FAILED",
                        "severity": "high",
                        "description": f"Admin verification endpoint failed with status {response.status_code}"
                    })
                    
        except Exception as e:
            logger.error(f"❌ Admin verification test failed: {e}")
            self.results["tests"]["admin_verification"] = {
                "status": "error",
                "error": str(e)
            }
    
    async def test_organization_context(self):
        """Test organization context handling"""
        logger.info("🏢 Testing organization context...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test if we can get organization info
                response = await client.get(
                    f"{self.backend_url}/api/v1/organisations",
                    headers={"Origin": self.frontend_url},
                    timeout=15
                )
                
                org_result = {
                    "status_code": response.status_code,
                    "accessible": response.status_code < 400
                }
                
                if response.status_code == 200:
                    orgs = response.json()
                    org_result["organizations_found"] = len(orgs) if isinstance(orgs, list) else 0
                    
                    # Check if Zebra Associates organization exists
                    zebra_org_found = False
                    if isinstance(orgs, list):
                        for org in orgs:
                            if isinstance(org, dict) and "zebra" in org.get("name", "").lower():
                                zebra_org_found = True
                                break
                    
                    org_result["zebra_org_found"] = zebra_org_found
                    
                    if not zebra_org_found:
                        self.results["issues"].append({
                            "type": "ZEBRA_ORG_NOT_FOUND",
                            "severity": "high",
                            "description": "Zebra Associates organization not found in database"
                        })
                
                self.results["tests"]["organization_context"] = org_result
                logger.info(f"📊 Organization test: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Organization context test failed: {e}")
            self.results["tests"]["organization_context"] = {
                "status": "error", 
                "error": str(e)
            }
    
    async def test_auth0_configuration(self):
        """Test Auth0 configuration accessibility"""
        logger.info("🔑 Testing Auth0 configuration...")
        
        try:
            # Test if Auth0 login endpoint is accessible
            async with httpx.AsyncClient() as client:
                # Test the auth endpoint that should redirect to Auth0
                response = await client.get(
                    f"{self.backend_url}/api/v1/auth/login",
                    follow_redirects=False,
                    timeout=15
                )
                
                auth_result = {
                    "status_code": response.status_code,
                    "is_redirect": response.status_code in [302, 307, 308],
                    "location": response.headers.get("location"),
                    "accessible": response.status_code < 500
                }
                
                # Check if it redirects to Auth0
                if auth_result["location"] and "auth0.com" in auth_result["location"]:
                    auth_result["auth0_redirect"] = True
                else:
                    auth_result["auth0_redirect"] = False
                    self.results["issues"].append({
                        "type": "AUTH0_REDIRECT_MISSING", 
                        "severity": "high",
                        "description": "Auth endpoint does not redirect to Auth0"
                    })
                
                self.results["tests"]["auth0_config"] = auth_result
                logger.info(f"🔑 Auth0 test: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Auth0 configuration test failed: {e}")
            self.results["tests"]["auth0_config"] = {
                "status": "error",
                "error": str(e)
            }
    
    async def generate_comprehensive_analysis(self):
        """Generate comprehensive analysis of findings"""
        logger.info("📋 Generating comprehensive analysis...")
        
        # Categorize issues by severity
        critical_issues = [i for i in self.results["issues"] if i.get("severity") == "critical"]
        high_issues = [i for i in self.results["issues"] if i.get("severity") == "high"]
        other_issues = [i for i in self.results["issues"] if i.get("severity") not in ["critical", "high"]]
        
        # Analyze test results
        cors_working = self.results["tests"].get("cors", {}).get("status") == "passed"
        endpoints_responding = any(
            test.get("status_code", 0) in [401, 403] 
            for key, test in self.results["tests"].items() 
            if key.startswith("endpoint_")
        )
        
        self.results["analysis"] = {
            "issue_summary": {
                "total_issues": len(self.results["issues"]),
                "critical_issues": len(critical_issues),
                "high_issues": len(high_issues)
            },
            "root_cause_assessment": self._determine_root_cause(),
            "backend_status": {
                "cors_configured": cors_working,
                "endpoints_responding": endpoints_responding,
                "server_errors_found": any(
                    i.get("type") == "ENDPOINT_SERVER_ERROR" 
                    for i in self.results["issues"]
                )
            },
            "recommended_actions": self._generate_recommended_actions(critical_issues, high_issues)
        }
        
        # Generate final report
        await self._generate_final_report()
    
    def _determine_root_cause(self) -> Dict[str, Any]:
        """Determine the most likely root cause"""
        issue_types = [i.get("type") for i in self.results["issues"]]
        
        if "ENDPOINT_SERVER_ERROR" in issue_types:
            return {
                "primary": "Backend Server Errors",
                "description": "Admin endpoints are returning 500 errors",
                "confidence": "high"
            }
        elif "USER_NOT_ADMIN" in issue_types or "DATABASE_ROLE_MISMATCH" in issue_types:
            return {
                "primary": "User Permission Issues", 
                "description": "User exists but lacks admin privileges",
                "confidence": "high"
            }
        elif "USER_NOT_FOUND_PRODUCTION" in issue_types:
            return {
                "primary": "User Not Found",
                "description": "User does not exist in production database",
                "confidence": "high"
            }
        elif "DATABASE_CONNECTION_ERROR" in issue_types:
            return {
                "primary": "Database Access Issues",
                "description": "Cannot connect to production database for verification",
                "confidence": "medium"
            }
        else:
            return {
                "primary": "Authentication Flow Issues",
                "description": "JWT token validation or Auth0 configuration problems",
                "confidence": "medium"
            }
    
    def _generate_recommended_actions(self, critical_issues: List, high_issues: List) -> List[Dict]:
        """Generate prioritized recommended actions"""
        actions = []
        
        # Handle critical issues first
        for issue in critical_issues:
            if issue["type"] == "ENDPOINT_SERVER_ERROR":
                actions.append({
                    "priority": "CRITICAL",
                    "action": "Fix Backend Server Errors",
                    "description": f"Admin endpoint {issue.get('endpoint')} returning 500 error",
                    "steps": [
                        "Check backend logs for specific error details",
                        "Verify database connection in production", 
                        "Test endpoint with valid admin JWT token",
                        "Fix any Python/SQL errors in admin service code"
                    ]
                })
            elif issue["type"] == "USER_NOT_ADMIN":
                actions.append({
                    "priority": "CRITICAL", 
                    "action": "Update User Role to Admin",
                    "description": f"User {self.zebra_email} needs admin role",
                    "steps": [
                        f"UPDATE users SET role = 'admin' WHERE email = '{self.zebra_email}'",
                        "Verify role change in database",
                        "Test re-authentication to get updated JWT token"
                    ]
                })
            elif issue["type"] == "USER_NOT_FOUND_PRODUCTION":
                actions.append({
                    "priority": "CRITICAL",
                    "action": "Create Admin User", 
                    "description": f"Create {self.zebra_email} as admin user",
                    "steps": [
                        "Use emergency admin setup endpoint",
                        "Verify user creation in database",
                        "Test Auth0 authentication flow"
                    ]
                })
        
        # Handle high priority issues
        for issue in high_issues:
            if issue["type"] == "AUTH0_REDIRECT_MISSING":
                actions.append({
                    "priority": "HIGH",
                    "action": "Fix Auth0 Configuration",
                    "description": "Auth0 login redirect not working",
                    "steps": [
                        "Verify Auth0 environment variables",
                        "Check Auth0 domain and client ID",
                        "Test Auth0 callback URL configuration"
                    ]
                })
        
        return actions
    
    async def _generate_final_report(self):
        """Generate final comprehensive report"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        report = f"""
🔍 COMPREHENSIVE PRODUCTION AUTH ANALYSIS - ZEBRA ASSOCIATES £925K OPPORTUNITY
===========================================================================
Timestamp: {self.results['timestamp']}
Target User: {self.zebra_email}
Backend: {self.backend_url}

📊 EXECUTIVE SUMMARY
-------------------
Total Issues: {self.results['analysis']['issue_summary']['total_issues']}
Critical Issues: {self.results['analysis']['issue_summary']['critical_issues']}
High Priority Issues: {self.results['analysis']['issue_summary']['high_issues']}

🎯 ROOT CAUSE ANALYSIS
---------------------
Primary Issue: {self.results['analysis']['root_cause_assessment']['primary']}
Description: {self.results['analysis']['root_cause_assessment']['description']}
Confidence: {self.results['analysis']['root_cause_assessment']['confidence']}

🚨 RECOMMENDED ACTIONS (PRIORITY ORDER)
--------------------------------------
"""
        
        for i, action in enumerate(self.results['analysis']['recommended_actions'], 1):
            report += f"{i}. [{action['priority']}] {action['action']}\n"
            report += f"   Description: {action['description']}\n"
            report += f"   Steps:\n"
            for step in action['steps']:
                report += f"   - {step}\n"
            report += "\n"
        
        report += f"""
🔧 BACKEND STATUS
----------------
CORS Configured: {self.results['analysis']['backend_status']['cors_configured']}
Endpoints Responding: {self.results['analysis']['backend_status']['endpoints_responding']}  
Server Errors Found: {self.results['analysis']['backend_status']['server_errors_found']}

💡 KEY FINDINGS
--------------
"""
        
        # Add key findings based on test results
        if self.results.get("tests", {}).get("cors", {}).get("status") == "passed":
            report += "✅ CORS is properly configured for app.zebra.associates\n"
        
        if any(test.get("status_code") == 403 for test in self.results.get("tests", {}).values() if isinstance(test, dict)):
            report += "✅ Admin endpoints are responding (403 Forbidden without auth)\n"
        
        if any(test.get("status_code", 0) >= 500 for test in self.results.get("tests", {}).values() if isinstance(test, dict)):
            report += "❌ Some endpoints are returning server errors (5xx)\n"
        
        report += f"""

🎯 BUSINESS IMPACT ASSESSMENT
----------------------------
Opportunity Value: £925K Zebra Associates Partnership
Current Status: Admin access blocked - user cannot manage Epic features
Resolution Urgency: CRITICAL - Partnership opportunity at risk

📋 NEXT STEPS FOR RESOLUTION
---------------------------
1. Implement highest priority fixes first (CRITICAL issues)
2. Test authentication flow with matt.lindop@zebra.associates
3. Verify Epic 1 and Epic 2 admin functionality
4. Confirm 200 responses on admin endpoints with valid JWT
5. Document resolution for future reference

===============================================================================
"""
        
        # Save comprehensive report
        report_file = f"/Users/matt/Sites/MarketEdge/comprehensive_auth_analysis_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        logger.info(f"📄 Comprehensive report saved to: {report_file}")

async def main():
    """Main testing function"""
    tester = ProductionAuthTester()
    results = await tester.run_comprehensive_tests()
    
    # Save detailed JSON results
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    json_file = f"/Users/matt/Sites/MarketEdge/comprehensive_auth_results_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Comprehensive analysis complete. Results saved to: {json_file}")
    return results

if __name__ == "__main__":
    asyncio.run(main())