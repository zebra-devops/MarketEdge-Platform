"""Add security constraints and indexes with defensive migration patterns.

Revision ID: 004
Revises: 003
Create Date: 2025-08-06 10:00:00.000000

This migration adds security constraints and performance indexes with comprehensive
prerequisite validation and fail-fast mechanisms to prevent partial failures.
"""
from alembic import op
import sqlalchemy as sa
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Apply security constraints and indexes with defensive validation."""
    from database.migrations.utils import get_validator, fail_fast

    print("\n" + "="*60)
    print("MIGRATION 004: ADDING SECURITY CONSTRAINTS")
    print("="*60)

    # Initialize validator
    validator = get_validator()

    # Print current migration status
    validator.print_migration_status()

    # Define all prerequisites for this migration
    required_tables = {
        'module_usage_logs',
        'feature_flag_usage',
        'organisation_modules',
        'feature_flags',
        'audit_logs',
        'competitive_factor_templates',
        'sic_codes'
    }

    # Define required columns for each table
    required_columns = {
        'feature_flags': ['flag_key', 'scope', 'is_enabled', 'rollout_percentage'],
        'audit_logs': ['user_id', 'action', 'timestamp'],
        'module_usage_logs': ['timestamp', 'module_id', 'organisation_id'],
        'feature_flag_usage': ['feature_flag_id', 'accessed_at', 'organisation_id'],
        'organisation_modules': ['organisation_id', 'is_enabled'],
        'competitive_factor_templates': ['weight'],
        'sic_codes': ['code']
    }

    # Optional columns that we'll check but won't fail on
    optional_columns = {
        'feature_flags': ['module_id'],
        'audit_logs': ['resource_type', 'resource_id']
    }

    try:
        # Validate all required prerequisites
        print("\nValidating prerequisites...")
        validator.validate_prerequisites(
            required_tables=required_tables,
            required_columns=required_columns,
            migration_id='004'
        )

        # Check optional columns separately
        print("\nChecking optional columns...")
        optional_status = {}
        for table, columns in optional_columns.items():
            if validator.table_exists(table):
                column_status = validator.columns_exist(table, columns)
                optional_status[table] = column_status
                for col, exists in column_status.items():
                    status = "present" if exists else "missing (will skip related indexes)"
                    print(f"  {table}.{col}: {status}")
            else:
                print(f"  Table '{table}' not found - skipping optional columns")

        # Now apply all changes with defensive patterns
        print("\n" + "-"*40)
        print("APPLYING INDEXES AND CONSTRAINTS")
        print("-"*40)

        # Feature flags indexes
        print("\nFeature flags indexes:")
        validator.safe_create_index(
            'idx_feature_flags_unique_scope',
            'feature_flags',
            ['flag_key', 'scope']
        )

        validator.safe_create_index(
            'idx_feature_flags_scope_enabled',
            'feature_flags',
            ['scope', 'is_enabled']
        )

        # Only create module index if module_id column exists
        if optional_status.get('feature_flags', {}).get('module_id', False):
            validator.safe_create_index(
                'idx_feature_flags_module_enabled',
                'feature_flags',
                ['module_id', 'is_enabled']
            )

        # Audit logs indexes
        print("\nAudit logs indexes:")
        validator.safe_create_index(
            'idx_audit_logs_user_action',
            'audit_logs',
            ['user_id', 'action']
        )

        validator.safe_create_index(
            'idx_audit_logs_timestamp_action',
            'audit_logs',
            ['timestamp', 'action']
        )

        # Only create resource index if both columns exist
        audit_has_resource = (
            optional_status.get('audit_logs', {}).get('resource_type', False) and
            optional_status.get('audit_logs', {}).get('resource_id', False)
        )
        if audit_has_resource:
            validator.safe_create_index(
                'idx_audit_logs_resource',
                'audit_logs',
                ['resource_type', 'resource_id']
            )

        # Module usage logs indexes
        print("\nModule usage logs indexes:")
        validator.safe_create_index(
            'idx_module_usage_logs_timestamp',
            'module_usage_logs',
            ['timestamp']
        )

        validator.safe_create_index(
            'idx_module_usage_logs_module',
            'module_usage_logs',
            ['module_id', 'organisation_id']
        )

        # Feature flag usage indexes
        print("\nFeature flag usage indexes:")
        validator.safe_create_index(
            'idx_feature_flag_usage_flag',
            'feature_flag_usage',
            ['feature_flag_id', 'accessed_at']
        )

        validator.safe_create_index(
            'idx_feature_flag_usage_org',
            'feature_flag_usage',
            ['organisation_id', 'accessed_at']
        )

        # Organisation modules indexes
        print("\nOrganisation modules indexes:")
        validator.safe_create_index(
            'idx_organisation_modules_enabled',
            'organisation_modules',
            ['organisation_id', 'is_enabled']
        )

        # Check constraints
        print("\nCheck constraints:")
        validator.safe_create_check_constraint(
            'chk_feature_flags_rollout_percentage',
            'feature_flags',
            'rollout_percentage >= 0 AND rollout_percentage <= 100'
        )

        validator.safe_create_check_constraint(
            'chk_competitive_factor_templates_weight',
            'competitive_factor_templates',
            'weight >= 0 AND weight <= 100'
        )

        validator.safe_create_check_constraint(
            'chk_sic_codes_code_format',
            'sic_codes',
            "code ~ '^[0-9]{4,5}$'"
        )

        print("\n" + "="*60)
        print("MIGRATION 004 COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")

    except Exception as e:
        # Enhanced error reporting
        print("\n" + "!"*60)
        print("MIGRATION 004 FAILED")
        print("!"*60)
        print(str(e))

        # Add additional diagnostic information
        print("\nDIAGNOSTIC INFORMATION:")
        status = validator.get_migration_status()
        print(f"  Current revision: {status['current_revision'] or 'None'}")
        print(f"  Tables found: {len(status['tables'])}")
        print(f"  Expected tables: {len(required_tables)}")

        missing_tables = required_tables - set(status['tables'])
        if missing_tables:
            print(f"  Missing tables: {sorted(missing_tables)}")

        print("\nRECOMMENDED ACTIONS:")
        print("  1. Check migration history: alembic history")
        print("  2. Check current state: alembic current")
        print("  3. If tables are missing, check if previous migrations ran:")
        print("     alembic show 003")
        print("  4. For emergency repair, create a sync migration:")
        print("     python database/create_sync_migration.py")
        print("!"*60 + "\n")

        raise


def downgrade():
    """Remove security constraints and indexes with defensive patterns."""
    from database.migrations.utils import get_validator

    print("\n" + "="*60)
    print("MIGRATION 004: REMOVING SECURITY CONSTRAINTS (DOWNGRADE)")
    print("="*60)

    # Initialize validator
    validator = get_validator()

    # Drop check constraints (safe - won't error if they don't exist)
    print("\nDropping check constraints...")
    validator.safe_drop_constraint('chk_sic_codes_code_format', 'sic_codes')
    validator.safe_drop_constraint('chk_competitive_factor_templates_weight', 'competitive_factor_templates')
    validator.safe_drop_constraint('chk_feature_flags_rollout_percentage', 'feature_flags')

    # Drop indexes (safe - won't error if they don't exist)
    print("\nDropping indexes...")

    # Organisation modules indexes
    validator.safe_drop_index('idx_organisation_modules_enabled', 'organisation_modules')

    # Feature flag usage indexes
    validator.safe_drop_index('idx_feature_flag_usage_org', 'feature_flag_usage')
    validator.safe_drop_index('idx_feature_flag_usage_flag', 'feature_flag_usage')

    # Module usage logs indexes
    validator.safe_drop_index('idx_module_usage_logs_module', 'module_usage_logs')
    validator.safe_drop_index('idx_module_usage_logs_timestamp', 'module_usage_logs')

    # Audit logs indexes
    validator.safe_drop_index('idx_audit_logs_timestamp_action', 'audit_logs')
    validator.safe_drop_index('idx_audit_logs_resource', 'audit_logs')
    validator.safe_drop_index('idx_audit_logs_user_action', 'audit_logs')

    # Feature flags indexes
    validator.safe_drop_index('idx_feature_flags_scope_enabled', 'feature_flags')
    validator.safe_drop_index('idx_feature_flags_module_enabled', 'feature_flags')
    validator.safe_drop_index('idx_feature_flags_unique_scope', 'feature_flags')

    print("\n" + "="*60)
    print("MIGRATION 004 DOWNGRADE COMPLETED")
    print("="*60 + "\n")