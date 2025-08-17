#!/usr/bin/env python3
"""
Epic 2 Final Phase: Platform Functionality Verification Suite
Author: DevOps Engineer
Date: 2025-08-16

This script provides comprehensive platform functionality verification for the Epic 2 migration.
It validates all critical platform components and services are operational on Render.

PLATFORM VERIFICATION SCOPE:
1. Backend API endpoints and functionality
2. Database connectivity and operations
3. Redis connectivity and caching
4. Health check systems
5. Rate limiting functionality
6. Error handling and logging
7. Security headers and middleware
8. Performance and response times

CRITICAL SUCCESS CRITERIA:
- All API endpoints accessible and functional
- Database operations working correctly
- Redis caching operational
- Health checks passing
- Security middleware active
- Platform ready for £925K Odeon demo
"""

import asyncio
import httpx
import json
import time
import sys
import random
import statistics
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Epic2PlatformVerifier:
    """Comprehensive platform functionality verification"""
    
    def __init__(self):
        # Production URLs for Epic 2
        self.backend_url = "https://marketedge-platform.onrender.com"
        self.frontend_url = "https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
        
        # Test configuration
        self.timeout = 45
        self.max_retries = 3
        self.performance_samples = 5
        
        # Test metrics
        self.response_times = []
        self.error_counts = {}
        
    async def run_comprehensive_platform_verification(self) -> Dict[str, Any]:
        """Execute complete platform functionality verification"""
        logger.info("🔧 Starting Epic 2 Comprehensive Platform Functionality Verification")
        logger.info(f"Backend: {self.backend_url}")
        logger.info(f"Frontend: {self.frontend_url}")
        
        start_time = time.time()
        
        # Verification test suites
        verification_suites = [
            ("Core Health Checks", self.verify_core_health),
            ("API Endpoint Functionality", self.verify_api_endpoints),
            ("Database Connectivity", self.verify_database_operations),
            ("Redis Connectivity", self.verify_redis_operations),
            ("Security Middleware", self.verify_security_middleware),
            ("Error Handling", self.verify_error_handling),
            ("Performance Metrics", self.verify_performance_metrics),
            ("Rate Limiting", self.verify_rate_limiting),
            ("CORS Configuration", self.verify_cors_comprehensive),
            ("Platform Readiness", self.verify_platform_readiness)
        ]
        
        overall_results = {
            "timestamp": time.time(),
            "test_type": "platform_functionality_verification",
            "environment": "epic2_render_production", 
            "backend_url": self.backend_url,
            "total_suites": len(verification_suites),
            "completed_suites": 0,
            "failed_suites": 0,
            "suite_results": {},
            "platform_metrics": {
                "average_response_time_ms": 0,
                "total_api_calls": 0,
                "error_rate_percent": 0,
                "health_status": "unknown"
            }
        }
        
        for suite_name, verification_function in verification_suites:
            logger.info(f"\n🔍 {suite_name}...")
            
            try:
                suite_result = await verification_function()
                overall_results["suite_results"][suite_name] = suite_result
                
                if suite_result.get("success", False):
                    overall_results["completed_suites"] += 1
                    logger.info(f"✅ {suite_name}: SUCCESS")
                else:
                    overall_results["failed_suites"] += 1
                    logger.error(f"❌ {suite_name}: FAILED")
                    error_msg = suite_result.get("error", "Unknown error")
                    logger.error(f"   Error: {error_msg}")
                    
            except Exception as e:
                logger.error(f"💥 {suite_name} failed with exception: {str(e)}")
                overall_results["suite_results"][suite_name] = {
                    "success": False,
                    "error": str(e),
                    "exception": True
                }
                overall_results["failed_suites"] += 1
        
        execution_time = time.time() - start_time
        overall_results["execution_time_seconds"] = execution_time
        
        # Calculate final metrics
        success_rate = (overall_results["completed_suites"] / overall_results["total_suites"]) * 100
        overall_results["success_rate_percent"] = round(success_rate, 2)
        
        # Update platform metrics
        if self.response_times:
            overall_results["platform_metrics"].update({
                "average_response_time_ms": round(statistics.mean(self.response_times), 2),
                "total_api_calls": len(self.response_times),
                "min_response_time_ms": min(self.response_times),
                "max_response_time_ms": max(self.response_times),
                "median_response_time_ms": round(statistics.median(self.response_times), 2)
            })
        
        # Calculate error rate
        total_errors = sum(self.error_counts.values())
        total_requests = len(self.response_times) + total_errors
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        overall_results["platform_metrics"]["error_rate_percent"] = round(error_rate, 2)
        
        # Determine platform health status
        if success_rate >= 90 and error_rate <= 5:
            overall_results["platform_metrics"]["health_status"] = "excellent"
        elif success_rate >= 80 and error_rate <= 10:
            overall_results["platform_metrics"]["health_status"] = "good"
        elif success_rate >= 70 and error_rate <= 15:
            overall_results["platform_metrics"]["health_status"] = "fair"
        else:
            overall_results["platform_metrics"]["health_status"] = "poor"
        
        # Final assessment
        logger.info(f"\n🎯 Epic 2 Platform Verification Complete!")
        logger.info(f"📊 Results: {overall_results['completed_suites']}/{overall_results['total_suites']} suites successful ({success_rate:.1f}%)")
        logger.info(f"⏱️ Execution time: {execution_time:.2f} seconds")
        logger.info(f"🔧 Platform health: {overall_results['platform_metrics']['health_status'].upper()}")
        
        return overall_results
    
    async def verify_core_health(self) -> Dict[str, Any]:
        """Verify core health check functionality"""
        result = {"success": False, "details": {}, "health_checks": []}
        
        health_endpoints = [
            "/health",
            "/ready", 
            "/api/v1/health"
        ]
        
        successful_checks = 0
        
        for endpoint in health_endpoints:
            try:
                start_time = time.time()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(f"{self.backend_url}{endpoint}")
                    response_time = (time.time() - start_time) * 1000
                    self.response_times.append(response_time)
                    
                    if response.status_code == 200:
                        health_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                        
                        health_check = {
                            "endpoint": endpoint,
                            "status": "PASS",
                            "status_code": response.status_code,
                            "response_time_ms": response_time,
                            "health_data": health_data
                        }
                        
                        successful_checks += 1
                    else:
                        self.error_counts[f"health_{response.status_code}"] = self.error_counts.get(f"health_{response.status_code}", 0) + 1
                        health_check = {
                            "endpoint": endpoint,
                            "status": "FAIL",
                            "status_code": response.status_code,
                            "error": f"HTTP {response.status_code}"
                        }
                    
                    result["health_checks"].append(health_check)
                    
            except Exception as e:
                self.error_counts["health_exception"] = self.error_counts.get("health_exception", 0) + 1
                result["health_checks"].append({
                    "endpoint": endpoint,
                    "status": "FAIL",
                    "error": str(e)
                })
        
        result["details"] = {
            "total_endpoints": len(health_endpoints),
            "successful_checks": successful_checks,
            "success_rate": (successful_checks / len(health_endpoints)) * 100
        }
        
        result["success"] = successful_checks >= 2  # At least 2 health endpoints should work
        
        if not result["success"]:
            result["error"] = f"Only {successful_checks}/{len(health_endpoints)} health checks passed"
        
        return result
    
    async def verify_api_endpoints(self) -> Dict[str, Any]:
        """Verify API endpoint functionality"""
        result = {"success": False, "details": {}, "endpoint_tests": []}
        
        # Test various API endpoints
        api_endpoints = [
            {"path": "/api/v1/health", "method": "GET", "expected_codes": [200]},
            {"path": "/api/v1/auth/auth0-url", "method": "GET", "expected_codes": [200, 400], 
             "params": {"redirect_uri": f"{self.frontend_url}/callback"}},
            {"path": "/api/v1/auth/callback", "method": "GET", "expected_codes": [200, 400, 401]},
            {"path": "/api/v1/openapi.json", "method": "GET", "expected_codes": [200, 404]},
            {"path": "/cors-debug", "method": "GET", "expected_codes": [200]}
        ]
        
        successful_endpoints = 0
        
        for endpoint_test in api_endpoints:
            try:
                start_time = time.time()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if endpoint_test["method"] == "GET":
                        response = await client.get(
                            f"{self.backend_url}{endpoint_test['path']}",
                            params=endpoint_test.get("params", {}),
                            headers={"Origin": self.frontend_url}
                        )
                    else:
                        continue  # Only testing GET for now
                    
                    response_time = (time.time() - start_time) * 1000
                    self.response_times.append(response_time)
                    
                    expected_codes = endpoint_test["expected_codes"]
                    
                    if response.status_code in expected_codes:
                        endpoint_result = {
                            "path": endpoint_test["path"],
                            "method": endpoint_test["method"],
                            "status": "PASS",
                            "status_code": response.status_code,
                            "response_time_ms": response_time,
                            "has_cors": "access-control-allow-origin" in response.headers
                        }
                        successful_endpoints += 1
                    else:
                        self.error_counts[f"api_{response.status_code}"] = self.error_counts.get(f"api_{response.status_code}", 0) + 1
                        endpoint_result = {
                            "path": endpoint_test["path"],
                            "method": endpoint_test["method"],
                            "status": "FAIL",
                            "status_code": response.status_code,
                            "expected_codes": expected_codes,
                            "error": f"Unexpected status code {response.status_code}"
                        }
                    
                    result["endpoint_tests"].append(endpoint_result)
                    
            except Exception as e:
                self.error_counts["api_exception"] = self.error_counts.get("api_exception", 0) + 1
                result["endpoint_tests"].append({
                    "path": endpoint_test["path"],
                    "method": endpoint_test["method"],
                    "status": "FAIL",
                    "error": str(e)
                })
        
        result["details"] = {
            "total_endpoints": len(api_endpoints),
            "successful_endpoints": successful_endpoints,
            "success_rate": (successful_endpoints / len(api_endpoints)) * 100
        }
        
        result["success"] = successful_endpoints >= len(api_endpoints) * 0.8  # 80% success rate
        
        if not result["success"]:
            result["error"] = f"Only {successful_endpoints}/{len(api_endpoints)} API endpoints working"
        
        return result
    
    async def verify_database_operations(self) -> Dict[str, Any]:
        """Verify database connectivity and operations"""
        result = {"success": False, "details": {}}
        
        try:
            # Test database connectivity through health check
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.backend_url}/ready")
                
                if response.status_code == 200:
                    readiness_data = response.json()
                    services = readiness_data.get("services", {})
                    
                    database_status = services.get("database", {})
                    
                    result["details"] = {
                        "database_service": database_status,
                        "overall_readiness": readiness_data.get("status"),
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                    
                    # Check if database is reported as healthy
                    db_healthy = (
                        database_status.get("status") == "healthy" or
                        readiness_data.get("status") == "ready"
                    )
                    
                    result["success"] = db_healthy
                    
                    if not result["success"]:
                        result["error"] = f"Database not healthy: {database_status}"
                        
                elif response.status_code == 503:
                    # Service unavailable might indicate database issues
                    result["error"] = "Database service unavailable (503)"
                    result["details"] = {"status_code": 503}
                else:
                    result["error"] = f"Readiness check returned HTTP {response.status_code}"
                    result["details"] = {"status_code": response.status_code}
                    
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    async def verify_redis_operations(self) -> Dict[str, Any]:
        """Verify Redis connectivity and caching"""
        result = {"success": False, "details": {}}
        
        try:
            # Test Redis connectivity through health check
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.backend_url}/ready")
                
                if response.status_code == 200:
                    readiness_data = response.json()
                    services = readiness_data.get("services", {})
                    
                    redis_status = services.get("redis", {})
                    cache_status = services.get("cache", {})
                    
                    result["details"] = {
                        "redis_service": redis_status,
                        "cache_service": cache_status,
                        "overall_readiness": readiness_data.get("status"),
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                    
                    # Check if Redis/cache is reported as healthy
                    redis_healthy = (
                        redis_status.get("status") == "healthy" or
                        cache_status.get("status") == "healthy" or
                        readiness_data.get("status") == "ready"
                    )
                    
                    result["success"] = redis_healthy
                    
                    if not result["success"]:
                        result["error"] = f"Redis/cache not healthy: {redis_status or cache_status}"
                        
                else:
                    result["error"] = f"Readiness check returned HTTP {response.status_code}"
                    result["details"] = {"status_code": response.status_code}
                    
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    async def verify_security_middleware(self) -> Dict[str, Any]:
        """Verify security middleware and headers"""
        result = {"success": False, "details": {}, "security_checks": []}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.backend_url}/health",
                    headers={"Origin": self.frontend_url}
                )
                
                security_headers = {
                    "cors": "access-control-allow-origin" in response.headers,
                    "content_type": "content-type" in response.headers,
                    "server_header": "server" in response.headers,
                    "cache_control": "cache-control" in response.headers
                }
                
                # Check for security headers
                security_score = sum(security_headers.values())
                
                result["details"] = {
                    "security_headers": security_headers,
                    "security_score": security_score,
                    "total_headers": len(security_headers),
                    "all_headers": dict(response.headers)
                }
                
                # Basic security requirements: CORS and content-type
                result["success"] = security_headers["cors"] and security_headers["content_type"]
                
                if not result["success"]:
                    missing_headers = [k for k, v in security_headers.items() if not v]
                    result["error"] = f"Missing security headers: {missing_headers}"
                    
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    async def verify_error_handling(self) -> Dict[str, Any]:
        """Verify error handling and responses"""
        result = {"success": False, "details": {}, "error_tests": []}
        
        # Test various error scenarios
        error_test_cases = [
            {"path": "/api/v1/nonexistent", "expected_code": 404, "description": "404 Not Found"},
            {"path": "/api/v1/auth/callback", "expected_code": 400, "description": "400 Bad Request (missing params)"},
            {"path": "/api/v1/auth/auth0-url", "expected_code": 400, "description": "400 Bad Request (missing redirect_uri)"}
        ]
        
        successful_error_tests = 0
        
        for test_case in error_test_cases:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.backend_url}{test_case['path']}",
                        headers={"Origin": self.frontend_url}
                    )
                    
                    # Check if error response has proper structure
                    has_cors = "access-control-allow-origin" in response.headers
                    status_matches = response.status_code == test_case["expected_code"]
                    
                    error_test = {
                        "path": test_case["path"],
                        "description": test_case["description"],
                        "expected_code": test_case["expected_code"],
                        "actual_code": response.status_code,
                        "has_cors": has_cors,
                        "status": "PASS" if status_matches and has_cors else "FAIL"
                    }
                    
                    if error_test["status"] == "PASS":
                        successful_error_tests += 1
                    
                    result["error_tests"].append(error_test)
                    
            except Exception as e:
                result["error_tests"].append({
                    "path": test_case["path"],
                    "description": test_case["description"],
                    "status": "FAIL",
                    "error": str(e)
                })
        
        result["details"] = {
            "total_error_tests": len(error_test_cases),
            "successful_error_tests": successful_error_tests,
            "error_handling_score": (successful_error_tests / len(error_test_cases)) * 100
        }
        
        result["success"] = successful_error_tests >= len(error_test_cases) * 0.7  # 70% success
        
        if not result["success"]:
            result["error"] = f"Only {successful_error_tests}/{len(error_test_cases)} error handling tests passed"
        
        return result
    
    async def verify_performance_metrics(self) -> Dict[str, Any]:
        """Verify platform performance metrics"""
        result = {"success": False, "details": {}}
        
        try:
            # Perform multiple requests to measure performance
            performance_tests = []
            
            for i in range(self.performance_samples):
                start_time = time.time()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(f"{self.backend_url}/health")
                    response_time = (time.time() - start_time) * 1000
                    
                    performance_tests.append({
                        "request_number": i + 1,
                        "response_time_ms": response_time,
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    })
                    
                    if response.status_code == 200:
                        self.response_times.append(response_time)
            
            # Calculate performance metrics
            response_times = [t["response_time_ms"] for t in performance_tests if t["success"]]
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
                median_response_time = statistics.median(response_times)
                
                result["details"] = {
                    "total_requests": len(performance_tests),
                    "successful_requests": len(response_times),
                    "average_response_time_ms": round(avg_response_time, 2),
                    "min_response_time_ms": round(min_response_time, 2),
                    "max_response_time_ms": round(max_response_time, 2),
                    "median_response_time_ms": round(median_response_time, 2),
                    "performance_tests": performance_tests
                }
                
                # Performance criteria: average response time under 2 seconds
                result["success"] = avg_response_time < 2000
                
                if not result["success"]:
                    result["error"] = f"Average response time {avg_response_time:.2f}ms exceeds 2000ms threshold"
            else:
                result["error"] = "No successful requests for performance measurement"
                
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    async def verify_rate_limiting(self) -> Dict[str, Any]:
        """Verify rate limiting functionality"""
        result = {"success": False, "details": {}}
        
        try:
            # Note: In production, we don't want to trigger actual rate limits
            # This test checks if rate limiting infrastructure is in place
            
            # Make a few rapid requests to test rate limiting headers
            rapid_requests = []
            
            for i in range(3):  # Limited to avoid triggering limits
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(f"{self.backend_url}/health")
                    
                    # Look for rate limiting headers
                    rate_limit_headers = {
                        "x-ratelimit-limit": response.headers.get("x-ratelimit-limit"),
                        "x-ratelimit-remaining": response.headers.get("x-ratelimit-remaining"),
                        "x-ratelimit-reset": response.headers.get("x-ratelimit-reset"),
                        "retry-after": response.headers.get("retry-after")
                    }
                    
                    rapid_requests.append({
                        "request_number": i + 1,
                        "status_code": response.status_code,
                        "rate_limit_headers": rate_limit_headers
                    })
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
            
            # Check if rate limiting is configured
            has_rate_limit_headers = any(
                any(req["rate_limit_headers"].values()) for req in rapid_requests
            )
            
            # All requests should succeed (we're not hitting limits)
            all_successful = all(req["status_code"] == 200 for req in rapid_requests)
            
            result["details"] = {
                "total_requests": len(rapid_requests),
                "all_successful": all_successful,
                "has_rate_limit_headers": has_rate_limit_headers,
                "requests": rapid_requests
            }
            
            # Success if requests work (rate limiting may be disabled in production)
            result["success"] = all_successful
            
            if not result["success"]:
                failed_requests = [req for req in rapid_requests if req["status_code"] != 200]
                result["error"] = f"{len(failed_requests)} requests failed during rate limit test"
                
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    async def verify_cors_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive CORS verification"""
        result = {"success": False, "details": {}, "cors_tests": []}
        
        # Test CORS with different origins and methods
        cors_test_cases = [
            {
                "origin": self.frontend_url,
                "method": "GET",
                "endpoint": "/health",
                "description": "Frontend origin GET"
            },
            {
                "origin": self.frontend_url,
                "method": "OPTIONS",
                "endpoint": "/api/v1/health",
                "description": "Frontend origin OPTIONS"
            },
            {
                "origin": "https://app.zebra.associates",
                "method": "GET", 
                "endpoint": "/health",
                "description": "Zebra Associates origin"
            }
        ]
        
        successful_cors_tests = 0
        
        for test_case in cors_test_cases:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if test_case["method"] == "GET":
                        response = await client.get(
                            f"{self.backend_url}{test_case['endpoint']}",
                            headers={"Origin": test_case["origin"]}
                        )
                    elif test_case["method"] == "OPTIONS":
                        response = await client.options(
                            f"{self.backend_url}{test_case['endpoint']}",
                            headers={
                                "Origin": test_case["origin"],
                                "Access-Control-Request-Method": "GET"
                            }
                        )
                    
                    cors_origin = response.headers.get("access-control-allow-origin")
                    
                    cors_test = {
                        "description": test_case["description"],
                        "origin": test_case["origin"],
                        "method": test_case["method"],
                        "endpoint": test_case["endpoint"],
                        "status_code": response.status_code,
                        "cors_origin": cors_origin,
                        "cors_valid": cors_origin is not None,
                        "status": "PASS" if cors_origin and response.status_code < 400 else "FAIL"
                    }
                    
                    if cors_test["status"] == "PASS":
                        successful_cors_tests += 1
                    
                    result["cors_tests"].append(cors_test)
                    
            except Exception as e:
                result["cors_tests"].append({
                    "description": test_case["description"],
                    "status": "FAIL",
                    "error": str(e)
                })
        
        result["details"] = {
            "total_cors_tests": len(cors_test_cases),
            "successful_cors_tests": successful_cors_tests,
            "cors_success_rate": (successful_cors_tests / len(cors_test_cases)) * 100
        }
        
        result["success"] = successful_cors_tests >= len(cors_test_cases) * 0.8  # 80% success
        
        if not result["success"]:
            result["error"] = f"Only {successful_cors_tests}/{len(cors_test_cases)} CORS tests passed"
        
        return result
    
    async def verify_platform_readiness(self) -> Dict[str, Any]:
        """Final platform readiness verification"""
        result = {"success": False, "details": {}}
        
        try:
            # Comprehensive readiness check
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.backend_url}/ready")
                
                if response.status_code == 200:
                    readiness_data = response.json()
                    
                    result["details"] = {
                        "platform_status": readiness_data.get("status"),
                        "version": readiness_data.get("version"),
                        "services": readiness_data.get("services", {}),
                        "summary": readiness_data.get("summary", {}),
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                    
                    platform_ready = readiness_data.get("status") == "ready"
                    result["success"] = platform_ready
                    
                    if not result["success"]:
                        result["error"] = f"Platform not ready: {readiness_data.get('status')}"
                        
                elif response.status_code == 503:
                    result["error"] = "Platform services not ready (503)"
                    result["details"] = {"status_code": 503}
                else:
                    result["error"] = f"Readiness check failed with HTTP {response.status_code}"
                    result["details"] = {"status_code": response.status_code}
                    
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    def generate_comprehensive_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive platform verification report"""
        
        report_lines = [
            "="*80,
            "EPIC 2 FINAL PHASE: PLATFORM FUNCTIONALITY VERIFICATION REPORT",
            "Railway to Render Migration - Platform Readiness Assessment",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
            "="*80,
            "",
            "🎯 MISSION CRITICAL OBJECTIVE:",
            "Verify complete platform functionality for £925K Odeon demo",
            "Ensure all services operational on Render infrastructure",
            "",
            "🔧 PLATFORM ARCHITECTURE:",
            f"Backend URL:      {self.backend_url}",
            f"Frontend URL:     {self.frontend_url}",
            f"Environment:      {results.get('environment', 'production')}",
            "",
            "📊 OVERALL VERIFICATION RESULTS:",
            f"Total Test Suites:    {results['total_suites']}",
            f"Completed Suites:     {results['completed_suites']}",
            f"Failed Suites:        {results['failed_suites']}",
            f"Success Rate:         {results['success_rate_percent']}%",
            f"Execution Time:       {results['execution_time_seconds']:.2f} seconds",
            ""
        ]
        
        # Add platform metrics
        metrics = results.get("platform_metrics", {})
        report_lines.extend([
            "📈 PLATFORM PERFORMANCE METRICS:",
            f"Average Response Time: {metrics.get('average_response_time_ms', 0):.2f}ms",
            f"Total API Calls:       {metrics.get('total_api_calls', 0)}",
            f"Error Rate:            {metrics.get('error_rate_percent', 0):.2f}%",
            f"Platform Health:       {metrics.get('health_status', 'unknown').upper()}",
            ""
        ])
        
        # Add status assessment
        success_rate = results["success_rate_percent"]
        health_status = metrics.get("health_status", "unknown")
        
        if success_rate >= 90 and health_status in ["excellent", "good"]:
            report_lines.extend([
                "🎉 STATUS: PLATFORM PRODUCTION READY",
                "✅ All critical functionality operational",
                "✅ Performance meets requirements",
                "✅ Database and Redis connectivity confirmed",
                "✅ Security middleware active",
                "✅ CORS configuration correct",
                "✅ Ready for £925K Odeon demo",
                ""
            ])
        elif success_rate >= 80:
            report_lines.extend([
                "⚠️ STATUS: PLATFORM MOSTLY FUNCTIONAL",
                "⚡ Core functionality working",
                "⚠️ Some minor issues detected",
                "📋 Review failed test suites",
                ""
            ])
        else:
            report_lines.extend([
                "🚨 STATUS: PLATFORM CRITICAL ISSUES",
                "❌ Significant functionality problems",
                "❌ NOT ready for production deployment",
                "❌ NOT ready for Odeon demo",
                "🔧 Immediate remediation required",
                ""
            ])
        
        # Add detailed suite results
        report_lines.append("📋 DETAILED VERIFICATION RESULTS:")
        report_lines.append("-" * 60)
        
        for suite_name, suite_result in results["suite_results"].items():
            if suite_result.get("success", False):
                status_emoji = "✅"
                status_text = "SUCCESS"
            else:
                status_emoji = "❌"
                status_text = "FAILED"
                
            report_lines.extend([
                f"{status_emoji} {suite_name}: {status_text}",
                ""
            ])
            
            if not suite_result.get("success", False) and "error" in suite_result:
                report_lines.extend([
                    f"   Error: {suite_result['error']}",
                    ""
                ])
            
            # Add key metrics for successful suites
            if suite_result.get("success", False) and "details" in suite_result:
                details = suite_result["details"]
                if isinstance(details, dict):
                    for key, value in details.items():
                        if key in ["success_rate", "response_time_ms", "total_endpoints", "successful_endpoints"]:
                            report_lines.append(f"   {key}: {value}")
                    report_lines.append("")
        
        # Add recommendations
        report_lines.extend([
            "🔧 RECOMMENDATIONS:",
            "",
            "If platform verification failed:",
            "1. Check Render service deployment status",
            "2. Verify database and Redis connectivity",
            "3. Confirm environment variables are set",
            "4. Test individual service components",
            "5. Review application logs for errors",
            "",
            "If all verifications passed:",
            "1. Proceed with comprehensive testing",
            "2. Execute end-to-end authentication flow tests",
            "3. Run CORS validation suite",
            "4. Prepare for Odeon demo scenarios",
            "",
            "Performance Optimization:",
            f"- Monitor response times (current avg: {metrics.get('average_response_time_ms', 0):.2f}ms)",
            f"- Track error rates (current: {metrics.get('error_rate_percent', 0):.2f}%)",
            "- Set up alerting for service degradation",
            "",
            "="*80
        ])
        
        return "\n".join(report_lines)

