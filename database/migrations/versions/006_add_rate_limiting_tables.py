"""Add rate limiting tables

Revision ID: 006
Revises: 005
Create Date: 2025-08-08 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tenant_rate_limits table
    op.create_table(
        'tenant_rate_limits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('tier', sa.String(50), nullable=False, default='standard'),
        sa.Column('requests_per_hour', sa.Integer(), nullable=False, default=1000),
        sa.Column('burst_size', sa.Integer(), nullable=False, default=100),
        sa.Column('endpoint_overrides', postgresql.JSON(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('emergency_bypass', sa.Boolean(), nullable=False, default=False),
        sa.Column('bypass_reason', sa.Text(), nullable=True),
        sa.Column('bypass_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    
    # Add unique constraint for tenant_id
    op.create_unique_constraint('uq_tenant_rate_limit', 'tenant_rate_limits', ['tenant_id'])
    
    # Add foreign key constraint to organisations table
    op.create_foreign_key(
        'fk_tenant_rate_limits_tenant_id',
        'tenant_rate_limits', 'organisations',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Add foreign key constraints for created_by and updated_by
    op.create_foreign_key(
        'fk_tenant_rate_limits_created_by',
        'tenant_rate_limits', 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_tenant_rate_limits_updated_by',
        'tenant_rate_limits', 'users',
        ['updated_by'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create rate_limit_violations table
    op.create_table(
        'rate_limit_violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('endpoint', sa.String(500), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('rate_limit', sa.Integer(), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False),
        sa.Column('client_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('headers', postgresql.JSON(), nullable=True),
        sa.Column('violation_time', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('retry_after_seconds', sa.Integer(), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False, default='medium'),
        sa.Column('automated_response', sa.String(100), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
    )
    
    # Add foreign key constraints for rate_limit_violations
    op.create_foreign_key(
        'fk_rate_limit_violations_tenant_id',
        'rate_limit_violations', 'organisations',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_rate_limit_violations_user_id',
        'rate_limit_violations', 'users',
        ['user_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create rate_limit_metrics table
    op.create_table(
        'rate_limit_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('aggregation_period', sa.String(10), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_requests', sa.Integer(), nullable=False, default=0),
        sa.Column('blocked_requests', sa.Integer(), nullable=False, default=0),
        sa.Column('unique_users', sa.Integer(), nullable=False, default=0),
        sa.Column('unique_ips', sa.Integer(), nullable=False, default=0),
        sa.Column('avg_processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('max_processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('rate_limit_overhead_ms', sa.Integer(), nullable=True),
        sa.Column('top_endpoints', postgresql.JSON(), nullable=True),
        sa.Column('top_violating_ips', postgresql.JSON(), nullable=True),
        sa.Column('redis_errors', sa.Integer(), nullable=False, default=0),
        sa.Column('bypass_events', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Add unique constraint for metrics aggregation
    op.create_unique_constraint(
        'uq_rate_limit_metrics_period',
        'rate_limit_metrics',
        ['tenant_id', 'aggregation_period', 'period_start']
    )
    
    # Add foreign key constraint for tenant_id in metrics
    op.create_foreign_key(
        'fk_rate_limit_metrics_tenant_id',
        'rate_limit_metrics', 'organisations',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes for performance
    op.create_index('idx_tenant_rate_limits_enabled', 'tenant_rate_limits', ['enabled'])
    op.create_index('idx_tenant_rate_limits_emergency', 'tenant_rate_limits', ['emergency_bypass'])
    op.create_index('idx_rate_limit_violations_time_tenant', 'rate_limit_violations', ['violation_time', 'tenant_id'])
    op.create_index('idx_rate_limit_violations_severity', 'rate_limit_violations', ['severity'])
    op.create_index('idx_rate_limit_metrics_period_tenant', 'rate_limit_metrics', ['aggregation_period', 'tenant_id'])
    
    # Insert default rate limits for existing organisations
    op.execute("""
        INSERT INTO tenant_rate_limits (id, tenant_id, tier, requests_per_hour, burst_size, enabled, created_at)
        SELECT 
            gen_random_uuid(),
            o.id,
            'standard',
            1000,
            100,
            true,
            NOW()
        FROM organisations o
        WHERE NOT EXISTS (
            SELECT 1 FROM tenant_rate_limits trl WHERE trl.tenant_id = o.id
        )
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_rate_limit_metrics_period_tenant', 'rate_limit_metrics')
    op.drop_index('idx_rate_limit_violations_severity', 'rate_limit_violations')
    op.drop_index('idx_rate_limit_violations_time_tenant', 'rate_limit_violations')
    op.drop_index('idx_tenant_rate_limits_emergency', 'tenant_rate_limits')
    op.drop_index('idx_tenant_rate_limits_enabled', 'tenant_rate_limits')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_rate_limit_metrics_tenant_id', 'rate_limit_metrics', type_='foreignkey')
    op.drop_constraint('fk_rate_limit_violations_user_id', 'rate_limit_violations', type_='foreignkey')
    op.drop_constraint('fk_rate_limit_violations_tenant_id', 'rate_limit_violations', type_='foreignkey')
    op.drop_constraint('fk_tenant_rate_limits_updated_by', 'tenant_rate_limits', type_='foreignkey')
    op.drop_constraint('fk_tenant_rate_limits_created_by', 'tenant_rate_limits', type_='foreignkey')
    op.drop_constraint('fk_tenant_rate_limits_tenant_id', 'tenant_rate_limits', type_='foreignkey')
    
    # Drop unique constraints
    op.drop_constraint('uq_rate_limit_metrics_period', 'rate_limit_metrics', type_='unique')
    op.drop_constraint('uq_tenant_rate_limit', 'tenant_rate_limits', type_='unique')
    
    # Drop tables
    op.drop_table('rate_limit_metrics')
    op.drop_table('rate_limit_violations')
    op.drop_table('tenant_rate_limits')