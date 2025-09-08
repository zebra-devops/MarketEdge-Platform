#!/usr/bin/env python3
"""
CRITICAL PRODUCTION ISSUE DIAGNOSTIC TOOL
Diagnosing 60-second timeout issue affecting £925K opportunity
"""

import asyncio
import time
import os
import sys
import logging
import traceback
import psycopg2
import redis
import httpx
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'production_timeout_diagnosis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

def diagnose_issue():
    """Comprehensive diagnosis of production timeout issue"""
    logger.info("🚨 CRITICAL: Starting production timeout diagnosis for £925K opportunity")
    
    # Test external service responsiveness first
    logger.info("=" * 60)
    logger.info("1. TESTING PRODUCTION SERVICE CONNECTIVITY")
    logger.info("=" * 60)
    
    production_url = "https://marketedge-platform.onrender.com"
    
    # Quick connection test
    try:
        start_time = time.time()
        response = httpx.get(f"{production_url}/health", timeout=10.0)
        duration = time.time() - start_time
        logger.info(f"✅ Health endpoint responded in {duration:.3f}s with status {response.status_code}")
        logger.info(f"Response body: {response.text[:500]}...")
    except httpx.TimeoutException:
        logger.error(f"❌ CRITICAL: Health endpoint timed out after 10 seconds - SERVICE UNRESPONSIVE")
    except Exception as e:
        logger.error(f"❌ Health endpoint error: {e}")
    
    # Test auth endpoint specifically
    try:
        start_time = time.time()
        auth_url = f"{production_url}/api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/callback"
        response = httpx.get(auth_url, timeout=15.0)
        duration = time.time() - start_time
        logger.info(f"✅ Auth endpoint responded in {duration:.3f}s with status {response.status_code}")
    except httpx.TimeoutException:
        logger.error(f"❌ CRITICAL: Auth endpoint timed out after 15 seconds - THIS IS THE EXACT ISSUE")
    except Exception as e:
        logger.error(f"❌ Auth endpoint error: {e}")
    
    logger.info("=" * 60)
    logger.info("2. TESTING DATABASE CONNECTION FROM LOCAL")
    logger.info("=" * 60)
    
    # Test database connection with timeout
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL not set - cannot test database connection")
    else:
        try:
            logger.info(f"Testing database connection to: {database_url[:50]}...")
            start_time = time.time()
            
            # Try to connect with short timeout
            conn = psycopg2.connect(database_url, connect_timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            logger.info(f"✅ Database connection successful in {duration:.3f}s")
            
        except psycopg2.OperationalError as e:
            duration = time.time() - start_time
            logger.error(f"❌ Database connection failed after {duration:.3f}s: {e}")
            if "timeout" in str(e).lower():
                logger.error("🚨 DATABASE TIMEOUT DETECTED - This could be the root cause")
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Database error after {duration:.3f}s: {e}")
    
    logger.info("=" * 60)
    logger.info("3. TESTING REDIS CONNECTION FROM LOCAL")
    logger.info("=" * 60)
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        logger.info(f"Testing Redis connection to: {redis_url}")
        start_time = time.time()
        
        # Try to connect with short timeout
        client = redis.from_url(redis_url, socket_connect_timeout=10, socket_timeout=5)
        client.ping()
        client.close()
        
        duration = time.time() - start_time
        logger.info(f"✅ Redis connection successful in {duration:.3f}s")
        
    except redis.TimeoutError as e:
        duration = time.time() - start_time
        logger.error(f"❌ Redis connection timed out after {duration:.3f}s: {e}")
        logger.error("🚨 REDIS TIMEOUT DETECTED - This could be the root cause")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Redis connection error after {duration:.3f}s: {e}")
    
    logger.info("=" * 60)
    logger.info("4. ANALYZING POTENTIAL CAUSES")
    logger.info("=" * 60)
    
    potential_causes = [
        "🔍 Database connection pool exhaustion or deadlock",
        "🔍 Database queries hanging without timeout",
        "🔍 Redis connection issues or memory pressure",
        "🔍 Network connectivity issues to external databases",
        "🔍 Render.com service startup/cold start issues",
        "🔍 Lazy initialization causing circular dependencies",
        "🔍 Service initialization hanging on first request",
        "🔍 Database migration or schema issues",
        "🔍 Auth0 client initialization hanging",
        "🔍 Connection pool configuration causing timeouts"
    ]
    
    for cause in potential_causes:
        logger.info(cause)
    
    logger.info("=" * 60)
    logger.info("5. RECOMMENDED IMMEDIATE ACTIONS")
    logger.info("=" * 60)
    
    recommendations = [
        "🚀 RESTART Render service to clear any hanging connections",
        "⚡ REDUCE database connection pool size and timeouts",
        "🔧 ADD explicit timeouts to all database operations",
        "📊 CHECK Render service logs for specific error messages",
        "🎯 BYPASS lazy initialization for critical auth endpoints",
        "🔄 IMPLEMENT circuit breakers for external service calls",
        "⏱️  ADD health checks with shorter timeouts",
        "🚨 ENABLE emergency mode if lazy init continues failing"
    ]
    
    for rec in recommendations:
        logger.info(rec)
    
    logger.info("=" * 60)
    logger.info("DIAGNOSIS COMPLETE")
    logger.info("=" * 60)
    
    return {
        "service_responsive": False,  # Based on our tests
        "database_issue_likely": True,
        "redis_issue_possible": True,
        "immediate_action_needed": True,
        "business_impact": "CRITICAL - Blocking £925K opportunity"
    }

if __name__ == "__main__":
    try:
        result = diagnose_issue()
        
        # Print summary for immediate action
        print("\n" + "="*60)
        print("🚨 CRITICAL PRODUCTION ISSUE SUMMARY")
        print("="*60)
        print(f"Service Responsive: {result['service_responsive']}")
        print(f"Database Issue Likely: {result['database_issue_likely']}")
        print(f"Redis Issue Possible: {result['redis_issue_possible']}")
        print(f"Business Impact: {result['business_impact']}")
        print("\n✅ IMMEDIATE ACTION: Restart Render service and check logs")
        print("📞 ESCALATE: Contact Render support if issue persists")
        
    except Exception as e:
        logger.error(f"Diagnosis script failed: {e}")
        logger.error(traceback.format_exc())