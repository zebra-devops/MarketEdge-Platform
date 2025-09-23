"""Add Row Level Security policies for tenant isolation with defensive migration patterns.

Revision ID: 005_add_row_level_security
Revises: 004
Create Date: 2025-08-08 12:00:00.000000

This migration enables Row Level Security (RLS) for multi-tenant data isolation
with comprehensive prerequisite validation and fail-fast mechanisms.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# revision identifiers, used by Alembic.
revision = '005_add_row_level_security'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Enable RLS and create tenant isolation policies with defensive validation."""
    from database.migrations.utils import get_validator, fail_fast

    print("\n" + "="*60)
    print("MIGRATION 005: ENABLING ROW LEVEL SECURITY")
    print("="*60)

    # Initialize validator
    validator = get_validator()

    # Print current migration status
    validator.print_migration_status()

    # Define all tables that need RLS
    tables_with_rls = [
        'users',
        'audit_logs',
        'feature_flag_usage',
        'feature_flag_overrides',
        'organisation_modules',
        'module_configurations',
        'module_usage_logs'
    ]

    # Define required columns for RLS policies
    required_columns = {}
    for table in tables_with_rls:
        required_columns[table] = ['organisation_id']

    try:
        # Validate prerequisites
        print("\nValidating prerequisites...")

        # Check which tables exist
        existing_tables = set()
        missing_tables = set()

        for table_name in tables_with_rls:
            if validator.table_exists(table_name):
                existing_tables.add(table_name)
            else:
                missing_tables.add(table_name)

        if not existing_tables:
            fail_fast(
                "No tables found for RLS implementation!",
                [
                    "Ensure previous migrations have been applied",
                    "Run: alembic upgrade 004",
                    "Check migration history: alembic history",
                    "Verify database connection is correct"
                ]
            )

        if missing_tables:
            print(f"\nWARNING: Some tables not found (will skip): {sorted(missing_tables)}")
            print("These tables may be created in later migrations.")

        print(f"\nFound {len(existing_tables)} tables for RLS implementation:")
        for table in sorted(existing_tables):
            print(f"  - {table}")

        # Validate columns for existing tables
        print("\nValidating required columns...")
        tables_missing_org_id = []

        for table_name in existing_tables:
            if not validator.column_exists(table_name, 'organisation_id'):
                tables_missing_org_id.append(table_name)

        if tables_missing_org_id:
            print(f"\nWARNING: Tables without organisation_id column (will skip RLS):")
            for table in tables_missing_org_id:
                print(f"  - {table}")
                existing_tables.discard(table)

        if not existing_tables:
            fail_fast(
                "No tables with organisation_id column found for RLS!",
                [
                    "Check if tables have been properly created with tenant support",
                    "Verify organisation_id columns exist in tables",
                    "Run database validation: python database/validate_schema.py --check"
                ]
            )

        # Apply RLS to tables with organisation_id
        print("\n" + "-"*40)
        print("APPLYING ROW LEVEL SECURITY")
        print("-"*40)

        successful_rls = []
        failed_rls = []

        for table_name in sorted(existing_tables):
            try:
                print(f"\nEnabling RLS on '{table_name}'...")

                # Enable RLS on the table
                op.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))

                # Create tenant isolation policy
                policy_name = f"tenant_isolation_{table_name}"
                op.execute(text(f"""
                    CREATE POLICY {policy_name} ON {table_name}
                        FOR ALL TO public
                        USING (organisation_id = current_setting('app.current_tenant_id', true)::uuid)
                """))
                print(f"  Created policy: {policy_name}")

                # Create super admin access policy
                admin_policy_name = f"super_admin_access_{table_name}"
                op.execute(text(f"""
                    CREATE POLICY {admin_policy_name} ON {table_name}
                        FOR ALL TO public
                        USING (
                            current_setting('app.current_user_role', true) = 'super_admin'
                            AND current_setting('app.allow_cross_tenant', true) = 'true'
                        )
                """))
                print(f"  Created policy: {admin_policy_name}")

                successful_rls.append(table_name)

            except Exception as e:
                print(f"  ERROR: Failed to apply RLS to '{table_name}': {e}")
                failed_rls.append(table_name)

        # Create performance indexes for organisation_id columns
        print("\n" + "-"*40)
        print("CREATING PERFORMANCE INDEXES")
        print("-"*40)

        for table_name in successful_rls:
            index_name = f"idx_{table_name}_organisation_id"
            validator.safe_create_index(
                index_name,
                table_name,
                ['organisation_id']
            )

        # Create helper functions for tenant context
        print("\n" + "-"*40)
        print("CREATING HELPER FUNCTIONS")
        print("-"*40)

        try:
            # Create set_tenant_context function
            op.execute(text("""
                CREATE OR REPLACE FUNCTION set_tenant_context(
                    tenant_id uuid,
                    user_role text DEFAULT 'viewer',
                    allow_cross_tenant boolean DEFAULT false
                ) RETURNS void AS $function$
                BEGIN
                    -- Validate user role to prevent injection
                    IF user_role NOT IN ('super_admin', 'admin', 'analyst', 'viewer', 'user') THEN
                        RAISE EXCEPTION 'Invalid user role: %', user_role;
                    END IF;

                    PERFORM set_config('app.current_tenant_id', tenant_id::text, true);
                    PERFORM set_config('app.current_user_role', user_role, true);
                    PERFORM set_config('app.allow_cross_tenant', allow_cross_tenant::text, true);
                END;
                $function$ LANGUAGE plpgsql SECURITY DEFINER
            """))
            print("  Created function: set_tenant_context")

            # Create clear_tenant_context function
            op.execute(text("""
                CREATE OR REPLACE FUNCTION clear_tenant_context() RETURNS void AS $function$
                BEGIN
                    PERFORM set_config('app.current_tenant_id', null, true);
                    PERFORM set_config('app.current_user_role', null, true);
                    PERFORM set_config('app.allow_cross_tenant', null, true);
                END;
                $function$ LANGUAGE plpgsql SECURITY DEFINER
            """))
            print("  Created function: clear_tenant_context")

        except Exception as e:
            print(f"  WARNING: Helper functions may already exist: {e}")

        # Summary
        print("\n" + "="*60)
        print("MIGRATION 005 SUMMARY")
        print("="*60)

        if successful_rls:
            print(f"\nSuccessfully applied RLS to {len(successful_rls)} tables:")
            for table in successful_rls:
                print(f"  ✓ {table}")

        if failed_rls:
            print(f"\nFailed to apply RLS to {len(failed_rls)} tables:")
            for table in failed_rls:
                print(f"  ✗ {table}")

        if missing_tables:
            print(f"\nSkipped {len(missing_tables)} missing tables:")
            for table in sorted(missing_tables):
                print(f"  - {table}")

        print("\nRECOMMENDATIONS:")
        print("  1. Test RLS policies with: SELECT set_tenant_context('org-uuid')")
        print("  2. Verify tenant isolation is working correctly")
        print("  3. Monitor query performance with new indexes")

        if failed_rls:
            print("\n  WARNING: Some tables failed RLS application.")
            print("  Review errors and consider creating a repair migration.")

        print("="*60 + "\n")

    except Exception as e:
        # Enhanced error reporting
        print("\n" + "!"*60)
        print("MIGRATION 005 FAILED")
        print("!"*60)
        print(str(e))

        print("\nDIAGNOSTIC INFORMATION:")
        status = validator.get_migration_status()
        print(f"  Current revision: {status['current_revision'] or 'None'}")
        print(f"  Total tables in database: {len(status['tables'])}")

        print("\nRECOMMENDED ACTIONS:")
        print("  1. Review the error message above")
        print("  2. Check if previous migration (004) completed successfully")
        print("  3. Verify tables have organisation_id columns")
        print("  4. For missing prerequisites, run:")
        print("     python database/create_repair_migration.py")
        print("!"*60 + "\n")

        raise


