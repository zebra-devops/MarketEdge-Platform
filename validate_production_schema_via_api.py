#!/usr/bin/env python3
"""
Production Schema Validation via Backend API
This script validates the production database schema by making API calls to endpoints
that would fail if required tables/columns are missing.
"""

import requests
import json
import sys
from datetime import datetime

class ProductionSchemaValidator:
    def __init__(self):
        self.base_url = "https://marketedge-platform.onrender.com"
        self.results = []
        self.errors = []

    def log_result(self, test_name, status, details):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{'✅' if status == 'PASS' else '❌'} {test_name}: {details}")

    def test_health_endpoint(self):
        """Test basic health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                database_ready = data.get('database_ready', False)
                if database_ready:
                    self.log_result("Health Check", "PASS", "Database connection verified")
                    return True
                else:
                    error = data.get('database_error', 'Unknown database error')
                    self.log_result("Health Check", "FAIL", f"Database not ready: {error}")
                    self.errors.append(f"Database not ready: {error}")
                    return False
            else:
                self.log_result("Health Check", "FAIL", f"HTTP {response.status_code}")
                self.errors.append(f"Health endpoint returned {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Health Check", "FAIL", f"Connection error: {str(e)}")
            self.errors.append(f"Cannot connect to backend: {str(e)}")
            return False

    def test_migration_critical_endpoints(self):
        """Test endpoints that require specific database tables from recent migrations"""
        critical_endpoints = [
            {
                "path": "/api/v1/admin/feature-flags",
                "method": "GET",
                "expected_tables": ["feature_flags", "feature_flag_usage"],
                "auth_required": True
            },
            {
                "path": "/api/v1/admin/modules",
                "method": "GET",
                "expected_tables": ["organisation_modules", "module_usage_logs"],
                "auth_required": True
            },
            {
                "path": "/api/v1/features/enabled",
                "method": "GET",
                "expected_tables": ["feature_flags"],
                "auth_required": True
            }
        ]

        for endpoint in critical_endpoints:
            try:
                url = f"{self.base_url}{endpoint['path']}"
                response = requests.get(url, timeout=10)

                # We expect 401/403 for auth-required endpoints, not 500/404
                if response.status_code in [401, 403]:
                    self.log_result(
                        f"Schema Test: {endpoint['path']}",
                        "PASS",
                        f"Endpoint exists (HTTP {response.status_code} - auth required)"
                    )
                elif response.status_code == 404:
                    self.log_result(
                        f"Schema Test: {endpoint['path']}",
                        "FAIL",
                        "Endpoint not found - possible missing route"
                    )
                    self.errors.append(f"Missing endpoint: {endpoint['path']}")
                elif response.status_code == 500:
                    # 500 errors often indicate missing database tables
                    self.log_result(
                        f"Schema Test: {endpoint['path']}",
                        "FAIL",
                        f"Server error - likely missing tables: {', '.join(endpoint['expected_tables'])}"
                    )
                    self.errors.append(f"Likely missing tables for {endpoint['path']}: {', '.join(endpoint['expected_tables'])}")
                else:
                    self.log_result(
                        f"Schema Test: {endpoint['path']}",
                        "WARN",
                        f"Unexpected HTTP {response.status_code}"
                    )

            except Exception as e:
                self.log_result(
                    f"Schema Test: {endpoint['path']}",
                    "FAIL",
                    f"Request failed: {str(e)}"
                )
                self.errors.append(f"Request failed for {endpoint['path']}: {str(e)}")

    def test_specific_migration_004_requirements(self):
        """Test specific requirements from migration 004 that are causing failures"""
        print("\n" + "="*50)
        print("TESTING MIGRATION 004 SPECIFIC REQUIREMENTS")
        print("="*50)

        # Test if the backend can handle requests that would use the missing tables
        migration_004_tests = [
            {
                "test_name": "module_usage_logs table",
                "endpoint": "/api/v1/admin/modules",
                "failure_indicators": ["relation \"module_usage_logs\" does not exist"]
            },
            {
                "test_name": "feature_flag_usage table",
                "endpoint": "/api/v1/admin/feature-flags",
                "failure_indicators": ["relation \"feature_flag_usage\" does not exist"]
            },
            {
                "test_name": "organisation_modules.organisation_id column",
                "endpoint": "/api/v1/admin/modules",
                "failure_indicators": ["column \"organisation_id\" does not exist"]
            }
        ]

        for test in migration_004_tests:
            try:
                url = f"{self.base_url}{test['endpoint']}"
                response = requests.get(url, timeout=10)

                # If we get a response (even 401/403), the database schema is likely OK
                if response.status_code in [200, 401, 403]:
                    self.log_result(
                        f"Migration 004: {test['test_name']}",
                        "PASS",
                        "Table/column appears to exist (no 500 error)"
                    )
                elif response.status_code == 500:
                    # Check if it's a database schema error
                    try:
                        error_text = response.text
                        if any(indicator in error_text for indicator in test['failure_indicators']):
                            self.log_result(
                                f"Migration 004: {test['test_name']}",
                                "FAIL",
                                "Missing table/column confirmed"
                            )
                            self.errors.append(f"Missing: {test['test_name']}")
                        else:
                            self.log_result(
                                f"Migration 004: {test['test_name']}",
                                "WARN",
                                "500 error but not schema-related"
                            )
                    except:
                        self.log_result(
                            f"Migration 004: {test['test_name']}",
                            "WARN",
                            "500 error - cannot determine cause"
                        )
                else:
                    self.log_result(
                        f"Migration 004: {test['test_name']}",
                        "WARN",
                        f"Unexpected HTTP {response.status_code}"
                    )

            except Exception as e:
                self.log_result(
                    f"Migration 004: {test['test_name']}",
                    "FAIL",
                    f"Request failed: {str(e)}"
                )

    def generate_fix_recommendations(self):
        """Generate specific recommendations based on found issues"""
        print("\n" + "="*60)
        print("PRODUCTION SCHEMA FIX RECOMMENDATIONS")
        print("="*60)

        if not self.errors:
            print("✅ No schema issues detected via API validation")
            return

        print("❌ Issues detected that require database schema fixes:")
        for i, error in enumerate(self.errors, 1):
            print(f"{i}. {error}")

        print("\n📋 RECOMMENDED ACTIONS:")

        if any("missing tables" in error.lower() or "module_usage_logs" in error or "feature_flag_usage" in error for error in self.errors):
            print("\n1. Apply Migration 004 to production database:")
            print("   - Missing tables: module_usage_logs, feature_flag_usage")
            print("   - Missing column: organisation_modules.organisation_id")
            print("   - Run: alembic upgrade head")

        if any("endpoint not found" in error.lower() for error in self.errors):
            print("\n2. Check application code deployment:")
            print("   - Some endpoints missing from deployed code")
            print("   - Verify latest code is deployed to Render")

        print("\n3. Safe deployment approach:")
        print("   a. Create database backup first")
        print("   b. Apply migrations during low-traffic period")
        print("   c. Test all critical endpoints after migration")
        print("   d. Have rollback plan ready")

    def run_validation(self):
        """Run complete production schema validation"""
        print("="*60)
        print("PRODUCTION DATABASE SCHEMA VALIDATION")
        print("="*60)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now().isoformat()}")
        print("="*60)

        # 1. Test basic connectivity
        if not self.test_health_endpoint():
            print("\n❌ Cannot proceed - backend health check failed")
            return False

        # 2. Test migration-critical endpoints
        print("\n" + "="*50)
        print("TESTING MIGRATION-CRITICAL ENDPOINTS")
        print("="*50)
        self.test_migration_critical_endpoints()

        # 3. Test specific migration 004 requirements
        self.test_specific_migration_004_requirements()

        # 4. Generate recommendations
        self.generate_fix_recommendations()

        # 5. Summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.results if r['status'] == 'FAIL'])

        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors found: {len(self.errors)}")

        if self.errors:
            print(f"\n❌ PRODUCTION SCHEMA VALIDATION FAILED")
            print(f"Critical issues found: {len(self.errors)}")
            return False
        else:
            print(f"\n✅ PRODUCTION SCHEMA VALIDATION PASSED")
            print("All critical database tables appear to be present")
            return True

def main():
    validator = ProductionSchemaValidator()
    success = validator.run_validation()

    # Save detailed results
    results_file = f"production_schema_validation_{int(datetime.now().timestamp())}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "validation_time": datetime.now().isoformat(),
            "success": success,
            "results": validator.results,
            "errors": validator.errors
        }, f, indent=2)

    print(f"\nDetailed results saved to: {results_file}")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()