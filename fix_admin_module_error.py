#!/usr/bin/env python3
"""
Fix for ModuleNotFoundError: No module named 'app.api.admin'
This script identifies and fixes the incorrect import path
"""

import os
import sys
import re
from pathlib import Path

def find_bad_imports(directory):
    """Find all files with incorrect admin imports"""
    bad_files = []

    # Pattern to match incorrect imports
    bad_patterns = [
        r'from app\.api\.admin',
        r'import app\.api\.admin',
    ]

    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and backup directories
        if '__pycache__' in root or 'backup' in root:
            continue

        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern in bad_patterns:
                            if re.search(pattern, content):
                                bad_files.append(filepath)
                                print(f"Found bad import in: {filepath}")
                                # Show the problematic lines
                                lines = content.split('\n')
                                for i, line in enumerate(lines, 1):
                                    if re.search(pattern, line):
                                        print(f"  Line {i}: {line.strip()}")
                except Exception as e:
                    pass

    return bad_files

def check_dynamic_imports(directory):
    """Check for dynamic imports that might cause issues"""
    print("\nChecking for dynamic imports that might reference app.api.admin:")

    patterns = [
        r'exec\(',
        r'eval\(',
        r'__import__\(',
        r'importlib\.import_module\(',
    ]

    for root, dirs, files in os.walk(directory):
        if '__pycache__' in root or 'backup' in root:
            continue

        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern in patterns:
                            if re.search(pattern, content):
                                # Check if 'admin' is mentioned nearby
                                if 'admin' in content:
                                    print(f"\nPotential dynamic import in: {filepath}")
                                    lines = content.split('\n')
                                    for i, line in enumerate(lines, 1):
                                        if re.search(pattern, line) and 'admin' in line:
                                            print(f"  Line {i}: {line.strip()}")
                except Exception as e:
                    pass

def main():
    print("=" * 60)
    print("ADMIN MODULE ERROR FIX DIAGNOSTIC")
    print("=" * 60)

    # Check the app directory
    app_dir = '/Users/matt/Sites/MarketEdge/app'

    print(f"\nScanning directory: {app_dir}")
    print("-" * 60)

    # Find bad imports
    bad_files = find_bad_imports(app_dir)

    if bad_files:
        print(f"\n⚠️  Found {len(bad_files)} files with incorrect imports")
        print("These need to be fixed to use: from app.api.api_v1.endpoints.admin")
    else:
        print("\n✅ No incorrect static imports found")

    # Check dynamic imports
    check_dynamic_imports(app_dir)

    # Check if the correct module exists
    print("\n" + "=" * 60)
    print("VERIFYING CORRECT MODULE STRUCTURE:")
    print("-" * 60)

    correct_path = '/Users/matt/Sites/MarketEdge/app/api/api_v1/endpoints/admin.py'
    if os.path.exists(correct_path):
        print(f"✅ Correct admin module exists at: {correct_path}")
    else:
        print(f"❌ Admin module NOT FOUND at: {correct_path}")

    incorrect_path = '/Users/matt/Sites/MarketEdge/app/api/admin.py'
    if os.path.exists(incorrect_path):
        print(f"⚠️  Incorrect admin module exists at: {incorrect_path}")
        print("   This should be removed or moved to the correct location")
    else:
        print(f"✅ No incorrect admin module at: {incorrect_path}")

    # Check imports in main.py
    print("\n" + "=" * 60)
    print("CHECKING MAIN APP IMPORTS:")
    print("-" * 60)

    main_path = '/Users/matt/Sites/MarketEdge/app/main.py'
    if os.path.exists(main_path):
        with open(main_path, 'r') as f:
            content = f.read()
            if 'from app.api.api_v1.api import api_router' in content:
                print("✅ main.py uses correct API router import")
            else:
                print("⚠️  main.py may have incorrect imports")

    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()