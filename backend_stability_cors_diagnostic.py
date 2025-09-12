#!/usr/bin/env python3
"""
Backend Stability and CORS Headers Diagnostic Tool
==================================================
Comprehensive testing of backend stability and CORS header implementation
for the £925K Zebra Associates opportunity.

This script tests:
1. Backend stability with various request types
2. CORS headers on successful responses (200)
3. CORS headers on authentication errors (401) 
4. CORS headers on server errors (500)
5. OPTIONS preflight requests
6. Middleware ordering verification
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import traceback


class BackendStabilityCORSDiagnostic:
    """Comprehensive diagnostic tool for backend stability and CORS headers"""
    
    def __init__(self, base_url: str = "https://marketedge-platform.onrender.com"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "tests": [],
            "summary": {
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0,
                "backend_stable": False,
                "cors_working": False
            }
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, 
                          headers: Optional[Dict] = None,
                          data: Optional[Dict] = None,
                          expect_cors: bool = True,
                          origin: str = "https://app.zebra.associates") -> Dict[str, Any]:
        """Make HTTP request and analyze response including CORS headers"""
        
        if not self.session:
            raise RuntimeError("Session not initialized - use as async context manager")
            
        url = f"{self.base_url}{endpoint}"
        
        # Default headers including Origin for CORS testing
        request_headers = {
            "Origin": origin,
            "User-Agent": "MarketEdge-CORS-Diagnostic/1.0"
        }
        if headers:
            request_headers.update(headers)
            
        test_result = {
            "method": method,
            "endpoint": endpoint,
            "url": url,
            "origin": origin,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "response": {},
            "cors_analysis": {},
            "stability_analysis": {}
        }
        
        try:
            # Make the request
            start_time = time.time()
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    await self._analyze_response(response, test_result, start_time)
            elif method.upper() == "POST":
                json_data = json.dumps(data) if data else None
                async with self.session.post(url, headers=request_headers, data=json_data) as response:
                    await self._analyze_response(response, test_result, start_time)
            elif method.upper() == "OPTIONS":
                async with self.session.options(url, headers=request_headers) as response:
                    await self._analyze_response(response, test_result, start_time)
            
            test_result["success"] = True
            
        except asyncio.TimeoutError:
            test_result["error"] = "Request timeout - server may be unresponsive"
            test_result["stability_analysis"]["timeout"] = True
        except aiohttp.ClientConnectorError as e:
            test_result["error"] = f"Connection error: {str(e)}"
            test_result["stability_analysis"]["connection_failed"] = True
        except aiohttp.ClientResponseError as e:
            test_result["error"] = f"HTTP error: {e.status} {e.message}"
            test_result["response"]["status_code"] = e.status
        except Exception as e:
            test_result["error"] = f"Unexpected error: {str(e)}"
            test_result["stability_analysis"]["unexpected_error"] = str(e)
            
        # Analyze CORS compliance
        if expect_cors:
            self._analyze_cors_compliance(test_result)
            
        return test_result
    
    async def _analyze_response(self, response: aiohttp.ClientResponse, 
                               test_result: Dict, start_time: float):
        """Analyze HTTP response for stability and CORS headers"""
        
        response_time = time.time() - start_time
        
        # Basic response info
        test_result["response"] = {
            "status_code": response.status,
            "status_text": response.reason,
            "response_time_ms": round(response_time * 1000, 2),
            "headers": dict(response.headers),
            "content_type": response.headers.get("content-type", "unknown")
        }
        
        # Try to get response content
        try:
            if response.headers.get("content-type", "").startswith("application/json"):
                content = await response.json()
                test_result["response"]["content"] = content
            else:
                content = await response.text()
                test_result["response"]["content"] = content[:500]  # Truncate long responses
        except Exception as e:
            test_result["response"]["content_error"] = str(e)
        
        # Stability analysis
        test_result["stability_analysis"] = {
            "response_received": True,
            "response_time_acceptable": response_time < 30.0,  # 30 second threshold
            "status_code_valid": 200 <= response.status < 600,
            "server_error": 500 <= response.status < 600,
            "client_error": 400 <= response.status < 500,
            "success_response": 200 <= response.status < 300
        }
        
        # CORS header analysis
        headers = response.headers
        test_result["cors_analysis"] = {
            "access_control_allow_origin": headers.get("access-control-allow-origin"),
            "access_control_allow_methods": headers.get("access-control-allow-methods"),
            "access_control_allow_headers": headers.get("access-control-allow-headers"), 
            "access_control_allow_credentials": headers.get("access-control-allow-credentials"),
            "access_control_expose_headers": headers.get("access-control-expose-headers"),
            "access_control_max_age": headers.get("access-control-max-age"),
            "cors_headers_present": any(h.startswith("access-control-") for h in headers.keys())
        }
    
    def _analyze_cors_compliance(self, test_result: Dict):
        """Analyze CORS compliance and mark any issues"""
        cors_analysis = test_result.get("cors_analysis", {})
        
        # Check for required CORS headers
        cors_analysis["compliant"] = all([
            cors_analysis.get("access_control_allow_origin") is not None,
            cors_analysis.get("cors_headers_present", False)
        ])
        
        # Check if origin is properly allowed
        allowed_origin = cors_analysis.get("access_control_allow_origin")
        request_origin = "https://app.zebra.associates"  # Our test origin
        
        cors_analysis["origin_allowed"] = (
            allowed_origin == "*" or
            allowed_origin == request_origin or
            (allowed_origin and request_origin in allowed_origin)
        )
        
        # Mark CORS issues
        if not cors_analysis.get("compliant", False):
            cors_analysis["issues"] = []
            if not cors_analysis.get("access_control_allow_origin"):
                cors_analysis["issues"].append("Missing Access-Control-Allow-Origin header")
            if not cors_analysis.get("cors_headers_present", False):
                cors_analysis["issues"].append("No CORS headers present")
        
    async def test_backend_health(self):
        """Test basic backend health and stability"""
        print("🏥 Testing backend health and stability...")
        
        test = await self.make_request("GET", "/health")
        self.results["tests"].append(test)
        
        return test["success"] and test["response"]["status_code"] == 200
    
    async def test_cors_preflight(self):
        """Test CORS preflight OPTIONS requests"""
        print("✈️ Testing CORS preflight requests...")
        
        endpoints = [
            "/api/v1/admin/feature-flags",
            "/api/v1/auth/login", 
            "/health",
            "/cors-test"
        ]
        
        preflight_success = True
        
        for endpoint in endpoints:
            test = await self.make_request(
                "OPTIONS", 
                endpoint,
                headers={
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Authorization, Content-Type"
                }
            )
            self.results["tests"].append(test)
            
            if not (test["success"] and 200 <= test["response"]["status_code"] <= 204):
                preflight_success = False
                print(f"  ❌ Preflight failed for {endpoint}")
            else:
                print(f"  ✅ Preflight OK for {endpoint}")
        
        return preflight_success
    
    async def test_successful_responses_cors(self):
        """Test CORS headers on successful responses (200 OK)"""
        print("✅ Testing CORS headers on successful responses...")
        
        endpoints = [
            "/health",
            "/cors-test",
            "/",
            "/deployment-test"
        ]
        
        success_cors_working = True
        
        for endpoint in endpoints:
            test = await self.make_request("GET", endpoint)
            self.results["tests"].append(test)
            
            if test["success"] and test["response"]["status_code"] == 200:
                cors_ok = test["cors_analysis"]["compliant"]
                if cors_ok:
                    print(f"  ✅ CORS OK for {endpoint}")
                else:
                    print(f"  ❌ CORS missing for {endpoint}")
                    success_cors_working = False
            else:
                print(f"  ❌ Request failed for {endpoint}")
                success_cors_working = False
        
        return success_cors_working
    
    async def test_auth_error_cors(self):
        """Test CORS headers on authentication errors (401)"""
        print("🔐 Testing CORS headers on authentication errors...")
        
        # Test endpoints that should return 401 without valid auth
        endpoints = [
            "/api/v1/admin/feature-flags",
            "/api/v1/admin/dashboard/stats", 
        ]
        
        auth_cors_working = True
        
        for endpoint in endpoints:
            # Try with no authorization header
            test = await self.make_request("GET", endpoint)
            self.results["tests"].append(test)
            
            status_code = test["response"]["status_code"]
            if status_code == 401 or status_code == 403:
                cors_ok = test["cors_analysis"]["compliant"]
                if cors_ok:
                    print(f"  ✅ CORS OK on auth error for {endpoint} ({status_code})")
                else:
                    print(f"  ❌ CORS missing on auth error for {endpoint} ({status_code})")
                    auth_cors_working = False
            elif status_code == 404:
                print(f"  ⚠️ Endpoint not found: {endpoint}")
            else:
                print(f"  ❌ Unexpected status {status_code} for {endpoint}")
        
        return auth_cors_working
    
    async def test_server_error_cors(self):
        """Test CORS headers on server errors (500) - if any occur"""
        print("🔥 Testing CORS headers on server errors...")
        
        # Test endpoints that might produce server errors
        test_cases = [
            # Test with malformed data that might cause 500 errors
            ("POST", "/api/v1/admin/feature-flags", {"malformed": "data"}),
            # Test with invalid endpoints that might cause internal routing errors
            ("GET", "/api/v1/nonexistent/endpoint", None),
        ]
        
        server_error_cors_working = True
        found_server_errors = False
        
        for method, endpoint, data in test_cases:
            test = await self.make_request(method, endpoint, data=data)
            self.results["tests"].append(test)
            
            status_code = test["response"]["status_code"]
            if 500 <= status_code < 600:
                found_server_errors = True
                cors_ok = test["cors_analysis"]["compliant"]
                if cors_ok:
                    print(f"  ✅ CORS OK on server error for {endpoint} ({status_code})")
                else:
                    print(f"  ❌ CORS missing on server error for {endpoint} ({status_code})")
                    server_error_cors_working = False
            else:
                print(f"  ℹ️ No server error for {endpoint} (got {status_code})")
        
        if not found_server_errors:
            print("  ℹ️ No server errors encountered - this is good for stability!")
        
        return server_error_cors_working, found_server_errors
    
    async def test_middleware_ordering(self):
        """Test that middleware is correctly ordered for CORS to work on errors"""
        print("⚙️ Testing middleware ordering...")
        
        # Make a request that should trigger authentication error
        # This tests that CORS middleware runs after error handling
        test = await self.make_request(
            "GET", 
            "/api/v1/admin/feature-flags",
            headers={"Authorization": "Bearer invalid-token"}
        )
        self.results["tests"].append(test)
        
        status_code = test["response"]["status_code"]
        cors_present = test["cors_analysis"]["cors_headers_present"]
        
        middleware_ok = (status_code in [401, 403]) and cors_present
        
        if middleware_ok:
            print("  ✅ Middleware ordering correct - CORS headers present on auth error")
        else:
            print(f"  ❌ Middleware ordering issue - Status: {status_code}, CORS: {cors_present}")
        
        return middleware_ok
    
    async def run_comprehensive_diagnostic(self):
        """Run all diagnostic tests"""
        
        print("🔍 Starting comprehensive backend stability and CORS diagnostic...")
        print(f"🎯 Testing server: {self.base_url}")
        print(f"🕐 Started at: {datetime.now().isoformat()}")
        print("=" * 70)
        
        # Test backend health first
        backend_healthy = await self.test_backend_health()
        
        if not backend_healthy:
            print("❌ Backend health check failed - server may be down")
            self.results["summary"]["backend_stable"] = False
            return self.results
        
        print("✅ Backend is responding to health checks")
        
        # Test CORS functionality
        preflight_ok = await self.test_cors_preflight()
        success_cors_ok = await self.test_successful_responses_cors()
        auth_cors_ok = await self.test_auth_error_cors()
        server_error_cors_ok, found_errors = await self.test_server_error_cors()
        middleware_ok = await self.test_middleware_ordering()
        
        # Update summary
        self.results["summary"]["total_tests"] = len(self.results["tests"])
        self.results["summary"]["successful_tests"] = sum(1 for t in self.results["tests"] if t["success"])
        self.results["summary"]["failed_tests"] = self.results["summary"]["total_tests"] - self.results["summary"]["successful_tests"]
        
        self.results["summary"]["backend_stable"] = backend_healthy and not any(
            t["stability_analysis"].get("server_error", False) for t in self.results["tests"]
        )
        
        self.results["summary"]["cors_working"] = (
            preflight_ok and success_cors_ok and auth_cors_ok and 
            (server_error_cors_ok or not found_errors) and middleware_ok
        )
        
        # Final assessment
        print("\n" + "=" * 70)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 70)
        print(f"Backend Stability: {'✅ STABLE' if self.results['summary']['backend_stable'] else '❌ UNSTABLE'}")
        print(f"CORS Configuration: {'✅ WORKING' if self.results['summary']['cors_working'] else '❌ BROKEN'}")
        print(f"Total Tests: {self.results['summary']['total_tests']}")
        print(f"Successful: {self.results['summary']['successful_tests']}")
        print(f"Failed: {self.results['summary']['failed_tests']}")
        
        if self.results["summary"]["backend_stable"]:
            print("\n🎉 BACKEND IS STABLE - No crashes or 500 errors detected!")
        else:
            print("\n⚠️ BACKEND INSTABILITY DETECTED - 500 errors or crashes found")
            
        if self.results["summary"]["cors_working"]:
            print("🌐 CORS HEADERS WORKING CORRECTLY - Frontend communication should work")
        else:
            print("❌ CORS HEADER ISSUES FOUND - Frontend may see 'CORS policy' errors")
        
        return self.results
    
    def save_results(self, filename: str = None):
        """Save diagnostic results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backend_stability_cors_diagnostic_{timestamp}.json"
            
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\n💾 Results saved to: {filename}")
        return filename


