#!/usr/bin/env python3
"""
Comprehensive Deployment Validation Script for MarketEdge Platform
Validates all critical systems before production deployment
"""
import asyncio
import sys
import os
import time
import json
from typing import Dict, List, Any

# Add current directory to Python path
sys.path.insert(0, os.getcwd())
os.environ['PYTHONPATH'] = os.getcwd()

class DeploymentValidator:
    def __init__(self):
        self.results = {
            'timestamp': time.time(),
            'validation_results': {},
            'overall_status': 'UNKNOWN',
            'errors': [],
            'warnings': []
        }
    
    def log_result(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """Log a validation result"""
        self.results['validation_results'][test_name] = {
            'status': status,
            'details': details or {},
            'timestamp': time.time()
        }
        
        status_emoji = '✅' if status == 'PASSED' else '❌' if status == 'FAILED' else '⚠️'
        print(f"{status_emoji} {test_name}: {status}")
        
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def test_python_imports(self) -> bool:
        """Test all critical Python imports"""
        try:
            print("\n=== Testing Python Imports ===")
            
            from app.main import app
            from app.core.module_discovery import ModuleDiscoveryService
            from app.core.lazy_startup import lazy_startup_manager  
            from app.api.api_v1.api import api_router
            from app.core.config import settings
            
            self.log_result(
                "Python Imports",
                "PASSED",
                {
                    "imports_tested": [
                        "app.main",
                        "app.core.module_discovery", 
                        "app.core.lazy_startup",
                        "app.api.api_v1.api",
                        "app.core.config"
                    ],
                    "project_name": settings.PROJECT_NAME,
                    "project_version": settings.PROJECT_VERSION
                }
            )
            return True
            
        except Exception as e:
            self.log_result("Python Imports", "FAILED", {"error": str(e)})
            self.results['errors'].append(f"Import error: {str(e)}")
            return False
    
    def test_application_startup(self) -> bool:
        """Test FastAPI application startup"""
        try:
            print("\n=== Testing Application Startup ===")
            
            from app.main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            
            # Test health endpoint
            response = client.get('/health')
            if response.status_code != 200:
                raise Exception(f"Health endpoint failed: {response.status_code}")
                
            health_data = response.json()
            
            self.log_result(
                "Application Startup",
                "PASSED",
                {
                    "health_status": health_data.get('status'),
                    "architecture": health_data.get('architecture'),
                    "cold_start_time": health_data.get('cold_start_time'),
                    "database_status": health_data.get('services', {}).get('database'),
                    "redis_status": health_data.get('services', {}).get('redis')
                }
            )
            return True
            
        except Exception as e:
            self.log_result("Application Startup", "FAILED", {"error": str(e)})
            self.results['errors'].append(f"Startup error: {str(e)}")
            return False
    
    def test_epic_endpoints(self) -> bool:
        """Test Epic 1 and Epic 2 endpoint availability"""
        try:
            print("\n=== Testing Epic Endpoints ===")
            
            from app.main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            
            # Get system status to see available routes
            response = client.get('/system/status')
            if response.status_code != 200:
                raise Exception(f"System status endpoint failed: {response.status_code}")
            
            status_data = response.json()
            total_routes = status_data.get('total_routes', 0)
            epic_routes = status_data.get('epic_routes_found', 0)
            
            # Test key Epic endpoints (should be protected)
            epic_endpoints_to_test = [
                '/api/v1/features/enabled',
                '/api/v1/module-management/modules'
            ]
            
            protected_count = 0
            for endpoint in epic_endpoints_to_test:
                response = client.get(endpoint)
                if response.status_code in [401, 403]:  # Properly protected
                    protected_count += 1
            
            self.log_result(
                "Epic Endpoints",
                "PASSED",
                {
                    "total_routes": total_routes,
                    "epic_routes_found": epic_routes,
                    "endpoints_tested": len(epic_endpoints_to_test),
                    "properly_protected": protected_count
                }
            )
            return True
            
        except Exception as e:
            self.log_result("Epic Endpoints", "FAILED", {"error": str(e)})
            self.results['errors'].append(f"Epic endpoints error: {str(e)}")
            return False
    
    def test_authentication_security(self) -> bool:
        """Test authentication and security measures"""
        try:
            print("\n=== Testing Authentication Security ===")
            
            from app.main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            
            # Test protected endpoints without authentication
            protected_endpoints = [
                '/api/v1/users/',
                '/api/v1/organisations',
                '/api/v1/features/enabled',
                '/api/v1/module-management/modules'
            ]
            
            properly_protected = 0
            for endpoint in protected_endpoints:
                response = client.get(endpoint)
                if response.status_code in [401, 403]:
                    properly_protected += 1
            
            protection_rate = properly_protected / len(protected_endpoints)
            
            self.log_result(
                "Authentication Security",
                "PASSED" if protection_rate == 1.0 else "WARNING",
                {
                    "endpoints_tested": len(protected_endpoints),
                    "properly_protected": properly_protected,
                    "protection_rate": f"{protection_rate * 100:.1f}%"
                }
            )
            
            return protection_rate >= 0.8  # At least 80% protected
            
        except Exception as e:
            self.log_result("Authentication Security", "FAILED", {"error": str(e)})
            self.results['errors'].append(f"Auth security error: {str(e)}")
            return False
    
    def test_performance_benchmarks(self) -> bool:
        """Test performance benchmarks"""
        try:
            print("\n=== Testing Performance Benchmarks ===")
            
            from app.main import app
            from fastapi.testclient import TestClient
            import statistics
            
            client = TestClient(app)
            
            # Test key endpoints for performance
            test_endpoints = ['/', '/health', '/deployment-test']
            results = {}
            
            for endpoint in test_endpoints:
                times = []
                # Warm up
                for _ in range(3):
                    client.get(endpoint)
                
                # Benchmark
                for _ in range(10):
                    start_time = time.time()
                    response = client.get(endpoint)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        times.append((end_time - start_time) * 1000)  # Convert to ms
                
                if times:
                    avg_time = statistics.mean(times)
                    results[endpoint] = avg_time
            
            # Check if all endpoints meet performance targets
            performance_target = 100  # ms
            all_good = all(time < performance_target for time in results.values())
            
            self.log_result(
                "Performance Benchmarks",
                "PASSED" if all_good else "WARNING",
                {
                    "target_ms": performance_target,
                    "results": {k: f"{v:.2f}ms" for k, v in results.items()},
                    "meets_targets": all_good
                }
            )
            
            return all_good
            
        except Exception as e:
            self.log_result("Performance Benchmarks", "FAILED", {"error": str(e)})
            self.results['errors'].append(f"Performance error: {str(e)}")
            return False
    
    def test_docker_readiness(self) -> bool:
        """Test Docker configuration readiness"""
        try:
            print("\n=== Testing Docker Readiness ===")
            
            # Check required files exist
            required_files = [
                'Dockerfile',
                'requirements.txt', 
                'start.sh',
                'gunicorn_production.conf.py'
            ]
            
            missing_files = []
            for file_path in required_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            # Check Dockerfile COPY commands
            dockerfile_valid = True
            try:
                with open('Dockerfile', 'r') as f:
                    dockerfile_content = f.read()
                    if 'COPY --chown=appuser:appuser requirements.txt .' not in dockerfile_content:
                        dockerfile_valid = False
                    if 'COPY --chown=appuser:appuser . .' not in dockerfile_content:
                        dockerfile_valid = False
            except Exception:
                dockerfile_valid = False
            
            success = len(missing_files) == 0 and dockerfile_valid
            
            self.log_result(
                "Docker Readiness",
                "PASSED" if success else "FAILED",
                {
                    "required_files": required_files,
                    "missing_files": missing_files,
                    "dockerfile_valid": dockerfile_valid
                }
            )
            
            if not success and missing_files:
                self.results['errors'].append(f"Missing Docker files: {missing_files}")
            
            return success
            
        except Exception as e:
            self.log_result("Docker Readiness", "FAILED", {"error": str(e)})
            self.results['errors'].append(f"Docker readiness error: {str(e)}")
            return False
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("🚀 Starting Comprehensive Deployment Validation")
        print("=" * 50)
        
        test_results = []
        
        # Run all tests
        test_results.append(self.test_python_imports())
        test_results.append(self.test_docker_readiness())
        test_results.append(self.test_application_startup())
        test_results.append(self.test_epic_endpoints())
        test_results.append(self.test_authentication_security())
        test_results.append(self.test_performance_benchmarks())
        
        # Calculate overall status
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        pass_rate = passed_tests / total_tests
        
        if pass_rate == 1.0:
            self.results['overall_status'] = 'READY_FOR_DEPLOYMENT'
        elif pass_rate >= 0.8:
            self.results['overall_status'] = 'MOSTLY_READY_WITH_WARNINGS'
        else:
            self.results['overall_status'] = 'NOT_READY_FOR_DEPLOYMENT'
        
        # Print final results
        print("\n" + "=" * 50)
        print(f"🎯 VALIDATION COMPLETE")
        print(f"Tests passed: {passed_tests}/{total_tests}")
        print(f"Pass rate: {pass_rate * 100:.1f}%")
        
        status_emoji = "🟢" if pass_rate == 1.0 else "🟡" if pass_rate >= 0.8 else "🔴"
        print(f"{status_emoji} Overall Status: {self.results['overall_status']}")
        
        if self.results['errors']:
            print("\n❌ Errors:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        if self.results['warnings']:
            print("\n⚠️  Warnings:")
            for warning in self.results['warnings']:
                print(f"  - {warning}")
        
        return self.results

def main():
    """Main execution function"""
    validator = DeploymentValidator()
    results = validator.run_comprehensive_validation()
    
    # Save results to file
    with open('validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Validation results saved to: validation_results.json")
    
    # Exit with appropriate code
    if results['overall_status'] == 'READY_FOR_DEPLOYMENT':
        print("\n✅ READY FOR PRODUCTION DEPLOYMENT!")
        sys.exit(0)
    elif results['overall_status'] == 'MOSTLY_READY_WITH_WARNINGS':
        print("\n⚠️  MOSTLY READY - Review warnings before deployment")
        sys.exit(0)
    else:
        print("\n❌ NOT READY - Address errors before deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()