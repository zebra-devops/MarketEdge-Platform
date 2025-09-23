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

    # Cast to proper enum type if column was just created
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                      WHERE table_name = 'organisations'
                      AND column_name = 'industry_type'
                      AND data_type = 'character varying') THEN
                ALTER TABLE organisations ALTER COLUMN industry_type TYPE industry USING industry_type::industry;
            END IF;
        END $$;
    """)

    # Create index for industry_type for performance (safe create)
    validator.safe_create_index('ix_organisations_industry_type', 'organisations', ['industry_type'])
    
    # Migrate existing industry data to industry_type where possible (only if needed)
    # This is a safe migration that maps string values to enum values
    op.execute("""
        UPDATE organisations
        SET industry_type = CASE
            WHEN LOWER(industry) LIKE '%cinema%' OR LOWER(industry) LIKE '%movie%' OR LOWER(industry) LIKE '%theater%' THEN 'cinema'::industry
            WHEN LOWER(industry) LIKE '%hotel%' OR LOWER(industry) LIKE '%hospitality%' OR LOWER(industry) LIKE '%motel%' THEN 'hotel'::industry
            WHEN LOWER(industry) LIKE '%gym%' OR LOWER(industry) LIKE '%fitness%' OR LOWER(industry) LIKE '%health%' THEN 'gym'::industry
            WHEN LOWER(industry) LIKE '%b2b%' OR LOWER(industry) LIKE '%business%' OR LOWER(industry) LIKE '%consulting%' THEN 'b2b'::industry
            WHEN LOWER(industry) LIKE '%retail%' OR LOWER(industry) LIKE '%shop%' OR LOWER(industry) LIKE '%store%' THEN 'retail'::industry
            ELSE 'default'::industry
        END
        WHERE industry IS NOT NULL AND industry_type = 'default'::industry;
    """)


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