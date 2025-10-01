"""add frontend error logs simple

Revision ID: d8f5bb51ae7b
Revises: a0a2f1ab72ce
Create Date: 2025-09-23 21:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'd8f5bb51ae7b'
down_revision = 'a0a2f1ab72ce'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create frontend error logs table
    op.create_table(
        'frontend_error_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('timestamp', sa.String(length=50), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('stack', sa.Text(), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('build_time', sa.String(length=50), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('client_ip', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organisations.id'], ondelete='SET NULL')
    )

    # Create indexes for better query performance
    op.create_index('idx_frontend_error_logs_created_at', 'frontend_error_logs', ['created_at'])
    op.create_index('idx_frontend_error_logs_level', 'frontend_error_logs', ['level'])
    op.create_index('idx_frontend_error_logs_session_id', 'frontend_error_logs', ['session_id'])
    op.create_index('idx_frontend_error_logs_user_id', 'frontend_error_logs', ['user_id'])
    op.create_index('idx_frontend_error_logs_organization_id', 'frontend_error_logs', ['organization_id'])


def downgrade() -> None:
    # Drop the table and all its indexes
    op.drop_table('frontend_error_logs')