#!/usr/bin/env python3
"""
Check production analytics_modules table schema
"""
import os
import asyncio
import asyncpg
import json
from datetime import datetime

async def check_analytics_modules_schema():
    """Check production analytics_modules table schema"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        return

    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)

        # Check if analytics_modules table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'analytics_modules'
            );
        """)

        print(f"analytics_modules table exists: {table_exists}")

        if table_exists:
            # Get column information
            columns = await conn.fetch("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'analytics_modules'
                ORDER BY ordinal_position;
            """)

            print("\nCurrent columns in analytics_modules:")
            for col in columns:
                print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")

            # Check for required columns from model
            required_columns = [
                'id', 'name', 'description', 'version', 'module_type', 'status',
                'is_core', 'requires_license', 'entry_point', 'config_schema',
                'default_config', 'dependencies', 'min_data_requirements',
                'api_endpoints', 'frontend_components', 'documentation_url',
                'help_text', 'pricing_tier', 'license_requirements',
                'created_by', 'created_at', 'updated_at'
            ]

            existing_columns = [col['column_name'] for col in columns]
            missing_columns = [col for col in required_columns if col not in existing_columns]

            if missing_columns:
                print(f"\nMISSING COLUMNS: {missing_columns}")
            else:
                print("\nAll required columns are present!")

            # Check if description column exists and is correct type
            description_col = next((col for col in columns if col['column_name'] == 'description'), None)
            if description_col:
                print(f"\ndescription column: {description_col['data_type']} (nullable: {description_col['is_nullable']})")
            else:
                print("\nERROR: description column is missing!")

            # Count existing records
            count = await conn.fetchval("SELECT COUNT(*) FROM analytics_modules")
            print(f"\nTotal records: {count}")

        await conn.close()

        # Save results to file
        result = {
            "timestamp": datetime.now().isoformat(),
            "table_exists": table_exists,
            "columns": [dict(col) for col in columns] if table_exists else [],
            "missing_columns": missing_columns if table_exists else [],
            "record_count": count if table_exists else 0
        }

        with open(f"production_analytics_modules_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"\nResults saved to production_analytics_modules_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_analytics_modules_schema())