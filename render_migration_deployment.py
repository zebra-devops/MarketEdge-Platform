#!/usr/bin/env python3
"""
One-time Render deployment for emergency migrations
Executes the migration and then exits
"""

import os
import subprocess
import sys

def main():
    print("🚀 Render Emergency Migration Deployment")
    print("🎯 Target: Create missing analytics_modules table")

    # Verify DATABASE_URL is available
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL not available in Render environment!")
        sys.exit(1)

    print("✅ DATABASE_URL found in environment")

    # Run the migration script
    try:
        result = subprocess.run([
            sys.executable,
            'apply_production_migrations_emergency.py'
        ], check=True, capture_output=True, text=True)

        print("✅ Migration script output:")
        print(result.stdout)

        if result.stderr:
            print("⚠️ Migration script warnings:")
            print(result.stderr)

        print("🎉 EMERGENCY MIGRATION COMPLETED!")
        print("✅ analytics_modules table should now exist")
        print("🚀 Matt Lindop can now access admin features")

    except subprocess.CalledProcessError as e:
        print(f"❌ Migration script failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        sys.exit(1)

    print("👋 One-time migration deployment complete - container will exit")

if __name__ == "__main__":
    main()
