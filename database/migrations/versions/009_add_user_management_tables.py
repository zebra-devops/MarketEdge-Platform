"""Add user management tables

Revision ID: 009
Revises: 008
Create Date: 2025-01-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008_add_hierarchical_organizations'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_application_access table
    op.create_table('user_application_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application', sa.Enum('MARKET_EDGE', 'CAUSAL_EDGE', 'VALUE_EDGE', name='applicationtype'), nullable=False),
        sa.Column('has_access', sa.Boolean(), nullable=False, default=False),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'application', name='uq_user_application')
    )
    
    # Create user_invitations table
    op.create_table('user_invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invitation_token', sa.String(255), nullable=False, unique=True),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'EXPIRED', name='invitationstatus'), nullable=False, default='PENDING'),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_user_application_access_user_id', 'user_application_access', ['user_id'])
    op.create_index('idx_user_application_access_application', 'user_application_access', ['application'])
    op.create_index('idx_user_invitations_user_id', 'user_invitations', ['user_id'])
    op.create_index('idx_user_invitations_token', 'user_invitations', ['invitation_token'])
    op.create_index('idx_user_invitations_status', 'user_invitations', ['status'])
    op.create_index('idx_user_invitations_expires_at', 'user_invitations', ['expires_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_user_invitations_expires_at')
    op.drop_index('idx_user_invitations_status')
    op.drop_index('idx_user_invitations_token')
    op.drop_index('idx_user_invitations_user_id')
    op.drop_index('idx_user_application_access_application')
    op.drop_index('idx_user_application_access_user_id')
    
    # Drop tables
    op.drop_table('user_invitations')
    op.drop_table('user_application_access')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS invitationstatus')
    op.execute('DROP TYPE IF EXISTS applicationtype')