"""Fix Industry enum case sensitivity - update to uppercase

Revision ID: 003
Revises: 002
Create Date: 2025-08-18 21:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Fix the Industry enum case sensitivity issue by:
    1. Creating new UPPERCASE enum type
    2. Converting existing data to uppercase
    3. Replacing old enum with new one
    4. Updating constraints and defaults
    """
    
    # Create new uppercase enum type
    new_industry_enum = postgresql.ENUM(
        'CINEMA', 'HOTEL', 'GYM', 'B2B', 'RETAIL', 'DEFAULT',
        name='industry_new'
    )
    new_industry_enum.create(op.get_bind())
    
    # Update existing data to uppercase values
    op.execute("""
        UPDATE organisations 
        SET industry_type = CASE 
            WHEN industry_type = 'cinema' THEN 'CINEMA'
            WHEN industry_type = 'hotel' THEN 'HOTEL'
            WHEN industry_type = 'gym' THEN 'GYM'
            WHEN industry_type = 'b2b' THEN 'B2B'
            WHEN industry_type = 'retail' THEN 'RETAIL'
            WHEN industry_type = 'default' THEN 'DEFAULT'
            ELSE 'DEFAULT'
        END::text::industry_new
    """)
    
    # Drop the old constraint and column temporarily
    op.drop_index('ix_organisations_industry_type', table_name='organisations')
    op.alter_column('organisations', 'industry_type', 
                   type_=new_industry_enum,
                   server_default='DEFAULT',
                   postgresql_using='industry_type::text::industry_new')
    
    # Drop the old enum type
    op.execute('DROP TYPE IF EXISTS industry')
    
    # Rename the new enum type to the original name
    op.execute('ALTER TYPE industry_new RENAME TO industry')
    
    # Recreate the index
    op.create_index('ix_organisations_industry_type', 'organisations', ['industry_type'])


def downgrade() -> None:
    """
    Downgrade back to lowercase enum values
    """
    
    # Create old lowercase enum type
    old_industry_enum = postgresql.ENUM(
        'cinema', 'hotel', 'gym', 'b2b', 'retail', 'default',
        name='industry_old'
    )
    old_industry_enum.create(op.get_bind())
    
    # Convert data back to lowercase
    op.execute("""
        UPDATE organisations 
        SET industry_type = CASE 
            WHEN industry_type = 'CINEMA' THEN 'cinema'
            WHEN industry_type = 'HOTEL' THEN 'hotel'
            WHEN industry_type = 'GYM' THEN 'gym'
            WHEN industry_type = 'B2B' THEN 'b2b'
            WHEN industry_type = 'RETAIL' THEN 'retail'
            WHEN industry_type = 'DEFAULT' THEN 'default'
            ELSE 'default'
        END::text::industry_old
    """)
    
    # Drop index and update column
    op.drop_index('ix_organisations_industry_type', table_name='organisations')
    op.alter_column('organisations', 'industry_type',
                   type_=old_industry_enum,
                   server_default='default',
                   postgresql_using='industry_type::text::industry_old')
    
    # Drop the uppercase enum type
    op.execute('DROP TYPE IF EXISTS industry')
    
    # Rename back to original
    op.execute('ALTER TYPE industry_old RENAME TO industry')
    
    # Recreate the index
    op.create_index('ix_organisations_industry_type', 'organisations', ['industry_type'])