"""
Emergency auth fix - simplify organisation creation to avoid missing columns
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.organisation import Organisation
from sqlalchemy import text

def check_and_fix_database():
    db = SessionLocal()
    try:
        # Check if columns exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'organisations'
        """))
        columns = [row[0] for row in result]
        print(f"Existing columns: {columns}")
        
        # Check if we can query organisations
        try:
            orgs = db.query(Organisation).all()
            print(f"Found {len(orgs)} organisations")
        except Exception as e:
            print(f"Error querying organisations: {e}")
            
            # Try to add missing columns
            missing_columns_sql = """
            DO $$ 
            BEGIN
                -- Add industry_type if missing
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='organisations' AND column_name='industry_type') THEN
                    ALTER TABLE organisations ADD COLUMN industry_type VARCHAR(50) DEFAULT 'default';
                END IF;
                
                -- Add rate_limit_per_hour if missing
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='organisations' AND column_name='rate_limit_per_hour') THEN
                    ALTER TABLE organisations ADD COLUMN rate_limit_per_hour INTEGER DEFAULT 1000;
                END IF;
                
                -- Add burst_limit if missing
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='organisations' AND column_name='burst_limit') THEN
                    ALTER TABLE organisations ADD COLUMN burst_limit INTEGER DEFAULT 100;
                END IF;
                
                -- Add rate_limit_enabled if missing
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='organisations' AND column_name='rate_limit_enabled') THEN
                    ALTER TABLE organisations ADD COLUMN rate_limit_enabled BOOLEAN DEFAULT TRUE;
                END IF;
                
                -- Add sic_code if missing
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='organisations' AND column_name='sic_code') THEN
                    ALTER TABLE organisations ADD COLUMN sic_code VARCHAR(10);
                END IF;
            END $$;
            """
            
            db.execute(text(missing_columns_sql))
            db.commit()
            print("Added missing columns to organisations table")
            
    except Exception as e:
        print(f"Database fix error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    check_and_fix_database()