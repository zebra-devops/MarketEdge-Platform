"""Add Phase 3 enhancements: feature flags, SIC codes, modules, audit logging

Revision ID: 003
Revises: 002
Create Date: 2025-08-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create SIC Codes table
    op.create_table('sic_codes',
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('section', sa.String(length=1), nullable=False),
        sa.Column('division', sa.String(length=2), nullable=False),
        sa.Column('group', sa.String(length=5), nullable=False),
        sa.Column('class_code', sa.String(length=5), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_supported', sa.Boolean(), nullable=False),
        sa.Column('competitive_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('default_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('analytics_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('code')
    )
    op.create_index(op.f('ix_sic_codes_section'), 'sic_codes', ['section'], unique=False)
    op.create_index(op.f('ix_sic_codes_division'), 'sic_codes', ['division'], unique=False)
    op.create_index(op.f('ix_sic_codes_group'), 'sic_codes', ['group'], unique=False)
    op.create_index(op.f('ix_sic_codes_class_code'), 'sic_codes', ['class_code'], unique=False)

    # Create Analytics Modules table
    op.create_table('analytics_modules',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('module_type', sa.Enum('CORE', 'ANALYTICS', 'INTEGRATION', 'VISUALIZATION', 'REPORTING', 'AI_ML', name='moduletype'), nullable=False),
        sa.Column('status', sa.Enum('DEVELOPMENT', 'TESTING', 'ACTIVE', 'DEPRECATED', 'RETIRED', name='modulestatus'), nullable=False),
        sa.Column('is_core', sa.Boolean(), nullable=False),
        sa.Column('requires_license', sa.Boolean(), nullable=False),
        sa.Column('entry_point', sa.String(length=500), nullable=False),
        sa.Column('config_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('default_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('min_data_requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('api_endpoints', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('frontend_components', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('documentation_url', sa.String(length=500), nullable=True),
        sa.Column('help_text', sa.Text(), nullable=True),
        sa.Column('pricing_tier', sa.String(length=50), nullable=True),
        sa.Column('license_requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Feature Flags table
    op.create_table('feature_flags',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('flag_key', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('rollout_percentage', sa.Integer(), nullable=False),
        sa.Column('scope', sa.Enum('GLOBAL', 'ORGANISATION', 'SECTOR', 'USER', name='featureflagscope'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'DEPRECATED', name='featureflagstatus'), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('allowed_sectors', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('blocked_sectors', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('module_id', sa.String(length=255), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feature_flags_flag_key'), 'feature_flags', ['flag_key'], unique=True)
    op.create_index(op.f('ix_feature_flags_module_id'), 'feature_flags', ['module_id'], unique=False)

    # Create Audit Logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('action', sa.Enum('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'ENABLE', 'DISABLE', 'CONFIGURE', 'EXPORT', 'IMPORT', name='auditaction'), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='auditseverity'), nullable=False),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=255), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)

    # Create Sector Modules table
    op.create_table('sector_modules',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('sic_code', sa.String(length=10), nullable=False),
        sa.Column('module_id', sa.String(length=255), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['module_id'], ['analytics_modules.id'], ),
        sa.ForeignKeyConstraint(['sic_code'], ['sic_codes.code'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Organisation Modules table
    op.create_table('organisation_modules',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('module_id', sa.String(length=255), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('enabled_for_users', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('disabled_for_users', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('first_enabled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['module_id'], ['analytics_modules.id'], ),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Feature Flag Overrides table
    op.create_table('feature_flag_overrides',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('feature_flag_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['feature_flag_id'], ['feature_flags.id'], ),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Feature Flag Usage table
    op.create_table('feature_flag_usage',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('feature_flag_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('was_enabled', sa.Boolean(), nullable=False),
        sa.Column('evaluation_context', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('accessed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['feature_flag_id'], ['feature_flags.id'], ),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feature_flag_usage_accessed_at'), 'feature_flag_usage', ['accessed_at'], unique=False)

    # Create Module Configurations table
    op.create_table('module_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('module_id', sa.String(length=255), nullable=False),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('config_key', sa.String(length=255), nullable=False),
        sa.Column('config_value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('schema_version', sa.String(length=50), nullable=False),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['module_id'], ['analytics_modules.id'], ),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Module Usage Logs table
    op.create_table('module_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('module_id', sa.String(length=255), nullable=False),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('endpoint', sa.String(length=500), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['analytics_modules.id'], ),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_module_usage_logs_timestamp'), 'module_usage_logs', ['timestamp'], unique=False)

    # Create Competitive Factor Templates table
    op.create_table('competitive_factor_templates',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('sic_code', sa.String(length=10), nullable=False),
        sa.Column('factor_name', sa.String(length=255), nullable=False),
        sa.Column('factor_key', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('data_type', sa.String(length=50), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False),
        sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('is_visible', sa.Boolean(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['sic_code'], ['sic_codes.code'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Admin Actions table
    op.create_table('admin_actions',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('admin_user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('target_organisation_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('target_user_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('affected_users_count', sa.Integer(), nullable=False),
        sa.Column('affected_organisations_count', sa.Integer(), nullable=False),
        sa.Column('configuration_changes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('requires_approval', sa.Boolean(), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['target_organisation_id'], ['organisations.id'], ),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add SIC code column to organisations table
    op.add_column('organisations', sa.Column('sic_code', sa.String(length=10), nullable=True))
    op.create_foreign_key(None, 'organisations', 'sic_codes', ['sic_code'], ['code'])


def downgrade():
    # Remove SIC code column from organisations
    op.drop_constraint(None, 'organisations', type_='foreignkey')
    op.drop_column('organisations', 'sic_code')
    
    # Drop all new tables in reverse order
    op.drop_table('admin_actions')
    op.drop_table('competitive_factor_templates')
    op.drop_index(op.f('ix_module_usage_logs_timestamp'), table_name='module_usage_logs')
    op.drop_table('module_usage_logs')
    op.drop_table('module_configurations')
    op.drop_index(op.f('ix_feature_flag_usage_accessed_at'), table_name='feature_flag_usage')
    op.drop_table('feature_flag_usage')
    op.drop_table('feature_flag_overrides')
    op.drop_table('organisation_modules')
    op.drop_table('sector_modules')
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_feature_flags_module_id'), table_name='feature_flags')
    op.drop_index(op.f('ix_feature_flags_flag_key'), table_name='feature_flags')
    op.drop_table('feature_flags')
    op.drop_table('analytics_modules')
    op.drop_index(op.f('ix_sic_codes_class_code'), table_name='sic_codes')
    op.drop_index(op.f('ix_sic_codes_group'), table_name='sic_codes')
    op.drop_index(op.f('ix_sic_codes_division'), table_name='sic_codes')
    op.drop_index(op.f('ix_sic_codes_section'), table_name='sic_codes')
    op.drop_table('sic_codes')