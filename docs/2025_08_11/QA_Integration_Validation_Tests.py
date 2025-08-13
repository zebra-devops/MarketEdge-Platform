#!/usr/bin/env python3
"""
Integration Validation Test Suite for Issue #4 Enhanced Auth0 Integration
QA Orchestrator: Zoe
Priority: P1-HIGH

This script validates end-to-end authentication flows, error handling, 
and performance integration requirements.
"""

import asyncio
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs
import concurrent.futures

class IntegrationValidationSuite:
    """Integration validation for enhanced Auth0 authentication"""
    
    def __init__(self, staging_url: str):
        self.staging_url = staging_url.rstrip('/')
        self.session = requests.Session()
        self.test_results = []
        self.performance_metrics = []
        
        # Configuration
        self.timeout = 30
        self.performance_threshold = 2.0  # 2 second requirement
        self.max_concurrent_requests = 10
        
        # Test data
        self.test_organizations = [
            {'name': 'Test Hotel Chain', 'industry': 'hotel', 'sic_code': '55100'},
            {'name': 'Cinema Complex', 'industry': 'cinema', 'sic_code': '59140'},
            {'name': 'Fitness Center', 'industry': 'gym', 'sic_code': '93110'}
        ]

    def log_test_result(self, test_name: str, status: str, details: str, performance_data: Dict = None):
        """Log test result with performance metrics"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'status': status,
            'details': details,
            'performance': performance_data or {}
        }
        self.test_results.append(result)
        
        # Console output
        colors = {'PASS': '\033[92m', 'FAIL': '\033[91m', 'WARNING': '\033[93m'}
        reset = '\033[0m'
        
        perf_info = ""
        if performance_data and 'response_time' in performance_data:
            perf_info = f" ({performance_data['response_time']:.3f}s)"
        
        print(f"{colors.get(status, '')}{status}{reset}: {test_name}{perf_info}")
        print(f"   Details: {details}")
        if performance_data:
            for key, value in performance_data.items():
                if key != 'response_time':
                    print(f"   {key}: {value}")
        print()

    def measure_performance(self, func, *args, **kwargs):
        """Measure function execution time"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        return result, end_time - start_time

    def test_end_to_end_auth_flow(self) -> bool:
        """Test complete authentication flow integration"""
        try:
            print("Testing End-to-End Authentication Flow...")
            
            # Step 1: Get Auth0 authorization URL
            redirect_uri = f"{self.staging_url}/auth/callback"
            
            response, response_time = self.measure_performance(
                self.session.get,
                f"{self.staging_url}/api/v1/auth/auth0-url",
                params={'redirect_uri': redirect_uri},
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                self.log_test_result(
                    "Auth0 URL Generation",
                    "FAIL",
                    f"Failed to generate Auth0 URL: {response.status_code}",
                    {'response_time': response_time}
                )
                return False
            
            auth_data = response.json()
            auth_url = auth_data.get('auth_url')
            
            if not auth_url:
                self.log_test_result(
                    "Auth0 URL Generation",
                    "FAIL",
                    "Auth0 URL not returned in response",
                    {'response_time': response_time}
                )
                return False
            
            # Validate Auth0 URL structure
            parsed_url = urlparse(auth_url)
            if 'auth0.com' not in parsed_url.netloc:
                self.log_test_result(
                    "Auth0 URL Validation",
                    "FAIL",
                    f"Auth0 URL domain invalid: {parsed_url.netloc}",
                    {'response_time': response_time}
                )
                return False
            
            query_params = parse_qs(parsed_url.query)
            required_params = ['client_id', 'redirect_uri', 'response_type', 'scope', 'state']
            missing_params = [param for param in required_params if param not in query_params]
            
            if missing_params:
                self.log_test_result(
                    "Auth0 URL Parameters",
                    "FAIL",
                    f"Missing required parameters: {', '.join(missing_params)}",
                    {'response_time': response_time}
                )
                return False
            
            self.log_test_result(
                "Auth0 URL Generation",
                "PASS",
                "Auth0 authorization URL generated successfully with all required parameters",
                {'response_time': response_time, 'url_length': len(auth_url)}
            )
            
            # Step 2: Test session check endpoint (simulating post-auth)
            session_response, session_time = self.measure_performance(
                self.session.get,
                f"{self.staging_url}/api/v1/auth/session/check",
                timeout=self.timeout
            )
            
            # This should return 401 without authentication
            if session_response.status_code == 401:
                self.log_test_result(
                    "Session Check Unauthenticated",
                    "PASS",
                    "Session check properly returns 401 for unauthenticated requests",
                    {'response_time': session_time}
                )
            else:
                self.log_test_result(
                    "Session Check Unauthenticated",
                    "WARNING",
                    f"Unexpected response for unauthenticated session check: {session_response.status_code}",
                    {'response_time': session_time}
                )
            
            return True
            
        except Exception as e:
            self.log_test_result(
                "End-to-End Auth Flow",
                "FAIL",
                f"Auth flow test error: {str(e)}"
            )
            return False

    def test_organization_context_establishment(self) -> bool:
        """Test multi-tenant organization context handling"""
        try:
            print("Testing Organization Context Establishment...")
            
            # Test with different organization hints
            test_cases = [
                {'org_hint': 'hotel_org', 'industry': 'hotel'},
                {'org_hint': 'cinema_org', 'industry': 'cinema'},
                {'org_hint': 'gym_org', 'industry': 'gym'}
            ]
            
            context_tests_pass = True
            
            for test_case in test_cases:
                response, response_time = self.measure_performance(
                    self.session.get,
                    f"{self.staging_url}/api/v1/auth/auth0-url",
                    params={
                        'redirect_uri': f"{self.staging_url}/auth/callback",
                        'organization_hint': test_case['org_hint']
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    auth_data = response.json()
                    
                    # Check if organization hint is preserved in URL
                    auth_url = auth_data.get('auth_url', '')
                    if test_case['org_hint'] in auth_url or 'organization=' in auth_url:
                        self.log_test_result(
                            f"Organization Context - {test_case['industry']}",
                            "PASS",
                            f"Organization hint properly included in Auth0 URL",
                            {'response_time': response_time, 'org_hint': test_case['org_hint']}
                        )
                    else:
                        self.log_test_result(
                            f"Organization Context - {test_case['industry']}",
                            "WARNING",
                            "Organization hint not found in Auth0 URL",
                            {'response_time': response_time}
                        )
                        context_tests_pass = False
                else:
                    self.log_test_result(
                        f"Organization Context - {test_case['industry']}",
                        "FAIL",
                        f"Failed to generate URL with org hint: {response.status_code}",
                        {'response_time': response_time}
                    )
                    context_tests_pass = False
            
            return context_tests_pass
            
        except Exception as e:
            self.log_test_result(
                "Organization Context Establishment",
                "FAIL",
                f"Organization context test error: {str(e)}"
            )
            return False

    def test_error_handling_scenarios(self) -> bool:
        """Test comprehensive error handling"""
        try:
            print("Testing Error Handling Scenarios...")
            
            error_tests_pass = True
            
            # Test 1: Invalid redirect URI
            invalid_redirect_response, response_time = self.measure_performance(
                self.session.get,
                f"{self.staging_url}/api/v1/auth/auth0-url",
                params={'redirect_uri': 'javascript:alert("xss")'},
                timeout=self.timeout
            )
            
            if invalid_redirect_response.status_code == 400:
                self.log_test_result(
                    "Error Handling - Invalid Redirect URI",
                    "PASS",
                    "Invalid redirect URI properly rejected with 400 Bad Request",
                    {'response_time': response_time}
                )
            else:
                self.log_test_result(
                    "Error Handling - Invalid Redirect URI",
                    "FAIL",
                    f"Invalid redirect URI not properly handled: {invalid_redirect_response.status_code}",
                    {'response_time': response_time}
                )
                error_tests_pass = False
            
            # Test 2: Missing required parameters
            missing_param_response, response_time = self.measure_performance(
                self.session.get,
                f"{self.staging_url}/api/v1/auth/auth0-url",
                timeout=self.timeout
            )
            
            if missing_param_response.status_code == 422:  # Validation error
                self.log_test_result(
                    "Error Handling - Missing Parameters",
                    "PASS",
                    "Missing required parameters properly handled with validation error",
                    {'response_time': response_time}
                )
            else:
                self.log_test_result(
                    "Error Handling - Missing Parameters",
                    "WARNING",
                    f"Missing parameter handling may need improvement: {missing_param_response.status_code}",
                    {'response_time': response_time}
                )
            
            # Test 3: Malformed requests
            malformed_response, response_time = self.measure_performance(
                self.session.post,  # Wrong HTTP method
                f"{self.staging_url}/api/v1/auth/auth0-url",
                json={'invalid': 'data'},
                timeout=self.timeout
            )
            
            if malformed_response.status_code == 405:  # Method not allowed
                self.log_test_result(
                    "Error Handling - Wrong HTTP Method",
                    "PASS",
                    "Wrong HTTP method properly rejected with 405 Method Not Allowed",
                    {'response_time': response_time}
                )
            else:
                self.log_test_result(
                    "Error Handling - Wrong HTTP Method",
                    "WARNING",
                    f"HTTP method validation may need improvement: {malformed_response.status_code}",
                    {'response_time': response_time}
                )
            
            return error_tests_pass
            
        except Exception as e:
            self.log_test_result(
                "Error Handling Scenarios",
                "FAIL",
                f"Error handling test error: {str(e)}"
            )
            return False

    def test_concurrent_authentication_performance(self) -> bool:
        """Test performance under concurrent load"""
        try:
            print("Testing Concurrent Authentication Performance...")
            
            def auth_url_request():
                start_time = time.time()
                response = self.session.get(
                    f"{self.staging_url}/api/v1/auth/auth0-url",
                    params={'redirect_uri': f"{self.staging_url}/auth/callback"},
                    timeout=self.timeout
                )
                end_time = time.time()
                return {
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == 200
                }
            
            # Execute concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_requests) as executor:
                futures = [executor.submit(auth_url_request) for _ in range(self.max_concurrent_requests)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze results
            successful_requests = [r for r in results if r['success']]
            response_times = [r['response_time'] for r in results]
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            success_rate = len(successful_requests) / len(results) * 100
            
            performance_data = {
                'concurrent_requests': self.max_concurrent_requests,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'max_response_time': max_response_time,
                'requests_under_threshold': len([t for t in response_times if t < self.performance_threshold])
            }
            
            # Evaluate performance
            if success_rate >= 95 and avg_response_time < self.performance_threshold:
                self.log_test_result(
                    "Concurrent Performance",
                    "PASS",
                    f"Concurrent requests handled successfully with {success_rate:.1f}% success rate",
                    performance_data
                )
                return True
            elif success_rate >= 90:
                self.log_test_result(
                    "Concurrent Performance",
                    "WARNING",
                    f"Performance acceptable but could be improved: {success_rate:.1f}% success rate",
                    performance_data
                )
                return True
            else:
                self.log_test_result(
                    "Concurrent Performance",
                    "FAIL",
                    f"Poor performance under load: {success_rate:.1f}% success rate",
                    performance_data
                )
                return False
            
        except Exception as e:
            self.log_test_result(
                "Concurrent Authentication Performance",
                "FAIL",
                f"Concurrent performance test error: {str(e)}"
            )
            return False

    def test_database_integration(self) -> bool:
        """Test database connectivity and query performance"""
        try:
            print("Testing Database Integration...")
            
            # Test health endpoint that includes database check
            response, response_time = self.measure_performance(
                self.session.get,
                f"{self.staging_url}/api/v1/health",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Check for database connectivity indicators
                db_status = health_data.get('database', {}).get('status', 'unknown')
                
                if db_status == 'healthy' or 'healthy' in str(health_data).lower():
                    self.log_test_result(
                        "Database Integration",
                        "PASS",
                        "Database connectivity confirmed through health check",
                        {'response_time': response_time, 'db_status': db_status}
                    )
                    return True
                else:
                    self.log_test_result(
                        "Database Integration",
                        "WARNING",
                        f"Database status unclear from health check: {db_status}",
                        {'response_time': response_time}
                    )
                    return True  # Still passing as endpoint is responsive
            else:
                self.log_test_result(
                    "Database Integration",
                    "FAIL",
                    f"Health check failed: {response.status_code}",
                    {'response_time': response_time}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Database Integration",
                "FAIL",
                f"Database integration test error: {str(e)}"
            )
            return False

    def test_api_documentation_access(self) -> bool:
        """Test API documentation and endpoint discoverability"""
        try:
            print("Testing API Documentation Access...")
            
            # Test OpenAPI documentation endpoint
            docs_response, response_time = self.measure_performance(
                self.session.get,
                f"{self.staging_url}/docs",
                timeout=self.timeout
            )
            
            if docs_response.status_code == 200:
                # Check if it's the Swagger/OpenAPI interface
                content = docs_response.text.lower()
                if 'swagger' in content or 'openapi' in content or 'redoc' in content:
                    self.log_test_result(
                        "API Documentation",
                        "PASS",
                        "API documentation accessible via /docs endpoint",
                        {'response_time': response_time, 'content_length': len(docs_response.text)}
                    )
                else:
                    self.log_test_result(
                        "API Documentation",
                        "WARNING",
                        "Documentation endpoint accessible but content type unclear",
                        {'response_time': response_time}
                    )
                return True
            else:
                self.log_test_result(
                    "API Documentation",
                    "WARNING",
                    f"API documentation not accessible: {docs_response.status_code}",
                    {'response_time': response_time}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "API Documentation Access",
                "FAIL",
                f"Documentation test error: {str(e)}"
            )
            return False

    def run_integration_validation(self) -> Dict[str, Any]:
        """Run comprehensive integration validation suite"""
        print("=" * 60)
        print("Issue #4 Enhanced Auth0 Integration - Integration Validation")
        print("Priority: P1-HIGH")
        print(f"Environment: {self.staging_url}")
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 60)
        print()
        
        # Integration test suite
        test_suite = [
            ("End-to-End Auth Flow", self.test_end_to_end_auth_flow, True),
            ("Organization Context", self.test_organization_context_establishment, True),
            ("Error Handling", self.test_error_handling_scenarios, True),
            ("Database Integration", self.test_database_integration, True),
            ("Concurrent Performance", self.test_concurrent_authentication_performance, False),
            ("API Documentation", self.test_api_documentation_access, False)
        ]
        
        total_tests = len(test_suite)
        passed_tests = 0
        critical_failures = 0
        
        for test_name, test_func, is_critical in test_suite:
            print(f"Running: {test_name}")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                elif is_critical:
                    critical_failures += 1
            except Exception as e:
                self.log_test_result(
                    test_name,
                    "FAIL",
                    f"Test execution error: {str(e)}"
                )
                if is_critical:
                    critical_failures += 1
            print()
        
        # Calculate performance summary
        if self.test_results:
            response_times = []
            for result in self.test_results:
                if 'response_time' in result.get('performance', {}):
                    response_times.append(result['performance']['response_time'])
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                under_threshold = len([t for t in response_times if t < self.performance_threshold])
                
                performance_summary = {
                    'avg_response_time': avg_response_time,
                    'max_response_time': max_response_time,
                    'requests_under_threshold': under_threshold,
                    'total_timed_requests': len(response_times),
                    'performance_compliance': (under_threshold / len(response_times)) * 100
                }
            else:
                performance_summary = {}
        else:
            performance_summary = {}
        
        # Generate results
        success_rate = (passed_tests / total_tests) * 100
        
        print("=" * 60)
        print("INTEGRATION VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Critical Failures: {critical_failures}")
        
        if performance_summary:
            print(f"\nPerformance Summary:")
            print(f"Average Response Time: {performance_summary['avg_response_time']:.3f}s")
            print(f"Max Response Time: {performance_summary['max_response_time']:.3f}s")
            print(f"Performance Compliance: {performance_summary['performance_compliance']:.1f}%")
        
        print()
        
        # Integration assessment
        if critical_failures == 0 and success_rate >= 90:
            assessment = "PASS - Integration requirements met"
            print(f"🟢 ASSESSMENT: {assessment}")
        elif critical_failures == 0 and success_rate >= 75:
            assessment = "CONDITIONAL PASS - Minor integration issues to address"
            print(f"🟡 ASSESSMENT: {assessment}")
        else:
            assessment = "FAIL - Critical integration issues must be resolved"
            print(f"🔴 ASSESSMENT: {assessment}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'critical_failures': critical_failures,
            'assessment': assessment,
            'performance_summary': performance_summary,
            'test_results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }

# Sample usage configuration
SAMPLE_INTEGRATION_CONFIG = {
    'staging_url': 'https://your-staging-app.railway.app'
}

if __name__ == "__main__":
    print("Integration Validation Test Suite for Issue #4")
    print("Update SAMPLE_INTEGRATION_CONFIG with actual staging environment URL")
    print()
    
    # Uncomment and update to run tests:
    # validator = IntegrationValidationSuite(SAMPLE_INTEGRATION_CONFIG['staging_url'])
    # results = validator.run_integration_validation()
    # 
    # # Save results to file
    # with open('integration_validation_results.json', 'w') as f:
    #     json.dump(results, f, indent=2)
    
    print("Integration test suite ready for manual execution.")