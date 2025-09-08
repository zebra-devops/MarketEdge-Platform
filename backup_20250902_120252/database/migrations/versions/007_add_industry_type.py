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
    # Create Industry enum type
    industry_enum = postgresql.ENUM(
        'cinema', 'hotel', 'gym', 'b2b', 'retail', 'default',
        name='industry'
    )
    industry_enum.create(op.get_bind())
    
    # Add industry_type column with default value
    op.add_column(
        'organisations',
        sa.Column('industry_type', industry_enum, nullable=False, server_default='default')
    )
    
    # Create index for industry_type for performance
    op.create_index('ix_organisations_industry_type', 'organisations', ['industry_type'])
    
    # Migrate existing industry data to industry_type where possible
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
        WHERE industry IS NOT NULL;
    """)


def downgrade() -> None:
    # Drop the index
    op.drop_index('ix_organisations_industry_type', table_name='organisations')
    
    # Drop the column
    op.drop_column('organisations', 'industry_type')
    
    # Drop the enum type
    op.execute('DROP TYPE IF EXISTS industry')