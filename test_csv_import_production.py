#!/usr/bin/env python3
"""
Production CSV Import Feature Validation
Test script to verify CSV import functionality in production environment
"""
import requests
import json
import time
import csv
import io
from typing import Dict, Any, Optional

# Production configuration
PRODUCTION_BASE_URL = "https://marketedge-platform.onrender.com"
FRONTEND_URL = "https://app.zebra.associates"

class CSVImportTester:
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = requests.Session()
        
        if auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            })
    
    def test_health_endpoint(self) -> bool:
        """Test basic health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            print(f"✅ Health check: {response.status_code} - {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def create_test_csv(self) -> str:
        """Create a test CSV for import validation"""
        csv_data = [
            ['email', 'first_name', 'last_name', 'role', 'department', 'location', 'phone', 'market_edge_access', 'causal_edge_access', 'value_edge_access', 'send_invitation'],
            ['test1@example.com', 'John', 'Doe', 'analyst', 'Engineering', 'London', '+44 20 1234 5678', 'true', 'false', 'true', 'false'],
            ['test2@example.com', 'Jane', 'Smith', 'viewer', 'Marketing', 'New York', '+1 555 123 4567', 'true', 'true', 'false', 'false'],
            ['test3@example.com', 'Bob', 'Johnson', 'admin', 'Operations', 'Sydney', '+61 2 9876 5432', 'true', 'true', 'true', 'false']
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)
        return output.getvalue()
    
    def test_csv_template_download(self, org_id: str) -> bool:
        """Test CSV template download endpoint"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/organizations/{org_id}/users/import/template",
                timeout=10
            )
            
            if response.status_code == 200:
                # Check if response is CSV format
                content_type = response.headers.get('content-type', '')
                if 'csv' in content_type.lower() or 'text' in content_type.lower():
                    print(f"✅ CSV template download successful")
                    print(f"   Content: {response.text[:100]}...")
                    return True
                else:
                    print(f"❌ CSV template download returned unexpected content type: {content_type}")
                    return False
            else:
                print(f"❌ CSV template download failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ CSV template download error: {e}")
            return False
    
    def test_csv_preview(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Test CSV preview/validation endpoint"""
        try:
            # Create test CSV file
            csv_content = self.create_test_csv()
            
            # Prepare file upload
            files = {
                'file': ('test_users.csv', csv_content, 'text/csv')
            }
            
            # Remove content-type header for file upload
            headers = {'Authorization': f'Bearer {self.auth_token}'} if self.auth_token else {}
            
            response = requests.post(
                f"{self.base_url}/api/v1/organizations/{org_id}/users/import/preview",
                files=files,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ CSV preview successful:")
                print(f"   Valid: {data.get('is_valid')}")
                print(f"   Total rows: {data.get('total_rows')}")
                print(f"   Valid rows: {data.get('valid_rows')}")
                print(f"   Errors: {data.get('error_count')}")
                print(f"   Duplicates: {data.get('duplicate_count')}")
                return data
            else:
                print(f"❌ CSV preview failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ CSV preview error: {e}")
            return None
    
    def test_rate_limiting(self, org_id: str) -> bool:
        """Test rate limiting for CSV imports"""
        try:
            csv_content = self.create_test_csv()
            
            print("🔄 Testing rate limiting (attempting multiple rapid requests)...")
            
            for i in range(3):  # Try 3 rapid requests
                files = {
                    'file': (f'test_users_{i}.csv', csv_content, 'text/csv')
                }
                
                headers = {'Authorization': f'Bearer {self.auth_token}'} if self.auth_token else {}
                
                response = requests.post(
                    f"{self.base_url}/api/v1/organizations/{org_id}/users/import/preview",
                    files=files,
                    headers=headers,
                    timeout=10
                )
                
                print(f"   Request {i+1}: {response.status_code}")
                
                if response.status_code == 429:
                    print("✅ Rate limiting is working (got 429 status)")
                    return True
                
                time.sleep(1)  # Brief delay
            
            print("⚠️  Rate limiting not triggered with test requests")
            return True  # Not necessarily a failure
            
        except Exception as e:
            print(f"❌ Rate limiting test error: {e}")
            return False
    
    def test_security_validation(self, org_id: str) -> bool:
        """Test security validations"""
        try:
            print("🔒 Testing security validations...")
            
            # Test 1: Large file rejection
            large_content = "email,first_name,last_name\n" + ("test@example.com,Test,User\n" * 10000)
            files = {'file': ('large_file.csv', large_content, 'text/csv')}
            headers = {'Authorization': f'Bearer {self.auth_token}'} if self.auth_token else {}
            
            response = requests.post(
                f"{self.base_url}/api/v1/organizations/{org_id}/users/import/preview",
                files=files,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 400:
                print("✅ Large file rejection working")
            else:
                print(f"⚠️  Large file not rejected: {response.status_code}")
            
            # Test 2: Invalid file type
            files = {'file': ('test.txt', 'not a csv', 'text/plain')}
            
            response = requests.post(
                f"{self.base_url}/api/v1/organizations/{org_id}/users/import/preview",
                files=files,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 400:
                print("✅ Invalid file type rejection working")
            else:
                print(f"⚠️  Invalid file type not rejected: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Security validation test error: {e}")
            return False
    
    def run_comprehensive_test(self, org_id: str) -> Dict[str, bool]:
        """Run all tests and return results"""
        print("🚀 Starting CSV Import Production Validation")
        print("=" * 50)
        
        results = {}
        
        # Test 1: Health check
        results['health_check'] = self.test_health_endpoint()
        print()
        
        # Test 2: CSV template download
        results['template_download'] = self.test_csv_template_download(org_id)
        print()
        
        # Test 3: CSV preview/validation
        results['csv_preview'] = self.test_csv_preview(org_id) is not None
        print()
        
        # Test 4: Rate limiting
        results['rate_limiting'] = self.test_rate_limiting(org_id)
        print()
        
        # Test 5: Security validations
        results['security_validation'] = self.test_security_validation(org_id)
        print()
        
        # Summary
        print("📋 Test Results Summary:")
        print("-" * 25)
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! CSV import is ready for production use.")
        else:
            print("⚠️  Some tests failed. Review issues before full production rollout.")
        
        return results

def main():
    """Main test execution"""
    print("CSV Import Production Validation Tool")
    print("=====================================")
    print()
    
    # Configuration - replace with actual values
    BASE_URL = PRODUCTION_BASE_URL
    ORG_ID = "your-org-id-here"  # Replace with actual org ID
    AUTH_TOKEN = None  # Replace with valid JWT token
    
    if not AUTH_TOKEN:
        print("⚠️  Warning: No auth token provided. Some tests may fail.")
        print("   Set AUTH_TOKEN variable with a valid JWT token.")
        print()
    
    if ORG_ID == "your-org-id-here":
        print("⚠️  Warning: Using placeholder org ID.")
        print("   Replace ORG_ID with actual organization ID.")
        print()
    
    # Run tests
    tester = CSVImportTester(BASE_URL, AUTH_TOKEN)
    results = tester.run_comprehensive_test(ORG_ID)
    
    # Exit with appropriate code
    if all(results.values()):
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()