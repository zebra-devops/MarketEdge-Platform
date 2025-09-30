"""Add hierarchical organization structure and enhanced permissions

Revision ID: 008
Revises: 007
Create Date: 2025-08-14 10:00:00.000000

This migration adds:
- Hierarchical organization structure (Organization → Location → Department → User)
- Enhanced user roles with hierarchical permissions
- Industry configuration templates
- Permission resolution system
- Backward compatibility with existing system
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
import uuid

# revision identifiers, used by Alembic.
revision = '008_add_hierarchical_organizations'
down_revision = '007_add_industry_type'
branch_labels = None
depends_on = None


def upgrade():
    """Add hierarchical organization structure and enhanced permissions"""

    # Create enhanced user roles enum - check and create separately for idempotency
    conn = op.get_bind()
    result = conn.execute(text("SELECT COUNT(*) FROM pg_type WHERE typname = 'enhanceduserrole'"))
    exists = result.scalar() > 0

    if not exists:
        op.execute("CREATE TYPE enhanceduserrole AS ENUM ('super_admin', 'org_admin', 'location_manager', 'department_lead', 'user', 'viewer')")

    # Create hierarchy level enum - check and create separately for idempotency
    result = conn.execute(text("SELECT COUNT(*) FROM pg_type WHERE typname = 'hierarchylevel'"))
    exists = result.scalar() > 0

    if not exists:
        op.execute("CREATE TYPE hierarchylevel AS ENUM ('organization', 'location', 'department', 'user')")

    # Create permission scope enum - check and create separately for idempotency
    result = conn.execute(text("SELECT COUNT(*) FROM pg_type WHERE typname = 'permissionscope'"))
    exists = result.scalar() > 0

    if not exists:
        op.execute("CREATE TYPE permissionscope AS ENUM ('read', 'write', 'delete', 'admin', 'manage_users', 'manage_settings', 'view_reports', 'export_data')")
    
    # 1. Create organization_hierarchy table
    op.create_table('organization_hierarchy',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('level', sa.Enum('organization', 'location', 'department', 'user', name='hierarchylevel', create_type=False), nullable=False, default='organization'),
        sa.Column('hierarchy_path', sa.String(length=500), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=False, default=0),
        sa.Column('legacy_organisation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('settings', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['organization_hierarchy.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['legacy_organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('slug', 'parent_id', name='uq_hierarchy_slug_parent')
    )
    
    # Create indexes for organization_hierarchy
    op.create_index('idx_hierarchy_path', 'organization_hierarchy', ['hierarchy_path'])
    op.create_index('idx_hierarchy_level_active', 'organization_hierarchy', ['level', 'is_active'])
    op.create_index('idx_hierarchy_parent_level', 'organization_hierarchy', ['parent_id', 'level'])
    op.create_index('idx_hierarchy_legacy_org', 'organization_hierarchy', ['legacy_organisation_id'])
    
    # 2. Create user_hierarchy_assignments table
    op.create_table('user_hierarchy_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hierarchy_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('super_admin', 'org_admin', 'location_manager', 'department_lead', 'user', 'viewer', name='enhanceduserrole', create_type=False), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['hierarchy_node_id'], ['organization_hierarchy.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'hierarchy_node_id', name='uq_user_hierarchy_assignment')
    )
    
    # Create indexes for user_hierarchy_assignments
    op.create_index('idx_user_hierarchy_user_active', 'user_hierarchy_assignments', ['user_id', 'is_active'])
    op.create_index('idx_user_hierarchy_node_role', 'user_hierarchy_assignments', ['hierarchy_node_id', 'role'])
    
    # 3. Create hierarchy_role_assignments table
    op.create_table('hierarchy_role_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('hierarchy_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('super_admin', 'org_admin', 'location_manager', 'department_lead', 'user', 'viewer', name='enhanceduserrole', create_type=False), nullable=False),
        sa.Column('permissions', sa.Text(), nullable=False),  # JSON array
        sa.Column('inherits_from_parent', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['hierarchy_node_id'], ['organization_hierarchy.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('hierarchy_node_id', 'role', name='uq_hierarchy_role')
    )
    
    # Create indexes for hierarchy_role_assignments
    op.create_index('idx_hierarchy_role_active', 'hierarchy_role_assignments', ['role', 'is_active'])
    op.create_index('idx_hierarchy_role_node', 'hierarchy_role_assignments', ['hierarchy_node_id', 'is_active'])
    
    # 4. Create hierarchy_permission_overrides table
    op.create_table('hierarchy_permission_overrides',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hierarchy_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission', sa.String(length=100), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['hierarchy_node_id'], ['organization_hierarchy.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id']),
        sa.UniqueConstraint('user_id', 'hierarchy_node_id', 'permission', name='uq_user_permission_override')
    )
    
    # Create indexes for hierarchy_permission_overrides
    op.create_index('idx_permission_override_user_active', 'hierarchy_permission_overrides', ['user_id', 'is_active'])
    op.create_index('idx_permission_override_node_permission', 'hierarchy_permission_overrides', ['hierarchy_node_id', 'permission'])
    
    # 5. Create industry_templates table
    op.create_table('industry_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('industry_code', sa.String(length=20), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_settings', sa.Text(), nullable=False),  # JSON
        sa.Column('default_permissions', sa.Text(), nullable=False),  # JSON
        sa.Column('default_features', sa.Text(), nullable=False),  # JSON
        sa.Column('dashboard_config', sa.Text(), nullable=True),  # JSON
        sa.Column('parent_template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_base_template', sa.Boolean(), nullable=False, default=False),
        sa.Column('customizable_fields', sa.Text(), nullable=True),  # JSON
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('version', sa.String(length=20), nullable=False, default='1.0.0'),
        sa.ForeignKeyConstraint(['parent_template_id'], ['industry_templates.id']),
        sa.UniqueConstraint('name', name='uq_industry_template_name'),
        sa.UniqueConstraint('industry_code', name='uq_industry_template_code')
    )
    
    # Create indexes for industry_templates
    op.create_index('idx_industry_template_code_active', 'industry_templates', ['industry_code', 'is_active'])
    op.create_index('idx_industry_template_parent', 'industry_templates', ['parent_template_id', 'is_active'])
    
    # 6. Create organization_template_applications table
    op.create_table('organization_template_applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('applied_settings', sa.Text(), nullable=False),  # JSON
        sa.Column('customizations', sa.Text(), nullable=True),  # JSON
        sa.Column('applied_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['industry_templates.id']),
        sa.ForeignKeyConstraint(['applied_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'template_id', name='uq_org_template_application')
    )
    
    # Create indexes for organization_template_applications
    op.create_index('idx_org_template_org_active', 'organization_template_applications', ['organization_id', 'is_active'])
    op.create_index('idx_org_template_template_active', 'organization_template_applications', ['template_id', 'is_active'])
    
    # Enable RLS on new hierarchical tables
    hierarchical_tables = [
        'organization_hierarchy',
        'user_hierarchy_assignments',
        'hierarchy_role_assignments',
        'hierarchy_permission_overrides',
        'organization_template_applications'
    ]
    
    for table_name in hierarchical_tables:
        # Enable RLS
        op.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
        
        # Create policy for regular users - they can only access their organization's data
        op.execute(text(f"""
            CREATE POLICY tenant_isolation_{table_name} ON {table_name}
                FOR ALL TO public
                USING (
                    CASE 
                        WHEN '{table_name}' = 'organization_hierarchy' THEN
                            legacy_organisation_id = current_setting('app.current_tenant_id')::uuid
                        WHEN '{table_name}' = 'user_hierarchy_assignments' THEN
                            hierarchy_node_id IN (
                                SELECT id FROM organization_hierarchy 
                                WHERE legacy_organisation_id = current_setting('app.current_tenant_id')::uuid
                            )
                        WHEN '{table_name}' = 'hierarchy_role_assignments' THEN
                            hierarchy_node_id IN (
                                SELECT id FROM organization_hierarchy 
                                WHERE legacy_organisation_id = current_setting('app.current_tenant_id')::uuid
                            )
                        WHEN '{table_name}' = 'hierarchy_permission_overrides' THEN
                            hierarchy_node_id IN (
                                SELECT id FROM organization_hierarchy 
                                WHERE legacy_organisation_id = current_setting('app.current_tenant_id')::uuid
                            )
                        WHEN '{table_name}' = 'organization_template_applications' THEN
                            organization_id = current_setting('app.current_tenant_id')::uuid
                        ELSE false
                    END
                )
        """))
        
        # Create policy for super admins - they can access all data when explicitly allowed
        op.execute(text(f"""
            CREATE POLICY super_admin_access_{table_name} ON {table_name}
                FOR ALL TO public
                USING (
                    current_setting('app.current_user_role', true) = 'super_admin'
                    AND current_setting('app.allow_cross_tenant', true) = 'true'
                )
        """))
    
    # Update RLS helper functions to support enhanced roles
    op.execute(text("""
        CREATE OR REPLACE FUNCTION set_tenant_context(
            tenant_id uuid,
            user_role text DEFAULT 'viewer',
            allow_cross_tenant boolean DEFAULT false
        ) RETURNS void AS $function$
        BEGIN
            -- Validate user role to prevent injection
            IF user_role NOT IN ('admin', 'analyst', 'viewer', 'super_admin', 'org_admin', 'location_manager', 'department_lead', 'user') THEN
                RAISE EXCEPTION 'Invalid user role: %', user_role;
            END IF;
            
            PERFORM set_config('app.current_tenant_id', tenant_id::text, true);
            PERFORM set_config('app.current_user_role', user_role, true);
            PERFORM set_config('app.allow_cross_tenant', allow_cross_tenant::text, true);
        END;
        $function$ LANGUAGE plpgsql SECURITY DEFINER
    """))
    
    # Create helper function for permission resolution
    op.execute(text("""
        CREATE OR REPLACE FUNCTION resolve_user_permissions(
            user_uuid uuid,
            context_node_uuid uuid DEFAULT NULL
        ) RETURNS jsonb AS $function$
        DECLARE
            permissions jsonb := '[]'::jsonb;
            assignment RECORD;
            role_perms jsonb;
            override RECORD;
        BEGIN
            -- Get user's hierarchy assignments
            FOR assignment IN 
                SELECT uha.role, uha.hierarchy_node_id, oh.hierarchy_path
                FROM user_hierarchy_assignments uha
                JOIN organization_hierarchy oh ON uha.hierarchy_node_id = oh.id
                WHERE uha.user_id = user_uuid 
                  AND uha.is_active = true
                  AND (context_node_uuid IS NULL OR uha.hierarchy_node_id = context_node_uuid)
            LOOP
                -- Get role permissions for this assignment
                SELECT hra.permissions::jsonb INTO role_perms
                FROM hierarchy_role_assignments hra
                WHERE hra.hierarchy_node_id = assignment.hierarchy_node_id
                  AND hra.role::text = assignment.role::text
                  AND hra.is_active = true;
                
                -- Merge permissions
                IF role_perms IS NOT NULL THEN
                    permissions := permissions || role_perms;
                END IF;
            END LOOP;
            
            -- Apply permission overrides
            FOR override IN
                SELECT hpo.permission, hpo.granted
                FROM hierarchy_permission_overrides hpo
                WHERE hpo.user_id = user_uuid
                  AND hpo.is_active = true
                  AND (context_node_uuid IS NULL OR hpo.hierarchy_node_id = context_node_uuid)
            LOOP
                IF override.granted THEN
                    -- Grant permission
                    permissions := permissions || jsonb_build_array(override.permission);
                ELSE
                    -- Revoke permission
                    permissions := permissions - override.permission;
                END IF;
            END LOOP;
            
            -- Remove duplicates and return
            RETURN (SELECT jsonb_agg(DISTINCT value) FROM jsonb_array_elements_text(permissions) AS value);
        END;
        $function$ LANGUAGE plpgsql SECURITY DEFINER
    """))
    
    # Insert default industry templates
    op.execute(text("""
        INSERT INTO industry_templates (
            name, industry_code, display_name, description,
            default_settings, default_permissions, default_features,
            dashboard_config, customizable_fields, is_base_template, is_active, version
        ) VALUES 
        (
            'Cinema Industry Standard',
            'CINEMA',
            'Cinema & Entertainment',
            'Standard configuration for cinema and entertainment venues',
            '{"industry_type": "cinema", "subscription_plan": "professional", "rate_limit_per_hour": 2000, "burst_limit": 200, "features": {"dynamic_pricing": true, "competitor_tracking": true, "capacity_monitoring": true}}',
            '{"super_admin": ["read", "write", "delete", "admin", "manage_users", "manage_settings", "view_reports", "export_data"], "org_admin": ["read", "write", "delete", "manage_users", "manage_settings", "view_reports", "export_data"], "location_manager": ["read", "write", "manage_users", "view_reports"], "user": ["read", "view_reports"], "viewer": ["read"]}',
            '{"pricing_optimization": true, "competitor_analysis": true, "market_trends": true, "automated_alerts": true, "custom_reports": true}',
            '{"layout": "cinema", "default_view": "performance_overview", "widgets": [{"type": "revenue_chart", "position": {"row": 1, "col": 1}}]}',
            '["data_refresh_interval", "dashboard_widgets", "rate_limit_per_hour", "features.dynamic_pricing"]',
            true,
            true,
            '1.0.0'
        ),
        (
            'Hotel Industry Standard',
            'HOTEL',
            'Hotel & Hospitality',
            'Standard configuration for hotels and hospitality businesses',
            '{"industry_type": "hotel", "subscription_plan": "enterprise", "rate_limit_per_hour": 3000, "burst_limit": 300, "features": {"room_rate_optimization": true, "occupancy_forecasting": true, "competitor_benchmarking": true}}',
            '{"super_admin": ["read", "write", "delete", "admin", "manage_users", "manage_settings", "view_reports", "export_data"], "org_admin": ["read", "write", "delete", "manage_users", "manage_settings", "view_reports", "export_data"], "location_manager": ["read", "write", "manage_users", "view_reports"], "user": ["read", "view_reports"], "viewer": ["read"]}',
            '{"revenue_management": true, "competitor_analysis": true, "demand_forecasting": true, "rate_recommendations": true, "performance_analytics": true}',
            '{"layout": "hotel", "default_view": "revenue_dashboard", "widgets": [{"type": "adr_chart", "position": {"row": 1, "col": 1}}]}',
            '["data_refresh_interval", "dashboard_widgets", "rate_limit_per_hour", "features.room_rate_optimization"]',
            true,
            true,
            '1.0.0'
        )
    """))
    
    # Create migration function to populate hierarchy for existing organizations
    op.execute(text("""
        CREATE OR REPLACE FUNCTION migrate_existing_organizations() RETURNS void AS $migration$
        DECLARE
            org RECORD;
            root_node_id uuid;
            admin_user RECORD;
        BEGIN
            -- Create hierarchy nodes for existing organizations
            FOR org IN SELECT id, name FROM organisations WHERE name IS NOT NULL LOOP
                -- Create root hierarchy node
                INSERT INTO organization_hierarchy (
                    name, slug, description, level, hierarchy_path, depth,
                    legacy_organisation_id, is_active
                ) VALUES (
                    org.name,
                    lower(replace(replace(org.name, ' ', '-'), '_', '-')),
                    'Root organization node for ' || org.name,
                    'organization',
                    lower(replace(replace(org.name, ' ', '-'), '_', '-')),
                    0,
                    org.id,
                    true
                ) RETURNING id INTO root_node_id;
                
                -- Create role assignments for the root node with default permissions
                INSERT INTO hierarchy_role_assignments (hierarchy_node_id, role, permissions, inherits_from_parent, is_active)
                VALUES 
                (root_node_id, 'org_admin', '["read", "write", "delete", "admin", "manage_users", "manage_settings", "view_reports", "export_data"]', true, true),
                (root_node_id, 'location_manager', '["read", "write", "manage_users", "view_reports"]', true, true),
                (root_node_id, 'department_lead', '["read", "write", "view_reports"]', true, true),
                (root_node_id, 'user', '["read", "view_reports"]', true, true),
                (root_node_id, 'viewer', '["read"]', true, true);
                
                -- Assign existing admin users to root node
                FOR admin_user IN SELECT id FROM users WHERE organisation_id = org.id AND role = 'admin' LOOP
                    INSERT INTO user_hierarchy_assignments (user_id, hierarchy_node_id, role, is_primary, is_active)
                    VALUES (admin_user.id, root_node_id, 'org_admin', true, true);
                END LOOP;
                
                -- Assign other users to root node with appropriate roles
                INSERT INTO user_hierarchy_assignments (user_id, hierarchy_node_id, role, is_primary, is_active)
                SELECT u.id, root_node_id, 
                    CASE 
                        WHEN u.role = 'admin' THEN 'org_admin'::enhanceduserrole
                        WHEN u.role = 'analyst' THEN 'user'::enhanceduserrole
                        WHEN u.role = 'viewer' THEN 'viewer'::enhanceduserrole
                        ELSE 'user'::enhanceduserrole
                    END,
                    CASE WHEN u.role = 'admin' THEN false ELSE true END,
                    true
                FROM users u 
                WHERE u.organisation_id = org.id 
                  AND u.role != 'admin'
                  AND u.id NOT IN (SELECT user_id FROM user_hierarchy_assignments WHERE hierarchy_node_id = root_node_id);
                
                RAISE NOTICE 'Migrated organization: % (ID: %)', org.name, org.id;
            END LOOP;
        END;
        $migration$ LANGUAGE plpgsql
    """))
    
    # Execute the migration
    op.execute(text("SELECT migrate_existing_organizations()"))
    
    # Drop the migration function
    op.execute(text("DROP FUNCTION migrate_existing_organizations()"))


def downgrade():
    """Remove hierarchical organization structure"""
    
    # Drop helper functions
    op.execute("DROP FUNCTION IF EXISTS resolve_user_permissions(uuid, uuid);")
    
    # Drop RLS policies for hierarchical tables
    hierarchical_tables = [
        'organization_hierarchy',
        'user_hierarchy_assignments', 
        'hierarchy_role_assignments',
        'hierarchy_permission_overrides',
        'organization_template_applications'
    ]
    
    for table_name in hierarchical_tables:
        op.execute(text(f"DROP POLICY IF EXISTS tenant_isolation_{table_name} ON {table_name}"))
        op.execute(text(f"DROP POLICY IF EXISTS super_admin_access_{table_name} ON {table_name}"))
        op.execute(text(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY"))
    
    # Drop tables in reverse order of creation
    op.drop_table('organization_template_applications')
    op.drop_table('industry_templates')
    op.drop_table('hierarchy_permission_overrides')
    op.drop_table('hierarchy_role_assignments')
    op.drop_table('user_hierarchy_assignments')
    op.drop_table('organization_hierarchy')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS permissionscope")
    op.execute("DROP TYPE IF EXISTS hierarchylevel")
    op.execute("DROP TYPE IF EXISTS enhanceduserrole")
    
    # Restore original set_tenant_context function
    op.execute(text("""
        CREATE OR REPLACE FUNCTION set_tenant_context(
            tenant_id uuid,
            user_role text DEFAULT 'viewer',
            allow_cross_tenant boolean DEFAULT false
        ) RETURNS void AS $function$
        BEGIN
            -- Validate user role to prevent injection
            IF user_role NOT IN ('admin', 'analyst', 'viewer') THEN
                RAISE EXCEPTION 'Invalid user role: %', user_role;
            END IF;
            
            PERFORM set_config('app.current_tenant_id', tenant_id::text, true);
            PERFORM set_config('app.current_user_role', user_role, true);
            PERFORM set_config('app.allow_cross_tenant', allow_cross_tenant::text, true);
        END;
        $function$ LANGUAGE plpgsql SECURITY DEFINER
    """))