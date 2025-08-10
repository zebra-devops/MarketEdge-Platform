"""Add security constraints and indexes

Revision ID: 004
Revises: 003
Create Date: 2025-08-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add unique constraint for feature flag scopes
    op.create_index('idx_feature_flags_unique_scope', 'feature_flags', ['flag_key', 'scope'])
    
    # Add composite indexes for performance
    op.create_index('idx_feature_flags_module_enabled', 'feature_flags', ['module_id', 'is_enabled'])
    op.create_index('idx_feature_flags_scope_enabled', 'feature_flags', ['scope', 'is_enabled'])
    
    # Add audit log indexes for performance
    op.create_index('idx_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_timestamp_action', 'audit_logs', ['timestamp', 'action'])
    
    # Add module usage indexes
    op.create_index('idx_module_usage_logs_timestamp', 'module_usage_logs', ['timestamp'])
    op.create_index('idx_module_usage_logs_module', 'module_usage_logs', ['module_id', 'organisation_id'])
    
    # Add feature flag usage indexes
    op.create_index('idx_feature_flag_usage_flag', 'feature_flag_usage', ['feature_flag_id', 'accessed_at'])
    op.create_index('idx_feature_flag_usage_org', 'feature_flag_usage', ['organisation_id', 'accessed_at'])
    
    # Add organisation module indexes
    op.create_index('idx_organisation_modules_enabled', 'organisation_modules', ['organisation_id', 'is_enabled'])
    
    # Add check constraints for data validation
    op.create_check_constraint(
        'chk_feature_flags_rollout_percentage',
        'feature_flags',
        'rollout_percentage >= 0 AND rollout_percentage <= 100'
    )
    
    op.create_check_constraint(
        'chk_competitive_factor_templates_weight',
        'competitive_factor_templates',
        'weight >= 0.0 AND weight <= 1.0'
    )
    
    op.create_check_constraint(
        'chk_sic_codes_code_format',
        'sic_codes',
        "code ~ '^[0-9]{4,5}$'"
    )


def downgrade():
    # Drop check constraints
    op.drop_constraint('chk_sic_codes_code_format', 'sic_codes')
    op.drop_constraint('chk_competitive_factor_templates_weight', 'competitive_factor_templates')
    op.drop_constraint('chk_feature_flags_rollout_percentage', 'feature_flags')
    
    # Drop indexes
    op.drop_index('idx_organisation_modules_enabled', table_name='organisation_modules')
    op.drop_index('idx_feature_flag_usage_org', table_name='feature_flag_usage')
    op.drop_index('idx_feature_flag_usage_flag', table_name='feature_flag_usage')
    op.drop_index('idx_module_usage_logs_module', table_name='module_usage_logs')
    op.drop_index('idx_module_usage_logs_timestamp', table_name='module_usage_logs')
    op.drop_index('idx_audit_logs_timestamp_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_resource', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_action', table_name='audit_logs')
    op.drop_index('idx_feature_flags_scope_enabled', table_name='feature_flags')
    op.drop_index('idx_feature_flags_module_enabled', table_name='feature_flags')
    op.drop_index('idx_feature_flags_unique_scope', table_name='feature_flags')