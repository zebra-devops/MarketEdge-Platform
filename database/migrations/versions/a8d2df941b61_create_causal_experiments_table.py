"""Create causal experiments table

Revision ID: a8d2df941b61
Revises: d8f5bb51ae7b
Create Date: 2025-09-25 13:54:28.802746

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a8d2df941b61'
down_revision = 'd8f5bb51ae7b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create causal_experiments table for Causal Edge functionality
    op.create_table('causal_experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),

        # Experiment Metadata
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('experiment_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='DRAFT'),

        # Experiment Configuration
        sa.Column('hypothesis', sa.Text(), nullable=False),
        sa.Column('treatment_description', sa.Text()),
        sa.Column('control_description', sa.Text()),
        sa.Column('success_metrics', postgresql.JSON),
        sa.Column('config', postgresql.JSON),

        # Statistical Configuration
        sa.Column('statistical_power', sa.Float, default=0.8),
        sa.Column('significance_level', sa.Float, default=0.05),
        sa.Column('minimum_detectable_effect', sa.Float),
        sa.Column('expected_sample_size', sa.Integer),

        # Timing
        sa.Column('planned_start_date', sa.DateTime),
        sa.Column('planned_end_date', sa.DateTime),
        sa.Column('actual_start_date', sa.DateTime),
        sa.Column('actual_end_date', sa.DateTime),

        # Results
        sa.Column('results', postgresql.JSON),
        sa.Column('conclusions', sa.Text),
        sa.Column('recommendations', sa.Text),

        # Metadata
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Create indexes
    op.create_index('ix_causal_experiments_organisation_status', 'causal_experiments', ['organisation_id', 'status'])
    op.create_index('ix_causal_experiments_created_by', 'causal_experiments', ['created_by'])
    op.create_index('ix_causal_experiments_dates', 'causal_experiments', ['actual_start_date', 'actual_end_date'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_causal_experiments_dates', 'causal_experiments')
    op.drop_index('ix_causal_experiments_created_by', 'causal_experiments')
    op.drop_index('ix_causal_experiments_organisation_status', 'causal_experiments')

    # Drop table
    op.drop_table('causal_experiments')