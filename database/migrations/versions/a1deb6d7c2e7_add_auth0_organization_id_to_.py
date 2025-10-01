"""add_auth0_organization_id_to_organisations

Revision ID: a1deb6d7c2e7
Revises: a8d2df941b61
Create Date: 2025-10-01 11:24:52.871575

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1deb6d7c2e7'
down_revision = 'a8d2df941b61'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add auth0_organization_id column to organisations table"""

    # Add column with unique constraint
    op.add_column(
        'organisations',
        sa.Column(
            'auth0_organization_id',
            sa.String(255),
            nullable=True,
            unique=False  # Unique constraint will be added via index
        )
    )

    # Create unique index on auth0_organization_id
    op.create_index(
        'idx_organisations_auth0_org_id',
        'organisations',
        ['auth0_organization_id'],
        unique=True
    )

    # Seed existing Zebra Associates mapping
    # Map multiple Auth0 org IDs to single organisation UUID
    op.execute("""
        UPDATE organisations
        SET auth0_organization_id = 'zebra-associates-org-id'
        WHERE id = '835d4f24-cff2-43e8-a470-93216a3d99a3'
    """)


def downgrade() -> None:
    """Remove auth0_organization_id column"""
    op.drop_index('idx_organisations_auth0_org_id', table_name='organisations')
    op.drop_column('organisations', 'auth0_organization_id')