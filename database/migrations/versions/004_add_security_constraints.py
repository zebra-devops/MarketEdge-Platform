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
    # Check if tables and columns exist before creating indexes
    import sqlalchemy as sa
    from alembic import context

    # Get connection to check table and column existence
    connection = context.get_bind()

    # Check if tables exist
    result = connection.execute(sa.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('module_usage_logs', 'feature_flag_usage', 'organisation_modules', 'feature_flags', 'audit_logs', 'competitive_factor_templates', 'sic_codes')
    """))

    existing_tables = {row[0] for row in result.fetchall()}

    module_usage_logs_exists = 'module_usage_logs' in existing_tables
    feature_flag_usage_exists = 'feature_flag_usage' in existing_tables
    organisation_modules_exists = 'organisation_modules' in existing_tables
    feature_flags_exists = 'feature_flags' in existing_tables
    audit_logs_exists = 'audit_logs' in existing_tables
    competitive_factor_templates_exists = 'competitive_factor_templates' in existing_tables
    sic_codes_exists = 'sic_codes' in existing_tables

    print(f"DEBUG: Table existence check - module_usage_logs: {module_usage_logs_exists}, feature_flag_usage: {feature_flag_usage_exists}, organisation_modules: {organisation_modules_exists}")

    # Check if module_id column exists in feature_flags table (only if table exists)
    module_id_exists = False
    if feature_flags_exists:
        result = connection.execute(sa.text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'feature_flags'
            AND column_name = 'module_id'
        """))
        module_id_exists = result.fetchone() is not None

    # Check if resource_type and resource_id columns exist in audit_logs table (only if table exists)
    resource_type_exists = False
    resource_id_exists = False
    if audit_logs_exists:
        result = connection.execute(sa.text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'audit_logs'
            AND column_name IN ('resource_type', 'resource_id')
        """))

        audit_columns = {row[0] for row in result.fetchall()}
        resource_type_exists = 'resource_type' in audit_columns
        resource_id_exists = 'resource_id' in audit_columns

    # Add unique constraint for feature flag scopes (only if table exists)
    if feature_flags_exists:
        op.create_index('idx_feature_flags_unique_scope', 'feature_flags', ['flag_key', 'scope'])

        # Add composite indexes for performance
        if module_id_exists:
            op.create_index('idx_feature_flags_module_enabled', 'feature_flags', ['module_id', 'is_enabled'])
        else:
            print("WARNING: module_id column not found in feature_flags table - skipping module_id index")

        op.create_index('idx_feature_flags_scope_enabled', 'feature_flags', ['scope', 'is_enabled'])
    else:
        print("WARNING: feature_flags table not found - skipping all feature_flags indexes")

    # Add audit log indexes for performance (only if table exists)
    if audit_logs_exists:
        op.create_index('idx_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])

        # Only create resource index if both columns exist
        if resource_type_exists and resource_id_exists:
            op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
        else:
            print(f"WARNING: audit_logs columns missing - resource_type: {resource_type_exists}, resource_id: {resource_id_exists} - skipping resource index")

        op.create_index('idx_audit_logs_timestamp_action', 'audit_logs', ['timestamp', 'action'])
    else:
        print("WARNING: audit_logs table not found - skipping all audit_logs indexes")

    # Add module usage indexes (only if table exists)
    if module_usage_logs_exists:
        op.create_index('idx_module_usage_logs_timestamp', 'module_usage_logs', ['timestamp'])
        op.create_index('idx_module_usage_logs_module', 'module_usage_logs', ['module_id', 'organisation_id'])
    else:
        print("WARNING: module_usage_logs table not found - skipping module_usage_logs indexes")

    # Add feature flag usage indexes (only if table exists)
    if feature_flag_usage_exists:
        op.create_index('idx_feature_flag_usage_flag', 'feature_flag_usage', ['feature_flag_id', 'accessed_at'])
        op.create_index('idx_feature_flag_usage_org', 'feature_flag_usage', ['organisation_id', 'accessed_at'])
    else:
        print("WARNING: feature_flag_usage table not found - skipping feature_flag_usage indexes")

    # Add organisation module indexes (only if table exists)
    if organisation_modules_exists:
        op.create_index('idx_organisation_modules_enabled', 'organisation_modules', ['organisation_id', 'is_enabled'])
    else:
        print("WARNING: organisation_modules table not found - skipping organisation_modules indexes")

    # Add check constraints for data validation (only if tables exist)
    if feature_flags_exists:
        op.create_check_constraint(
            'chk_feature_flags_rollout_percentage',
            'feature_flags',
            'rollout_percentage >= 0 AND rollout_percentage <= 100'
        )
    else:
        print("WARNING: feature_flags table not found - skipping feature_flags check constraint")

    if competitive_factor_templates_exists:
        op.create_check_constraint(
            'chk_competitive_factor_templates_weight',
            'competitive_factor_templates',
            'weight >= 0 AND weight <= 100'
        )
    else:
        print("WARNING: competitive_factor_templates table not found - skipping competitive_factor_templates check constraint")

    if sic_codes_exists:
        op.create_check_constraint(
            'chk_sic_codes_code_format',
            'sic_codes',
            "code ~ '^[0-9]{4,5}$'"
        )
    else:
        print("WARNING: sic_codes table not found - skipping sic_codes check constraint")


def downgrade():
    # Check if tables and indexes exist before dropping
    import sqlalchemy as sa
    from alembic import context

    connection = context.get_bind()

    # Check if tables exist
    result = connection.execute(sa.text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('module_usage_logs', 'feature_flag_usage', 'organisation_modules', 'feature_flags', 'audit_logs', 'competitive_factor_templates', 'sic_codes')
    """))

    existing_tables = {row[0] for row in result.fetchall()}

    # Check if indexes exist
    result = connection.execute(sa.text("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename IN ('audit_logs', 'feature_flags')
        AND indexname IN ('idx_audit_logs_resource', 'idx_feature_flags_module_enabled')
    """))

    existing_indexes = {row[0] for row in result.fetchall()}

    # Drop check constraints (only if tables exist)
    if 'sic_codes' in existing_tables:
        try:
            op.drop_constraint('chk_sic_codes_code_format', 'sic_codes')
        except Exception as e:
            print(f"WARNING: Could not drop sic_codes constraint: {e}")

    if 'competitive_factor_templates' in existing_tables:
        try:
            op.drop_constraint('chk_competitive_factor_templates_weight', 'competitive_factor_templates')
        except Exception as e:
            print(f"WARNING: Could not drop competitive_factor_templates constraint: {e}")

    if 'feature_flags' in existing_tables:
        try:
            op.drop_constraint('chk_feature_flags_rollout_percentage', 'feature_flags')
        except Exception as e:
            print(f"WARNING: Could not drop feature_flags constraint: {e}")

    # Drop indexes (only if tables exist)
    if 'organisation_modules' in existing_tables:
        try:
            op.drop_index('idx_organisation_modules_enabled', table_name='organisation_modules')
        except Exception as e:
            print(f"WARNING: Could not drop organisation_modules index: {e}")

    if 'feature_flag_usage' in existing_tables:
        try:
            op.drop_index('idx_feature_flag_usage_org', table_name='feature_flag_usage')
            op.drop_index('idx_feature_flag_usage_flag', table_name='feature_flag_usage')
        except Exception as e:
            print(f"WARNING: Could not drop feature_flag_usage indexes: {e}")

    if 'module_usage_logs' in existing_tables:
        try:
            op.drop_index('idx_module_usage_logs_module', table_name='module_usage_logs')
            op.drop_index('idx_module_usage_logs_timestamp', table_name='module_usage_logs')
        except Exception as e:
            print(f"WARNING: Could not drop module_usage_logs indexes: {e}")

    if 'audit_logs' in existing_tables:
        try:
            op.drop_index('idx_audit_logs_timestamp_action', table_name='audit_logs')

            # Only drop resource index if it was created
            if 'idx_audit_logs_resource' in existing_indexes:
                op.drop_index('idx_audit_logs_resource', table_name='audit_logs')

            op.drop_index('idx_audit_logs_user_action', table_name='audit_logs')
        except Exception as e:
            print(f"WARNING: Could not drop audit_logs indexes: {e}")

    if 'feature_flags' in existing_tables:
        try:
            op.drop_index('idx_feature_flags_scope_enabled', table_name='feature_flags')

            # Only drop module_enabled index if it was created
            if 'idx_feature_flags_module_enabled' in existing_indexes:
                op.drop_index('idx_feature_flags_module_enabled', table_name='feature_flags')

            op.drop_index('idx_feature_flags_unique_scope', table_name='feature_flags')
        except Exception as e:
            print(f"WARNING: Could not drop feature_flags indexes: {e}")