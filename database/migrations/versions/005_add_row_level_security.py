"""Add Row Level Security policies for tenant isolation

Revision ID: 005
Revises: 004
Create Date: 2025-08-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '005_add_row_level_security'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Enable RLS and create tenant isolation policies."""
    
    # Enable Row Level Security on all tenant-scoped tables
    tables_with_rls = [
        'users',
        'audit_logs', 
        'feature_flag_usage',
        'feature_flag_overrides',
        'organisation_modules',
        'module_configurations',
        'module_usage_logs'
    ]
    
    for table_name in tables_with_rls:
        # Enable RLS on the table
        # Use safe string formatting with validated table names
        if table_name not in {'users', 'audit_logs', 'feature_flag_usage', 'feature_flag_overrides', 
                             'organisation_modules', 'module_configurations', 'module_usage_logs'}:
            raise ValueError(f"Invalid table name for RLS: {table_name}")
            
        op.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
        
        # Create policy for regular users - they can only access their organisation's data
        op.execute(text(f"""
            CREATE POLICY tenant_isolation_{table_name} ON {table_name}
                FOR ALL TO authenticated
                USING (organisation_id = current_setting('app.current_tenant_id')::uuid)
        """))
        
        # Create policy for super admins - they can access all data when explicitly allowed
        op.execute(text(f"""
            CREATE POLICY super_admin_access_{table_name} ON {table_name}
                FOR ALL TO authenticated
                USING (
                    current_setting('app.current_user_role', true) = 'super_admin'
                    AND current_setting('app.allow_cross_tenant', true) = 'true'
                )
        """))
    
    # Add indexes on organisation_id columns for performance (if not already present)
    # Note: These might already exist, so we'll use IF NOT EXISTS where supported
    performance_indexes = [
        ('users', 'idx_users_organisation_id'),
        ('audit_logs', 'idx_audit_logs_organisation_id'),
        ('feature_flag_usage', 'idx_feature_flag_usage_organisation_id'),
        ('feature_flag_overrides', 'idx_feature_flag_overrides_organisation_id'),
        ('organisation_modules', 'idx_organisation_modules_organisation_id'),
        ('module_configurations', 'idx_module_configurations_organisation_id'),
        ('module_usage_logs', 'idx_module_usage_logs_organisation_id')
    ]
    
    for table_name, index_name in performance_indexes:
        try:
            # Validate table and index names to prevent injection
            if table_name not in {'users', 'audit_logs', 'feature_flag_usage', 'feature_flag_overrides', 
                                 'organisation_modules', 'module_configurations', 'module_usage_logs'}:
                raise ValueError(f"Invalid table name for index: {table_name}")
            if not index_name.startswith('idx_') or not index_name.endswith('_organisation_id'):
                raise ValueError(f"Invalid index name format: {index_name}")
                
            op.execute(text(f"""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} 
                ON {table_name} (organisation_id)
            """))
        except Exception:
            # Index might already exist, continue with migration
            pass

    # Create helper function to set tenant context
    op.execute(text("""
        CREATE OR REPLACE FUNCTION set_tenant_context(
            tenant_id uuid,
            user_role text DEFAULT 'viewer',
            allow_cross_tenant boolean DEFAULT false
        ) RETURNS void AS $$
        BEGIN
            -- Validate user role to prevent injection
            IF user_role NOT IN ('admin', 'analyst', 'viewer') THEN
                RAISE EXCEPTION 'Invalid user role: %', user_role;
            END IF;
            
            PERFORM set_config('app.current_tenant_id', tenant_id::text, true);
            PERFORM set_config('app.current_user_role', user_role, true);
            PERFORM set_config('app.allow_cross_tenant', allow_cross_tenant::text, true);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER
    """))

    # Create helper function to clear tenant context
    op.execute(text("""
        CREATE OR REPLACE FUNCTION clear_tenant_context() RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.current_tenant_id', null, true);
            PERFORM set_config('app.current_user_role', null, true);
            PERFORM set_config('app.allow_cross_tenant', null, true);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER
    """))


def downgrade():
    """Disable RLS and drop tenant isolation policies."""
    
    # Drop helper functions
    op.execute("DROP FUNCTION IF EXISTS set_tenant_context(uuid, text, boolean);")
    op.execute("DROP FUNCTION IF EXISTS clear_tenant_context();")
    
    # Drop RLS policies and disable RLS
    tables_with_rls = [
        'users',
        'audit_logs',
        'feature_flag_usage', 
        'feature_flag_overrides',
        'organisation_modules',
        'module_configurations',
        'module_usage_logs'
    ]
    
    for table_name in tables_with_rls:
        # Validate table name to prevent injection
        if table_name not in {'users', 'audit_logs', 'feature_flag_usage', 'feature_flag_overrides', 
                             'organisation_modules', 'module_configurations', 'module_usage_logs'}:
            raise ValueError(f"Invalid table name for RLS downgrade: {table_name}")
            
        # Drop policies
        op.execute(text(f"DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name}"))
        op.execute(text(f"DROP POLICY IF EXISTS super_admin_access_{table_name} ON {table_name}"))
        
        # Disable RLS
        op.execute(text(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY"))
    
    # Drop performance indexes (optional - they don't hurt to keep)
    performance_indexes = [
        'idx_users_organisation_id',
        'idx_audit_logs_organisation_id',
        'idx_feature_flag_usage_organisation_id',
        'idx_feature_flag_overrides_organisation_id',
        'idx_organisation_modules_organisation_id',
        'idx_module_configurations_organisation_id',
        'idx_module_usage_logs_organisation_id'
    ]
    
    for index_name in performance_indexes:
        # Validate index name to prevent injection
        if not index_name.startswith('idx_') or not index_name.endswith('_organisation_id'):
            raise ValueError(f"Invalid index name format for drop: {index_name}")
            
        op.execute(text(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}"))