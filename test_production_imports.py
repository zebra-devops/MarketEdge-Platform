#!/usr/bin/env python3
"""
Production Import Test - Verify all critical imports work before deployment
This test simulates the Docker production environment import conditions
"""

import sys
import os
import traceback
from pathlib import Path

def test_critical_imports():
    """Test all critical imports that could fail in production"""
    
    print("=== PRODUCTION IMPORT VERIFICATION ===")
    
    critical_imports = [
        ("Secret Manager", "from app.core.secret_manager import validate_secrets_startup, get_secrets_health"),
        ("Main App", "from app.main import app"),
        ("Core Config", "from app.core.config import settings"),
        ("Database", "from app.core.database import engine, get_db"),
        ("Health Checks", "from app.core.health_checks import health_checker"),
        ("API Router", "from app.api.api_v1.api import api_router"),
        ("Middleware", "from app.middleware.error_handler import ErrorHandlerMiddleware"),
        ("Auth", "from app.auth.dependencies import get_current_user"),
        ("Services", "from app.services.admin_service import AdminService"),
        ("Models", "from app.models.user import User, UserRole"),
    ]
    
    success_count = 0
    failure_count = 0
    
    for import_name, import_statement in critical_imports:
        try:
            print(f"Testing {import_name}...", end=" ")
            exec(import_statement)
            print("✅ SUCCESS")
            success_count += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failure_count += 1
            if "ModuleNotFoundError" in str(type(e)):
                print(f"   This is the exact error that was blocking deployment!")
    
    print(f"\n=== RESULTS ===")
    print(f"Total tests: {len(critical_imports)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    
    if failure_count == 0:
        print("🎯 ALL IMPORTS SUCCESSFUL - Ready for deployment!")
        return True
    else:
        print("❌ IMPORT FAILURES DETECTED - Do not deploy yet!")
        return False

def test_gunicorn_compatibility():
    """Test that the app can be imported by Gunicorn"""
    print("\n=== GUNICORN COMPATIBILITY TEST ===")
    
    try:
        # This is exactly how Gunicorn imports the app
        print("Testing Gunicorn-style import: 'app.main:app'")
        import importlib
        
        # Import the module
        module = importlib.import_module("app.main")
        
        # Get the app attribute
        app_instance = getattr(module, "app")
        
        print(f"✅ SUCCESS - App type: {type(app_instance)}")
        print(f"✅ SUCCESS - App title: {getattr(app_instance, 'title', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all production readiness tests"""
    print("MARKEDGE PLATFORM - PRODUCTION IMPORT READINESS TEST")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    
    # Test critical imports
    imports_ok = test_critical_imports()
    
    # Test Gunicorn compatibility
    gunicorn_ok = test_gunicorn_compatibility()
    
    print("\n" + "=" * 60)
    if imports_ok and gunicorn_ok:
        print("🚀 PRODUCTION READY - All tests passed!")
        print("✅ Deploy to production with confidence")
        return 0
    else:
        print("❌ NOT PRODUCTION READY - Fix issues before deployment")
        return 1

if __name__ == "__main__":
    exit(main())