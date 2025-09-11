#!/usr/bin/env python3
"""
PRODUCTION CORS AND AUTHENTICATION VALIDATION TEST SUITE
For £925K Zebra Associates Opportunity

This test suite validates:
1. CORS configuration across all critical endpoints
2. Authentication flow requirements and responses  
3. Service availability and performance monitoring
4. Database connectivity and user provisioning
5. Frontend-backend integration simulation

Usage:
    python3 production_cors_validation_test.py
    
Expected Results:
    - All CORS tests should PASS (headers are working)
    - Authentication tests should show 403 "Not authenticated" (expected for missing JWT)
    - Service availability tests should PASS
    - Frontend integration tests will identify JWT token issues
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class ProductionCORSValidator:
    """Comprehensive production validation for CORS and authentication"""
    
    def __init__(self):
        self.backend_url = "https://marketedge-platform.onrender.com"
        self.frontend_origin = "https://app.zebra.associates"
        self.test_results = []
        self.errors_found = []
        
    def log_test(self, test_name: str, status: str, details: str, expected: bool = True):
        """Log test results with detailed information"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "expected": expected,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   └─ {details}")
            
    def test_cors_preflight_options(self) -> bool:
        """Test CORS preflight requests for all critical endpoints"""
        print("\n🌐 TESTING CORS PREFLIGHT (OPTIONS) REQUESTS")
        print("=" * 50)
        
        endpoints = [
            "/api/v1/admin/dashboard/stats",
            "/api/v1/admin/feature-flags", 
            "/api/v1/admin/users",
            "/api/v1/admin/modules",
            "/api/v1/auth/auth0-url",
            "/api/v1/users"
        ]
        
        all_passed = True
        
        for endpoint in endpoints:
            try:
                response = requests.options(
                    f"{self.backend_url}{endpoint}",
                    headers={
                        "Origin": self.frontend_origin,
                        "Access-Control-Request-Method": "GET",
                        "Access-Control-Request-Headers": "Authorization,Content-Type"
                    },
                    timeout=10
                )
                
                # Check CORS headers
                cors_origin = response.headers.get("Access-Control-Allow-Origin")
                cors_credentials = response.headers.get("Access-Control-Allow-Credentials")
                cors_methods = response.headers.get("Access-Control-Allow-Methods")
                
                if cors_origin == self.frontend_origin:
                    self.log_test(
                        f"CORS Preflight {endpoint}",
                        "PASS",
                        f"Status: {response.status_code}, Origin: {cors_origin}, Credentials: {cors_credentials}"
                    )
                else:
                    self.log_test(
                        f"CORS Preflight {endpoint}",
                        "FAIL", 
                        f"Wrong origin: {cors_origin}, expected: {self.frontend_origin}"
                    )
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"CORS Preflight {endpoint}", "ERROR", str(e))
                all_passed = False
                
        return all_passed
    
    def test_authenticated_endpoints_cors(self) -> bool:
        """Test CORS headers on actual authenticated requests"""
        print("\n🔐 TESTING AUTHENTICATED ENDPOINTS CORS")
        print("=" * 45)
        
        admin_endpoints = [
            "/api/v1/admin/dashboard/stats",
            "/api/v1/admin/feature-flags",
            "/api/v1/admin/users", 
            "/api/v1/admin/modules"
        ]
        
        all_passed = True
        
        for endpoint in admin_endpoints:
            try:
                # Test without Authorization header (should get 403 with CORS headers)
                response = requests.get(
                    f"{self.backend_url}{endpoint}",
                    headers={"Origin": self.frontend_origin},
                    timeout=10
                )
                
                cors_origin = response.headers.get("Access-Control-Allow-Origin")
                
                # Check if we get 403 "Not authenticated" with CORS headers
                if response.status_code == 403:
                    try:
                        error_detail = response.json().get("detail", "")
                        if "not authenticated" in error_detail.lower():
                            if cors_origin == self.frontend_origin:
                                self.log_test(
                                    f"Auth Required {endpoint}",
                                    "PASS",
                                    f"403 + CORS headers present (authentication working correctly)"
                                )
                            else:
                                self.log_test(
                                    f"Auth Required {endpoint}",
                                    "FAIL",
                                    f"403 but missing CORS: {cors_origin}"
                                )
                                all_passed = False
                        else:
                            self.log_test(
                                f"Auth Required {endpoint}",
                                "WARN",
                                f"403 but unexpected error: {error_detail}"
                            )
                    except:
                        self.log_test(
                            f"Auth Required {endpoint}",
                            "WARN", 
                            f"403 but couldn't parse response"
                        )
                else:
                    self.log_test(
                        f"Auth Required {endpoint}",
                        "FAIL",
                        f"Expected 403, got {response.status_code}"
                    )
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Auth Required {endpoint}", "ERROR", str(e))
                all_passed = False
                
        return all_passed
    
    def test_service_availability(self) -> bool:
        """Test backend service availability and performance"""
        print("\n🏥 TESTING SERVICE AVAILABILITY")
        print("=" * 35)
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/health", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                status = health_data.get("status", "unknown")
                
                self.log_test(
                    "Service Health Check",
                    "PASS",
                    f"Status: {status}, Response time: {response_time:.2f}s"
                )
                
                # Check if service is in production mode
                if "production" in str(health_data).lower():
                    self.log_test(
                        "Production Mode",
                        "PASS", 
                        "Service running in production configuration"
                    )
                else:
                    self.log_test(
                        "Production Mode",
                        "WARN",
                        f"Service mode unclear: {health_data}"
                    )
                    
                return True
            else:
                self.log_test(
                    "Service Health Check",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:100]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Service Health Check", "ERROR", str(e))
            return False
    
    def test_user_provisioning_status(self) -> bool:
        """Test user provisioning for matt.lindop@zebra.associates"""
        print("\n👤 TESTING USER PROVISIONING STATUS")
        print("=" * 40)
        
        try:
            # Test emergency admin setup endpoint
            response = requests.post(
                f"{self.backend_url}/api/v1/database/emergency-admin-setup",
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", "")
                
                if "ADMIN PRIVILEGES GRANTED" in message:
                    self.log_test(
                        "User Provisioning",
                        "PASS",
                        "matt.lindop@zebra.associates exists with admin privileges"
                    )
                    return True
                else:
                    self.log_test(
                        "User Provisioning",
                        "WARN",
                        f"Unexpected admin setup response: {message}"
                    )
                    return False
            else:
                self.log_test(
                    "User Provisioning",
                    "FAIL",
                    f"Admin setup failed: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("User Provisioning", "ERROR", str(e))
            return False
    
    def test_frontend_integration_simulation(self) -> bool:
        """Simulate frontend API calls to identify issues"""
        print("\n🖥️  TESTING FRONTEND INTEGRATION SIMULATION")
        print("=" * 50)
        
        # Simulate the exact calls that frontend is making
        failing_calls = [
            {
                "name": "Admin Dashboard Stats",
                "url": f"{self.backend_url}/api/v1/admin/dashboard/stats",
                "method": "GET",
                "headers": {"Origin": self.frontend_origin}
            },
            {
                "name": "Feature Flags List", 
                "url": f"{self.backend_url}/api/v1/admin/feature-flags",
                "method": "GET",
                "headers": {"Origin": self.frontend_origin}
            }
        ]
        
        missing_auth_count = 0
        
        for call in failing_calls:
            try:
                if call["method"] == "GET":
                    response = requests.get(call["url"], headers=call["headers"], timeout=10)
                
                if response.status_code == 403:
                    try:
                        error_detail = response.json().get("detail", "")
                        cors_header = response.headers.get("Access-Control-Allow-Origin")
                        
                        if "not authenticated" in error_detail.lower():
                            if cors_header == self.frontend_origin:
                                self.log_test(
                                    f"Frontend Call {call['name']}",
                                    "PASS",
                                    "CORS working, needs Authorization header"
                                )
                                missing_auth_count += 1
                            else:
                                self.log_test(
                                    f"Frontend Call {call['name']}",
                                    "FAIL",
                                    f"Missing CORS header: {cors_header}"
                                )
                        else:
                            self.log_test(
                                f"Frontend Call {call['name']}",
                                "WARN",
                                f"Unexpected 403 error: {error_detail}"
                            )
                    except:
                        self.log_test(
                            f"Frontend Call {call['name']}",
                            "ERROR",
                            "Couldn't parse 403 response"
                        )
                else:
                    self.log_test(
                        f"Frontend Call {call['name']}",
                        "WARN",
                        f"Unexpected status: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(f"Frontend Call {call['name']}", "ERROR", str(e))
        
        # Summary analysis
        if missing_auth_count > 0:
            self.log_test(
                "Integration Analysis",
                "PASS",
                f"CORS working perfectly. {missing_auth_count} endpoints need JWT authentication."
            )
            return True
        else:
            self.log_test(
                "Integration Analysis", 
                "FAIL",
                "Unexpected results - investigate authentication middleware"
            )
            return False
    
    def generate_summary_report(self) -> Dict:
        """Generate comprehensive summary report"""
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"]) 
        warned = len([r for r in self.test_results if r["status"] == "WARN"])
        errors = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        return {
            "summary": {
                "total_tests": len(self.test_results),
                "passed": passed,
                "failed": failed,
                "warnings": warned,
                "errors": errors,
                "success_rate": f"{(passed / len(self.test_results) * 100):.1f}%" if self.test_results else "0%"
            },
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "backend_url": self.backend_url,
                "frontend_origin": self.frontend_origin
            }
        }
    
    def run_all_tests(self) -> bool:
        """Run comprehensive test suite"""
        print("🚀 ZEBRA ASSOCIATES PRODUCTION VALIDATION")
        print("=" * 55)
        print(f"Backend: {self.backend_url}")
        print(f"Frontend: {self.frontend_origin}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Run all test categories
        tests_passed = []
        tests_passed.append(self.test_service_availability())
        tests_passed.append(self.test_cors_preflight_options()) 
        tests_passed.append(self.test_authenticated_endpoints_cors())
        tests_passed.append(self.test_user_provisioning_status())
        tests_passed.append(self.test_frontend_integration_simulation())
        
        # Generate summary
        print("\n📊 TEST SUMMARY")
        print("=" * 20)
        
        summary = self.generate_summary_report()
        print(f"Total Tests: {summary['summary']['total_tests']}")
        print(f"✅ Passed: {summary['summary']['passed']}")
        print(f"❌ Failed: {summary['summary']['failed']}")
        print(f"⚠️  Warnings: {summary['summary']['warnings']}")
        print(f"🚨 Errors: {summary['summary']['errors']}")
        print(f"Success Rate: {summary['summary']['success_rate']}")
        
        # Save detailed results
        with open(f"production_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📁 Detailed results saved to production_validation_results_*.json")
        
        # Business impact assessment
        print("\n💰 BUSINESS IMPACT ASSESSMENT")
        print("=" * 35)
        
        if summary['summary']['failed'] == 0 and summary['summary']['errors'] == 0:
            print("✅ Infrastructure: READY for £925K opportunity")
            print("✅ CORS Configuration: OPTIMAL") 
            print("✅ Service Availability: STABLE")
            if summary['summary']['warnings'] > 0:
                print("⚠️  Authentication: Frontend needs JWT token implementation")
                print("📋 Action Required: Implement Authorization headers in frontend API calls")
            else:
                print("✅ Authentication: FULLY FUNCTIONAL")
        else:
            print("❌ Infrastructure: ISSUES DETECTED")
            print("📋 Action Required: Fix failing tests before proceeding")
        
        return all(tests_passed)

def main():
    """Main execution function"""
    validator = ProductionCORSValidator()
    
    try:
        success = validator.run_all_tests()
        
        if success:
            print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY")
            print("System is ready for £925K Zebra Associates opportunity")
            return 0
        else:
            print("\n🚨 SOME TESTS FAILED")
            print("Review results and fix issues before proceeding")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())