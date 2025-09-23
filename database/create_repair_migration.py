#!/usr/bin/env python3
"""Create a repair migration to fix missing prerequisites.

This script analyzes the current database state and creates a migration
that adds any missing tables, columns, or indexes that are preventing
other migrations from running successfully.
"""

import os
import sys
from datetime import datetime
from typing import Set, Dict, List, Tuple
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.migrations.utils import MigrationValidator
from alembic import context
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker


def analyze_missing_prerequisites(validator: MigrationValidator) -> Dict:
    """Analyze the database to find missing prerequisites.

    Returns:
        Dictionary with analysis results
    """
    missing = {
        'tables': [],
        'columns': {},
        'indexes': [],
        'constraints': []
    }

    # Expected schema based on migrations
    expected_tables = {
        # Core tables
        'organisations': ['id', 'name', 'created_at', 'updated_at'],
        'users': ['id', 'email', 'organisation_id', 'role', 'created_at', 'updated_at'],

        # Feature flag tables
        'feature_flags': ['id', 'flag_key', 'scope', 'is_enabled', 'rollout_percentage', 'created_at', 'updated_at'],
        'feature_flag_usage': ['id', 'feature_flag_id', 'organisation_id', 'accessed_at'],
        'feature_flag_overrides': ['id', 'feature_flag_id', 'organisation_id', 'is_enabled'],

        # Module tables
        'modules': ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at'],
        'organisation_modules': ['id', 'organisation_id', 'module_id', 'is_enabled', 'created_at', 'updated_at'],
        'module_configurations': ['id', 'organisation_id', 'module_id', 'config_key', 'config_value'],
        'module_usage_logs': ['id', 'module_id', 'organisation_id', 'timestamp', 'action'],

        # Audit and logging
        'audit_logs': ['id', 'user_id', 'organisation_id', 'action', 'timestamp', 'resource_type', 'resource_id'],

        # Business tables
        'competitive_factor_templates': ['id', 'name', 'weight', 'category', 'created_at', 'updated_at'],
        'sic_codes': ['id', 'code', 'description', 'parent_code', 'created_at', 'updated_at']
    }

    # Check for missing tables
    for table_name, expected_columns in expected_tables.items():
        if not validator.table_exists(table_name):
            missing['tables'].append(table_name)
            missing['columns'][table_name] = expected_columns
        else:
            # Check for missing columns
            column_status = validator.columns_exist(table_name, expected_columns)
            missing_cols = [col for col, exists in column_status.items() if not exists]
            if missing_cols:
                missing['columns'][table_name] = missing_cols

    # Check for missing critical indexes
    critical_indexes = [
        ('organisations', 'idx_organisations_name'),
        ('users', 'idx_users_email'),
        ('users', 'idx_users_organisation_id'),
        ('feature_flags', 'idx_feature_flags_unique_scope'),
        ('audit_logs', 'idx_audit_logs_user_action')
    ]

    for table_name, index_name in critical_indexes:
        if validator.table_exists(table_name):
            if not validator.index_exists(index_name, table_name):
                missing['indexes'].append((table_name, index_name))

    return missing


def generate_repair_migration(missing: Dict, migration_name: str = None) -> str:
    """Generate a repair migration file content.

    Args:
        missing: Dictionary of missing prerequisites
        migration_name: Optional custom migration name

    Returns:
        Migration file content as string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not migration_name:
        migration_name = f"repair_missing_prerequisites_{timestamp}"

    migration_content = f'''"""Repair migration to add missing prerequisites.

This migration was auto-generated to fix missing database objects
that are preventing other migrations from running successfully.

Generated: {datetime.now().isoformat()}
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# revision identifiers, used by Alembic.
revision = '{timestamp}_repair'
down_revision = None  # Will be set based on current state
branch_labels = None
depends_on = None


def upgrade():
    """Add missing prerequisites to fix migration issues."""
    from database.migrations.utils import get_validator

    print("\\n" + "="*60)
    print("REPAIR MIGRATION: ADDING MISSING PREREQUISITES")
    print("="*60)

    validator = get_validator()
    validator.print_migration_status()

    print("\\nApplying repairs...")
