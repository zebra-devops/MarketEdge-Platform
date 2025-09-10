#!/usr/bin/env python3
"""
DIRECT DATABASE ENUM CASE FIX
=============================
Execute the exact SQL UPDATE statements to fix the enum case mismatch

CRITICAL SQL COMMANDS:
UPDATE user_application_access SET application_type = 'MARKET_EDGE' WHERE application_type = 'market_edge';
UPDATE user_application_access SET application_type = 'CAUSAL_EDGE' WHERE application_type = 'causal_edge';
UPDATE user_application_access SET application_type = 'VALUE_EDGE' WHERE application_type = 'value_edge';
"""

import requests
import json
import os
from datetime import datetime

def execute_direct_sql_fix():
    """Execute direct SQL commands via database endpoints"""
    
    print("🚨 EXECUTING DIRECT SQL ENUM CASE FIX")
    print("=" * 50)
    print("Target: user_application_access table enum case fix")
    print()
    
    backend_url = "https://marketedge-platform.onrender.com"
    
    # First, let's see if there's a direct SQL execution endpoint
    print("1. Testing if backend has direct SQL execution capability...")
    
    # Check available endpoints by trying health check first
    try:
        response = requests.get(f"{backend_url}/api/v1/database/health-detailed", timeout=30)
        print(f"   Database health: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Database connection: {result.get('database', 'Unknown')}")
    except Exception as e:
        print(f"   ❌ Error checking health: {e}")
    
    print()
    
    # Try to use the emergency admin setup endpoint but examine what tables it updates
    print("2. Attempting to use emergency admin endpoints for SQL fixes...")
    
    # The issue is that the emergency-admin-setup endpoint doesn't fix the enum case
    # Let's see if we can create a custom solution by understanding the backend structure
    
    # Let me try to create a Python script that uses the existing database connection
    # from the backend to execute our SQL directly
    
    sql_commands = [
        "UPDATE user_application_access SET application_type = 'MARKET_EDGE' WHERE application_type = 'market_edge';",
        "UPDATE user_application_access SET application_type = 'CAUSAL_EDGE' WHERE application_type = 'causal_edge';",
        "UPDATE user_application_access SET application_type = 'VALUE_EDGE' WHERE application_type = 'value_edge';"
    ]
    
    print("   📝 SQL commands to execute:")
    for cmd in sql_commands:
        print(f"   {cmd}")
    
    print()
    print("3. Checking if backend has custom SQL execution endpoint...")
    
    # Let's try to send a custom request that might trigger SQL execution
    # Based on the backend code, I need to look for endpoints that can execute custom SQL
    
    try:
        # Check if there's a transaction test endpoint we can modify
        response = requests.post(f"{backend_url}/api/v1/database/test-transaction", timeout=30)
        print(f"   Transaction test: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Database transaction capability confirmed")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("4. Alternative approach - Check if we can modify admin setup to include enum fix...")
    
    # Since we have access to the backend's emergency admin setup endpoint,
    # and it uses direct SQL, we need to see if we can extend it or
    # create a new endpoint specifically for this enum fix
    
    print("   💡 INSIGHT: Backend emergency-admin-setup endpoint uses direct SQL")
    print("   💡 INSIGHT: We need to modify it to include the enum case fix")
    print("   💡 SOLUTION: Create a new endpoint or modify existing one")
    
    return False

def check_backend_source_code():
    """Check if we can modify the backend source code directly"""
    
    print("🔧 CHECKING BACKEND SOURCE CODE MODIFICATION OPTIONS")
    print("=" * 55)
    
    # Check if the backend source is available in the codebase
    database_endpoint_file = "/Users/matt/Sites/MarketEdge/app/api/api_v1/endpoints/database.py"
    
    if os.path.exists(database_endpoint_file):
        print(f"✅ Found backend database endpoint file: {database_endpoint_file}")
        print("💡 SOLUTION: Add new endpoint to execute enum fix SQL")
        
        # Read the current file to see the structure
        with open(database_endpoint_file, 'r') as f:
            content = f.read()
        
        # Check if we can add a new endpoint
        if "emergency-admin-setup" in content:
            print("✅ Emergency admin setup endpoint found in source")
            print("🔧 RECOMMENDED: Add enum fix SQL to existing emergency-admin-setup")
            
            # Look for the exact location to add the enum fix
            if "UPDATE users SET role" in content:
                print("✅ Found SQL UPDATE statements in emergency-admin-setup")
                print("💡 PLAN: Modify emergency-admin-setup to include enum fix SQL")
                return True
    
    return False

if __name__ == "__main__":
    print("CRITICAL DATABASE ENUM CASE FIX ANALYSIS")
    print("=" * 45)
    
    # First try direct approach
    success = execute_direct_sql_fix()
    
    print()
    
    # Check source code modification approach
    source_available = check_backend_source_code()
    
    if source_available:
        print("\n🎯 RECOMMENDED SOLUTION:")
        print("1. Modify the emergency-admin-setup endpoint to include enum fix SQL")
        print("2. Add the three UPDATE statements to fix enum case")
        print("3. Deploy the updated endpoint")
        print("4. Test the fix")
        print("\n📝 SQL to add to emergency-admin-setup:")
        print("   UPDATE user_application_access SET application_type = 'MARKET_EDGE' WHERE application_type = 'market_edge';")
        print("   UPDATE user_application_access SET application_type = 'CAUSAL_EDGE' WHERE application_type = 'causal_edge';")
        print("   UPDATE user_application_access SET application_type = 'VALUE_EDGE' WHERE application_type = 'value_edge';")
    else:
        print("\n⚠️  Source code modification required")
        print("Manual database intervention needed via production database access")