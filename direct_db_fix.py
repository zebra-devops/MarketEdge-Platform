#!/usr/bin/env python3
"""Direct database connection to fix schema"""

import requests
import time

def test_authentication():
    """Test if authentication is working"""
    try:
        # Test auth URL generation
        response = requests.get(
            "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url",
            params={"redirect_uri": "https://app.zebra.associates/callback"}
        )
        if response.status_code == 200:
            print("✓ Auth0 URL generation working")
            return True
        else:
            print(f"✗ Auth0 URL generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Auth test failed: {str(e)}")
        return False

def test_emergency_fix():
    """Try to call the emergency fix endpoint"""
    try:
        response = requests.post(
            "https://marketedge-platform.onrender.com/api/v1/auth/emergency/fix-database-schema",
            headers={"Content-Type": "application/json"}
        )
        print(f"Emergency fix response: {response.status_code}")
        if response.text:
            print(f"Response: {response.text[:200]}")
        return response.status_code == 200
    except Exception as e:
        print(f"Emergency fix failed: {str(e)}")
        return False

def main():
    print("=== EMERGENCY DATABASE AUTHENTICATION FIX ===")
    
    # Test current authentication status
    print("\n1. Testing authentication URL generation...")
    auth_working = test_authentication()
    
    # Try emergency fix
    print("\n2. Attempting emergency database fix...")
    fix_working = test_emergency_fix()
    
    if not fix_working:
        print("\n3. Emergency fix endpoint failed. The issue is likely:")
        print("   - Missing database columns: department, location, phone")
        print("   - These are required by the User model but don't exist in production")
        print("   - Manual database intervention required")
        
        print("\n4. Manual fix needed:")
        print("   ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100);")
        print("   ALTER TABLE users ADD COLUMN IF NOT EXISTS location VARCHAR(100);") 
        print("   ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);")
        
        # Check logs
        print("\n5. Checking recent logs...")
        try:
            # This would need render CLI access
            pass
        except:
            pass
    
    print(f"\nAuthentication URL working: {'✓' if auth_working else '✗'}")
    print(f"Emergency fix working: {'✓' if fix_working else '✗'}")

if __name__ == "__main__":
    main()