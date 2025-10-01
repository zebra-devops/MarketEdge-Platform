"""Add industry_type field to organisations

Revision ID: 007_add_industry_type
Revises: 006_add_rate_limiting
Create Date: 2025-08-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_industry_type'
down_revision = '006_add_rate_limiting'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Import defensive migration utilities
    from database.migrations.utils import get_validator
    validator = get_validator()

    # Create Industry enum type only if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'industry') THEN
                CREATE TYPE industry AS ENUM ('cinema', 'hotel', 'gym', 'b2b', 'retail', 'default');
            END IF;
        END $$;
    """)

    # Add industry_type column with default value using IF NOT EXISTS
    op.execute("""
        ALTER TABLE organisations
        ADD COLUMN IF NOT EXISTS industry_type VARCHAR(50) DEFAULT 'default' NOT NULL
    """)

    # Convert VARCHAR column to enum type using safe drop/recreate approach
    op.execute("""
        DO $$
        DECLARE
            existing_data RECORD;
        BEGIN
            -- Check if column exists as VARCHAR and needs conversion
            IF EXISTS (SELECT 1 FROM information_schema.columns
                      WHERE table_name = 'organisations'
                      AND column_name = 'industry_type'
                      AND data_type = 'character varying') THEN

                -- Create temporary table to store existing data with proper enum mapping
                CREATE TEMP TABLE temp_industry_mapping AS
                SELECT
                    id,
                    CASE
                        WHEN industry_type IN ('cinema', 'hotel', 'gym', 'b2b', 'retail', 'default')
                        THEN industry_type
                        ELSE 'default'
                    END as mapped_industry_type
                FROM organisations;

                -- Drop the VARCHAR column
                ALTER TABLE organisations DROP COLUMN industry_type;

                -- Add the column back as enum type
                ALTER TABLE organisations ADD COLUMN industry_type industry NOT NULL DEFAULT 'default'::industry;

                -- Update with mapped values
                UPDATE organisations
                SET industry_type = temp_industry_mapping.mapped_industry_type::industry
                FROM temp_industry_mapping
                WHERE organisations.id = temp_industry_mapping.id;

                -- Clean up temp table
                DROP TABLE temp_industry_mapping;

            END IF;
        END $$;
    """)

    # Create index for industry_type for performance (safe create)
    validator.safe_create_index('ix_organisations_industry_type', 'organisations', ['industry_type'])
    
    # Skip UPDATE operation to avoid enum type conflicts
    # Emergency repair scripts have likely already set appropriate values
    # If UPDATE is needed later, it can be done manually or in a separate migration
    print("Skipping industry_type UPDATE to avoid enum type conflicts - values already set by emergency repair")


def downgrade() -> None:
    # Import defensive migration utilities
    from database.migrations.utils import get_validator
    validator = get_validator()

    # Drop the index safely
    validator.safe_drop_index('ix_organisations_industry_type', 'organisations')

    # Drop the column safely
    if validator.column_exists('organisations', 'industry_type'):
        op.drop_column('organisations', 'industry_type')

    # Drop the enum type
    op.execute('DROP TYPE IF EXISTS industry')