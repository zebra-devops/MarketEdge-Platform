"""Add rate limiting fields to organisations

Revision ID: 006_add_rate_limiting
Revises: 005_add_row_level_security
Create Date: 2025-01-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_add_rate_limiting'
down_revision: Union[str, None] = '005_add_row_level_security'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Import defensive migration utilities
    from database.migrations.utils import get_validator
    validator = get_validator()

    # Add rate limiting columns to organisations table using safe column addition
    validator.safe_add_column('organisations', sa.Column('rate_limit_per_hour', sa.Integer(), nullable=False, server_default='1000'))
    validator.safe_add_column('organisations', sa.Column('burst_limit', sa.Integer(), nullable=False, server_default='100'))
    validator.safe_add_column('organisations', sa.Column('rate_limit_enabled', sa.Boolean(), nullable=False, server_default='true'))

    # Set default rate limits based on subscription plan
    connection = op.get_bind()
    
    # Enterprise: 10000 requests/hour, 500 burst
    connection.execute(
        sa.text("""
            UPDATE organisations 
            SET rate_limit_per_hour = 10000, burst_limit = 500 
            WHERE subscription_plan = 'enterprise'
        """)
    )
    
    # Professional: 5000 requests/hour, 250 burst
    connection.execute(
        sa.text("""
            UPDATE organisations 
            SET rate_limit_per_hour = 5000, burst_limit = 250 
            WHERE subscription_plan = 'professional'
        """)
    )
    
    # Basic: 1000 requests/hour, 100 burst (already set as default)


def downgrade() -> None:
    # Import defensive migration utilities
    from database.migrations.utils import get_validator
    validator = get_validator()

    # Remove rate limiting columns safely (only if they exist)
    if validator.column_exists('organisations', 'rate_limit_enabled'):
        op.drop_column('organisations', 'rate_limit_enabled')
    if validator.column_exists('organisations', 'burst_limit'):
        op.drop_column('organisations', 'burst_limit')
    if validator.column_exists('organisations', 'rate_limit_per_hour'):
        op.drop_column('organisations', 'rate_limit_per_hour')