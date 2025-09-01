#!/usr/bin/env python3
"""
Diagnostic script to identify the root cause of the secret_manager import issue
This script simulates the exact conditions during Gunicorn worker startup
"""

import os
import sys
import traceback
from pathlib import Path

def diagnose_import_paths():
    """Diagnose Python import path configuration"""
    print("=== PYTHON PATH DIAGNOSIS ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {__file__}")
    
    print("\n=== PYTHON IMPORT PATHS ===")
    for i, path in enumerate(sys.path):
        print(f"{i}: {path}")

def diagnose_file_structure():
    """Diagnose file structure around the secret_manager module"""
    print("\n=== FILE STRUCTURE DIAGNOSIS ===")
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Check for app directory
    app_dir = current_dir / "app"
    print(f"App directory exists: {app_dir.exists()} ({app_dir})")
    
    if app_dir.exists():
        # Check for core directory
        core_dir = app_dir / "core"
        print(f"Core directory exists: {core_dir.exists()} ({core_dir})")
        
        if core_dir.exists():
            # Check for secret_manager.py
            secret_manager_file = core_dir / "secret_manager.py"
            print(f"secret_manager.py exists: {secret_manager_file.exists()} ({secret_manager_file})")
            
            if secret_manager_file.exists():
                print(f"secret_manager.py size: {secret_manager_file.stat().st_size} bytes")
                
                # Check if __init__.py files exist
                app_init = app_dir / "__init__.py"
                core_init = core_dir / "__init__.py"
                print(f"app/__init__.py exists: {app_init.exists()}")
                print(f"app/core/__init__.py exists: {core_init.exists()}")

def test_import_variations():
    """Test different import variations to identify which works"""
    print("\n=== IMPORT VARIATIONS TEST ===")
    
    import_tests = [
        ("Absolute import", "from app.core.secret_manager import validate_secrets_startup"),
        ("Relative import", "from .core.secret_manager import validate_secrets_startup"),
        ("Direct module import", "import app.core.secret_manager"),
        ("Nested absolute", "from app.core import secret_manager"),
    ]
    
    for test_name, import_statement in import_tests:
        print(f"\n{test_name}: {import_statement}")
        try:
            exec(import_statement)
            print(f"  ✅ SUCCESS - {test_name} works")
        except Exception as e:
            print(f"  ❌ FAILED - {test_name}: {e}")
            print(f"  Error type: {type(e).__name__}")

def test_sys_path_modifications():
    """Test adding current directory to sys.path"""
    print("\n=== SYS.PATH MODIFICATION TEST ===")
    
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        print(f"Adding current directory to sys.path: {current_dir}")
        sys.path.insert(0, current_dir)
        
        # Test import again
        try:
            from app.core.secret_manager import validate_secrets_startup
            print("✅ SUCCESS - Import works after adding current directory to sys.path")
        except Exception as e:
            print(f"❌ FAILED - Still doesn't work: {e}")
    else:
        print(f"Current directory already in sys.path: {current_dir}")

def simulate_gunicorn_environment():
    """Simulate the exact environment that Gunicorn creates"""
    print("\n=== GUNICORN ENVIRONMENT SIMULATION ===")
    
    # Check if we're in the expected Docker environment
    docker_indicators = [
        ("/app", "Docker working directory"),
        (os.getenv("RENDER"), "Render environment variable"),
        (os.path.exists("/.dockerenv"), "Docker container indicator"),
        (os.path.exists("/app/app/main.py"), "Expected main.py location")
    ]
    
    print("Environment indicators:")
    for indicator, description in docker_indicators:
        status = bool(indicator) if not isinstance(indicator, str) else bool(indicator)
        print(f"  {description}: {status}")

def main():
    """Run all diagnostic tests"""
    print("MARKEDGE PLATFORM - SECRET MANAGER IMPORT DIAGNOSTICS")
    print("=" * 60)
    
    try:
        diagnose_import_paths()
        diagnose_file_structure()
        simulate_gunicorn_environment()
        test_sys_path_modifications()
        test_import_variations()
        
        print("\n" + "=" * 60)
        print("DIAGNOSIS COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR DURING DIAGNOSIS: {e}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())