#!/usr/bin/env python3
"""
Enhanced Auth0 Real Token Debugging Script
==========================================

This script provides detailed debugging capabilities to identify why real Auth0 tokens
cause 500 "Database error occurred" responses while test codes work correctly.

CRITICAL ANALYSIS:
- Test codes fail at Auth0 token exchange (400 response)  
- Real Auth0 tokens pass exchange but fail at database operations (500 response)
- The failure occurs AFTER successful Auth0 interaction during user creation/lookup

DEBUGGING STRATEGY:
1. Capture real Auth0 user info structure 
2. Test database operations with realistic data
3. Identify specific SQLAlchemy constraint violations
4. Fix data validation issues
"""

import asyncio
import httpx
import json
import os
from typing import Dict, Any, Optional


class Auth0DebugClient:
    """Debug client to analyze Auth0 responses and identify database issues"""
    
    def __init__(self):
        # Load configuration from environment
        self.domain = os.getenv('AUTH0_DOMAIN', 'dev-ph7m31mc6y5yxsw2.us.auth0.com')
        self.client_id = os.getenv('AUTH0_CLIENT_ID')
        self.client_secret = os.getenv('AUTH0_CLIENT_SECRET')
        self.base_url = f"https://{self.domain}"
        
        if not self.client_id or not self.client_secret:
            print("❌ ERROR: AUTH0_CLIENT_ID and AUTH0_CLIENT_SECRET must be set")
            exit(1)
    
    async def debug_auth0_userinfo_structure(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Fetch and analyze Auth0 user info structure"""
        print(f"\n🔍 DEBUGGING: Auth0 User Info Structure")
        print(f"   Domain: {self.domain}")
        print(f"   Endpoint: {self.base_url}/userinfo")
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/userinfo",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                print(f"   Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    user_info = response.json()
                    print(f"   ✅ SUCCESS: Retrieved user info")
                    print(f"\n📋 AUTH0 USER INFO STRUCTURE:")
                    print(f"   Available Fields: {list(user_info.keys())}")
                    print(f"   Email: {user_info.get('email', 'NOT SET')}")
                    print(f"   Sub (ID): {user_info.get('sub', 'NOT SET')}")
                    print(f"   Given Name: {user_info.get('given_name', 'NOT SET')}")
                    print(f"   Family Name: {user_info.get('family_name', 'NOT SET')}")
                    print(f"   Email Verified: {user_info.get('email_verified', 'NOT SET')}")
                    print(f"   Picture: {user_info.get('picture', 'NOT SET')}")
                    print(f"   Updated At: {user_info.get('updated_at', 'NOT SET')}")
                    
                    print(f"\n📊 FULL USER INFO JSON:")
                    print(json.dumps(user_info, indent=2))
                    
                    return user_info
                else:
                    print(f"   ❌ FAILED: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return None
                    
            except Exception as e:
                print(f"   ❌ EXCEPTION: {type(e).__name__}: {str(e)}")
                return None
    
    def analyze_user_data_for_database(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user data for potential database issues"""
        print(f"\n🔬 ANALYZING: User Data for Database Compatibility")
        
        analysis = {
            "email_issues": [],
            "name_issues": [],
            "constraint_issues": [],
            "recommendations": []
        }
        
        # Check email
        email = user_info.get('email')
        if not email:
            analysis["email_issues"].append("Missing email field")
        elif len(email) > 254:
            analysis["email_issues"].append(f"Email too long: {len(email)} chars (max 254)")
        elif '@' not in email:
            analysis["email_issues"].append("Invalid email format")
        
        # Check names
        given_name = user_info.get('given_name', '')
        family_name = user_info.get('family_name', '')
        
        if not given_name and not family_name:
            analysis["name_issues"].append("Both given_name and family_name are missing")
        
        if given_name and len(given_name) > 100:
            analysis["name_issues"].append(f"Given name too long: {len(given_name)} chars (max 100)")
            
        if family_name and len(family_name) > 100:
            analysis["name_issues"].append(f"Family name too long: {len(family_name)} chars (max 100)")
        
        # Check for special characters that might cause issues
        if email and any(char in email for char in ['"', "'", "<", ">", "&"]):
            analysis["constraint_issues"].append("Email contains special characters that might cause SQL issues")
        
        # Generate recommendations
        if analysis["email_issues"]:
            analysis["recommendations"].append("Fix email validation in user creation")
        
        if analysis["name_issues"]:
            analysis["recommendations"].append("Handle missing names with defaults")
            
        if not any([analysis["email_issues"], analysis["name_issues"], analysis["constraint_issues"]]):
            analysis["recommendations"].append("User data appears valid - investigate database constraints")
        
        return analysis
    
    def simulate_user_creation(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the user creation process to identify issues"""
        print(f"\n🧪 SIMULATING: User Creation Process")
        
        try:
            # Extract and sanitize data like the real endpoint does
            email = user_info.get('email', '').strip()
            given_name = user_info.get('given_name', '').strip()
            family_name = user_info.get('family_name', '').strip()
            
            print(f"   Email: '{email}'")
            print(f"   Given Name: '{given_name}'")
            print(f"   Family Name: '{family_name}'")
            
            # Check what would happen during User model creation
            user_data = {
                "email": email,
                "first_name": given_name,
                "last_name": family_name,
            }
            
            # Identify potential issues
            issues = []
            
            if not email:
                issues.append("CRITICAL: Empty email after sanitization")
            
            if not given_name and not family_name:
                issues.append("WARNING: Both names are empty")
                
            if len(email.encode('utf-8')) != len(email):
                issues.append("WARNING: Email contains non-ASCII characters")
            
            print(f"   Processed User Data: {user_data}")
            
            if issues:
                print(f"   🚨 ISSUES FOUND:")
                for issue in issues:
                    print(f"      - {issue}")
            else:
                print(f"   ✅ No obvious issues found")
                
            return {
                "user_data": user_data,
                "issues": issues,
                "valid": len(issues) == 0
            }
            
        except Exception as e:
            print(f"   ❌ SIMULATION FAILED: {type(e).__name__}: {str(e)}")
            return {
                "user_data": None,
                "issues": [f"Simulation exception: {str(e)}"],
                "valid": False
            }


async def main():
    """Main debugging function"""
    print("🚀 ENHANCED AUTH0 REAL TOKEN DEBUGGING")
    print("=" * 60)
    
    # Get access token from user
    print("\n📝 INSTRUCTIONS:")
    print("1. Go to Auth0 and get a fresh access token")
    print("2. Use 'clear session and get fresh code' method")  
    print("3. Paste the access token below")
    print("4. This will analyze the REAL user data structure")
    
    access_token = input("\n🔐 Enter Auth0 access token: ").strip()
    
    if not access_token:
        print("❌ No access token provided")
        return
    
    debug_client = Auth0DebugClient()
    
    # Step 1: Get real Auth0 user info
    user_info = await debug_client.debug_auth0_userinfo_structure(access_token)
    
    if not user_info:
        print("❌ Failed to get user info - cannot continue debugging")
        return
    
    # Step 2: Analyze for database compatibility
    analysis = debug_client.analyze_user_data_for_database(user_info)
    
    print(f"\n🔍 DATABASE COMPATIBILITY ANALYSIS:")
    print(f"   Email Issues: {len(analysis['email_issues'])}")
    for issue in analysis["email_issues"]:
        print(f"      ❌ {issue}")
    
    print(f"   Name Issues: {len(analysis['name_issues'])}")
    for issue in analysis["name_issues"]:
        print(f"      ⚠️ {issue}")
    
    print(f"   Constraint Issues: {len(analysis['constraint_issues'])}")
    for issue in analysis["constraint_issues"]:
        print(f"      🚨 {issue}")
        
    print(f"   Recommendations:")
    for rec in analysis["recommendations"]:
        print(f"      💡 {rec}")
    
    # Step 3: Simulate user creation
    simulation = debug_client.simulate_user_creation(user_info)
    
    print(f"\n📊 SUMMARY:")
    print(f"   User Info Retrieved: ✅")
    print(f"   Database Compatible: {'✅' if simulation['valid'] else '❌'}")
    
    if simulation['issues']:
        print(f"   Critical Issues Found: {len(simulation['issues'])}")
        print(f"\n🔧 NEXT STEPS:")
        print("   1. Review database schema constraints")
        print("   2. Check for unique email violations")
        print("   3. Verify SQLAlchemy model validations")
        print("   4. Test user creation with real data locally")
    else:
        print(f"\n🔧 NEXT STEPS:")
        print("   1. Data appears valid - investigate database connection")
        print("   2. Check for concurrent user creation issues")
        print("   3. Review database transaction isolation")
        print("   4. Examine SQLAlchemy session management")


if __name__ == "__main__":
    asyncio.run(main())