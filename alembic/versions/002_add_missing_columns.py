"""Add missing columns to organisations table

Revision ID: 002
Revises: 001
Create Date: 2025-08-17 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to organisations table
    
    # Add SIC code column
    op.add_column('organisations', sa.Column('sic_code', sa.String(length=10), nullable=True))
    
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
    
    # Add rate limiting columns to organisations table
    op.add_column('organisations', sa.Column('rate_limit_per_hour', sa.Integer(), nullable=False, server_default='1000'))
    op.add_column('organisations', sa.Column('burst_limit', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('organisations', sa.Column('rate_limit_enabled', sa.Boolean(), nullable=False, server_default='true'))
    
    # Create indices for performance
    op.create_index('ix_organisations_industry_type', 'organisations', ['industry_type'])


def downgrade() -> None:
    # Remove all added columns and indices
    op.drop_index('ix_organisations_industry_type', table_name='organisations')
    op.drop_column('organisations', 'rate_limit_enabled')
    op.drop_column('organisations', 'burst_limit')  
    op.drop_column('organisations', 'rate_limit_per_hour')
    op.drop_column('organisations', 'industry_type')
    op.drop_column('organisations', 'sic_code')
    
    # Drop the enum type
    op.execute('DROP TYPE IF EXISTS industry')