def downgrade():
    """Disable RLS and drop tenant isolation policies with defensive patterns."""
    from database.migrations.utils import get_validator

    print("\n" + "="*60)
    print("MIGRATION 005: DISABLING ROW LEVEL SECURITY (DOWNGRADE)")
    print("="*60)

    # Initialize validator
    validator = get_validator()

    # Drop helper functions
    print("\nDropping helper functions...")
    try:
        op.execute(text("DROP FUNCTION IF EXISTS set_tenant_context(uuid, text, boolean);"))
        print("  Dropped function: set_tenant_context")
    except Exception as e:
        print(f"  WARNING: Could not drop set_tenant_context: {e}")

    try:
        op.execute(text("DROP FUNCTION IF EXISTS clear_tenant_context();"))
        print("  Dropped function: clear_tenant_context")
    except Exception as e:
        print(f"  WARNING: Could not drop clear_tenant_context: {e}")

    # Define tables that might have RLS
    tables_with_rls = [
        'users',
        'audit_logs',
        'feature_flag_usage',
        'feature_flag_overrides',
        'organisation_modules',
        'module_configurations',
        'module_usage_logs'
    ]

    # Disable RLS policies for existing tables
    print("\nDisabling Row Level Security...")
    for table_name in tables_with_rls:
        if validator.table_exists(table_name):
            try:
                # Drop policies
                op.execute(text(f"DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name}"))
                op.execute(text(f"DROP POLICY IF EXISTS super_admin_access_{table_name} ON {table_name}"))

                # Disable RLS
                op.execute(text(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY"))
                print(f"  Disabled RLS on: {table_name}")

            except Exception as e:
                print(f"  WARNING: Could not disable RLS on '{table_name}': {e}")
        else:
            print(f"  Skipped (table not found): {table_name}")

    # Drop performance indexes
    print("\nDropping performance indexes...")
    for table_name in tables_with_rls:
        index_name = f"idx_{table_name}_organisation_id"
        validator.safe_drop_index(index_name, table_name)

    print("\n" + "="*60)
    print("MIGRATION 005 DOWNGRADE COMPLETED")
    print("="*60 + "\n")