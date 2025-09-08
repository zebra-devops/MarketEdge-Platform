#!/usr/bin/env python3
"""
Comprehensive Base Columns Fix

This script identifies and fixes ALL tables missing Base columns (created_at, updated_at)
that should inherit from the Base class but don't have these columns in the database.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings


def get_tables_missing_base_columns():
    """Find all tables that should have Base columns but are missing them"""
    print("🔍 Identifying tables missing Base columns...")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # Get all tables in the public schema
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """))
            
            all_tables = [row[0] for row in result.fetchall()]
            print(f"📋 Found {len(all_tables)} tables: {', '.join(all_tables)}")
            
            # Check which tables are missing created_at or updated_at columns
            missing_columns = {}
            
            for table in all_tables:
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                    AND column_name IN ('created_at', 'updated_at')
                    ORDER BY column_name;
                """))
                
                existing_columns = [row[0] for row in result.fetchall()]
                needed_columns = []
                
                if 'created_at' not in existing_columns:
                    needed_columns.append('created_at')
                if 'updated_at' not in existing_columns:
                    needed_columns.append('updated_at')
                
                if needed_columns:
                    missing_columns[table] = needed_columns
                    
            return missing_columns
            
    except Exception as e:
        print(f"❌ Failed to identify missing columns: {e}")
        return {}


def fix_table_base_columns(table_name, missing_columns):
    """Add missing Base columns to a specific table"""
    print(f"🔧 Fixing table '{table_name}' - missing: {', '.join(missing_columns)}")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            with conn.begin():
                for column in missing_columns:
                    if column == 'created_at':
                        print(f"   Adding 'created_at' column...")
                        conn.execute(text(f"""
                            ALTER TABLE {table_name}
                            ADD COLUMN created_at TIMESTAMP WITH TIME ZONE 
                            DEFAULT now() NOT NULL;
                        """))
                        
                    elif column == 'updated_at':
                        print(f"   Adding 'updated_at' column...")
                        conn.execute(text(f"""
                            ALTER TABLE {table_name}
                            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE 
                            DEFAULT now();
                        """))
                
                print(f"✅ Successfully fixed table '{table_name}'")
                return True
                
    except Exception as e:
        print(f"❌ Failed to fix table '{table_name}': {e}")
        return False


def verify_all_fixes(original_missing):
    """Verify that all missing columns have been added"""
    print("\n🔍 Verifying all fixes...")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            all_fixed = True
            
            for table_name, expected_columns in original_missing.items():
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                    AND column_name IN ('created_at', 'updated_at')
                    ORDER BY column_name;
                """))
                
                existing_columns = [row[0] for row in result.fetchall()]
                still_missing = [col for col in expected_columns if col not in existing_columns]
                
                if still_missing:
                    print(f"❌ Table '{table_name}' still missing: {', '.join(still_missing)}")
                    all_fixed = False
                else:
                    print(f"✅ Table '{table_name}' - all columns present")
            
            return all_fixed
            
    except Exception as e:
        print(f"❌ Failed to verify fixes: {e}")
        return False


def main():
    """Main function to apply comprehensive Base column fixes"""
    print("🚨 MarketEdge Comprehensive Base Columns Fix")
    print("=" * 50)
    print("Issue: Multiple tables missing Base columns (created_at, updated_at)")
    print("Impact: 500 error during authentication for £925K opportunity")
    print()
    
    # Step 1: Identify all tables with missing columns
    missing_columns = get_tables_missing_base_columns()
    
    if not missing_columns:
        print("🎉 No tables found with missing Base columns!")
        return
    
    print(f"\n⚠️  Found {len(missing_columns)} tables with missing Base columns:")
    for table, columns in missing_columns.items():
        print(f"   - {table}: missing {', '.join(columns)}")
    
    print(f"\n🔧 Applying fixes...")
    
    # Step 2: Fix each table
    success_count = 0
    for table_name, columns in missing_columns.items():
        if fix_table_base_columns(table_name, columns):
            success_count += 1
    
    # Step 3: Verify all fixes
    if success_count == len(missing_columns):
        if verify_all_fixes(missing_columns):
            print(f"\n🎉 Comprehensive fix completed successfully!")
            print(f"✅ Fixed {success_count} tables")
            print("💡 The authentication flow should now work properly.")
            print("⚠️  Remember to create proper migrations for these fixes.")
        else:
            print(f"\n⚠️  Some fixes may not have been applied correctly.")
    else:
        print(f"\n❌ Only {success_count}/{len(missing_columns)} tables were fixed successfully.")


if __name__ == "__main__":
    main()