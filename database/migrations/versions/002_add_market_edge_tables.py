"""Add Market Edge tables

Revision ID: 002
Revises: 001
Create Date: 2025-07-31 11:30:00.000000

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
    # Create markets table
    op.create_table(
        'markets',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('geographic_bounds', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('competitor_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('tracking_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_markets_organisation_id', 'markets', ['organisation_id'])
    op.create_index('ix_markets_name', 'markets', ['name'])

    # Create competitors table
    op.create_table(
        'competitors',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('market_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('business_type', sa.String(length=100), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('locations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tracking_priority', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('market_share_estimate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_competitors_market_id', 'competitors', ['market_id'])
    op.create_index('ix_competitors_organisation_id', 'competitors', ['organisation_id'])
    op.create_index('ix_competitors_name', 'competitors', ['name'])

    # Create pricing_data table
    op.create_table(
        'pricing_data',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('competitor_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('market_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('product_service', sa.String(length=255), nullable=False),
        sa.Column('price_point', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='GBP'),
        sa.Column('date_collected', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_promotion', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('promotion_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['competitor_id'], ['competitors.id'], ),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pricing_data_competitor_id', 'pricing_data', ['competitor_id'])
    op.create_index('ix_pricing_data_market_id', 'pricing_data', ['market_id'])
    op.create_index('ix_pricing_data_product_service', 'pricing_data', ['product_service'])
    op.create_index('ix_pricing_data_date_collected', 'pricing_data', ['date_collected'])

    # Create market_alerts table
    op.create_table(
        'market_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('market_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('trigger_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_market_alerts_market_id', 'market_alerts', ['market_id'])
    op.create_index('ix_market_alerts_organisation_id', 'market_alerts', ['organisation_id'])
    op.create_index('ix_market_alerts_alert_type', 'market_alerts', ['alert_type'])
    op.create_index('ix_market_alerts_created_at', 'market_alerts', ['created_at'])

    # Create user_market_preferences table
    op.create_table(
        'user_market_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('market_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('dashboard_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('alert_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('favorite_competitors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'market_id', name='uq_user_market_preference')
    )
    op.create_index('ix_user_market_preferences_user_id', 'user_market_preferences', ['user_id'])
    op.create_index('ix_user_market_preferences_market_id', 'user_market_preferences', ['market_id'])

    # Create competitive_insights table
    op.create_table(
        'competitive_insights',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('market_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('insight_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('impact_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('confidence_level', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('data_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_competitive_insights_market_id', 'competitive_insights', ['market_id'])
    op.create_index('ix_competitive_insights_organisation_id', 'competitive_insights', ['organisation_id'])
    op.create_index('ix_competitive_insights_insight_type', 'competitive_insights', ['insight_type'])

    # Create market_analytics table
    op.create_table(
        'market_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('market_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('calculation_method', sa.String(length=100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_market_analytics_market_id', 'market_analytics', ['market_id'])
    op.create_index('ix_market_analytics_organisation_id', 'market_analytics', ['organisation_id'])
    op.create_index('ix_market_analytics_metric_type', 'market_analytics', ['metric_type'])
    op.create_index('ix_market_analytics_period_start', 'market_analytics', ['period_start'])


def downgrade() -> None:
    op.drop_table('market_analytics')
    op.drop_table('competitive_insights')
    op.drop_table('user_market_preferences')
    op.drop_table('market_alerts')
    op.drop_table('pricing_data')
    op.drop_table('competitors')
    op.drop_table('markets')