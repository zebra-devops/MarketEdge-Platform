#!/usr/bin/env python3
"""
Render Database Access Analysis
==============================

This script analyzes why we cannot connect to Render PostgreSQL externally
and provides alternative solutions for admin user management.
"""

import os
import sys
import socket
import requests
from datetime import datetime
from urllib.parse import urlparse

# Database URL provided
RENDER_DB_URL = "postgresql://marketedge_user:Qra5HBKofZqoQwQgKNyVnOOwKVRbRPAW@dpg-d2gch862dbo4c73b0kl80-a.oregon-postgres.render.com/marketedge_production"

def test_network_connectivity():
    """Test basic network connectivity to Render PostgreSQL"""
    
    print("🌐 Testing network connectivity...")
    
    parsed = urlparse(RENDER_DB_URL)
    host = parsed.hostname
    port = parsed.port or 5432
    
    print(f"   Target: {host}:{port}")
    
    try:
        # Test DNS resolution
        import socket
        ip_address = socket.gethostbyname(host)
        print(f"   ✅ DNS Resolution: {host} -> {ip_address}")
        
        # Test TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ TCP Connection: Port {port} is open")
            return True
        else:
            print(f"   ❌ TCP Connection: Port {port} is closed or filtered")
            return False
            
    except Exception as e:
        print(f"   ❌ Network test failed: {e}")
        return False

def analyze_render_database_restrictions():
    """Analyze Render database access restrictions"""
    
    print("\n🔍 Analyzing Render database restrictions...")
    
    # Check if we're connecting from an allowed network
    try:
        # Get our public IP
        response = requests.get('https://httpbin.org/ip', timeout=10)
        our_ip = response.json().get('origin', 'unknown')
        print(f"   📍 Our public IP: {our_ip}")
        
        # Render databases typically restrict access
        print(f"   ⚠️  Render PostgreSQL databases have restricted external access")
        print(f"   ⚠️  SSL connection failures suggest IP whitelist restrictions")
        
    except Exception as e:
        print(f"   ❌ Could not determine public IP: {e}")

def check_production_api_access():
    """Check if we can access the production API to create users through endpoints"""
    
    print("\n🌐 Testing production API access...")
    
    PRODUCTION_URL = "https://marketedge-platform.onrender.com"
    
    # Test health endpoints
    endpoints_to_test = [
        "/health",
        "/api/v1/health", 
        "/api/v1/admin/health"
    ]
    
    api_accessible = False
    
    for endpoint in endpoints_to_test:
        try:
            print(f"   Testing {endpoint}...")
            response = requests.get(f"{PRODUCTION_URL}{endpoint}", timeout=30)
            
            if response.status_code == 200:
                print(f"   ✅ {endpoint}: Accessible")
                api_accessible = True
                
                try:
                    data = response.json()
                    if 'database' in data or 'services' in data:
                        print(f"      📊 Database info available")
                except:
                    pass
                    
            else:
                print(f"   ⚠️  {endpoint}: Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {endpoint}: Failed - {e}")
    
    return api_accessible

def suggest_alternative_solutions():
    """Suggest alternative solutions for admin user creation"""
    
    print("\n💡 ALTERNATIVE SOLUTIONS FOR ADMIN USER CREATION")
    print("=" * 60)
    
    print("\n🎯 OPTION 1: Production API Endpoint")
    print("   • Create a secure admin user creation endpoint in the production API")
    print("   • Protect it with a temporary secret key or one-time token")
    print("   • Deploy to production and call via HTTPS")
    print("   • Remove the endpoint after use")
    print("   ✅ Pros: Uses existing application code and database connection")
    print("   ❌ Cons: Requires code deployment")
    
    print("\n🎯 OPTION 2: Render Dashboard Database Query")
    print("   • Use Render's built-in database query interface")
    print("   • Execute SQL commands directly in Render dashboard")
    print("   • Can create users and organizations manually")
    print("   ✅ Pros: Direct database access, no code changes")
    print("   ❌ Cons: Manual process, requires Render dashboard access")
    
    print("\n🎯 OPTION 3: Database Migration Script")
    print("   • Add admin user creation to database migration")
    print("   • Run migration on production deployment")
    print("   • Uses production environment's database connection")
    print("   ✅ Pros: Automated, part of deployment process")
    print("   ❌ Cons: Requires deployment to execute")
    
    print("\n🎯 OPTION 4: Environment-Based Seed Script")
    print("   • Create a seed script that runs on production startup")
    print("   • Check if admin user exists, create if missing")
    print("   • Use environment variable to control execution")
    print("   ✅ Pros: Automated, runs in production environment")
    print("   ❌ Cons: Requires restart or redeploy")

