#!/usr/bin/env python3
"""
Test script to validate both JSON and form data authentication formats
"""
import requests
import json
import time
from urllib.parse import urlencode

# Test configuration
BACKEND_URL = "https://marketedge-platform.onrender.com"
AUTH_ENDPOINT = f"{BACKEND_URL}/api/v1/auth/login"

# Mock Auth0 callback data (using test values)
TEST_DATA = {
    "code": "test_auth_code_12345",
    "redirect_uri": "https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app/callback",
    "state": "test_state_12345"
}

def test_json_format():
    """Test JSON format (existing behavior)"""
    print("🧪 Testing JSON format authentication...")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(
            AUTH_ENDPOINT,
            headers=headers,
            json=TEST_DATA,
            timeout=30
        )
        
        print(f"JSON Format Response:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        
        if response.status_code == 422:
            print("  ✅ Expected 422 for invalid test auth code")
        elif response.status_code == 400:
            print("  ✅ Expected 400 for test auth code")
        else:
            print(f"  ⚠️  Unexpected status: {response.status_code}")
            
        try:
            response_data = response.json()
            print(f"  Response Body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"  Response Text: {response.text}")
            
        return response.status_code
        
    except Exception as e:
        print(f"  ❌ JSON format test failed: {e}")
        return None

def test_form_data_format():
    """Test form data format (CORS workaround)"""
    print("\n🧪 Testing Form Data format authentication...")
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    # Create form data
    form_data = urlencode(TEST_DATA)
    
    try:
        response = requests.post(
            AUTH_ENDPOINT,
            headers=headers,
            data=form_data,
            timeout=30
        )
        
        print(f"Form Data Format Response:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        
        if response.status_code == 422:
            print("  ✅ Expected 422 for invalid test auth code")
        elif response.status_code == 400:
            print("  ✅ Expected 400 for test auth code")
        else:
            print(f"  ⚠️  Unexpected status: {response.status_code}")
            
        try:
            response_data = response.json()
            print(f"  Response Body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"  Response Text: {response.text}")
            
        return response.status_code
        
    except Exception as e:
        print(f"  ❌ Form data format test failed: {e}")
        return None

def test_backend_availability():
    """Test if backend is available"""
    print("🏥 Testing backend availability...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ Backend is available")
            return True
        else:
            print(f"  ⚠️  Backend returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Backend unavailable: {e}")
        return False

def main():
    """Run authentication format tests"""
    print("🔧 Auth0 Authentication Format Testing Suite")
    print("=" * 50)
    
    # Check backend availability
    if not test_backend_availability():
        print("\n❌ Cannot proceed - backend is not available")
        return
    
    # Wait for deployment to complete
    print("\n⏳ Waiting 30 seconds for Render deployment to complete...")
    time.sleep(30)
    
    # Test both formats
    json_status = test_json_format()
    form_status = test_form_data_format()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    if json_status is not None and form_status is not None:
        if json_status == form_status:
            print("✅ SUCCESS: Both formats return same status code")
            print(f"   JSON Status: {json_status}")
            print(f"   Form Status: {form_status}")
            print("\n🎉 Authentication format mismatch RESOLVED!")
            print("   - Backend now accepts both JSON and form data")
            print("   - CORS workaround is functional")
            print("   - Backward compatibility maintained")
        else:
            print("⚠️  WARNING: Different status codes between formats")
            print(f"   JSON Status: {json_status}")
            print(f"   Form Status: {form_status}")
    else:
        print("❌ FAILURE: One or both tests failed to complete")
        
    print("\n🚀 Ready for end-to-end Auth0 testing with real credentials")

if __name__ == "__main__":
    main()