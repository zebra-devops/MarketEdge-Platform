#!/usr/bin/env python3
"""
Diagnostic script to identify Gunicorn worker boot failures.
This script tests each component that might cause exit code 3.
"""

import sys
import os
import traceback
import time
from pathlib import Path

print("=" * 60)
print("GUNICORN WORKER BOOT FAILURE DIAGNOSTIC")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"PYTHONPATH: {sys.path}")
print()

# Test 1: Environment Variables
print("1. TESTING ENVIRONMENT VARIABLES...")
critical_env_vars = [
    "DATABASE_URL", "REDIS_URL", "JWT_SECRET_KEY", 
    "AUTH0_DOMAIN", "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET",
    "ENVIRONMENT", "PORT"
]

missing_vars = []
for var in critical_env_vars:
    value = os.getenv(var)
    if not value:
        missing_vars.append(var)
        print(f"   ❌ {var}: NOT SET")
    else:
        # Mask sensitive values
        if "SECRET" in var or "PASSWORD" in var:
            masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
        elif "URL" in var:
            masked_value = value.split("@")[0] + "@***" if "@" in value else value[:20] + "..."
        else:
            masked_value = value[:20] + "..." if len(value) > 20 else value
        print(f"   ✅ {var}: {masked_value}")

if missing_vars:
    print(f"   WARNING: Missing environment variables: {missing_vars}")
print()

# Test 2: Application Import
print("2. TESTING APPLICATION IMPORT...")
try:
    print("   Testing: import app")
    import app
    print("   ✅ Successfully imported app")
    
    print("   Testing: import app.main")
    import app.main
    print("   ✅ Successfully imported app.main")
    
    print("   Testing: app.main.app object")
    fastapi_app = app.main.app
    print(f"   ✅ Successfully got FastAPI app: {type(fastapi_app)}")
    
except Exception as e:
    print(f"   ❌ Application import failed: {e}")
    traceback.print_exc()
    print()

# Test 3: Database Connection
print("3. TESTING DATABASE CONNECTION...")
try:
    from app.core.database import engine, get_database_url
    db_url = get_database_url()
    print(f"   Using database URL: {db_url.split('@')[0]}@***" if '@' in db_url else db_url[:30] + "...")
    
    # Test database connection
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        row = result.fetchone()
        if row and row[0] == 1:
            print("   ✅ Database connection successful")
        else:
            print("   ❌ Database connection failed - unexpected result")
except Exception as e:
    print(f"   ❌ Database connection failed: {e}")
    traceback.print_exc()
print()

# Test 4: Redis Connection
print("4. TESTING REDIS CONNECTION...")
try:
    from app.core.database import redis_client
    redis_client.ping()
    print("   ✅ Redis connection successful")
except Exception as e:
    print(f"   ❌ Redis connection failed: {e}")
    traceback.print_exc()
print()

# Test 5: Secret Manager
print("5. TESTING SECRET MANAGER...")
try:
    from app.core.secret_manager import validate_secrets_startup
    validate_secrets_startup()
    print("   ✅ Secret validation successful")
except Exception as e:
    print(f"   ❌ Secret validation failed: {e}")
    traceback.print_exc()
print()

# Test 6: FastAPI Application Startup
print("6. TESTING FASTAPI APPLICATION STARTUP...")
try:
    from app.main import app as fastapi_app
    
    # Test if app is callable
    if callable(fastapi_app):
        print("   ✅ FastAPI app is callable")
    else:
        print("   ❌ FastAPI app is not callable")
    
    # Test if app has required attributes
    if hasattr(fastapi_app, 'router'):
        print("   ✅ FastAPI app has router")
    else:
        print("   ❌ FastAPI app missing router")
        
    # Test middleware stack
    if hasattr(fastapi_app, 'middleware_stack'):
        print(f"   ✅ FastAPI app has middleware stack: {len(fastapi_app.middleware_stack)} middlewares")
    else:
        print("   ❌ FastAPI app missing middleware stack")
        
except Exception as e:
    print(f"   ❌ FastAPI application startup test failed: {e}")
    traceback.print_exc()
print()

# Test 7: Gunicorn Worker Configuration Test
print("7. TESTING GUNICORN WORKER COMPATIBILITY...")
try:
    import uvicorn.workers
    print("   ✅ uvicorn.workers module available")
    
    from uvicorn.workers import UvicornWorker
    print("   ✅ UvicornWorker class available")
    
    # Test if we can create a mock worker
    class TestWorker(UvicornWorker):
        pass
    print("   ✅ Can subclass UvicornWorker")
    
except Exception as e:
    print(f"   ❌ Gunicorn worker compatibility test failed: {e}")
    traceback.print_exc()
print()

# Test 8: Module System Initialization
print("8. TESTING MODULE SYSTEM INITIALIZATION...")
try:
    from app.core.module_startup import get_module_system_info
    info = get_module_system_info()
    print(f"   ✅ Module system info available: {info.get('status', 'unknown')}")
except Exception as e:
    print(f"   ❌ Module system test failed: {e}")
    traceback.print_exc()
print()

# Test 9: Memory and Resource Usage
print("9. CHECKING MEMORY AND RESOURCE USAGE...")
try:
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"   Memory usage: {memory_info.rss / 1024 / 1024:.1f} MB RSS, {memory_info.vms / 1024 / 1024:.1f} MB VMS")
    print(f"   CPU percent: {process.cpu_percent()}%")
    print(f"   File descriptors: {process.num_fds()}")
    print("   ✅ Resource usage check completed")
except ImportError:
    print("   ⚠️  psutil not available - skipping resource check")
except Exception as e:
    print(f"   ❌ Resource check failed: {e}")
print()

# Test 10: Simple HTTP Test
print("10. TESTING SIMPLE HTTP SERVER STARTUP...")
try:
    import uvicorn
    from app.main import app as fastapi_app
    
    # Create a simple test to see if uvicorn can bind to the app
    config = uvicorn.Config(
        app=fastapi_app,
        host="127.0.0.1", 
        port=8001,  # Use different port for test
        log_level="error"  # Suppress logs for test
    )
    server = uvicorn.Server(config)
    print("   ✅ Uvicorn server configuration successful")
    
    # Don't actually start the server, just test creation
    
except Exception as e:
    print(f"   ❌ HTTP server test failed: {e}")
    traceback.print_exc()
print()

print("=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)

# Final assessment
print("\nFINAL ASSESSMENT:")
if missing_vars:
    print(f"⚠️  Missing environment variables may cause worker boot failure: {missing_vars}")

# Check for common Gunicorn exit code 3 causes
potential_issues = []

if missing_vars:
    potential_issues.append("Missing environment variables")

print("\nRECOMMENDATIONS:")
if not potential_issues:
    print("✅ No obvious issues found - worker boot failure may be deployment-specific")
    print("Consider:")
    print("   - Check Render deployment environment variables")
    print("   - Verify database and Redis connectivity from Render")
    print("   - Check Render resource limits (memory, CPU)")
    print("   - Try single Uvicorn worker as fallback")
else:
    for issue in potential_issues:
        print(f"❌ Address: {issue}")

print("\nDEBUG COMMANDS FOR RENDER:")
print("1. Test direct import: python3 -c 'import app.main; print(\"SUCCESS\")'")
print("2. Test single Uvicorn: python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT")
print("3. Test minimal Gunicorn: gunicorn app.main:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120")