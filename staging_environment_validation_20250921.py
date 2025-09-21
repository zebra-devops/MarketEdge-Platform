#!/usr/bin/env python3
"""
Comprehensive Staging Environment Validation
==========================================

Tests all staging-related endpoints and configurations to validate
the staging isolation implementation from PR #15.

This script validates:
1. Environment configuration endpoint
2. Staging health endpoint functionality
3. Auth0 staging configuration availability
4. CORS configuration and wildcard support
5. Production isolation and protection
6. Database and Redis connectivity validation
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, Any, List

class StagingEnvironmentValidator:
    def __init__(self, base_url: str = "https://marketedge-platform.onrender.com"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "validation_summary": {},
            "detailed_results": {},
            "auth0_validation": {},
            "production_protection": {},
            "recommendations": []
        }

    def test_basic_health(self) -> Dict[str, Any]:
        """Test basic health endpoint"""
        print("Testing basic health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=30)
            result = {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "content": response.json() if response.status_code == 200 else response.text,
                "accessible": True
            }
        except Exception as e:
            result = {
                "status_code": None,
                "accessible": False,
                "error": str(e)
            }

        self.results["detailed_results"]["basic_health"] = result
        return result

    def test_environment_config(self) -> Dict[str, Any]:
        """Test environment configuration endpoint"""
        print("Testing environment configuration endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/v1/system/environment-config", timeout=30)
            result = {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "accessible": True
            }

            if response.status_code == 200:
                data = response.json()
                result["content"] = data

                # Validate staging configuration presence
                env = data.get("environment", {})
                auth0 = data.get("auth0_config", {})
                debug = data.get("debug_info", {})

                result["validation"] = {
                    "environment_detected": env.get("ENVIRONMENT"),
                    "is_production": env.get("is_production"),
                    "is_staging": env.get("is_staging"),
                    "use_staging_auth0": env.get("USE_STAGING_AUTH0"),
                    "has_staging_config": env.get("has_staging_config"),
                    "staging_domain_set": debug.get("staging_domain_set"),
                    "staging_client_id_set": debug.get("staging_client_id_set"),
                    "staging_client_secret_set": debug.get("staging_client_secret_set"),
                    "preview_environment_detected": debug.get("preview_environment_detected"),
                    "auth0_domain": auth0.get("domain"),
                    "cors_origins_count": len(data.get("cors_origins", []))
                }
            else:
                result["content"] = response.text

        except Exception as e:
            result = {
                "status_code": None,
                "accessible": False,
                "error": str(e)
            }

        self.results["detailed_results"]["environment_config"] = result
        return result

    def test_staging_health(self) -> Dict[str, Any]:
        """Test staging health endpoint"""
        print("Testing staging health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/v1/system/staging-health", timeout=30)
            result = {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "accessible": True
            }

            if response.status_code == 200:
                data = response.json()
                result["content"] = data

                # Validate staging health information
                result["validation"] = {
                    "status": data.get("status"),
                    "environment": data.get("environment"),
                    "staging_mode": data.get("staging_mode"),
                    "auth0_environment": data.get("auth0_environment"),
                    "database_connected": data.get("database_connected"),
                    "redis_connected": data.get("redis_connected"),
                    "has_database_error": "database_error" in data,
                    "database_error": data.get("database_error")
                }
            else:
                result["content"] = response.text

        except Exception as e:
            result = {
                "status_code": None,
                "accessible": False,
                "error": str(e)
            }

        self.results["detailed_results"]["staging_health"] = result
        return result

    def test_cors_configuration(self) -> Dict[str, Any]:
        """Test CORS configuration by examining headers and origins"""
        print("Testing CORS configuration...")
        try:
            # Test basic CORS headers
            response = requests.options(f"{self.base_url}/health",
                                      headers={
                                          "Origin": "https://test.onrender.com",
                                          "Access-Control-Request-Method": "GET"
                                      }, timeout=30)

            result = {
                "status_code": response.status_code,
                "accessible": True,
                "cors_headers": {
                    "access_control_allow_origin": response.headers.get("Access-Control-Allow-Origin"),
                    "access_control_allow_methods": response.headers.get("Access-Control-Allow-Methods"),
                    "access_control_allow_headers": response.headers.get("Access-Control-Allow-Headers"),
                    "access_control_allow_credentials": response.headers.get("Access-Control-Allow-Credentials")
                }
            }

            # Test wildcard support for onrender.com domains
            wildcard_test = requests.get(f"{self.base_url}/api/v1/system/environment-config",
                                       headers={"Origin": "https://preview-123.onrender.com"},
                                       timeout=30)

            result["wildcard_test"] = {
                "status_code": wildcard_test.status_code,
                "cors_origin": wildcard_test.headers.get("Access-Control-Allow-Origin"),
                "wildcard_supported": wildcard_test.headers.get("Access-Control-Allow-Origin") == "*" or
                                    "onrender.com" in (wildcard_test.headers.get("Access-Control-Allow-Origin") or "")
            }

        except Exception as e:
            result = {
                "accessible": False,
                "error": str(e)
            }

        self.results["detailed_results"]["cors_configuration"] = result
        return result

    def validate_auth0_isolation(self) -> Dict[str, Any]:
        """Validate Auth0 staging isolation capabilities"""
        print("Validating Auth0 staging isolation...")

        env_result = self.results["detailed_results"].get("environment_config", {})
        staging_result = self.results["detailed_results"].get("staging_health", {})

        auth0_validation = {
            "staging_credentials_available": False,
            "production_credentials_active": False,
            "isolation_capable": False,
            "environment_switching_ready": False
        }

        if env_result.get("accessible") and env_result.get("status_code") == 200:
            validation = env_result.get("validation", {})

            auth0_validation.update({
                "staging_credentials_available": (
                    validation.get("staging_domain_set") and
                    validation.get("staging_client_id_set") and
                    validation.get("staging_client_secret_set")
                ),
                "production_credentials_active": not validation.get("use_staging_auth0", True),
                "has_staging_config": validation.get("has_staging_config", False),
                "environment_switching_ready": validation.get("has_staging_config", False)
            })

        if staging_result.get("accessible") and staging_result.get("status_code") == 200:
            staging_validation = staging_result.get("validation", {})
            auth0_validation["auth0_environment_detected"] = staging_validation.get("auth0_environment")

        # Determine isolation capability
        auth0_validation["isolation_capable"] = (
            auth0_validation["staging_credentials_available"] and
            auth0_validation["environment_switching_ready"]
        )

        self.results["auth0_validation"] = auth0_validation
        return auth0_validation

    def validate_production_protection(self) -> Dict[str, Any]:
        """Validate that production environment is properly protected"""
        print("Validating production protection...")

        env_result = self.results["detailed_results"].get("environment_config", {})
        staging_result = self.results["detailed_results"].get("staging_health", {})

        protection = {
            "production_mode_active": False,
            "staging_mode_inactive": False,
            "production_auth0_active": False,
            "production_isolated": False
        }

        if env_result.get("accessible") and env_result.get("status_code") == 200:
            validation = env_result.get("validation", {})
            protection.update({
                "production_mode_active": validation.get("is_production", False),
                "staging_mode_inactive": not validation.get("is_staging", True),
                "production_auth0_active": not validation.get("use_staging_auth0", True)
            })

        if staging_result.get("accessible") and staging_result.get("status_code") == 200:
            staging_validation = staging_result.get("validation", {})
            protection["staging_mode_reported"] = staging_validation.get("staging_mode", True)

        # Overall protection status
        protection["production_isolated"] = (
            protection["production_mode_active"] and
            protection["staging_mode_inactive"] and
            protection["production_auth0_active"]
        )

        self.results["production_protection"] = protection
        return protection

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        env_result = self.results["detailed_results"].get("environment_config", {})
        staging_result = self.results["detailed_results"].get("staging_health", {})
        auth0_validation = self.results.get("auth0_validation", {})

        # Database connectivity issue
        if staging_result.get("accessible") and staging_result.get("status_code") == 200:
            staging_validation = staging_result.get("validation", {})
            if not staging_validation.get("database_connected"):
                recommendations.append("CRITICAL: Database connectivity issue detected - fix database import module path")

        # Preview environment recommendation
        if not auth0_validation.get("isolation_capable"):
            recommendations.append("Consider creating dedicated preview environments for isolated staging testing")

        # Environment switching capability
        if auth0_validation.get("staging_credentials_available"):
            recommendations.append("Staging credentials available - environment switching capability confirmed")

        # Production protection
        production_protection = self.results.get("production_protection", {})
        if production_protection.get("production_isolated"):
            recommendations.append("Production environment properly isolated and protected")

        self.results["recommendations"] = recommendations
        return recommendations

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("Starting comprehensive staging environment validation...")
        print(f"Target URL: {self.base_url}")
        print("=" * 50)

        # Run all tests
        self.test_basic_health()
        self.test_environment_config()
        self.test_staging_health()
        self.test_cors_configuration()

        # Analyze results
        self.validate_auth0_isolation()
        self.validate_production_protection()
        self.generate_recommendations()

        # Generate summary
        summary = {
            "basic_health_accessible": self.results["detailed_results"]["basic_health"].get("accessible", False),
            "environment_config_accessible": self.results["detailed_results"]["environment_config"].get("accessible", False),
            "staging_health_accessible": self.results["detailed_results"]["staging_health"].get("accessible", False),
            "cors_configuration_accessible": self.results["detailed_results"]["cors_configuration"].get("accessible", False),
            "auth0_isolation_capable": self.results["auth0_validation"].get("isolation_capable", False),
            "production_protected": self.results["production_protection"].get("production_isolated", False),
            "overall_status": "OPERATIONAL" if all([
                self.results["detailed_results"]["basic_health"].get("accessible", False),
                self.results["detailed_results"]["environment_config"].get("accessible", False),
                self.results["detailed_results"]["staging_health"].get("accessible", False)
            ]) else "ISSUES_DETECTED"
        }

        self.results["validation_summary"] = summary

        print("\nValidation Summary:")
        print("=" * 30)
        for key, value in summary.items():
            print(f"{key}: {value}")

        return self.results

    def save_results(self, filename: str = None) -> str:
        """Save validation results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"staging_validation_report_{timestamp}.json"

        filepath = f"/Users/matt/Sites/MarketEdge/{filename}"
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to: {filepath}")
        return filepath

def main():
    """Main validation execution"""
    validator = StagingEnvironmentValidator()
    results = validator.run_comprehensive_validation()

    # Save results
    report_file = validator.save_results()

    print("\n" + "=" * 50)
    print("STAGING ENVIRONMENT VALIDATION COMPLETE")
    print("=" * 50)

    print(f"\nOverall Status: {results['validation_summary']['overall_status']}")
    print(f"Auth0 Isolation Capable: {results['auth0_validation']['isolation_capable']}")
    print(f"Production Protected: {results['production_protection']['production_isolated']}")

    print("\nRecommendations:")
    for rec in results["recommendations"]:
        print(f"- {rec}")

    print(f"\nDetailed report: {report_file}")

if __name__ == "__main__":
    main()