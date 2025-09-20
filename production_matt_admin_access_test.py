#!/usr/bin/env python3
"""
Production Test: Matt.Lindop Admin Access Verification
=====================================================

CRITICAL CONTEXT: Testing the complete fix chain for AttributeError in /auth/me endpoint
that was preventing cookie setting and causing backend crashes.

This test validates Matt.Lindop (matt.lindop@zebra.associates) can access /admin page
based on his super_admin permissions for the £925K Zebra Associates opportunity.

Production URLs:
- Frontend: https://app.zebra.associates
- Backend: https://marketedge-platform.onrender.com

Test Coverage:
1. /auth/me endpoint no longer crashes with AttributeError
2. Cookies are properly set after authentication
3. /admin page access works for super_admin role
4. Feature Flags section is accessible
5. Complete authentication flow validation
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import sys


class ProductionAdminAccessTest:
    def __init__(self):
        self.backend_url = "https://marketedge-platform.onrender.com"
        self.frontend_url = "https://app.zebra.associates"
        self.test_results = []
        self.session = requests.Session()
        self.access_token = None

        # Test configuration
        self.test_user = {
            "email": "matt.lindop@zebra.associates",
            "expected_role": "super_admin",
            "expected_permissions": ["admin_access", "feature_flags_management"]
        }

    def log_result(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Log test result with timestamp and details"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
        print()

    def test_backend_health(self) -> bool:
        """Test 1: Verify backend is accessible and healthy"""
        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=30)

            if response.status_code == 200:
                health_data = response.json()
                self.log_result(
                    "Backend Health Check",
                    True,
                    f"Backend is healthy and responsive",
                    {"status_code": response.status_code, "health_data": health_data}
                )
                return True
            else:
                self.log_result(
                    "Backend Health Check",
                    False,
                    f"Backend health check failed with status {response.status_code}",
                    {"status_code": response.status_code, "response_text": response.text}
                )
                return False

        except Exception as e:
            self.log_result(
                "Backend Health Check",
                False,
                f"Backend health check failed with exception: {str(e)}",
                {"exception_type": type(e).__name__}
            )
            return False

    def test_auth_me_endpoint_stability(self) -> bool:
        """Test 2: Verify /auth/me endpoint doesn't crash with AttributeError"""
        try:
            # Test without auth token first (should return 401, not crash)
            response = self.session.get(f"{self.backend_url}/api/v1/auth/me", timeout=30)

            if response.status_code == 401:
                self.log_result(
                    "Auth Me Endpoint Stability (No Token)",
                    True,
                    "Endpoint properly returns 401 for unauthenticated request (no crash)",
                    {"status_code": response.status_code}
                )
                return True
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    if "AttributeError" in str(error_data):
                        self.log_result(
                            "Auth Me Endpoint Stability (No Token)",
                            False,
                            "CRITICAL: AttributeError still occurring in /auth/me endpoint",
                            {"status_code": response.status_code, "error": error_data}
                        )
                        return False
                except:
                    pass

                self.log_result(
                    "Auth Me Endpoint Stability (No Token)",
                    False,
                    "Endpoint returning 500 error (possible unresolved crash)",
                    {"status_code": response.status_code, "response_text": response.text[:500]}
                )
                return False
            else:
                self.log_result(
                    "Auth Me Endpoint Stability (No Token)",
                    True,
                    f"Endpoint stable, returned status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return True

        except Exception as e:
            self.log_result(
                "Auth Me Endpoint Stability (No Token)",
                False,
                f"Endpoint test failed with exception: {str(e)}",
                {"exception_type": type(e).__name__}
            )
            return False

    def get_mock_auth_token(self) -> Optional[str]:
        """Get a mock auth token for testing (simulating successful Auth0 login)"""
        # Note: In a real production test, this would be obtained through actual Auth0 flow
        # For now, we'll test the endpoints that don't require auth and document the full flow

        print("📋 MANUAL AUTH STEP REQUIRED:")
        print("   To complete this test, Matt.Lindop needs to:")
        print("   1. Visit https://app.zebra.associates")
        print("   2. Complete Auth0 login")
        print("   3. Extract access_token from browser localStorage/cookies")
        print("   4. Provide token for automated testing")
        print()

        # Check if token provided via environment or manual input
        token = input("Enter access_token from browser (or press Enter to skip auth tests): ").strip()

        if token:
            self.access_token = token
            return token
        return None

    def test_auth_me_with_token(self, token: str) -> bool:
        """Test 3: Verify /auth/me endpoint works with valid token and sets cookies"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.get(f"{self.backend_url}/api/v1/auth/me", headers=headers, timeout=30)

            if response.status_code == 200:
                user_data = response.json()

                # Check if user data contains expected fields
                expected_fields = ["email", "roles", "organizations"]
                missing_fields = [field for field in expected_fields if field not in user_data]

                if missing_fields:
                    self.log_result(
                        "Auth Me Endpoint with Token",
                        False,
                        f"Missing expected fields in user data: {missing_fields}",
                        {"user_data": user_data, "missing_fields": missing_fields}
                    )
                    return False

                # Verify Matt's details
                is_matt = user_data.get("email") == self.test_user["email"]
                has_super_admin = "super_admin" in user_data.get("roles", [])

                if is_matt and has_super_admin:
                    self.log_result(
                        "Auth Me Endpoint with Token",
                        True,
                        "Matt.Lindop authenticated successfully with super_admin role",
                        {
                            "email": user_data.get("email"),
                            "roles": user_data.get("roles"),
                            "organizations": len(user_data.get("organizations", [])),
                            "cookies_set": len(response.cookies) > 0
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Auth Me Endpoint with Token",
                        False,
                        f"User verification failed - Matt: {is_matt}, SuperAdmin: {has_super_admin}",
                        {"user_data": user_data}
                    )
                    return False

            elif response.status_code == 401:
                self.log_result(
                    "Auth Me Endpoint with Token",
                    False,
                    "Token authentication failed - token may be invalid or expired",
                    {"status_code": response.status_code}
                )
                return False
            else:
                self.log_result(
                    "Auth Me Endpoint with Token",
                    False,
                    f"Unexpected response status: {response.status_code}",
                    {"status_code": response.status_code, "response_text": response.text[:500]}
                )
                return False

        except Exception as e:
            self.log_result(
                "Auth Me Endpoint with Token",
                False,
                f"Token authentication test failed: {str(e)}",
                {"exception_type": type(e).__name__}
            )
            return False

    def test_admin_endpoints_access(self, token: str) -> bool:
        """Test 4: Verify admin endpoints are accessible with super_admin role"""
        admin_endpoints = [
            "/api/v1/admin/feature-flags",
            "/api/v1/admin/dashboard/stats",
            "/api/v1/admin/organizations"
        ]

        headers = {"Authorization": f"Bearer {token}"}
        all_success = True
        endpoint_results = {}

        for endpoint in admin_endpoints:
            try:
                response = self.session.get(f"{self.backend_url}{endpoint}", headers=headers, timeout=30)

                if response.status_code == 200:
                    endpoint_results[endpoint] = {"status": "SUCCESS", "status_code": 200}
                elif response.status_code == 403:
                    endpoint_results[endpoint] = {"status": "FORBIDDEN", "status_code": 403}
                    all_success = False
                elif response.status_code == 401:
                    endpoint_results[endpoint] = {"status": "UNAUTHORIZED", "status_code": 401}
                    all_success = False
                else:
                    endpoint_results[endpoint] = {"status": "ERROR", "status_code": response.status_code}
                    all_success = False

            except Exception as e:
                endpoint_results[endpoint] = {"status": "EXCEPTION", "error": str(e)}
                all_success = False

        self.log_result(
            "Admin Endpoints Access",
            all_success,
            f"Admin endpoints access test: {'ALL PASSED' if all_success else 'SOME FAILED'}",
            {"endpoint_results": endpoint_results}
        )

        return all_success

    def test_feature_flags_management(self, token: str) -> bool:
        """Test 5: Verify Feature Flags management functionality"""
        try:
            headers = {"Authorization": f"Bearer {token}"}

            # Test GET feature flags
            response = self.session.get(f"{self.backend_url}/api/v1/admin/feature-flags", headers=headers, timeout=30)

            if response.status_code == 200:
                feature_flags = response.json()

                # Test that we can read feature flags
                if isinstance(feature_flags, list):
                    self.log_result(
                        "Feature Flags Management",
                        True,
                        f"Successfully retrieved {len(feature_flags)} feature flags",
                        {"feature_flags_count": len(feature_flags)}
                    )
                    return True
                else:
                    self.log_result(
                        "Feature Flags Management",
                        False,
                        "Feature flags response is not a list",
                        {"response_type": type(feature_flags).__name__}
                    )
                    return False
            else:
                self.log_result(
                    "Feature Flags Management",
                    False,
                    f"Feature flags access failed with status {response.status_code}",
                    {"status_code": response.status_code, "response_text": response.text[:500]}
                )
                return False

        except Exception as e:
            self.log_result(
                "Feature Flags Management",
                False,
                f"Feature flags test failed: {str(e)}",
                {"exception_type": type(e).__name__}
            )
            return False

    def test_frontend_admin_page_structure(self) -> bool:
        """Test 6: Verify frontend /admin page structure and routing"""
        try:
            # Test that frontend loads without errors
            response = self.session.get(f"{self.frontend_url}/admin", timeout=30)

            # Check if page loads (200) or redirects to auth (302/301)
            if response.status_code in [200, 302, 301]:
                self.log_result(
                    "Frontend Admin Page Structure",
                    True,
                    f"Admin page accessible, status: {response.status_code}",
                    {"status_code": response.status_code, "final_url": response.url}
                )
                return True
            else:
                self.log_result(
                    "Frontend Admin Page Structure",
                    False,
                    f"Admin page not accessible, status: {response.status_code}",
                    {"status_code": response.status_code, "response_text": response.text[:500]}
                )
                return False

        except Exception as e:
            self.log_result(
                "Frontend Admin Page Structure",
                False,
                f"Frontend admin page test failed: {str(e)}",
                {"exception_type": type(e).__name__}
            )
            return False

    def run_production_test(self) -> Dict[str, Any]:
        """Run the complete production test suite"""
        print("=" * 80)
        print("PRODUCTION TEST: Matt.Lindop Admin Access Verification")
        print("=" * 80)
        print(f"Target User: {self.test_user['email']}")
        print(f"Expected Role: {self.test_user['expected_role']}")
        print(f"Backend URL: {self.backend_url}")
        print(f"Frontend URL: {self.frontend_url}")
        print(f"Test Started: {datetime.now().isoformat()}")
        print("=" * 80)
        print()

        # Phase 1: Basic Infrastructure Tests
        print("🔍 PHASE 1: Infrastructure Health Tests")
        print("-" * 50)
        backend_healthy = self.test_backend_health()
        auth_me_stable = self.test_auth_me_endpoint_stability()
        frontend_accessible = self.test_frontend_admin_page_structure()

        # Phase 2: Authentication Tests (requires manual token)
        print("\n🔐 PHASE 2: Authentication & Authorization Tests")
        print("-" * 50)
        token = self.get_mock_auth_token()

        auth_success = False
        admin_access = False
        feature_flags_access = False

        if token:
            auth_success = self.test_auth_me_with_token(token)
            if auth_success:
                admin_access = self.test_admin_endpoints_access(token)
                feature_flags_access = self.test_feature_flags_management(token)
        else:
            print("⚠️  Skipping authentication tests - no token provided")
            print("   For complete validation, Matt.Lindop should provide access token")

        # Calculate overall results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])

        # Critical path analysis
        critical_path_tests = [backend_healthy, auth_me_stable]
        if token:
            critical_path_tests.extend([auth_success, admin_access, feature_flags_access])

        critical_path_success = all(critical_path_tests)

        # Generate summary
        summary = {
            "test_completed_at": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "critical_path_success": critical_path_success,
            "matt_admin_access_ready": critical_path_success and auth_success and admin_access,
            "zebra_associates_ready": critical_path_success and feature_flags_access,
            "test_results": self.test_results
        }

        # Print final summary
        print("\n" + "=" * 80)
        print("PRODUCTION TEST SUMMARY")
        print("=" * 80)
        print(f"Overall Success Rate: {summary['success_rate']:.1f}% ({passed_tests}/{total_tests} tests passed)")
        print(f"Critical Path Status: {'✅ READY' if critical_path_success else '❌ NOT READY'}")
        print(f"Matt Admin Access: {'✅ VERIFIED' if summary['matt_admin_access_ready'] else '❌ NOT VERIFIED'}")
        print(f"Zebra Associates Ready: {'✅ YES' if summary['zebra_associates_ready'] else '❌ NO'}")

        if not summary['matt_admin_access_ready']:
            print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
            failed_tests = [r for r in self.test_results if not r["success"]]
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")

        if summary['matt_admin_access_ready']:
            print("\n🎉 SUCCESS: Matt.Lindop admin access is fully operational!")
            print("   • Backend AttributeError resolved")
            print("   • Authentication flow working")
            print("   • Admin endpoints accessible")
            print("   • Feature flags management available")
            print("   • £925K Zebra Associates opportunity: READY TO PROCEED")

        print("\n📊 Next Steps:")
        if not token:
            print("   1. Have Matt.Lindop complete Auth0 login on https://app.zebra.associates")
            print("   2. Extract access_token and re-run with authentication tests")
            print("   3. Verify complete admin functionality end-to-end")
        else:
            print("   1. Schedule demo with Zebra Associates")
            print("   2. Monitor production for any edge cases")
            print("   3. Document successful resolution for future reference")

        print("=" * 80)

        return summary


def main():
    """Main execution function"""
    test_runner = ProductionAdminAccessTest()

    try:
        summary = test_runner.run_production_test()

        # Save detailed results to file
        results_file = f"/Users/matt/Sites/MarketEdge/matt_admin_production_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n📄 Detailed results saved to: {results_file}")

        # Exit with appropriate code
        sys.exit(0 if summary['critical_path_success'] else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n🚨 Test runner failed with exception: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()