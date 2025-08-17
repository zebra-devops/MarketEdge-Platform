#!/usr/bin/env python3
"""
Update Render Backend CORS Configuration
========================================

This script updates the CORS_ORIGINS environment variable on the Render backend
to include the new Vercel deployment URL for the frontend.

Author: DevOps Engineer
Date: 2025-08-16
Purpose: Complete Epic 2 Migration - Fix CORS for new frontend deployment
"""

import os
import json
import requests
import subprocess
import sys

def get_render_api_key():
    """Get Render API key from environment or prompt user"""
    api_key = os.getenv('RENDER_API_KEY')
    if not api_key:
        print("❌ RENDER_API_KEY environment variable not set")
        print("Please set it or visit https://dashboard.render.com/account/settings to get your API key")
        return None
    return api_key

def update_cors_origins():
    """Update CORS origins to include new Vercel deployment"""
    
    # New CORS origins list that includes the new Vercel deployment
    new_cors_origins = [
        "https://app.zebra.associates",
        "https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001"
    ]
    
    print("🔧 CORS Configuration Update")
    print("="*50)
    print(f"Adding frontend URL: https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app")
    print(f"Complete CORS origins list:")
    for origin in new_cors_origins:
        print(f"  - {origin}")
    
    # Convert to JSON string format expected by backend
    cors_json = json.dumps(new_cors_origins)
    print(f"\nJSON format: {cors_json}")
    
    return cors_json

def manual_instructions():
    """Provide manual instructions for updating CORS in Render dashboard"""
    
    cors_json = update_cors_origins()
    
    print("\n" + "="*60)
    print("MANUAL RENDER DASHBOARD UPDATE INSTRUCTIONS")
    print("="*60)
    
    print("\n📋 Steps to update CORS configuration:")
    print("1. Go to https://dashboard.render.com")
    print("2. Navigate to your 'marketedge-platform' service")
    print("3. Click on 'Environment' tab")
    print("4. Find the 'CORS_ORIGINS' environment variable")
    print("5. Update its value to:")
    print(f"\n   {cors_json}")
    print("\n6. Click 'Save Changes'")
    print("7. Wait for automatic redeployment to complete")
    print("8. Verify with health check")
    
    print("\n🔍 Verification steps:")
    print("1. Check health endpoint:")
    print("   curl https://marketedge-platform.onrender.com/health")
    print("\n2. Test CORS from browser console:")
    print("   fetch('https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app/callback', {")
    print("     credentials: 'include',")
    print("     headers: { 'Origin': 'https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app' }")
    print("   })")
    
    print("\n3. Test full auth flow:")
    print("   - Visit: https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app")
    print("   - Attempt login")
    print("   - Verify no CORS errors in browser console")

def test_current_cors():
    """Test current CORS configuration"""
    print("\n🔍 Testing Current CORS Configuration...")
    
    test_origin = "https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app"
    
    try:
        # Test preflight request
        response = requests.options(
            "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url",
            headers={
                'Origin': test_origin,
                'Access-Control-Request-Method': 'GET'
            },
            timeout=10
        )
        
        allow_origin = response.headers.get('Access-Control-Allow-Origin')
        allow_methods = response.headers.get('Access-Control-Allow-Methods')
        
        print(f"Status Code: {response.status_code}")
        print(f"Access-Control-Allow-Origin: {allow_origin}")
        print(f"Access-Control-Allow-Methods: {allow_methods}")
        
        if allow_origin == test_origin or allow_origin == "*":
            print("✅ CORS is properly configured for the new frontend!")
            return True
        else:
            print("❌ CORS is not configured for the new frontend")
            return False
            
    except Exception as e:
        print(f"❌ Error testing CORS: {e}")
        return False

def check_backend_health():
    """Check if backend is healthy"""
    try:
        response = requests.get("https://marketedge-platform.onrender.com/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend Health: {health_data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Backend Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend Health Check Error: {e}")
        return False

def main():
    """Main execution"""
    print("🚀 Render CORS Configuration Update Tool")
    print("=" * 50)
    
    # Check backend health first
    if not check_backend_health():
        print("❌ Backend is not healthy, cannot proceed with CORS update")
        return False
    
    # Test current CORS
    if test_current_cors():
        print("✅ CORS is already configured correctly!")
        return True
    
    # Provide manual instructions
    manual_instructions()
    
    print("\n" + "="*60)
    print("POST-UPDATE VALIDATION")
    print("="*60)
    print("\nAfter updating CORS in Render dashboard, run this script again to verify:")
    print(f"python3 {__file__}")
    
    print("\n🎯 Expected Result:")
    print("- Frontend connects to backend without CORS errors")
    print("- Auth0 login flow works end-to-end")
    print("- £925K demo is fully operational")

if __name__ == "__main__":
    main()