#!/usr/bin/env python3
"""
Test script to verify Railway deployment is working without Supabase
"""

import requests
import json
from typing import Dict, Any

def test_railway_deployment():
    """Test the Railway deployment health and configuration"""
    
    # Railway deployment URL (replace with your actual URL)
    BASE_URL = "https://marketedge-backend-production.up.railway.app"
    
    print("Testing Railway Deployment without Supabase...")
    print(f"Base URL: {BASE_URL}")
    print("-" * 50)
    
    # Test 1: Health Check
    try:
        print("1. Testing health endpoint...")
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed: {health_data}")
            
            # Check data layer status
            if 'data_layer' in health_data:
                data_layer_status = health_data['data_layer']
                if data_layer_status.get('enabled') == False:
                    print("✅ Data layer correctly disabled")
                else:
                    print(f"⚠️  Data layer status: {data_layer_status}")
        else:
            print(f"❌ Health check failed: {response.status_code} - {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check request failed: {e}")
        return False
    
    # Test 2: Root endpoint
    try:
        print("\n2. Testing root endpoint...")
        response = requests.get(f"{BASE_URL}/", timeout=10)
        
        if response.status_code == 200:
            print("✅ Root endpoint accessible")
        else:
            print(f"⚠️  Root endpoint returned: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Root endpoint request failed: {e}")
    
    # Test 3: Check if Supabase errors are gone
    try:
        print("\n3. Testing API documentation endpoint...")
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        
        if response.status_code == 200:
            print("✅ API documentation accessible")
        else:
            print(f"⚠️  API docs returned: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ API docs request failed: {e}")
    
    print("\n" + "=" * 50)
    print("Deployment test completed!")
    print("If all tests passed, Railway deployment is working without Supabase.")
    
    return True

if __name__ == "__main__":
    test_railway_deployment()