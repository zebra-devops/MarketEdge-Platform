#!/usr/bin/env python3
"""
Simple Render PostgreSQL SSL Connection Test
==========================================

This script tests different SSL connection methods to Render PostgreSQL
to determine the correct configuration needed.
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse
from sqlalchemy import create_engine

# Database URL provided
RENDER_DB_URL = "postgresql://marketedge_user:Qra5HBKofZqoQwQgKNyVnOOwKVRbRPAW@dpg-d2gch862dbo4c73b0kl80-a.oregon-postgres.render.com/marketedge_production"

def test_psycopg2_direct():
    """Test direct psycopg2 connection with different SSL modes"""
    
    print("🔌 Testing direct psycopg2 connection...")
    
    # Parse URL
    parsed = urlparse(RENDER_DB_URL)
    
    # Connection parameters
    conn_params = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/'),
        'user': parsed.username,
        'password': parsed.password,
        'connect_timeout': 30
    }
    
    # Try different SSL modes
    ssl_modes = ['require', 'prefer', 'allow', 'disable']
    
    for ssl_mode in ssl_modes:
        print(f"\n   Testing SSL mode: {ssl_mode}")
        
        try:
            conn_params['sslmode'] = ssl_mode
            
            connection = psycopg2.connect(**conn_params)
            cursor = connection.cursor()
            
            # Test basic query
            cursor.execute("SELECT version(), current_database(), current_user")
            result = cursor.fetchone()
            
            print(f"   ✅ Success with sslmode={ssl_mode}")
            print(f"      Version: {result[0].split(',')[0]}")
            print(f"      Database: {result[1]}")
            print(f"      User: {result[2]}")
            
            cursor.close()
            connection.close()
            return ssl_mode
            
        except Exception as e:
            print(f"   ❌ Failed with sslmode={ssl_mode}: {e}")
    
    return None

def test_sqlalchemy_with_ssl(ssl_mode):
    """Test SQLAlchemy connection with successful SSL mode"""
    
    if not ssl_mode:
        print("\n❌ No working SSL mode found, skipping SQLAlchemy test")
        return False
    
    print(f"\n🔧 Testing SQLAlchemy with sslmode={ssl_mode}...")
    
    try:
        engine = create_engine(
            RENDER_DB_URL,
            connect_args={
                "sslmode": ssl_mode,
                "connect_timeout": 30,
                "application_name": "MarketEdge_Test"
            }
        )
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version(), current_database()"))
            version_info, db_name = result.fetchone()
            
            print(f"   ✅ SQLAlchemy connection successful!")
            print(f"      Version: {version_info.split(',')[0]}")
            print(f"      Database: {db_name}")
            
            # Test basic table access
            result = connection.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' LIMIT 5
            """))
            
            tables = result.fetchall()
            print(f"      Tables available: {len(tables)}")
            for table in tables:
                print(f"        - {table[0]}")
                
            return True
            
    except Exception as e:
        print(f"   ❌ SQLAlchemy failed: {e}")
        return False

def test_render_specific_configs():
    """Test Render-specific configurations"""
    
    print("\n🎯 Testing Render-specific configurations...")
    
    # Try with the exact URL as-is (Render might handle SSL automatically)
    try:
        print("   Testing URL as-is...")
        connection = psycopg2.connect(RENDER_DB_URL)
        cursor = connection.cursor()
        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()[0]
        
        print(f"   ✅ Direct URL connection successful!")
        print(f"      Database: {db_name}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Direct URL failed: {e}")
    
    # Try with SSL parameters in URL
    ssl_urls = [
        RENDER_DB_URL + "?sslmode=require",
        RENDER_DB_URL + "?sslmode=prefer", 
        RENDER_DB_URL + "?sslmode=allow"
    ]
    
    for url in ssl_urls:
        try:
            sslmode = url.split('=')[-1]
            print(f"   Testing URL with ?sslmode={sslmode}...")
            
            connection = psycopg2.connect(url)
            cursor = connection.cursor()
            cursor.execute("SELECT current_database()")
            db_name = cursor.fetchone()[0]
            
            print(f"   ✅ URL with SSL parameter successful!")
            print(f"      Database: {db_name}")
            
            cursor.close()
            connection.close()
            return True
            
        except Exception as e:
            print(f"   ❌ URL with ?sslmode={sslmode} failed: {e}")
    
    return False

def main():
    """Main test execution"""
    
    print("=" * 70)
    print("RENDER POSTGRESQL SSL CONNECTION DIAGNOSIS")
    print("=" * 70)
    
    # Import SQLAlchemy text here to avoid import issues
    try:
        from sqlalchemy import text
        globals()['text'] = text
    except ImportError:
        print("⚠️  SQLAlchemy not available, testing with psycopg2 only")
    
    # Test 1: Direct psycopg2 with different SSL modes
    working_ssl_mode = test_psycopg2_direct()
    
    # Test 2: Render-specific configurations  
    render_config_works = test_render_specific_configs()
    
    # Test 3: SQLAlchemy if we found a working SSL mode
    if 'text' in globals():
        sqlalchemy_works = test_sqlalchemy_with_ssl(working_ssl_mode)
    else:
        sqlalchemy_works = False
    
    # Results summary
    print("\n" + "=" * 70)
    print("CONNECTION TEST RESULTS")
    print("=" * 70)
    
    if working_ssl_mode:
        print(f"✅ Working SSL Mode: {working_ssl_mode}")
    else:
        print("❌ No working SSL mode found")
    
    if render_config_works:
        print("✅ Render-specific config works")
    else:
        print("❌ Render-specific configs failed")
        
    if sqlalchemy_works:
        print("✅ SQLAlchemy connection works")
    else:
        print("❌ SQLAlchemy connection failed")
    
    # Recommendations
    print("\n📋 RECOMMENDATIONS:")
    
    if working_ssl_mode or render_config_works:
        print("   • Database connection is possible with proper SSL configuration")
        
        if working_ssl_mode:
            print(f"   • Use sslmode='{working_ssl_mode}' for connections")
            
        if render_config_works:
            print("   • Direct URL connection works (Render handles SSL automatically)")
            
        print("   • Proceed with admin user creation script")
        print("   • Direct database administration is viable")
        
    else:
        print("   • Check network connectivity to Render")
        print("   • Verify database credentials are correct")
        print("   • Check if database is accessible from current IP")
        print("   • Consider using Render dashboard for manual operations")
    
    print("=" * 70)
    
    return working_ssl_mode is not None or render_config_works

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)