'''

    # Add table creation for missing tables
    if missing['tables']:
        migration_content += "\n    # Create missing tables\n"
        for table_name in missing['tables']:
            migration_content += f"""
    if not validator.table_exists('{table_name}'):
        print(f"Creating table: {table_name}")
        op.create_table(
            '{table_name}',
"""
            # Add columns based on table type
            if table_name == 'organisations':
                migration_content += """            sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
"""
            elif table_name == 'users':
                migration_content += """            sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('organisation_id', postgresql.UUID(), nullable=True),
            sa.Column('role', sa.String(50), nullable=False, server_default='viewer'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'])
"""
            elif table_name in ['feature_flags', 'modules', 'audit_logs', 'competitive_factor_templates', 'sic_codes']:
                # Generate generic structure based on expected columns
                columns = missing['columns'].get(table_name, [])
                for col in columns:
                    if col == 'id':
                        migration_content += "            sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),\n"
                    elif col == 'organisation_id':
                        migration_content += "            sa.Column('organisation_id', postgresql.UUID(), nullable=True),\n"
                    elif col in ['created_at', 'updated_at', 'timestamp', 'accessed_at']:
                        migration_content += f"            sa.Column('{col}', sa.DateTime(), server_default=sa.text('now()'), nullable=False),\n"
                    elif col in ['is_enabled', 'is_active']:
                        migration_content += f"            sa.Column('{col}', sa.Boolean(), server_default='false', nullable=False),\n"
                    elif col in ['weight', 'rollout_percentage']:
                        migration_content += f"            sa.Column('{col}', sa.Integer(), server_default='0', nullable=False),\n"
                    else:
                        migration_content += f"            sa.Column('{col}', sa.String(255), nullable=True),\n"
                migration_content += "            sa.PrimaryKeyConstraint('id')\n"

            migration_content += """        )
    else:
        print(f"Table already exists: {table_name}")
"""

    # Add missing columns to existing tables
    if any(cols for cols in missing['columns'].values() if cols):
        migration_content += "\n    # Add missing columns to existing tables\n"
        for table_name, columns in missing['columns'].items():
            if table_name not in missing['tables'] and columns:
                for col in columns:
                    migration_content += f"""
    if validator.table_exists('{table_name}'):
        if not validator.column_exists('{table_name}', '{col}'):
            print(f"Adding column: {table_name}.{col}")
"""
                    # Determine column type based on name
                    if col == 'organisation_id':
                        migration_content += f"            validator.safe_add_column('{table_name}', sa.Column('{col}', postgresql.UUID(), nullable=True))\n"
                    elif col in ['created_at', 'updated_at', 'timestamp', 'accessed_at']:
                        migration_content += f"            validator.safe_add_column('{table_name}', sa.Column('{col}', sa.DateTime(), server_default=sa.text('now()')))\n"
                    elif col in ['is_enabled', 'is_active']:
                        migration_content += f"            validator.safe_add_column('{table_name}', sa.Column('{col}', sa.Boolean(), server_default='false'))\n"
                    elif col in ['weight', 'rollout_percentage']:
                        migration_content += f"            validator.safe_add_column('{table_name}', sa.Column('{col}', sa.Integer(), server_default='0'))\n"
                    elif col in ['resource_type', 'resource_id']:
                        migration_content += f"            validator.safe_add_column('{table_name}', sa.Column('{col}', sa.String(255), nullable=True))\n"
                    else:
                        migration_content += f"            validator.safe_add_column('{table_name}', sa.Column('{col}', sa.String(255), nullable=True))\n"

    # Add missing indexes
    if missing['indexes']:
        migration_content += "\n    # Create missing indexes\n"
        for table_name, index_name in missing['indexes']:
            # Determine columns based on index name
            if 'email' in index_name:
                columns = "['email']"
            elif 'organisation_id' in index_name:
                columns = "['organisation_id']"
            elif 'unique_scope' in index_name:
                columns = "['flag_key', 'scope']"
            elif 'user_action' in index_name:
                columns = "['user_id', 'action']"
            else:
                columns = "['id']"  # Default

            migration_content += f"""
    validator.safe_create_index(
        '{index_name}',
        '{table_name}',
        {columns}
    )
"""

    migration_content += """
    print("\\n" + "="*60)
    print("REPAIR MIGRATION COMPLETED")
    print("="*60 + "\\n")


def downgrade():
    \"\"\"This repair migration should not be downgraded.\"\"\"
    print("\\nWARNING: Repair migrations should not be downgraded.")
    print("These changes fix critical prerequisites for other migrations.")
    print("Skipping downgrade.\\n")
    pass
"""

    return migration_content


def save_migration_file(content: str, migrations_dir: str = None) -> str:
    """Save the migration file to disk.

    Args:
        content: Migration file content
        migrations_dir: Directory to save migration (default: database/migrations/versions)

    Returns:
        Path to created file
    """
    if not migrations_dir:
        migrations_dir = os.path.join(
            os.path.dirname(__file__),
            'migrations',
            'versions'
        )

    # Ensure directory exists
    os.makedirs(migrations_dir, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"repair_{timestamp}.py"
    filepath = os.path.join(migrations_dir, filename)

    # Save file
    with open(filepath, 'w') as f:
        f.write(content)

    return filepath


def main():
    """Main function to create repair migration."""
    parser = argparse.ArgumentParser(description='Create a repair migration for missing prerequisites')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be created without saving')
    parser.add_argument('--name', help='Custom name for the migration')
    parser.add_argument('--output', help='Output directory for migration file')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("DATABASE REPAIR MIGRATION GENERATOR")
    print("="*60)

    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("\nERROR: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL to your database connection string")
        sys.exit(1)

    # Create engine and validator
    engine = create_engine(database_url)

    # Create a mock context for the validator
    from unittest.mock import Mock
    mock_context = Mock()
    mock_context.get_bind = lambda: engine.connect()

    # Monkey-patch the context module
    import database.migrations.utils as utils_module
    original_context = utils_module.context
    utils_module.context = mock_context

    try:
        with engine.connect() as connection:
            mock_context.get_bind = lambda: connection
            validator = MigrationValidator()

            print("\nAnalyzing database state...")
            missing = analyze_missing_prerequisites(validator)

            # Report findings
            print("\n" + "-"*40)
            print("ANALYSIS RESULTS")
            print("-"*40)

            if missing['tables']:
                print(f"\nMissing tables ({len(missing['tables'])}):")
                for table in missing['tables']:
                    print(f"  - {table}")

            missing_column_tables = [t for t, cols in missing['columns'].items()
                                    if cols and t not in missing['tables']]
            if missing_column_tables:
                print(f"\nTables with missing columns ({len(missing_column_tables)}):")
                for table in missing_column_tables:
                    cols = missing['columns'][table]
                    print(f"  - {table}: {', '.join(cols)}")

            if missing['indexes']:
                print(f"\nMissing indexes ({len(missing['indexes'])}):")
                for table, index in missing['indexes']:
                    print(f"  - {index} on {table}")

            if not any([missing['tables'], missing_column_tables, missing['indexes']]):
                print("\nNo missing prerequisites found!")
                print("Database appears to be in good state.")
                return

            # Generate migration
            print("\n" + "-"*40)
            print("GENERATING REPAIR MIGRATION")
            print("-"*40)

            migration_content = generate_repair_migration(missing, args.name)

            if args.dry_run:
                print("\n[DRY RUN MODE - Migration not saved]")
                print("\nGenerated migration content:")
                print("="*60)
                print(migration_content)
                print("="*60)
            else:
                filepath = save_migration_file(migration_content, args.output)
                print(f"\nRepair migration created: {filepath}")
                print("\nNext steps:")
                print("  1. Review the generated migration file")
                print("  2. Run: alembic upgrade head")
                print("  3. Retry failed migrations")

    finally:
        # Restore original context
        utils_module.context = original_context

    print("\n" + "="*60)
    print("REPAIR MIGRATION GENERATOR COMPLETE")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()