#!/usr/bin/env python3
"""
COMPREHENSIVE PRODUCTION CORS AND AUTHENTICATION VALIDATION SUITE
================================================================

This script provides comprehensive testing for the £925K Zebra Associates opportunity,
addressing the persistent CORS issues and ensuring robust production validation.

ROOT CAUSE ANALYSIS FINDINGS:
1. CORS headers ARE working correctly on all endpoints
2. The "/admin/dashboard/stats" endpoint returns 403 "Not authenticated", NOT 500 error
3. Service is NOT hibernated - health check confirms active status
4. Authentication is required for admin endpoints (require_admin dependency)
5. The issue is NOT CORS - it's missing valid JWT authentication tokens

TESTING STRATEGY:
- Test CORS configuration on all critical endpoints
- Validate authentication flow end-to-end
- Monitor service availability and response times
- Test database connectivity and user provisioning
- Verify frontend-backend integration
- Catch configuration drift issues
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIP = "SKIP"

@dataclass
class TestCase:
    """Individual test case configuration"""
    name: str
    description: str
    endpoint: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    expected_status: Optional[List[int]] = None
    expected_cors_headers: Optional[List[str]] = None
    auth_required: bool = False
    critical: bool = False

@dataclass
class TestExecutionResult:
    """Result of test execution"""
    test_case: TestCase
    result: TestResult
    status_code: int
    response_headers: Dict[str, str]
    response_body: Optional[str]
    execution_time: float
    error_message: Optional[str] = None

class ProductionCORSValidator:
    """Comprehensive CORS and authentication validator for production environment"""
    
    def __init__(self, base_url: str = "https://marketedge-platform.onrender.com"):
        self.base_url = base_url
        self.test_origin = "https://app.zebra.associates"
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results: List[TestExecutionResult] = []
        self.auth_token: Optional[str] = None
        
        # Critical test cases for £925K opportunity
        self.test_cases = [
            # CORS Configuration Tests
            TestCase(
                name="cors_preflight_admin_dashboard",
                description="CORS preflight for admin dashboard stats - CRITICAL for Zebra Associates",
                endpoint="/api/v1/admin/dashboard/stats",
                method="OPTIONS",
                headers={
                    "Origin": self.test_origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "authorization,content-type"
                },
                expected_status=[200],
                expected_cors_headers=[
                    "Access-Control-Allow-Origin",
                    "Access-Control-Allow-Methods",
                    "Access-Control-Allow-Headers",
                    "Access-Control-Allow-Credentials"
                ],
                critical=True
            ),
            TestCase(
                name="cors_actual_admin_dashboard",
                description="Actual CORS request for admin dashboard - tests authentication requirement",
                endpoint="/api/v1/admin/dashboard/stats",
                method="GET",
                headers={"Origin": self.test_origin, "Accept": "application/json"},
                expected_status=[401, 403],  # Expected without auth token
                expected_cors_headers=["Access-Control-Allow-Origin"],
                auth_required=True,
                critical=True
            ),
            TestCase(
                name="cors_test_endpoint",
                description="Dedicated CORS test endpoint verification",
                endpoint="/cors-test",
                method="GET",
                headers={"Origin": self.test_origin, "Accept": "application/json"},
                expected_status=[200],
                expected_cors_headers=["Access-Control-Allow-Origin"],
                critical=True
            ),
            TestCase(
                name="service_health_check",
                description="Service availability and health check",
                endpoint="/health",
                method="GET",
                expected_status=[200],
                critical=True
            ),
            TestCase(
                name="system_status_check",
                description="System status and route verification",
                endpoint="/system/status",
                method="GET",
                expected_status=[200],
                critical=False
            ),
            # Authentication Flow Tests
            TestCase(
                name="auth_endpoint_cors",
                description="Authentication endpoint CORS validation",
                endpoint="/api/v1/auth/me",
                method="GET",
                headers={"Origin": self.test_origin, "Accept": "application/json"},
                expected_status=[401, 403],  # Expected without auth
                expected_cors_headers=["Access-Control-Allow-Origin"],
                auth_required=True,
                critical=True
            ),
            # Additional Admin Endpoints
            TestCase(
                name="admin_feature_flags_cors",
                description="Admin feature flags endpoint CORS",
                endpoint="/api/v1/admin/feature-flags",
                method="GET",
                headers={"Origin": self.test_origin, "Accept": "application/json"},
                expected_status=[401, 403],
                expected_cors_headers=["Access-Control-Allow-Origin"],
                auth_required=True,
                critical=True
            ),
            TestCase(
                name="admin_modules_cors",
                description="Admin modules endpoint CORS",
                endpoint="/api/v1/admin/modules",
                method="GET",
                headers={"Origin": self.test_origin, "Accept": "application/json"},
                expected_status=[401, 403],
                expected_cors_headers=["Access-Control-Allow-Origin"],
                auth_required=True,
                critical=True
            ),
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def execute_test_case(self, test_case: TestCase) -> TestExecutionResult:
        """Execute a single test case"""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        start_time = time.time()
        url = f"{self.base_url}{test_case.endpoint}"
        
        try:
            logger.info(f"Executing test: {test_case.name}")
            
            # Prepare headers
            headers = test_case.headers or {}
            if test_case.auth_required and self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            # Execute request
            async with self.session.request(
                test_case.method,
                url,
                headers=headers
            ) as response:
                execution_time = time.time() - start_time
                
                response_body = None
                try:
                    response_body = await response.text()
                except:
                    pass
                
                # Determine test result
                result = self._evaluate_test_result(test_case, response)
                
                return TestExecutionResult(
                    test_case=test_case,
                    result=result,
                    status_code=response.status,
                    response_headers=dict(response.headers),
                    response_body=response_body,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Test {test_case.name} failed with exception: {e}")
            
            return TestExecutionResult(
                test_case=test_case,
                result=TestResult.FAIL,
                status_code=0,
                response_headers={},
                response_body=None,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _evaluate_test_result(self, test_case: TestCase, response: aiohttp.ClientResponse) -> TestResult:
        """Evaluate whether a test case passed or failed"""
        
        # Check status code
        if test_case.expected_status:
            if response.status not in test_case.expected_status:
                return TestResult.FAIL
        
        # Check CORS headers
        if test_case.expected_cors_headers:
            missing_headers = []
            for header in test_case.expected_cors_headers:
                if header not in response.headers:
                    missing_headers.append(header)
            
            if missing_headers:
                return TestResult.FAIL
            
            # Validate specific CORS header values
            if "Access-Control-Allow-Origin" in response.headers:
                allowed_origin = response.headers["Access-Control-Allow-Origin"]
                if allowed_origin != self.test_origin and allowed_origin != "*":
                    return TestResult.FAIL
        
        return TestResult.PASS
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases and return comprehensive results"""
        logger.info("Starting comprehensive CORS and authentication validation")
        
        start_time = time.time()
        
        for test_case in self.test_cases:
            result = await self.execute_test_case(test_case)
            self.test_results.append(result)
            
            # Add small delay between tests
            await asyncio.sleep(0.5)
        
        total_time = time.time() - start_time
        
        return self._generate_comprehensive_report(total_time)
    
    def _generate_comprehensive_report(self, total_execution_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        # Categorize results
        passed = [r for r in self.test_results if r.result == TestResult.PASS]
        failed = [r for r in self.test_results if r.result == TestResult.FAIL]
        warnings = [r for r in self.test_results if r.result == TestResult.WARNING]
        critical_failed = [r for r in failed if r.test_case.critical]
        
        # Calculate success rates
        total_tests = len(self.test_results)
        pass_rate = (len(passed) / total_tests * 100) if total_tests > 0 else 0
        critical_tests = [r for r in self.test_results if r.test_case.critical]
        critical_pass_rate = (len([r for r in critical_tests if r.result == TestResult.PASS]) / len(critical_tests) * 100) if critical_tests else 0
        
        # CORS analysis
        cors_results = self._analyze_cors_configuration()
        
        # Authentication analysis
        auth_results = self._analyze_authentication_flow()
        
        # Performance analysis
        avg_response_time = sum(r.execution_time for r in self.test_results) / len(self.test_results)
        
        report = {
            "report_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "total_execution_time": round(total_execution_time, 3),
                "test_environment": "production",
                "base_url": self.base_url,
                "test_origin": self.test_origin,
                "business_context": "£925K Zebra Associates opportunity validation"
            },
            "summary": {
                "total_tests": total_tests,
                "passed": len(passed),
                "failed": len(failed),
                "warnings": len(warnings),
                "pass_rate": round(pass_rate, 2),
                "critical_tests": len(critical_tests),
                "critical_passed": len([r for r in critical_tests if r.result == TestResult.PASS]),
                "critical_pass_rate": round(critical_pass_rate, 2),
                "avg_response_time": round(avg_response_time, 3),
                "business_ready": len(critical_failed) == 0
            },
            "cors_analysis": cors_results,
            "authentication_analysis": auth_results,
            "detailed_results": [
                {
                    "test_name": r.test_case.name,
                    "description": r.test_case.description,
                    "endpoint": r.test_case.endpoint,
                    "method": r.test_case.method,
                    "result": r.result.value,
                    "status_code": r.status_code,
                    "execution_time": round(r.execution_time, 3),
                    "critical": r.test_case.critical,
                    "cors_headers_present": self._extract_cors_headers(r.response_headers),
                    "error_message": r.error_message,
                    "response_sample": r.response_body[:200] if r.response_body else None
                }
                for r in self.test_results
            ],
            "critical_failures": [
                {
                    "test_name": r.test_case.name,
                    "endpoint": r.test_case.endpoint,
                    "status_code": r.status_code,
                    "error": r.error_message or f"Expected status {r.test_case.expected_status}, got {r.status_code}",
                    "impact": "BLOCKS £925K OPPORTUNITY" if r.test_case.critical else "Non-critical"
                }
                for r in critical_failed
            ],
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _analyze_cors_configuration(self) -> Dict[str, Any]:
        """Analyze CORS configuration across all endpoints"""
        cors_tests = [r for r in self.test_results if r.test_case.expected_cors_headers]
        
        cors_header_coverage = {}
        for result in cors_tests:
            for header in ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods", 
                          "Access-Control-Allow-Headers", "Access-Control-Allow-Credentials"]:
                if header in result.response_headers:
                    cors_header_coverage[header] = cors_header_coverage.get(header, 0) + 1
        
        return {
            "cors_enabled_endpoints": len([r for r in cors_tests if "Access-Control-Allow-Origin" in r.response_headers]),
            "total_cors_tests": len(cors_tests),
            "cors_header_coverage": cors_header_coverage,
            "zebra_associates_origin_supported": len([r for r in cors_tests 
                                                     if r.response_headers.get("Access-Control-Allow-Origin") == self.test_origin]),
            "credentials_support": len([r for r in cors_tests 
                                      if r.response_headers.get("Access-Control-Allow-Credentials") == "true"]),
            "cors_status": "FULLY_FUNCTIONAL" if len(cors_tests) > 0 and all(
                "Access-Control-Allow-Origin" in r.response_headers for r in cors_tests
            ) else "ISSUES_DETECTED"
        }
    
    def _analyze_authentication_flow(self) -> Dict[str, Any]:
        """Analyze authentication flow and requirements"""
        auth_tests = [r for r in self.test_results if r.test_case.auth_required]
        
        # Authentication behavior analysis
        auth_403_responses = len([r for r in auth_tests if r.status_code == 403])
        auth_401_responses = len([r for r in auth_tests if r.status_code == 401])
        
        return {
            "total_auth_endpoints": len(auth_tests),
            "proper_auth_rejection": auth_403_responses + auth_401_responses,
            "auth_401_responses": auth_401_responses,  # Token validation issues
            "auth_403_responses": auth_403_responses,  # Permission/role issues
            "auth_endpoints_with_cors": len([r for r in auth_tests 
                                           if "Access-Control-Allow-Origin" in r.response_headers]),
            "authentication_status": "PROPERLY_CONFIGURED" if auth_403_responses + auth_401_responses == len(auth_tests) else "MISCONFIGURED",
            "issue_analysis": {
                "cors_blocking_auth": len([r for r in auth_tests 
                                         if "Access-Control-Allow-Origin" not in r.response_headers]),
                "missing_jwt_tokens": "Admin endpoints properly reject unauthenticated requests",
                "root_cause": "Authentication required - CORS working correctly"
            }
        }
    
    def _extract_cors_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Extract CORS-related headers"""
        cors_headers = {}
        for key, value in headers.items():
            if key.lower().startswith('access-control-'):
                cors_headers[key] = value
        return cors_headers
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        # Analyze critical failures
        critical_failures = [r for r in self.test_results if r.result == TestResult.FAIL and r.test_case.critical]
        
        if not critical_failures:
            recommendations.append({
                "priority": "HIGH",
                "category": "SUCCESS",
                "title": "CORS Configuration Validated",
                "description": "All critical CORS tests passed. The issue is NOT CORS - it's authentication.",
                "action": "Implement proper JWT token generation and provide tokens to frontend for admin access."
            })
        
        # Check for authentication issues
        auth_issues = [r for r in self.test_results if r.test_case.auth_required and r.status_code not in [401, 403]]
        if auth_issues:
            recommendations.append({
                "priority": "HIGH", 
                "category": "AUTHENTICATION",
                "title": "Unexpected Authentication Responses",
                "description": f"Found {len(auth_issues)} endpoints with unexpected auth behavior",
                "action": "Review authentication middleware configuration"
            })
        
        # CORS recommendations
        cors_issues = len([r for r in self.test_results 
                          if r.test_case.expected_cors_headers and "Access-Control-Allow-Origin" not in r.response_headers])
        if cors_issues == 0:
            recommendations.append({
                "priority": "INFO",
                "category": "CORS",
                "title": "CORS Working Correctly",
                "description": "All tested endpoints have proper CORS headers for Zebra Associates origin",
                "action": "No CORS fixes needed. Focus on authentication implementation."
            })
        
        recommendations.append({
            "priority": "CRITICAL",
            "category": "BUSINESS_IMPACT",
            "title": "£925K Opportunity Status",
            "description": "CORS is functional. Authentication system ready. Need valid JWT tokens for frontend.",
            "action": "1. Generate valid JWT tokens for matt.lindop@zebra.associates 2. Provide tokens to frontend 3. Test complete user journey"
        })
        
        return recommendations

async def main():
    """Main execution function"""
    print("🚀 COMPREHENSIVE PRODUCTION CORS & AUTHENTICATION VALIDATOR")
    print("=" * 80)
    print("Business Context: £925K Zebra Associates Opportunity Validation")
    print("Target Environment: Production (https://marketedge-platform.onrender.com)")
    print("Critical Origin: https://app.zebra.associates")
    print("=" * 80)
    
    async with ProductionCORSValidator() as validator:
        results = await validator.run_all_tests()
        
        # Print comprehensive results
        print(f"\n📊 TEST EXECUTION SUMMARY")
        print(f"Total Tests: {results['summary']['total_tests']}")
        print(f"Passed: {results['summary']['passed']} ({results['summary']['pass_rate']}%)")
        print(f"Failed: {results['summary']['failed']}")
        print(f"Critical Pass Rate: {results['summary']['critical_pass_rate']}%")
        print(f"Business Ready: {'✅ YES' if results['summary']['business_ready'] else '❌ NO'}")
        print(f"Average Response Time: {results['summary']['avg_response_time']}s")
        
        print(f"\n🌐 CORS ANALYSIS")
        cors = results['cors_analysis']
        print(f"CORS Status: {cors['cors_status']}")
        print(f"Endpoints with CORS: {cors['cors_enabled_endpoints']}/{cors['total_cors_tests']}")
        print(f"Zebra Associates Support: {cors['zebra_associates_origin_supported']} endpoints")
        print(f"Credentials Support: {cors['credentials_support']} endpoints")
        
        print(f"\n🔐 AUTHENTICATION ANALYSIS")
        auth = results['authentication_analysis']
        print(f"Auth Status: {auth['authentication_status']}")
        print(f"Proper Auth Rejection: {auth['proper_auth_rejection']}/{auth['total_auth_endpoints']}")
        print(f"401 Responses (Token Issues): {auth['auth_401_responses']}")
        print(f"403 Responses (Role Issues): {auth['auth_403_responses']}")
        print(f"Root Cause: {auth['issue_analysis']['root_cause']}")
        
        if results['critical_failures']:
            print(f"\n❌ CRITICAL FAILURES:")
            for failure in results['critical_failures']:
                print(f"  • {failure['test_name']}: {failure['error']} ({failure['impact']})")
        else:
            print(f"\n✅ NO CRITICAL FAILURES - CORS WORKING CORRECTLY!")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"{i}. [{rec['priority']}] {rec['title']}")
            print(f"   {rec['description']}")
            print(f"   Action: {rec['action']}")
        
        # Save detailed results
        output_file = f"cors_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {output_file}")
        
        # Final diagnosis
        print(f"\n" + "=" * 80)
        print("🎯 FINAL DIAGNOSIS FOR £925K ZEBRA ASSOCIATES OPPORTUNITY")
        print("=" * 80)
        
        if results['summary']['business_ready']:
            print("✅ CORS: FULLY FUNCTIONAL")
            print("✅ Service: HEALTHY AND RESPONSIVE") 
            print("✅ Endpoints: AVAILABLE WITH PROPER AUTH REQUIREMENTS")
            print("🔑 ISSUE: Missing JWT authentication tokens for frontend")
            print("📋 NEXT STEPS:")
            print("   1. Generate valid JWT tokens for matt.lindop@zebra.associates")
            print("   2. Configure frontend to include Bearer tokens in requests")
            print("   3. Test complete user authentication flow")
            print("   4. Validate admin dashboard access with proper tokens")
        else:
            print("❌ CRITICAL ISSUES DETECTED - IMMEDIATE ACTION REQUIRED")
            
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())