#!/usr/bin/env python3
"""
Emergency debug script to check matt.lindop@zebra.associates admin status
and verify why admin endpoints return 403
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL - use production
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://marketedge_user:ZrGqvLGKAhT0RXqajH2YFR7nYClPmVbW@dpg-crs50552ng1s73b9kp00-a.oregon-postgres.render.com/marketedge'
)

def create_db_engine():
    """Create database engine"""
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        logger.info(f"✅ Database engine created successfully")
        return engine
    except Exception as e:
        logger.error(f"❌ Failed to create database engine: {e}")
        return None

def check_zebra_user_admin_status():
    """Check matt.lindop@zebra.associates admin status and auth details"""
    engine = create_db_engine()
    if not engine:
        return None
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'user_check': {},
        'admin_users': [],
        'organization_check': {},
        'database_status': 'unknown'
    }
    
    try:
        with engine.connect() as conn:
            results['database_status'] = 'connected'
            
            # 1. Check if matt.lindop@zebra.associates exists and has admin role
            logger.info("🔍 Checking matt.lindop@zebra.associates user status...")
            
            user_query = text("""
            SELECT 
                u.id,
                u.email,
                u.first_name,
                u.last_name,
                u.role,
                u.is_active,
                u.organisation_id,
                o.name as organisation_name,
                o.domain as organisation_domain,
                u.created_at,
                u.updated_at
            FROM users u
            LEFT JOIN organisations o ON u.organisation_id = o.id  
            WHERE u.email = 'matt.lindop@zebra.associates'
            """)
            
            user_result = conn.execute(user_query).fetchone()
            
            if user_result:
                user_data = dict(user_result._mapping)
                results['user_check'] = {
                    'exists': True,
                    'id': str(user_data['id']),
                    'email': user_data['email'],
                    'name': f"{user_data['first_name']} {user_data['last_name']}",
                    'role': user_data['role'],
                    'is_active': user_data['is_active'],
                    'organisation_id': str(user_data['organisation_id']),
                    'organisation_name': user_data['organisation_name'],
                    'organisation_domain': user_data['organisation_domain'],
                    'created_at': user_data['created_at'].isoformat() if user_data['created_at'] else None,
                    'is_admin': user_data['role'] == 'admin',
                    'should_have_admin_access': user_data['role'] == 'admin' and user_data['is_active']
                }
                
                if user_data['role'] == 'admin':
                    logger.info("✅ User has admin role")
                else:
                    logger.warning(f"⚠️  User role is '{user_data['role']}' but should be 'admin'")
                
                if not user_data['is_active']:
                    logger.warning("⚠️  User account is INACTIVE")
                else:
                    logger.info("✅ User account is active")
                    
            else:
                results['user_check'] = {
                    'exists': False,
                    'error': 'User matt.lindop@zebra.associates not found in database'
                }
                logger.error("❌ User matt.lindop@zebra.associates not found in database!")
            
            # 2. List all admin users for comparison
            logger.info("🔍 Checking all admin users...")
            
            admin_query = text("""
            SELECT 
                u.id,
                u.email,
                u.first_name,
                u.last_name,
                u.role,
                u.is_active,
                o.name as organisation_name
            FROM users u
            LEFT JOIN organisations o ON u.organisation_id = o.id
            WHERE u.role = 'admin'
            ORDER BY u.created_at DESC
            """)
            
            admin_results = conn.execute(admin_query).fetchall()
            results['admin_users'] = []
            
            for admin_user in admin_results:
                admin_data = dict(admin_user._mapping)
                results['admin_users'].append({
                    'id': str(admin_data['id']),
                    'email': admin_data['email'],
                    'name': f"{admin_data['first_name']} {admin_data['last_name']}",
                    'is_active': admin_data['is_active'],
                    'organisation': admin_data['organisation_name']
                })
            
            logger.info(f"Found {len(admin_results)} admin users in database")
            
            # 3. Check Zebra Associates organization
            logger.info("🔍 Checking Zebra Associates organization...")
            
            org_query = text("""
            SELECT 
                id,
                name,
                domain,
                is_active,
                subscription_plan,
                created_at
            FROM organisations 
            WHERE domain = 'zebra.associates' OR name ILIKE '%zebra%'
            """)
            
            org_results = conn.execute(org_query).fetchall()
            
            if org_results:
                org_data = dict(org_results[0]._mapping)
                results['organization_check'] = {
                    'exists': True,
                    'id': str(org_data['id']),
                    'name': org_data['name'],
                    'domain': org_data['domain'],
                    'is_active': org_data['is_active'],
                    'subscription_plan': org_data['subscription_plan'],
                    'created_at': org_data['created_at'].isoformat() if org_data['created_at'] else None
                }
                logger.info(f"✅ Found organization: {org_data['name']}")
            else:
                results['organization_check'] = {
                    'exists': False,
                    'error': 'No Zebra Associates organization found'
                }
                logger.warning("⚠️  No Zebra Associates organization found")
            
            # 4. Check if we can determine the auth issue
            if results['user_check'].get('exists'):
                user_info = results['user_check']
                if user_info['role'] != 'admin':
                    results['auth_issue'] = 'USER_ROLE_NOT_ADMIN'
                    results['fix_needed'] = f"UPDATE users SET role = 'admin' WHERE email = 'matt.lindop@zebra.associates'"
                elif not user_info['is_active']:
                    results['auth_issue'] = 'USER_ACCOUNT_INACTIVE'
                    results['fix_needed'] = f"UPDATE users SET is_active = true WHERE email = 'matt.lindop@zebra.associates'"
                else:
                    results['auth_issue'] = 'UNKNOWN_TOKEN_OR_AUTH_ISSUE'
                    results['fix_needed'] = 'User appears correct - check JWT token or Auth0 configuration'
            else:
                results['auth_issue'] = 'USER_NOT_FOUND'
                results['fix_needed'] = 'Create user account for matt.lindop@zebra.associates'
                
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        results['error'] = str(e)
        results['database_status'] = 'error'
    
    return results

if __name__ == "__main__":
    print("🚀 Emergency debug: Checking matt.lindop@zebra.associates admin status...")
    
    results = check_zebra_user_admin_status()
    
    if results:
        # Save results to file
        results_file = f"zebra_admin_debug_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"================")
        
        if results['user_check'].get('exists'):
            user = results['user_check']
            print(f"✅ User Found: {user['email']}")
            print(f"   Role: {user['role']} {'✅' if user['role'] == 'admin' else '❌'}")
            print(f"   Active: {user['is_active']} {'✅' if user['is_active'] else '❌'}")
            print(f"   Organization: {user['organisation_name']}")
        else:
            print(f"❌ User NOT found: matt.lindop@zebra.associates")
        
        print(f"\n👥 Admin Users in Database: {len(results['admin_users'])}")
        for admin in results['admin_users']:
            print(f"   - {admin['email']} ({'active' if admin['is_active'] else 'inactive'})")
        
        if results['organization_check'].get('exists'):
            org = results['organization_check']
            print(f"\n🏢 Zebra Organization: {org['name']} ({'active' if org['is_active'] else 'inactive'})")
        
        if 'auth_issue' in results:
            print(f"\n🔧 ISSUE IDENTIFIED: {results['auth_issue']}")
            print(f"🛠️  FIX NEEDED: {results['fix_needed']}")
        
        print(f"\n📄 Full results saved to: {results_file}")
        
        # Return exit code based on issue severity
        if results['user_check'].get('exists') and results['user_check'].get('should_have_admin_access'):
            sys.exit(0)  # Success - user should have admin access
        else:
            sys.exit(1)  # Issue found
    else:
        print("❌ Failed to check user status")
        sys.exit(1)