async def main():
    """Main diagnostic function"""
    
    # Test production server
    async with BackendStabilityCORSDiagnostic() as diagnostic:
        results = await diagnostic.run_comprehensive_diagnostic()
        
        # Save results
        results_file = diagnostic.save_results()
        
        # Print key findings
        print("\n" + "🔑 KEY FINDINGS" + "\n" + "=" * 50)
        
        if results["summary"]["backend_stable"]:
            print("✅ BACKEND CRASHES FIXED - Server is stable and responding correctly")
        else:
            print("❌ BACKEND STILL UNSTABLE - Server crashes or 500 errors detected")
            
        if results["summary"]["cors_working"]:
            print("✅ CORS HEADERS WORKING - All endpoints return proper CORS headers")
        else:
            print("❌ CORS CONFIGURATION ISSUES - Some endpoints missing CORS headers")
        
        # Specific findings for the £925K opportunity
        print("\n🎯 ZEBRA ASSOCIATES £925K OPPORTUNITY STATUS:")
        
        auth_tests = [t for t in results["tests"] if "admin" in t["endpoint"]]
        auth_working = all(
            t["cors_analysis"]["compliant"] and t["response"]["status_code"] in [200, 401, 403]
            for t in auth_tests if t["success"]
        )
        
        if auth_working:
            print("✅ Admin endpoints properly configured with CORS")
            print("✅ Authentication flow should work correctly")
        else:
            print("❌ Admin endpoint issues detected")
            print("❌ Authentication flow may have problems")
        
        return results


if __name__ == "__main__":
    asyncio.run(main())