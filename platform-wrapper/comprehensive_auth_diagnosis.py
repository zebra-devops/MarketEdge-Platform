#!/usr/bin/env python3
"""
Comprehensive Authentication Diagnosis

This script performs a deep analysis of the authentication failure patterns
to identify the exact cause of persistent "Database error occurred" messages
despite having correct Auth0 configuration.
"""
import requests
import json
import time
from typing import Dict, Any, List, Optional

class AuthDiagnosticAnalyzer:
    def __init__(self):
        self.backend_url = "https://marketedge-backend-production.up.railway.app"
        self.frontend_url = "https://app.zebra.associates"
        self.test_results = []
        
    def test_backend_connectivity(self) -> Dict[str, Any]:
        """Test basic backend connectivity and health"""
        result = {
            "test": "Backend Connectivity",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Test health endpoint
            health_response = requests.get(f"{self.backend_url}/health", timeout=10)
            result["details"]["health_endpoint"] = {
                "status_code": health_response.status_code,
                "accessible": health_response.status_code == 200
            }
            
            # Test root endpoint
            root_response = requests.get(f"{self.backend_url}/", timeout=10)
            result["details"]["root_endpoint"] = {
                "status_code": root_response.status_code,
                "accessible": root_response.status_code in [200, 404]  # 404 is expected
            }
            
            # Test API root
            api_response = requests.get(f"{self.backend_url}/api/v1/", timeout=10)
            result["details"]["api_endpoint"] = {
                "status_code": api_response.status_code,
                "accessible": api_response.status_code in [200, 404]
            }
            
            if any(detail["accessible"] for detail in result["details"].values()):
                result["status"] = "accessible"
            else:
                result["status"] = "inaccessible"
                
        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)
            
        return result
    
    def test_database_operations(self) -> Dict[str, Any]:
        """Test database operations through direct endpoints"""
        result = {
            "test": "Database Operations",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Test database health endpoint if it exists
            db_health_response = requests.get(f"{self.backend_url}/api/v1/database/health", timeout=10)
            result["details"]["db_health"] = {
                "status_code": db_health_response.status_code,
                "response": db_health_response.text[:500] if db_health_response.text else "No response"
            }
            
            # Test organization creation (this often fails)
            org_test_response = requests.post(
                f"{self.backend_url}/api/v1/database/test-org-creation",
                json={"name": "Test Org", "industry": "Technology"},
                timeout=10
            )
            result["details"]["org_creation"] = {
                "status_code": org_test_response.status_code,
                "response": org_test_response.text[:500] if org_test_response.text else "No response"
            }
            
            if db_health_response.status_code == 200:
                result["status"] = "working"
            elif "Database error occurred" in db_health_response.text:
                result["status"] = "database_error"
            else:
                result["status"] = "issues"
                
        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)
            
        return result
    
    def test_auth0_token_exchange(self) -> Dict[str, Any]:
        """Test Auth0 token exchange simulation"""
        result = {
            "test": "Auth0 Token Exchange",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Test with a mock/test code
            auth_response = requests.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={
                    "code": "test_code_for_diagnostic",
                    "redirect_uri": f"{self.frontend_url}/callback"
                },
                headers={
                    "Content-Type": "application/json",
                    "Origin": self.frontend_url
                },
                timeout=15
            )
            
            result["details"]["auth_endpoint"] = {
                "status_code": auth_response.status_code,
                "response": auth_response.text[:1000] if auth_response.text else "No response",
                "has_cors_headers": "Access-Control-Allow-Origin" in auth_response.headers
            }
            
            # Analyze the specific error pattern
            response_text = auth_response.text.lower()
            if "database error occurred" in response_text:
                result["status"] = "database_error"
                result["details"]["error_type"] = "database"
            elif "failed to exchange authorization code" in response_text:
                result["status"] = "auth0_exchange_error"
                result["details"]["error_type"] = "auth0_exchange"
            elif auth_response.status_code == 404:
                result["status"] = "endpoint_not_found"
                result["details"]["error_type"] = "deployment"
            elif auth_response.status_code == 500:
                result["status"] = "server_error"
                result["details"]["error_type"] = "server"
            else:
                result["status"] = "other"
                
        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)
            
        return result
    
    def test_auth0_configuration(self) -> Dict[str, Any]:
        """Test Auth0 URL generation and configuration"""
        result = {
            "test": "Auth0 Configuration",
            "status": "unknown",
            "details": {}
        }
        
        try:
            auth_url_response = requests.get(
                f"{self.backend_url}/api/v1/auth/auth0-url",
                params={"redirect_uri": f"{self.frontend_url}/callback"},
                timeout=10
            )
            
            result["details"]["auth0_url"] = {
                "status_code": auth_url_response.status_code,
                "response": auth_url_response.text[:500] if auth_url_response.text else "No response"
            }
            
            if auth_url_response.status_code == 200:
                try:
                    url_data = auth_url_response.json()
                    result["details"]["auth_url_data"] = url_data
                    result["status"] = "working"
                except:
                    result["status"] = "invalid_response"
            else:
                result["status"] = "error"
                
        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)
            
        return result
    
    def test_environment_variables(self) -> Dict[str, Any]:
        """Test if environment variables are properly configured"""
        result = {
            "test": "Environment Variables",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Test config endpoint if it exists
            config_response = requests.get(f"{self.backend_url}/api/v1/config/status", timeout=10)
            result["details"]["config_status"] = {
                "status_code": config_response.status_code,
                "response": config_response.text[:500] if config_response.text else "No response"
            }
            
            if config_response.status_code == 200:
                result["status"] = "accessible"
            else:
                result["status"] = "not_accessible"
                
        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)
            
        return result
    
    def analyze_failure_patterns(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze test results to identify the root cause"""
        analysis = {
            "primary_issue": "unknown",
            "confidence": "low",
            "evidence": [],
            "recommendations": []
        }
        
        # Check for consistent patterns
        database_errors = 0
        auth0_errors = 0
        deployment_errors = 0
        
        for result in test_results:
            if result["status"] == "database_error":
                database_errors += 1
                analysis["evidence"].append(f"{result['test']}: Database error detected")
            elif result["status"] == "auth0_exchange_error":
                auth0_errors += 1
                analysis["evidence"].append(f"{result['test']}: Auth0 exchange error")
            elif result["status"] in ["inaccessible", "endpoint_not_found"]:
                deployment_errors += 1
                analysis["evidence"].append(f"{result['test']}: Deployment/routing error")
        
        # Determine primary issue
        if deployment_errors > 0:
            analysis["primary_issue"] = "deployment_routing"
            analysis["confidence"] = "high"
            analysis["recommendations"] = [
                "1. Check Railway deployment status and logs",
                "2. Verify service is running and accessible",
                "3. Check domain routing configuration",
                "4. Verify build and start commands"
            ]
        elif database_errors > auth0_errors:
            analysis["primary_issue"] = "database_configuration"
            analysis["confidence"] = "high"
            analysis["recommendations"] = [
                "1. Check database connection string and credentials",
                "2. Verify enum constraints (Industry, SubscriptionPlan)",
                "3. Check organization creation logic",
                "4. Validate database schema and migrations"
            ]
        elif auth0_errors > 0:
            analysis["primary_issue"] = "auth0_token_exchange"
            analysis["confidence"] = "medium"
            analysis["recommendations"] = [
                "1. Verify Auth0 CLIENT_SECRET is correctly set",
                "2. Check Auth0 application configuration",
                "3. Verify callback URLs match exactly",
                "4. Test Auth0 connectivity from production environment"
            ]
        else:
            analysis["primary_issue"] = "unknown"
            analysis["recommendations"] = [
                "1. Run more detailed diagnostics",
                "2. Check application logs",
                "3. Verify all environment variables"
            ]
            
        return analysis
    
    def run_comprehensive_diagnosis(self):
        """Run all diagnostic tests and provide analysis"""
        print("🔍 COMPREHENSIVE AUTHENTICATION DIAGNOSIS")
        print("=" * 50)
        print()
        
        tests = [
            self.test_backend_connectivity,
            self.test_auth0_configuration,
            self.test_database_operations,
            self.test_auth0_token_exchange,
            self.test_environment_variables
        ]
        
        results = []
        for test_func in tests:
            print(f"Running {test_func.__name__.replace('test_', '').replace('_', ' ').title()}...")
            result = test_func()
            results.append(result)
            
            status_emoji = {
                "working": "✅",
                "accessible": "✅", 
                "error": "❌",
                "database_error": "🔴",
                "auth0_exchange_error": "🟠",
                "endpoint_not_found": "⚠️",
                "unknown": "❓"
            }.get(result["status"], "❓")
            
            print(f"   {status_emoji} Status: {result['status']}")
            if result["details"]:
                for key, value in result["details"].items():
                    if isinstance(value, dict):
                        print(f"      {key}: {value}")
                    else:
                        print(f"      {key}: {str(value)[:100]}")
            print()
        
        # Analyze results
        print("📊 FAILURE PATTERN ANALYSIS")
        print("=" * 50)
        analysis = self.analyze_failure_patterns(results)
        
        print(f"Primary Issue: {analysis['primary_issue']}")
        print(f"Confidence: {analysis['confidence']}")
        print()
        
        if analysis["evidence"]:
            print("Evidence:")
            for evidence in analysis["evidence"]:
                print(f"   • {evidence}")
            print()
        
        print("Recommended Actions:")
        for i, recommendation in enumerate(analysis["recommendations"], 1):
            print(f"   {recommendation}")
        
        print()
        print("💡 NEXT STEPS:")
        if analysis["primary_issue"] == "deployment_routing":
            print("   Focus on deployment and routing issues first.")
            print("   The authentication logic may be working but unreachable.")
        elif analysis["primary_issue"] == "database_configuration":
            print("   Focus on database schema and enum constraints.")
            print("   The 'Database error occurred' messages indicate SQL issues.")
        elif analysis["primary_issue"] == "auth0_token_exchange":
            print("   Focus on Auth0 configuration and token exchange.")
            print("   The AUTH0_CLIENT_SECRET may be set but Auth0 calls are failing.")
        
        return results, analysis

def main():
    analyzer = AuthDiagnosticAnalyzer()
    results, analysis = analyzer.run_comprehensive_diagnosis()
    
    # Save results to file for further analysis
    with open("auth_diagnosis_results.json", "w") as f:
        json.dump({
            "timestamp": time.time(),
            "results": results,
            "analysis": analysis
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: auth_diagnosis_results.json")

if __name__ == "__main__":
    main()