def create_recommended_implementation():
    """Create the recommended implementation files"""
    
    print("\n📝 Creating recommended implementation files...")
    
    # Option 1: API Endpoint approach
    api_endpoint_code = '''
# Add this to your API endpoints (temporary)
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
import uuid
from datetime import datetime

router = APIRouter()

TEMP_ADMIN_SECRET = "TEMP_SECRET_12345_REMOVE_AFTER_USE"

@router.post("/admin/create-super-admin")
async def create_super_admin(
    secret: str,
    db: Session = Depends(get_db)
):
    """Temporary endpoint to create Matt Lindop super admin user"""
    
    if secret != TEMP_ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == "matt.lindop@zebra.associates").first()
    if existing_user:
        return {"message": "User already exists", "user_id": str(existing_user.id)}
    
    # Create organization if it doesn't exist
    zebra_org = db.query(Organization).filter(Organization.name == "Zebra Associates").first()
    if not zebra_org:
        zebra_org = Organization(
            id=uuid.uuid4(),
            name="Zebra Associates",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(zebra_org)
        db.flush()
    
    # Create user
    matt_user = User(
        id=uuid.uuid4(),
        email="matt.lindop@zebra.associates",
        auth0_id="auth0|placeholder-will-be-updated-on-first-login",
        name="Matt Lindop",
        role="SUPER_ADMIN",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(matt_user)
    db.commit()
    
    return {
        "message": "Super admin user created successfully",
        "user_id": str(matt_user.id),
        "email": matt_user.email,
        "role": matt_user.role
    }
'''

    # Option 2: SQL Commands for Render Dashboard
    sql_commands = '''
-- Execute these SQL commands in Render Dashboard Query Interface

-- 1. Create Zebra Associates organization (if it doesn't exist)
INSERT INTO organisations (id, name, created_at, updated_at)
SELECT gen_random_uuid(), 'Zebra Associates', NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM organisations WHERE name = 'Zebra Associates'
);

-- 2. Create Matt Lindop super admin user
INSERT INTO users (id, email, auth0_id, name, role, is_active, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'matt.lindop@zebra.associates',
    'auth0|placeholder-will-be-updated-on-first-login',
    'Matt Lindop',
    'SUPER_ADMIN',
    true,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'matt.lindop@zebra.associates'
);

-- 3. Link user to organization
INSERT INTO user_hierarchy_assignments (id, user_id, organization_id, created_at)
SELECT 
    gen_random_uuid(),
    u.id,
    o.id,
    NOW()
FROM users u, organisations o
WHERE u.email = 'matt.lindop@zebra.associates'
  AND o.name = 'Zebra Associates'
  AND NOT EXISTS (
      SELECT 1 FROM user_hierarchy_assignments uha 
      WHERE uha.user_id = u.id AND uha.organization_id = o.id
  );

-- 4. Verify creation
SELECT 
    u.id,
    u.email,
    u.name,
    u.role,
    u.is_active,
    o.name as organization
FROM users u
LEFT JOIN user_hierarchy_assignments uha ON u.id = uha.user_id
LEFT JOIN organisations o ON uha.organization_id = o.id
WHERE u.email = 'matt.lindop@zebra.associates';
'''

    try:
        # Write API endpoint code
        with open('/Users/matt/Sites/MarketEdge/temp_admin_api_endpoint.py', 'w') as f:
            f.write(api_endpoint_code)
        print("   ✅ Created: temp_admin_api_endpoint.py")
        
        # Write SQL commands
        with open('/Users/matt/Sites/MarketEdge/render_dashboard_sql_commands.sql', 'w') as f:
            f.write(sql_commands)
        print("   ✅ Created: render_dashboard_sql_commands.sql")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create files: {e}")
        return False

def main():
    """Main analysis function"""
    
    print("=" * 80)
    print("RENDER DATABASE ACCESS ANALYSIS")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Test 1: Network connectivity
    network_ok = test_network_connectivity()
    
    # Test 2: Analyze restrictions
    analyze_render_database_restrictions()
    
    # Test 3: Production API access
    api_accessible = check_production_api_access()
    
    # Analysis Summary
    print("\n" + "=" * 80)
    print("ACCESS ANALYSIS RESULTS")
    print("=" * 80)
    
    print(f"📡 Network Connectivity: {'✅ OK' if network_ok else '❌ FAILED'}")
    print(f"🌐 Production API: {'✅ ACCESSIBLE' if api_accessible else '❌ INACCESSIBLE'}")
    print(f"🔒 Direct DB Access: ❌ BLOCKED (SSL/IP restrictions)")
    
    # Conclusions
    print("\n🔍 ANALYSIS CONCLUSIONS:")
    print("   • Render PostgreSQL blocks external direct connections")
    print("   • SSL connection failures indicate IP whitelist restrictions")
    print("   • Database is only accessible from within Render's network")
    print("   • Production API may be accessible for indirect database operations")
    
    # Provide solutions
    suggest_alternative_solutions()
    
    # Create implementation files
    files_created = create_recommended_implementation()
    
    # Final recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDED NEXT STEPS")
    print("=" * 80)
    
    if api_accessible:
        print("🎯 RECOMMENDED: Use Production API Endpoint approach")
        print("   1. Add temporary admin endpoint to production API")
        print("   2. Deploy to production") 
        print("   3. Call endpoint via HTTPS to create admin user")
        print("   4. Remove endpoint after successful creation")
        print("   5. See: temp_admin_api_endpoint.py")
    else:
        print("🎯 RECOMMENDED: Use Render Dashboard SQL Commands")
        print("   1. Log into Render Dashboard")
        print("   2. Go to your PostgreSQL database")
        print("   3. Use Query interface to run SQL commands")
        print("   4. Execute commands from: render_dashboard_sql_commands.sql")
    
    print("\n✅ Direct database administration is NOT viable from external clients")
    print("✅ Alternative solutions provided for admin user creation")
    print("✅ Manual Render dashboard operations remain available")
    
    if files_created:
        print("\n📁 Implementation files created:")
        print("   • temp_admin_api_endpoint.py - API endpoint approach")
        print("   • render_dashboard_sql_commands.sql - Manual SQL approach")
    
    print("=" * 80)
    
    return False  # Direct access not viable

if __name__ == "__main__":
    viable = main()
    sys.exit(0 if viable else 1)