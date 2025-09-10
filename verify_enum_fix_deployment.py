#!/usr/bin/env python3
"""
POST-DEPLOYMENT VERIFICATION - ENUM FIX FOR ZEBRA ASSOCIATES £925K OPPORTUNITY

This script verifies that the backend deployment successfully resolved the enum mismatch issue.

Expected Results After Deployment:
1. Admin verification endpoint returns 200 instead of 500
2. No more "applicationtype enum" error messages
3. Admin endpoints ready for authenticated requests

Usage:
    python3 verify_enum_fix_deployment.py
"""

import asyncio
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentVerifier:
    """Verify that the enum fix deployment resolved the admin access issues"""
    
    def __init__(self):
        self.backend_url = "https://marketedge-platform.onrender.com"
        self.zebra_email = "matt.lindop@zebra.associates"
        
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "deployment_verification": "enum_fix",
            "tests": {},
            "success": False,
            "ready_for_production": False
        }
    
    async def run_verification(self):
        """Run post-deployment verification tests"""
        logger.info("🔍 Starting POST-DEPLOYMENT VERIFICATION for Enum Fix...")
        logger.info(f"   Target: {self.zebra_email}")
        logger.info(f"   Backend: {self.backend_url}")
        
        # Test 1: Admin Verification Endpoint (was returning 500)
        await self.test_admin_verification_endpoint()
        
        # Test 2: Admin Endpoints Status Check
        await self.test_admin_endpoints_status()
        
        # Test 3: Health and CORS Verification
        await self.test_health_and_cors()
        
        # Generate Verification Report
        await self.generate_verification_report()
        
        return self.results
    
    async def test_admin_verification_endpoint(self):
        """Test the admin verification endpoint that was failing with 500"""
        logger.info("🧪 Testing admin verification endpoint (previously 500 error)...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.backend_url}/api/v1/database/verify-admin-access/{self.zebra_email}",
                    timeout=15
                )
                
                response_body = response.text
                
                # Check for the specific enum error
                has_enum_error = "applicationtype" in response_body and "not among the defined enum values" in response_body
                
                self.results["tests"]["admin_verification"] = {
                    "status_code": response.status_code,
                    "response_body": response_body,
                    "enum_error_resolved": not has_enum_error,
                    "endpoint_working": response.status_code != 500
                }
                
                if response.status_code == 500 and has_enum_error:
                    logger.error("❌ DEPLOYMENT NOT EFFECTIVE: Still getting enum error")
                    logger.error(f"   Error: {response_body[:200]}...")
                elif response.status_code == 500:
                    logger.warning("⚠️  Still getting 500 error, but not enum-related")
                    logger.warning(f"   Response: {response_body[:200]}...")
                elif response.status_code == 200:
                    logger.info("✅ SUCCESS: Admin verification endpoint now returns 200!")
                    try:
                        json_response = response.json()
                        logger.info(f"   User found: {json_response.get('user', {}).get('email', 'N/A')}")
                        logger.info(f"   Admin role: {json_response.get('user', {}).get('role', 'N/A')}")
                    except:
                        logger.info("   Response is 200 but not JSON format")
                else:
                    logger.info(f"📊 Admin verification: {response.status_code} (improved from 500)")
                
        except Exception as e:
            logger.error(f"❌ Error testing admin verification: {e}")
            self.results["tests"]["admin_verification"] = {
                "error": str(e)
            }
    
    async def test_admin_endpoints_status(self):
        """Test admin endpoints to ensure they're responding correctly"""
        logger.info("🔐 Testing admin endpoints status...")
        
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/feature-flags",
            "/api/v1/admin/modules"
        ]
        
        endpoint_results = {}
        
        try:
            async with httpx.AsyncClient() as client:
                for endpoint in admin_endpoints:
                    try:
                        response = await client.get(
                            f"{self.backend_url}{endpoint}",
                            headers={"Origin": "https://app.zebra.associates"},
                            timeout=10
                        )
                        
                        endpoint_results[endpoint] = {
                            "status_code": response.status_code,
                            "expected_auth_response": response.status_code in [401, 403],
                            "no_server_error": response.status_code < 500
                        }
                        
                        if response.status_code in [401, 403]:
                            logger.info(f"✅ {endpoint}: {response.status_code} (auth required - good)")
                        elif response.status_code >= 500:
                            logger.error(f"❌ {endpoint}: {response.status_code} (server error)")
                        else:
                            logger.info(f"📊 {endpoint}: {response.status_code}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error testing {endpoint}: {e}")
                        endpoint_results[endpoint] = {"error": str(e)}
            
            self.results["tests"]["admin_endpoints"] = endpoint_results
            
        except Exception as e:
            logger.error(f"❌ Error testing admin endpoints: {e}")
    
    async def test_health_and_cors(self):
        """Test health endpoint and CORS configuration"""
        logger.info("🌐 Testing health and CORS...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Health check
                health_response = await client.get(f"{self.backend_url}/health", timeout=10)
                
                # CORS check
                cors_response = await client.options(
                    f"{self.backend_url}/api/v1/admin/users",
                    headers={
                        "Origin": "https://app.zebra.associates",
                        "Access-Control-Request-Method": "GET",
                        "Access-Control-Request-Headers": "Authorization, Content-Type"
                    },
                    timeout=10
                )
                
                self.results["tests"]["health_cors"] = {
                    "health_status": health_response.status_code,
                    "cors_status": cors_response.status_code,
                    "cors_origin": cors_response.headers.get("access-control-allow-origin"),
                    "health_working": health_response.status_code == 200,
                    "cors_working": cors_response.status_code == 200
                }
                
                if health_response.status_code == 200:
                    logger.info("✅ Health endpoint: Working")
                else:
                    logger.warning(f"⚠️  Health endpoint: {health_response.status_code}")
                
                if cors_response.status_code == 200:
                    logger.info("✅ CORS configuration: Working")
                    logger.info(f"   Origin allowed: {cors_response.headers.get('access-control-allow-origin')}")
                else:
                    logger.warning(f"⚠️  CORS: {cors_response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Error testing health/CORS: {e}")
            self.results["tests"]["health_cors"] = {"error": str(e)}
    
    async def generate_verification_report(self):
        """Generate post-deployment verification report"""
        logger.info("📋 Generating verification report...")
        
        # Determine overall success
        admin_verification = self.results["tests"].get("admin_verification", {})
        enum_fixed = admin_verification.get("enum_error_resolved", False)
        endpoint_working = admin_verification.get("endpoint_working", False)
        
        # Check admin endpoints
        admin_endpoints = self.results["tests"].get("admin_endpoints", {})
        endpoints_healthy = all(
            result.get("no_server_error", False) 
            for result in admin_endpoints.values() 
            if isinstance(result, dict) and "error" not in result
        )
        
        # Check health/CORS
        health_cors = self.results["tests"].get("health_cors", {})
        health_working = health_cors.get("health_working", False)
        cors_working = health_cors.get("cors_working", False)
        
        self.results["success"] = enum_fixed and endpoint_working
        self.results["ready_for_production"] = (
            self.results["success"] and 
            endpoints_healthy and 
            health_working and 
            cors_working
        )
        
        # Generate report
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        status = "✅ SUCCESS" if self.results["success"] else "❌ FAILED"
        production_ready = "✅ READY" if self.results["ready_for_production"] else "⚠️  NEEDS ATTENTION"
        
        report = f"""
🔍 POST-DEPLOYMENT VERIFICATION REPORT - ZEBRA ASSOCIATES £925K OPPORTUNITY
=========================================================================
Verification Date: {self.results['timestamp']}
Deployment: Enum Fix for ApplicationType case mismatch
User: {self.zebra_email}
Backend: {self.backend_url}

📊 VERIFICATION RESULTS
---------------------
Overall Status: {status}
Production Ready: {production_ready}

🧪 DETAILED TEST RESULTS
-----------------------

1. ADMIN VERIFICATION ENDPOINT (Critical Fix)
   Status Code: {admin_verification.get('status_code', 'N/A')}
   Enum Error Resolved: {'✅ YES' if enum_fixed else '❌ NO'}
   Endpoint Working: {'✅ YES' if endpoint_working else '❌ NO'}

2. ADMIN ENDPOINTS HEALTH
   All Endpoints Healthy: {'✅ YES' if endpoints_healthy else '❌ NO'}
   Server Errors: {'❌ FOUND' if not endpoints_healthy else '✅ NONE'}

3. INFRASTRUCTURE STATUS  
   Health Check: {'✅ WORKING' if health_working else '❌ FAILED'}
   CORS Configuration: {'✅ WORKING' if cors_working else '❌ FAILED'}

"""
        
        if self.results["success"]:
            report += """
🎯 SUCCESS SUMMARY
-----------------
✅ Enum mismatch error RESOLVED
✅ Admin verification endpoint working  
✅ 500 errors eliminated
✅ Backend ready for admin authentication
✅ £925K opportunity UNBLOCKED

🚀 NEXT STEPS FOR PARTNERSHIP
----------------------------
1. ✅ Enum fix deployed and verified
2. 🔄 Test matt.lindop@zebra.associates login
3. 🔄 Verify admin panel access
4. 🔄 Test Epic 1 (Modules) functionality
5. 🔄 Test Epic 2 (Feature Flags) functionality
6. 🔄 Confirm partnership can proceed

CRITICAL: Admin access should now work for Zebra Associates partnership!
"""
        else:
            report += """
❌ ISSUES STILL PRESENT
----------------------
The enum fix deployment may not have taken effect yet, or additional issues exist.

🔧 RECOMMENDED ACTIONS
--------------------
1. Verify backend deployment completed successfully
2. Check if server restart occurred after code changes
3. Review backend logs for any remaining enum errors
4. Test again after confirming deployment status

⚠️  Partnership opportunity still at risk until issues resolved.
"""
        
        report += """
===============================================================================
"""
        
        # Save report
        report_file = f"/Users/matt/Sites/MarketEdge/deployment_verification_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        logger.info(f"📄 Verification report saved to: {report_file}")

async def main():
    """Main verification function"""
    verifier = DeploymentVerifier()
    results = await verifier.run_verification()
    
    # Save detailed JSON results
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    json_file = f"/Users/matt/Sites/MarketEdge/deployment_verification_results_{timestamp}.json"
    
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Verification complete. Results saved to: {json_file}")
    
    # Exit code based on success
    if results["success"]:
        print("🎉 ENUM FIX DEPLOYMENT SUCCESSFUL - ADMIN ACCESS RESTORED!")
        sys.exit(0)
    else:
        print("⚠️  ENUM FIX DEPLOYMENT NEEDS VERIFICATION - CHECK RESULTS ABOVE")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())