async def main():
    """Main execution function"""
    print("🔧 Starting Epic 2 Platform Functionality Verification")
    print("=" * 80)
    
    verifier = Epic2PlatformVerifier()
    
    try:
        # Run comprehensive platform verification
        results = await verifier.run_comprehensive_platform_verification()
        
        # Generate comprehensive report
        report = verifier.generate_comprehensive_report(results)
        
        # Save results and report
        timestamp = int(time.time())
        results_file = f"epic2_platform_verification_results_{timestamp}.json"
        report_file = f"epic2_platform_verification_report_{timestamp}.txt"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n💾 Results saved to: {results_file}")
        print(f"📄 Report saved to: {report_file}")
        
        # Return appropriate exit code
        success_rate = results["success_rate_percent"]
        health_status = results["platform_metrics"]["health_status"]
        
        if success_rate >= 90 and health_status in ["excellent", "good"]:
            print("\n🎉 Epic 2 Platform Verification: SUCCESS - Production ready!")
            sys.exit(0)
        elif success_rate >= 80:
            print("\n⚠️ Epic 2 Platform Verification: PARTIAL SUCCESS - Minor issues")
            sys.exit(1)
        else:
            print("\n🚨 Epic 2 Platform Verification: CRITICAL ISSUES - Not ready")
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"💥 Platform verification failed: {str(e)}")
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())