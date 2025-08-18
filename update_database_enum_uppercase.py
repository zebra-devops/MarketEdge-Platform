#!/usr/bin/env python3
"""
Update database enum values to uppercase to match Python enum
Production Database Enum Uppercase Migration
Author: DevOps Engineer
Date: 2025-08-18
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.config import settings

def update_database_enum_to_uppercase():
    """Update database enum constraint and existing records to use uppercase values"""
    
    print("🔧 DATABASE ENUM UPPERCASE MIGRATION")
    print("===================================")
    print("Target: Update enum constraint and records to use uppercase values")
    print("Reason: Match database constraint with Python enum case sensitivity")
    print()
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            print("🔍 Step 1: Check current database enum values...")
            
            # Check current enum definition
            result = conn.execute(text("""
                SELECT unnest(enum_range(NULL::industry)) as enum_values
            """))
            
            current_values = [row.enum_values for row in result]
            print(f"Current enum values: {current_values}")
            
            if all(val.isupper() for val in current_values):
                print("✅ Database enum is already uppercase - no changes needed")
                trans.rollback()
                return True
            
            print()
            print("🔍 Step 2: Check existing organization records...")
            
            # Check current records
            result = conn.execute(text("""
                SELECT id, name, industry_type, COUNT(*) OVER() as total_count
                FROM organisations 
                WHERE industry_type IS NOT NULL
                LIMIT 5
            """))
            
            records = list(result.fetchall())
            if records:
                total_count = records[0].total_count
                print(f"Found {total_count} organization records with industry_type:")
                for record in records[:5]:
                    print(f"  - {record.name}: {record.industry_type}")
                if len(records) == 5 and total_count > 5:
                    print(f"  ... and {total_count - 5} more")
            
            print()
            print("🛠️  Step 3: Update database enum constraint to uppercase...")
            
            # Drop the existing enum constraint and recreate with uppercase values
            conn.execute(text("""
                -- Create new enum type with uppercase values
                CREATE TYPE industry_new AS ENUM ('CINEMA', 'HOTEL', 'GYM', 'B2B', 'RETAIL', 'DEFAULT');
            """))
            
            print("✅ Created new uppercase enum type")
            
            # Update the column to use new enum temporarily allowing conversion
            conn.execute(text("""
                -- Add temporary column with new enum type
                ALTER TABLE organisations ADD COLUMN industry_type_new industry_new;
            """))
            
            print("✅ Added temporary column")
            
            # Convert existing values to uppercase
            conn.execute(text("""
                UPDATE organisations SET industry_type_new = UPPER(industry_type::text)::industry_new 
                WHERE industry_type IS NOT NULL;
            """))
            
            print("✅ Converted existing values to uppercase")
            
            # Drop old column and rename new one
            conn.execute(text("""
                ALTER TABLE organisations DROP COLUMN industry_type;
                ALTER TABLE organisations RENAME COLUMN industry_type_new TO industry_type;
            """))
            
            print("✅ Replaced column with uppercase version")
            
            # Drop old enum type and rename new one
            conn.execute(text("""
                DROP TYPE industry;
                ALTER TYPE industry_new RENAME TO industry;
            """))
            
            print("✅ Updated enum type name")
            
            # Set proper defaults and constraints
            conn.execute(text("""
                ALTER TABLE organisations ALTER COLUMN industry_type SET NOT NULL;
                ALTER TABLE organisations ALTER COLUMN industry_type SET DEFAULT 'DEFAULT';
            """))
            
            print("✅ Set proper constraints and defaults")
            
            # Commit the transaction
            trans.commit()
            print()
            print("💾 All changes committed successfully")
            
    except Exception as e:
        print(f"❌ Error updating database enum: {e}")
        return False
    
    print()
    print("🎉 DATABASE ENUM UPPERCASE MIGRATION COMPLETE")
    print("Database enum now uses uppercase values matching Python enum")
    print("Expected values: CINEMA, HOTEL, GYM, B2B, RETAIL, DEFAULT")
    return True

if __name__ == "__main__":
    success = update_database_enum_to_uppercase()
    sys.exit(0 if success else 1)