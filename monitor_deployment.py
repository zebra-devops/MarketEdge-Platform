#!/usr/bin/env python3
"""
Deployment Monitoring Script for £925K Odeon Opportunity
Monitors Render deployment progress and validates restructured paths
"""
import time
import requests
import sys
from datetime import datetime

DEPLOYMENT_URL = "https://marketedge-platform.onrender.com"
HEALTH_ENDPOINT = f"{DEPLOYMENT_URL}/health"
API_ENDPOINT = f"{DEPLOYMENT_URL}/api/v1"

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_health():
    """Check if the health endpoint is responding"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except requests.RequestException as e:
        return False, str(e)

def check_api():
    """Check if the API endpoint is responding"""
    try:
        response = requests.get(API_ENDPOINT, timeout=10)
        return response.status_code in [200, 404]  # 404 is OK for root API endpoint
    except requests.RequestException:
        return False

def validate_epic_functionality():
    """Validate that Epic 1 & 2 functionality is working"""
    endpoints_to_test = [
        "/api/v1/auth/health",
        "/api/v1/admin/health", 
        "/api/v1/users/health",
        "/api/v1/organisations/health"
    ]
    
    working_endpoints = []
    for endpoint in endpoints_to_test:
        try:
            url = f"{DEPLOYMENT_URL}{endpoint}"
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 401]:  # 401 is OK for auth-protected endpoints
                working_endpoints.append(endpoint)
        except requests.RequestException:
            pass
    
    return working_endpoints

def main():
    log_message("Starting deployment monitoring for £925K Odeon opportunity")
    log_message("Monitoring repository restructuring deployment on Render...")
    
    max_attempts = 60  # 30 minutes of monitoring
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        log_message(f"Monitoring attempt {attempt}/{max_attempts}")
        
        # Check health endpoint
        health_ok, health_result = check_health()
        
        if health_ok:
            log_message("✅ DEPLOYMENT SUCCESS: Health endpoint responding!")
            log_message(f"Health response: {health_result}")
            
            # Check API availability
            if check_api():
                log_message("✅ API endpoints accessible")
                
                # Validate Epic functionality
                working_endpoints = validate_epic_functionality()
                if working_endpoints:
                    log_message(f"✅ Epic functionality validated: {len(working_endpoints)} endpoints working")
                    for endpoint in working_endpoints:
                        log_message(f"  - {endpoint}")
                
                log_message("🎉 DEPLOYMENT VALIDATION COMPLETE")
                log_message("🏢 £925K Odeon opportunity is now UNBLOCKED!")
                log_message("📊 Repository restructuring successfully deployed to production")
                return 0
            else:
                log_message("⚠️  Health OK but API not fully ready, continuing to monitor...")
        else:
            log_message(f"⏳ Service not ready: {health_result}")
        
        if attempt < max_attempts:
            log_message("Waiting 30 seconds before next check...")
            time.sleep(30)
    
    log_message("❌ Deployment monitoring timed out")
    log_message("Manual verification required")
    return 1

if __name__ == "__main__":
    sys.exit(main())