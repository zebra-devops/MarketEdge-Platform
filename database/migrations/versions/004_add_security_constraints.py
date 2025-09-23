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
    # Check if module_id column exists before creating index
    import sqlalchemy as sa
    from alembic import context

    # Get connection to check column existence
    connection = context.get_bind()

    # Check if module_id column exists in feature_flags table
    result = connection.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'feature_flags'
        AND column_name = 'module_id'
    """))

    module_id_exists = result.fetchone() is not None

    # Check if resource_type and resource_id columns exist in audit_logs table
    result = connection.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'audit_logs'
        AND column_name IN ('resource_type', 'resource_id')
    """))

    audit_columns = {row[0] for row in result.fetchall()}
    resource_type_exists = 'resource_type' in audit_columns
    resource_id_exists = 'resource_id' in audit_columns

    # Add unique constraint for feature flag scopes
    op.create_index('idx_feature_flags_unique_scope', 'feature_flags', ['flag_key', 'scope'])

    # Add composite indexes for performance
    if module_id_exists:
        op.create_index('idx_feature_flags_module_enabled', 'feature_flags', ['module_id', 'is_enabled'])
    else:
        print("WARNING: module_id column not found in feature_flags table - skipping module_id index")

    op.create_index('idx_feature_flags_scope_enabled', 'feature_flags', ['scope', 'is_enabled'])
    
    # Add audit log indexes for performance
    op.create_index('idx_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])

    # Only create resource index if both columns exist
    if resource_type_exists and resource_id_exists:
        op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    else:
        print(f"WARNING: audit_logs columns missing - resource_type: {resource_type_exists}, resource_id: {resource_id_exists} - skipping resource index")

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
        'weight >= 0 AND weight <= 100'
    )
    
    op.create_check_constraint(
        'chk_sic_codes_code_format',
        'sic_codes',
        "code ~ '^[0-9]{4,5}$'"
    )


def downgrade():
    # Check if indexes exist before dropping
    import sqlalchemy as sa
    from alembic import context

    connection = context.get_bind()

    # Check if indexes exist
    result = connection.execute(sa.text("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename IN ('audit_logs', 'feature_flags')
        AND indexname IN ('idx_audit_logs_resource', 'idx_feature_flags_module_enabled')
    """))

    existing_indexes = {row[0] for row in result.fetchall()}

    # Drop check constraints
    op.drop_constraint('chk_sic_codes_code_format', 'sic_codes')
    op.drop_constraint('chk_competitive_factor_templates_weight', 'competitive_factor_templates')
    op.drop_constraint('chk_feature_flags_rollout_percentage', 'feature_flags')

    # Drop indexes (only if they exist)
    op.drop_index('idx_organisation_modules_enabled', table_name='organisation_modules')
    op.drop_index('idx_feature_flag_usage_org', table_name='feature_flag_usage')
    op.drop_index('idx_feature_flag_usage_flag', table_name='feature_flag_usage')
    op.drop_index('idx_module_usage_logs_module', table_name='module_usage_logs')
    op.drop_index('idx_module_usage_logs_timestamp', table_name='module_usage_logs')
    op.drop_index('idx_audit_logs_timestamp_action', table_name='audit_logs')

    # Only drop resource index if it was created
    if 'idx_audit_logs_resource' in existing_indexes:
        op.drop_index('idx_audit_logs_resource', table_name='audit_logs')

    op.drop_index('idx_audit_logs_user_action', table_name='audit_logs')
    op.drop_index('idx_feature_flags_scope_enabled', table_name='feature_flags')

    # Only drop module_enabled index if it was created
    if 'idx_feature_flags_module_enabled' in existing_indexes:
        op.drop_index('idx_feature_flags_module_enabled', table_name='feature_flags')

    op.drop_index('idx_feature_flags_unique_scope', table_name='feature_flags')