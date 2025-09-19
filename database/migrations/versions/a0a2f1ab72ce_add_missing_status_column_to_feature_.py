"""Add missing status column to feature_flags table

This migration fixes a critical production issue where the feature_flags.status
column is missing, causing 500 errors for Matt.Lindop's admin access.

The column should have been created in migration 003 but appears to be missing
in the production database.

Revision ID: a0a2f1ab72ce
Revises: 80105006e3d3
Create Date: 2025-09-19 21:41:20.894420

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'a0a2f1ab72ce'
down_revision = '80105006e3d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, check if the featureflagstatus enum type exists
    # If not, create it
    connection = op.get_bind()

    # Check if enum type exists
    enum_exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'featureflagstatus'")
    ).fetchone()

    if not enum_exists:
        # Create the enum type if it doesn't exist
        featureflagstatus_enum = postgresql.ENUM(
            'ACTIVE', 'INACTIVE', 'DEPRECATED',
            name='featureflagstatus'
        )
        featureflagstatus_enum.create(connection)

    # Check if the status column already exists
    column_exists = connection.execute(
        sa.text("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'feature_flags'
            AND column_name = 'status'
        """)
    ).fetchone()

    if not column_exists:
        # Add the status column with default value
        op.add_column('feature_flags',
            sa.Column('status',
                sa.Enum('ACTIVE', 'INACTIVE', 'DEPRECATED', name='featureflagstatus'),
                nullable=False,
                server_default='ACTIVE'
            )
        )
        print("✅ Added status column to feature_flags table")
    else:
        print("ℹ️  Status column already exists in feature_flags table")


def downgrade() -> None:
    # Remove the status column
    connection = op.get_bind()

    # Check if column exists before trying to drop it
    column_exists = connection.execute(
        sa.text("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'feature_flags'
            AND column_name = 'status'
        """)
    ).fetchone()

    if column_exists:
        op.drop_column('feature_flags', 'status')
        print("✅ Removed status column from feature_flags table")

    # Note: We don't drop the enum type in downgrade as it might be used by other tables
    # and could break the original migration 003 if we need to re-run it