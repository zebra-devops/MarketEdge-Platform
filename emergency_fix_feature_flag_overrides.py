#!/usr/bin/env python3
"""
Emergency Fix: Add missing updated_at column to feature_flag_overrides table

This script directly adds the missing 'updated_at' column that is causing
the 500 "Database error during authentication" issue.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings


def fix_feature_flag_tables():
    """Add missing Base columns to feature flag tables"""
    print("🔧 Emergency Fix: Adding missing Base columns to feature flag tables")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # Start transaction
            with conn.begin():
                success = True
                
                # Fix feature_flag_overrides table
                print("🔧 Checking feature_flag_overrides table...")
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'feature_flag_overrides' 
                    AND column_name IN ('updated_at');
                """))
                existing_columns = [row[0] for row in result.fetchall()]
                
                if 'updated_at' not in existing_columns:
                    print("   Adding 'updated_at' column...")
                    conn.execute(text("""
                        ALTER TABLE feature_flag_overrides 
                        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE 
                        DEFAULT now();
                    """))
                    conn.execute(text("""
                        UPDATE feature_flag_overrides 
                        SET updated_at = created_at 
                        WHERE updated_at IS NULL;
                    """))
                else:
                    print("   ✅ 'updated_at' column already exists")
                
                # Fix feature_flag_usage table
                print("🔧 Checking feature_flag_usage table...")
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'feature_flag_usage' 
                    AND column_name IN ('created_at', 'updated_at');
                """))
                existing_columns = [row[0] for row in result.fetchall()]
                
                if 'created_at' not in existing_columns:
                    print("   Adding 'created_at' column...")
                    conn.execute(text("""
                        ALTER TABLE feature_flag_usage 
                        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE 
                        DEFAULT now();
                    """))
                    conn.execute(text("""
                        UPDATE feature_flag_usage 
                        SET created_at = accessed_at 
                        WHERE created_at IS NULL;
                    """))
                else:
                    print("   ✅ 'created_at' column already exists")
                
                if 'updated_at' not in existing_columns:
                    print("   Adding 'updated_at' column...")
                    conn.execute(text("""
                        ALTER TABLE feature_flag_usage 
                        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE 
                        DEFAULT now();
                    """))
                    conn.execute(text("""
                        UPDATE feature_flag_usage 
                        SET updated_at = accessed_at 
                        WHERE updated_at IS NULL;
                    """))
                else:
                    print("   ✅ 'updated_at' column already exists")
                
                print("✅ Successfully fixed feature flag tables")
                return True
                
    except Exception as e:
        print(f"❌ Failed to fix feature flag tables: {e}")
        return False


def verify_fix():
    """Verify that the fix was successful"""
    print("\n🔍 Verifying the fix...")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # Check feature_flag_overrides columns
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'feature_flag_overrides' 
                AND column_name IN ('updated_at')
                ORDER BY column_name;
            """))
            
            columns = result.fetchall()
            print(f"✅ feature_flag_overrides columns:")
            for column_info in columns:
                print(f"   - {column_info[0]}: {column_info[1]} (nullable={column_info[2]}, default={column_info[3]})")
            
            # Check feature_flag_usage columns
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'feature_flag_usage' 
                AND column_name IN ('created_at', 'updated_at')
                ORDER BY column_name;
            """))
            
            columns = result.fetchall()
            print(f"✅ feature_flag_usage columns:")
            for column_info in columns:
                print(f"   - {column_info[0]}: {column_info[1]} (nullable={column_info[2]}, default={column_info[3]})")
            
            return len(columns) >= 2  # Should have at least created_at and updated_at
                
    except Exception as e:
        print(f"❌ Failed to verify fix: {e}")
        return False


def main():
    """Main function to apply emergency fix"""
    print("🚨 MarketEdge Emergency Database Fix")
    print("=" * 45)
    print("Issue: Missing Base columns in feature flag tables")
    print("Impact: 500 error during authentication for £925K opportunity")
    print()
    
    # Apply the fix
    if fix_feature_flag_tables():
        # Verify the fix
        if verify_fix():
            print("\n🎉 Emergency fix completed successfully!")
            print("💡 The authentication flow should now work properly.")
            print("⚠️  Remember to create a proper migration for this fix.")
        else:
            print("\n❌ Fix verification failed. Manual intervention required.")
    else:
        print("\n❌ Emergency fix failed. Check database permissions and connectivity.")


if __name__ == "__main__":
    main()