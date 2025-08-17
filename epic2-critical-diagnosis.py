#!/usr/bin/env python3
"""
Epic 2 Critical Diagnosis Tool
Diagnose critical issues found during testing
"""

import asyncio
import httpx
import json
import time

async def diagnose_backend_issues():
    backend_url = "https://marketedge-platform.onrender.com"
    
    print("🚨 Epic 2 Critical Issue Diagnosis")
    print("=" * 50)
    
    # Test basic connectivity
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            print("\n1. Testing basic connectivity...")
            response = await client.get(f"{backend_url}/health")
            print(f"   /health: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   Health data: {json.dumps(health_data, indent=2)}")
            
            print("\n2. Testing readiness endpoint...")
            response = await client.get(f"{backend_url}/ready")
            print(f"   /ready: {response.status_code}")
            if response.status_code == 503:
                try:
                    error_data = response.json()
                    print(f"   Error details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error response: {response.text}")
            
            print("\n3. Testing API v1 endpoints...")
            endpoints = [
                "/api/v1/health",
                "/api/v1/auth/auth0-url",
                "/api/v1/auth/callback",
                "/api/v1/openapi.json"
            ]
            
            for endpoint in endpoints:
                try:
                    response = await client.get(f"{backend_url}{endpoint}")
                    print(f"   {endpoint}: {response.status_code}")
                except Exception as e:
                    print(f"   {endpoint}: ERROR - {str(e)}")
            
            print("\n4. Testing CORS debug...")
            response = await client.get(f"{backend_url}/cors-debug")
            print(f"   /cors-debug: {response.status_code}")
            if response.status_code == 200:
                cors_data = response.json()
                print(f"   CORS origins: {cors_data.get('cors_origins_configured', 'N/A')}")
                print(f"   Environment: {cors_data.get('environment', 'N/A')}")
                print(f"   Service type: {cors_data.get('service_type', 'N/A')}")
    
    except Exception as e:
        print(f"Critical error during diagnosis: {str(e)}")

if __name__ == "__main__":
    asyncio.run(diagnose_backend_issues())