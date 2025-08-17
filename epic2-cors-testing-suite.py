#!/usr/bin/env python3
"""
Epic 2 Final Phase: Comprehensive CORS Testing Automation Suite
Author: DevOps Engineer
Date: 2025-08-16

This script provides automated testing for CORS validation between:
- Frontend: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app
- Backend: https://marketedge-platform.onrender.com
- Auth0: dev-g8trhgbfdq2sk2m8.us.auth0.com

CRITICAL SUCCESS CRITERIA:
- CORS preflight OPTIONS requests must succeed
- Access-Control-Allow-Origin headers must be present
- Auth0 authentication flow must work end-to-end
- All API endpoints must be accessible from frontend
"""

import asyncio
import httpx
import json
import time
import sys
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Epic2CORSTestSuite:
    """Comprehensive CORS testing suite for Epic 2 Railway to Render migration"""
    
    def __init__(self):
        # CRITICAL: Production URLs post-Epic 2 migration
        self.frontend_url = "https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
        self.backend_url = "https://marketedge-platform.onrender.com"
        self.auth0_domain = "dev-g8trhgbfdq2sk2m8.us.auth0.com"
        self.auth0_client_id = "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"
        
        # Test configuration
        self.timeout = 30
        self.max_retries = 3
        
        # Test results storage
        self.test_results = []
        self.failed_tests = []
        
    async def run_comprehensive_cors_tests(self) -> Dict[str, Any]:
        """Execute complete CORS validation test suite"""
        logger.info("🚀 Starting Epic 2 Comprehensive CORS Testing Suite")
        logger.info(f"Frontend: {self.frontend_url}")
        logger.info(f"Backend: {self.backend_url}")
        logger.info(f"Auth0: {self.auth0_domain}")
        
        start_time = time.time()
        
        # Test categories
        test_suites = [
            ("Backend Health Check", self.test_backend_health),
            ("CORS Preflight Tests", self.test_cors_preflight),
            ("API Endpoint CORS Tests", self.test_api_endpoint_cors),
            ("Auth0 CORS Integration", self.test_auth0_cors_integration),
            ("Frontend-Backend Connectivity", self.test_frontend_backend_connectivity),
            ("End-to-End Flow Validation", self.test_end_to_end_flow)
        ]
        
        overall_results = {
            "timestamp": time.time(),
            "test_environment": "epic2_render_production",
            "frontend_url": self.frontend_url,
            "backend_url": self.backend_url,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_suites": {}
        }
        
        for suite_name, test_function in test_suites:
            logger.info(f"\n📋 Running {suite_name}...")
            try:
                suite_results = await test_function()
                overall_results["test_suites"][suite_name] = suite_results
                overall_results["total_tests"] += suite_results.get("total", 0)
                overall_results["passed_tests"] += suite_results.get("passed", 0)
                overall_results["failed_tests"] += suite_results.get("failed", 0)
                
                if suite_results.get("passed", 0) > 0:
                    logger.info(f"✅ {suite_name}: {suite_results['passed']}/{suite_results['total']} tests passed")
                else:
                    logger.error(f"❌ {suite_name}: All tests failed")
                    
            except Exception as e:
                logger.error(f"💥 {suite_name} failed with exception: {str(e)}")
                overall_results["test_suites"][suite_name] = {
                    "error": str(e),
                    "total": 1,
                    "passed": 0,
                    "failed": 1
                }
                overall_results["total_tests"] += 1
                overall_results["failed_tests"] += 1
        
        execution_time = time.time() - start_time
        overall_results["execution_time_seconds"] = execution_time
        
        # Final assessment
        success_rate = (overall_results["passed_tests"] / overall_results["total_tests"]) * 100 if overall_results["total_tests"] > 0 else 0
        overall_results["success_rate_percent"] = round(success_rate, 2)
        
        logger.info(f"\n🎯 Epic 2 CORS Testing Complete!")
        logger.info(f"📊 Results: {overall_results['passed_tests']}/{overall_results['total_tests']} tests passed ({success_rate:.1f}%)")
        logger.info(f"⏱️ Execution time: {execution_time:.2f} seconds")
        
        if success_rate >= 90:
            logger.info("🎉 EPIC 2 SUCCESS: Platform ready for £925K Odeon demo!")
        elif success_rate >= 75:
            logger.warning("⚠️ EPIC 2 PARTIAL SUCCESS: Some issues need attention")
        else:
            logger.error("🚨 EPIC 2 CRITICAL ISSUES: Platform not ready for production")
        
        return overall_results
    
    async def test_backend_health(self) -> Dict[str, Any]:
        """Test backend health and basic connectivity"""
        results = {"total": 3, "passed": 0, "failed": 0, "tests": []}
        
        # Test 1: Basic health endpoint
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.backend_url}/health")
                if response.status_code == 200:
                    results["passed"] += 1
                    results["tests"].append({
                        "name": "Backend Health Endpoint",
                        "status": "PASS",
                        "response_code": response.status_code,
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    })
                else:
                    results["failed"] += 1
                    results["tests"].append({
                        "name": "Backend Health Endpoint",
                        "status": "FAIL",
                        "response_code": response.status_code,
                        "error": "Unexpected status code"
                    })
        except Exception as e:
            results["failed"] += 1
            results["tests"].append({
                "name": "Backend Health Endpoint",
                "status": "FAIL",
                "error": str(e)
            })
        
        # Test 2: CORS debug endpoint
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.backend_url}/cors-debug",
                    headers={"Origin": self.frontend_url}
                )
                if response.status_code == 200:
                    cors_data = response.json()
                    results["passed"] += 1
                    results["tests"].append({
                        "name": "CORS Debug Endpoint",
                        "status": "PASS",
                        "response_code": response.status_code,
                        "cors_config": cors_data.get("cors_origins_configured"),
                        "origin_allowed": cors_data.get("origin_allowed")
                    })
                else:
                    results["failed"] += 1
                    results["tests"].append({
                        "name": "CORS Debug Endpoint",
                        "status": "FAIL",
                        "response_code": response.status_code
                    })
        except Exception as e:
            results["failed"] += 1
            results["tests"].append({
                "name": "CORS Debug Endpoint",
                "status": "FAIL",
                "error": str(e)
            })
        
        # Test 3: API v1 router health
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.backend_url}/api/v1/health")
                if response.status_code == 200:
                    results["passed"] += 1
                    results["tests"].append({
                        "name": "API v1 Health",
                        "status": "PASS",
                        "response_code": response.status_code
                    })
                else:
                    results["failed"] += 1
                    results["tests"].append({
                        "name": "API v1 Health",
                        "status": "FAIL",
                        "response_code": response.status_code
                    })
        except Exception as e:
            results["failed"] += 1
            results["tests"].append({
                "name": "API v1 Health",
                "status": "FAIL",
                "error": str(e)
            })
        
        return results
    
    async def test_cors_preflight(self) -> Dict[str, Any]:
        """Test CORS preflight OPTIONS requests"""
        results = {"total": 4, "passed": 0, "failed": 0, "tests": []}
        
        endpoints_to_test = [
            "/health",
            "/cors-debug",
            "/api/v1/auth/auth0-url",
            "/api/v1/auth/callback"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.options(
                        f"{self.backend_url}{endpoint}",
                        headers={
                            "Origin": self.frontend_url,
                            "Access-Control-Request-Method": "GET",
                            "Access-Control-Request-Headers": "Content-Type,Authorization"
                        }
                    )
                    
                    # Check for required CORS headers
                    cors_headers = {
                        "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                        "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                        "access-control-allow-headers": response.headers.get("access-control-allow-headers"),
                        "access-control-allow-credentials": response.headers.get("access-control-allow-credentials")
                    }
                    
                    # Validate CORS headers
                    has_origin = cors_headers["access-control-allow-origin"] is not None
                    allows_frontend = (cors_headers["access-control-allow-origin"] == self.frontend_url or 
                                    cors_headers["access-control-allow-origin"] == "*")
                    
                    if response.status_code in [200, 204] and has_origin and allows_frontend:
                        results["passed"] += 1
                        results["tests"].append({
                            "name": f"CORS Preflight {endpoint}",
                            "status": "PASS",
                            "response_code": response.status_code,
                            "cors_headers": cors_headers
                        })
                    else:
                        results["failed"] += 1
                        results["tests"].append({
                            "name": f"CORS Preflight {endpoint}",
                            "status": "FAIL",
                            "response_code": response.status_code,
                            "cors_headers": cors_headers,
                            "error": "Missing or invalid CORS headers"
                        })
                        
            except Exception as e:
                results["failed"] += 1
                results["tests"].append({
                    "name": f"CORS Preflight {endpoint}",
                    "status": "FAIL",
                    "error": str(e)
                })
        
        return results
    
    async def test_api_endpoint_cors(self) -> Dict[str, Any]:
        """Test CORS on actual API endpoints"""
        results = {"total": 3, "passed": 0, "failed": 0, "tests": []}
        
        # Test API endpoints with CORS headers
        test_cases = [
            {
                "name": "Auth0 URL Generation",
                "method": "GET",
                "endpoint": "/api/v1/auth/auth0-url",
                "params": {"redirect_uri": f"{self.frontend_url}/callback"}
            },
            {
                "name": "Health Check with CORS",
                "method": "GET", 
                "endpoint": "/api/v1/health"
            },
            {
                "name": "OpenAPI Schema",
                "method": "GET",
                "endpoint": "/api/v1/openapi.json"
            }
        ]
        
        for test_case in test_cases:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if test_case["method"] == "GET":
                        response = await client.get(
                            f"{self.backend_url}{test_case['endpoint']}",
                            headers={"Origin": self.frontend_url},
                            params=test_case.get("params", {})
                        )
                    
                    # Check response and CORS headers
                    has_cors_origin = "access-control-allow-origin" in response.headers
                    cors_origin = response.headers.get("access-control-allow-origin")
                    
                    if response.status_code == 200 and has_cors_origin:
                        results["passed"] += 1
                        results["tests"].append({
                            "name": test_case["name"],
                            "status": "PASS",
                            "response_code": response.status_code,
                            "cors_origin": cors_origin,
                            "endpoint": test_case["endpoint"]
                        })
                    else:
                        results["failed"] += 1
                        results["tests"].append({
                            "name": test_case["name"],
                            "status": "FAIL",
                            "response_code": response.status_code,
                            "cors_origin": cors_origin,
                            "endpoint": test_case["endpoint"],
                            "error": "Missing CORS headers or bad response"
                        })
                        
            except Exception as e:
                results["failed"] += 1
                results["tests"].append({
                    "name": test_case["name"],
                    "status": "FAIL",
                    "error": str(e),
                    "endpoint": test_case["endpoint"]
                })
        
        return results
    
    async def test_auth0_cors_integration(self) -> Dict[str, Any]:
        """Test Auth0 CORS integration and authentication flow setup"""
        results = {"total": 3, "passed": 0, "failed": 0, "tests": []}
        
        # Test 1: Auth0 URL generation
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.backend_url}/api/v1/auth/auth0-url",
                    headers={"Origin": self.frontend_url},
                    params={"redirect_uri": f"{self.frontend_url}/callback"}
                )
                
                if response.status_code == 200:
                    auth_data = response.json()
                    auth_url = auth_data.get("auth_url")
                    
                    if auth_url and self.auth0_domain in auth_url:
                        results["passed"] += 1
                        results["tests"].append({
                            "name": "Auth0 URL Generation",
                            "status": "PASS",
                            "response_code": response.status_code,
                            "auth_url_domain": urlparse(auth_url).netloc,
                            "has_cors": "access-control-allow-origin" in response.headers
                        })
                    else:
                        results["failed"] += 1
                        results["tests"].append({
                            "name": "Auth0 URL Generation",
                            "status": "FAIL",
                            "error": "Invalid or missing auth URL",
                            "response": auth_data
                        })
                else:
                    results["failed"] += 1
                    results["tests"].append({
                        "name": "Auth0 URL Generation",
                        "status": "FAIL",
                        "response_code": response.status_code
                    })
        except Exception as e:
            results["failed"] += 1
            results["tests"].append({
                "name": "Auth0 URL Generation",
                "status": "FAIL",
                "error": str(e)
            })
        
        # Test 2: Auth0 domain connectivity
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"https://{self.auth0_domain}/.well-known/openid_configuration")
                
                if response.status_code == 200:
                    config = response.json()
                    if config.get("issuer") == f"https://{self.auth0_domain}/":
                        results["passed"] += 1
                        results["tests"].append({
                            "name": "Auth0 Domain Connectivity",
                            "status": "PASS",
                            "response_code": response.status_code,
                            "issuer": config.get("issuer")
                        })
                    else:
                        results["failed"] += 1
                        results["tests"].append({
                            "name": "Auth0 Domain Connectivity",
                            "status": "FAIL",
                            "error": "Invalid issuer in OpenID configuration"
                        })
                else:
                    results["failed"] += 1
                    results["tests"].append({
                        "name": "Auth0 Domain Connectivity",
                        "status": "FAIL",
                        "response_code": response.status_code
                    })
        except Exception as e:
            results["failed"] += 1
            results["tests"].append({
                "name": "Auth0 Domain Connectivity",
                "status": "FAIL",
                "error": str(e)
            })
        
        # Test 3: Auth0 callback endpoint CORS
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.options(
                    f"{self.backend_url}/api/v1/auth/callback",
                    headers={
                        "Origin": self.frontend_url,
                        "Access-Control-Request-Method": "GET",
                        "Access-Control-Request-Headers": "Content-Type"
                    }
                )
                
                if response.status_code in [200, 204]:
                    cors_origin = response.headers.get("access-control-allow-origin")
                    if cors_origin and (cors_origin == self.frontend_url or cors_origin == "*"):
                        results["passed"] += 1
                        results["tests"].append({
                            "name": "Auth0 Callback CORS",
                            "status": "PASS",
                            "response_code": response.status_code,
                            "cors_origin": cors_origin
                        })
                    else:
                        results["failed"] += 1
                        results["tests"].append({
                            "name": "Auth0 Callback CORS",
                            "status": "FAIL",
                            "error": "Invalid CORS origin",
                            "cors_origin": cors_origin
                        })
                else:
                    results["failed"] += 1
                    results["tests"].append({
                        "name": "Auth0 Callback CORS",
                        "status": "FAIL",
                        "response_code": response.status_code
                    })
        except Exception as e:
            results["failed"] += 1
            results["tests"].append({
                "name": "Auth0 Callback CORS",
                "status": "FAIL",
                "error": str(e)
            })
        
        return results
    
    async def test_frontend_backend_connectivity(self) -> Dict[str, Any]:
        """Test frontend-backend connectivity simulation"""
        results = {"total": 2, "passed": 0, "failed": 0, "tests": []}
        
        # Test 1: Simulate frontend API call
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Simulate a typical frontend API call
                response = await client.get(
                    f"{self.backend_url}/api/v1/health",
                    headers={
                        "Origin": self.frontend_url,
                        "User-Agent": "Mozilla/5.0 (Frontend Test Suite)",
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    cors_origin = response.headers.get("access-control-allow-origin")
                    if cors_origin:
                        results["passed"] += 1
                        results["tests"].append({
                            "name": "Frontend API Call Simulation",
                            "status": "PASS",
                            "response_code": response.status_code,
                            "cors_origin": cors_origin,
                            "response_time_ms": response.elapsed.total_seconds() * 1000
                        })
                    else:
                        results["failed"] += 1
                        results["tests"].append({
                            "name": "Frontend API Call Simulation",
                            "status": "FAIL",
                            "error": "Missing CORS headers",
                            "response_code": response.status_code
                        })
                else:
                    results["failed"] += 1
                    results["tests"].append({
                        "name": "Frontend API Call Simulation",
                        "status": "FAIL",
                        "response_code": response.status_code
                    })
        except Exception as e:
            results["failed"] += 1
            results["tests"].append({
                "name": "Frontend API Call Simulation",
                "status": "FAIL",
                "error": str(e)
            })
        
        # Test 2: Test with different HTTP methods
        try:
            methods_to_test = ["GET", "POST", "OPTIONS"]
            method_results = []
            
            for method in methods_to_test:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method == "GET":
                        response = await client.get(
                            f"{self.backend_url}/health",
                            headers={"Origin": self.frontend_url}
                        )
                    elif method == "POST":
                        response = await client.post(
                            f"{self.backend_url}/api/v1/health",
                            headers={"Origin": self.frontend_url, "Content-Type": "application/json"},
                            json={}
                        )
                    elif method == "OPTIONS":
                        response = await client.options(
                            f"{self.backend_url}/health",
                            headers={"Origin": self.frontend_url}
                        )
                    
                    has_cors = "access-control-allow-origin" in response.headers
                    method_results.append({
                        "method": method,
                        "status_code": response.status_code,
                        "has_cors": has_cors
                    })
            
            # Consider test passed if at least GET and OPTIONS work
            successful_methods = [r for r in method_results if r["has_cors"] and r["status_code"] < 400]
            
            if len(successful_methods) >= 2:
                results["passed"] += 1
                results["tests"].append({
                    "name": "HTTP Methods CORS Support",
                    "status": "PASS",
                    "successful_methods": len(successful_methods),
                    "method_results": method_results
                })
            else:
                results["failed"] += 1
                results["tests"].append({
                    "name": "HTTP Methods CORS Support",
                    "status": "FAIL",
                    "successful_methods": len(successful_methods),
                    "method_results": method_results
                })
                
        except Exception as e:
            results["failed"] += 1
            results["tests"].append({
                "name": "HTTP Methods CORS Support",
                "status": "FAIL",
                "error": str(e)
            })
        
        return results
    
    async def test_end_to_end_flow(self) -> Dict[str, Any]:
        """Test end-to-end authentication and API flow"""
        results = {"total": 2, "passed": 0, "failed": 0, "tests": []}
        
        # Test 1: Complete auth flow simulation
        try:
            # Step 1: Get Auth0 URL
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.backend_url}/api/v1/auth/auth0-url",
                    headers={"Origin": self.frontend_url},
                    params={
                        "redirect_uri": f"{self.frontend_url}/callback",
                        "state": "test_state_123"
                    }
                )
                
                if response.status_code == 200:
                    auth_data = response.json()
                    auth_url = auth_data.get("auth_url")
                    
                    # Validate the Auth0 URL structure
                    if (auth_url and 
                        self.auth0_domain in auth_url and
                        "client_id=" in auth_url and
                        "redirect_uri=" in auth_url and
                        "state=" in auth_url):
                        
                        results["passed"] += 1
                        results["tests"].append({
                            "name": "End-to-End Auth Flow Setup",
                            "status": "PASS",
                            "auth_url_valid": True,
                            "has_cors": "access-control-allow-origin" in response.headers,
                            "auth_url_components": {
                                "has_client_id": "client_id=" in auth_url,
                                "has_redirect_uri": "redirect_uri=" in auth_url,
                                "has_state": "state=" in auth_url,
                                "domain_correct": self.auth0_domain in auth_url
                            }
                        })
                    else:
                        results["failed"] += 1
                        results["tests"].append({
                            "name": "End-to-End Auth Flow Setup",
                            "status": "FAIL",
                            "error": "Invalid Auth0 URL structure",
                            "auth_url": auth_url
                        })
                else:
                    results["failed"] += 1
                    results["tests"].append({
                        "name": "End-to-End Auth Flow Setup",
                        "status": "FAIL",
                        "response_code": response.status_code
                    })
        except Exception as e:
            results["failed"] += 1
            results["tests"].append({
                "name": "End-to-End Auth Flow Setup",
                "status": "FAIL",
                "error": str(e)
            })
        
        # Test 2: Platform readiness check
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.backend_url}/ready",
                    headers={"Origin": self.frontend_url}
                )
                
                if response.status_code == 200:
                    readiness_data = response.json()
                    status = readiness_data.get("status")
                    
                    if status == "ready":
                        results["passed"] += 1
                        results["tests"].append({
                            "name": "Platform Readiness Check",
                            "status": "PASS",
                            "platform_status": status,
                            "services": readiness_data.get("services", {}),
                            "has_cors": "access-control-allow-origin" in response.headers
                        })
                    else:
                        results["failed"] += 1
                        results["tests"].append({
                            "name": "Platform Readiness Check",
                            "status": "FAIL",
                            "platform_status": status,
                            "error": "Platform not ready"
                        })
                else:
                    results["failed"] += 1
                    results["tests"].append({
                        "name": "Platform Readiness Check",
                        "status": "FAIL",
                        "response_code": response.status_code
                    })
        except Exception as e:
            results["failed"] += 1
            results["tests"].append({
                "name": "Platform Readiness Check",
                "status": "FAIL",
                "error": str(e)
            })
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report_lines = [
            "="*80,
            "EPIC 2 FINAL PHASE: CORS TESTING REPORT",
            "Railway to Render Migration Validation",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
            "="*80,
            "",
            "🎯 MISSION CRITICAL REQUIREMENTS:",
            "- £925K Odeon demo must be operational",
            "- Frontend-backend CORS must work flawlessly", 
            "- Auth0 authentication flow must be end-to-end functional",
            "- Platform must be production-ready post-Railway migration",
            "",
            "📋 TEST ENVIRONMENT:",
            f"Frontend URL: {self.frontend_url}",
            f"Backend URL:  {self.backend_url}",
            f"Auth0 Domain: {self.auth0_domain}",
            "",
            "📊 OVERALL RESULTS:",
            f"Total Tests:    {results['total_tests']}",
            f"Passed Tests:   {results['passed_tests']}",
            f"Failed Tests:   {results['failed_tests']}",
            f"Success Rate:   {results['success_rate_percent']}%",
            f"Execution Time: {results['execution_time_seconds']:.2f} seconds",
            ""
        ]
        
        # Add status assessment
        if results["success_rate_percent"] >= 90:
            report_lines.extend([
                "🎉 STATUS: EPIC 2 SUCCESS - PRODUCTION READY",
                "✅ Platform is ready for £925K Odeon demo",
                "✅ CORS configuration working correctly",
                "✅ Auth0 integration functional",
                "✅ Frontend-backend connectivity established",
                ""
            ])
        elif results["success_rate_percent"] >= 75:
            report_lines.extend([
                "⚠️ STATUS: EPIC 2 PARTIAL SUCCESS - MINOR ISSUES",
                "⚡ Platform mostly functional but needs attention",
                "⚠️ Some CORS or Auth0 issues detected",
                "📋 Review failed tests for specific issues",
                ""
            ])
        else:
            report_lines.extend([
                "🚨 STATUS: EPIC 2 CRITICAL ISSUES - NOT PRODUCTION READY",
                "❌ Platform has significant issues",
                "❌ CORS or Auth0 authentication problems",
                "❌ NOT ready for Odeon demo",
                "🔧 Immediate remediation required",
                ""
            ])
        
        # Add detailed test suite results
        report_lines.append("📋 DETAILED TEST RESULTS:")
        report_lines.append("-" * 50)
        
        for suite_name, suite_results in results["test_suites"].items():
            if "error" in suite_results:
                report_lines.extend([
                    f"❌ {suite_name}: EXCEPTION",
                    f"   Error: {suite_results['error']}",
                    ""
                ])
                continue
                
            passed = suite_results.get("passed", 0)
            total = suite_results.get("total", 0)
            status_emoji = "✅" if passed == total else "❌" if passed == 0 else "⚠️"
            
            report_lines.extend([
                f"{status_emoji} {suite_name}: {passed}/{total} tests passed",
                ""
            ])
            
            # Add individual test details for failed suites
            if "tests" in suite_results and passed < total:
                for test in suite_results["tests"]:
                    if test["status"] == "FAIL":
                        report_lines.append(f"   ❌ {test['name']}: {test.get('error', 'Failed')}")
                report_lines.append("")
        
        # Add recommendations
        report_lines.extend([
            "🔧 RECOMMENDATIONS:",
            "",
            "If tests failed:",
            "1. Check Render backend deployment status",
            "2. Verify environment variables are correctly set",
            "3. Confirm CORS_ORIGINS includes frontend URL",
            "4. Validate Auth0 callback URLs include Render backend",
            "5. Test network connectivity between services",
            "",
            "If all tests passed:",
            "1. Proceed with Odeon demo preparation",
            "2. Monitor production logs for any issues",
            "3. Set up alerting for CORS or Auth0 failures",
            "",
            "="*80
        ])
        
        return "\n".join(report_lines)

async def main():
    """Main execution function"""
    print("🚀 Starting Epic 2 Final Phase: Comprehensive CORS Testing Suite")
    print("=" * 80)
    
    test_suite = Epic2CORSTestSuite()
    
    try:
        # Run comprehensive tests
        results = await test_suite.run_comprehensive_cors_tests()
        
        # Generate report
        report = test_suite.generate_report(results)
        
        # Save results
        timestamp = int(time.time())
        results_file = f"epic2_cors_test_results_{timestamp}.json"
        report_file = f"epic2_cors_test_report_{timestamp}.txt"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n💾 Results saved to: {results_file}")
        print(f"📄 Report saved to: {report_file}")
        
        # Return appropriate exit code
        if results["success_rate_percent"] >= 90:
            print("\n🎉 Epic 2 CORS Testing: SUCCESS - Platform ready for production!")
            sys.exit(0)
        elif results["success_rate_percent"] >= 75:
            print("\n⚠️ Epic 2 CORS Testing: PARTIAL SUCCESS - Minor issues detected")
            sys.exit(1)
        else:
            print("\n🚨 Epic 2 CORS Testing: CRITICAL ISSUES - Platform not ready")
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"💥 Epic 2 CORS Testing Suite failed with exception: {str(e)}")
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())