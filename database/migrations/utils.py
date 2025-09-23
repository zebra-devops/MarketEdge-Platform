"""Migration utilities for defensive migration patterns.

This module provides defensive utilities to make migrations more resilient
and fail fast with clear error messages when prerequisites are missing.
"""

from typing import List, Set, Dict, Any, Optional, Tuple
import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.exc import ProgrammingError, OperationalError


class MigrationValidator:
    """Provides defensive migration validation and utilities."""

    def __init__(self):
        """Initialize the validator with the current database connection."""
        self.connection = context.get_bind()

    def table_exists(self, table_name: str, schema: str = 'public') -> bool:
        """Check if a table exists in the database.

        Args:
            table_name: Name of the table to check
            schema: Schema name (default: 'public')

        Returns:
            True if table exists, False otherwise
        """
        query = sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_name = :table_name
            )
        """)
        result = self.connection.execute(
            query,
            {"schema": schema, "table_name": table_name}
        )
        return result.scalar()

    def column_exists(self, table_name: str, column_name: str, schema: str = 'public') -> bool:
        """Check if a column exists in a table.

        Args:
            table_name: Name of the table
            column_name: Name of the column to check
            schema: Schema name (default: 'public')

        Returns:
            True if column exists, False otherwise
        """
        query = sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = :table_name
                AND column_name = :column_name
            )
        """)
        result = self.connection.execute(
            query,
            {"schema": schema, "table_name": table_name, "column_name": column_name}
        )
        return result.scalar()

    def columns_exist(self, table_name: str, column_names: List[str], schema: str = 'public') -> Dict[str, bool]:
        """Check if multiple columns exist in a table.

        Args:
            table_name: Name of the table
            column_names: List of column names to check
            schema: Schema name (default: 'public')

        Returns:
            Dictionary mapping column names to their existence status
        """
        query = sa.text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = :schema
            AND table_name = :table_name
            AND column_name = ANY(:column_names)
        """)
        result = self.connection.execute(
            query,
            {"schema": schema, "table_name": table_name, "column_names": column_names}
        )
        existing_columns = {row[0] for row in result.fetchall()}

        return {col: col in existing_columns for col in column_names}

    def index_exists(self, index_name: str, table_name: str = None) -> bool:
        """Check if an index exists.

        Args:
            index_name: Name of the index
            table_name: Optional table name to check

        Returns:
            True if index exists, False otherwise
        """
        if table_name:
            query = sa.text("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE indexname = :index_name
                    AND tablename = :table_name
                )
            """)
            result = self.connection.execute(
                query,
                {"index_name": index_name, "table_name": table_name}
            )
        else:
            query = sa.text("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE indexname = :index_name
                )
            """)
            result = self.connection.execute(
                query,
                {"index_name": index_name}
            )
        return result.scalar()

    def constraint_exists(self, constraint_name: str, table_name: str, schema: str = 'public') -> bool:
        """Check if a constraint exists on a table.

        Args:
            constraint_name: Name of the constraint
            table_name: Name of the table
            schema: Schema name (default: 'public')

        Returns:
            True if constraint exists, False otherwise
        """
        query = sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.table_constraints
                WHERE constraint_schema = :schema
                AND table_name = :table_name
                AND constraint_name = :constraint_name
            )
        """)
        result = self.connection.execute(
            query,
            {"schema": schema, "table_name": table_name, "constraint_name": constraint_name}
        )
        return result.scalar()

    def validate_prerequisites(
        self,
        required_tables: Set[str] = None,
        required_columns: Dict[str, List[str]] = None,
        required_indexes: List[Tuple[str, str]] = None,
        migration_id: str = None
    ) -> None:
        """Validate all prerequisites for a migration and fail fast with clear errors.

        Args:
            required_tables: Set of table names that must exist
            required_columns: Dict mapping table names to required columns
            required_indexes: List of (index_name, table_name) tuples
            migration_id: Current migration ID for error messages

        Raises:
            Exception: With detailed error message if prerequisites are not met
        """
        errors = []
        migration_prefix = f"Migration {migration_id}: " if migration_id else ""

        # Check required tables
        if required_tables:
            missing_tables = set()
            for table in required_tables:
                if not self.table_exists(table):
                    missing_tables.add(table)

            if missing_tables:
                errors.append(f"Missing required tables: {sorted(missing_tables)}")

        # Check required columns
        if required_columns:
            for table, columns in required_columns.items():
                if not self.table_exists(table):
                    errors.append(f"Table '{table}' does not exist (needed for columns: {columns})")
                else:
                    column_status = self.columns_exist(table, columns)
                    missing = [col for col, exists in column_status.items() if not exists]
                    if missing:
                        errors.append(f"Table '{table}' is missing columns: {sorted(missing)}")

        # Check required indexes
        if required_indexes:
            missing_indexes = []
            for index_name, table_name in required_indexes:
                if not self.index_exists(index_name, table_name):
                    missing_indexes.append(f"{index_name} (on {table_name})")

            if missing_indexes:
                errors.append(f"Missing required indexes: {missing_indexes}")

        # If there are errors, fail with comprehensive message
        if errors:
            error_msg = [
                f"{migration_prefix}Prerequisites validation FAILED!",
                "",
                "MISSING PREREQUISITES:",
            ]
            error_msg.extend([f"  - {error}" for error in errors])
            error_msg.extend([
                "",
                "ACTION REQUIRED:",
                "1. Check if previous migrations completed successfully:",
                "   alembic current",
                "",
                "2. If migrations are out of order, create a repair migration:",
                "   python database/create_repair_migration.py",
                "",
                "3. For missing base schema, run:",
                "   python database/validate_schema.py --fix",
                "",
                "4. To apply all pending migrations:",
                "   alembic upgrade head",
            ])

            raise Exception("\n".join(error_msg))

        print(f"{migration_prefix}All prerequisites validated successfully")

    def safe_add_column(
        self,
        table_name: str,
        column: sa.Column,
        schema: str = 'public'
    ) -> bool:
        """Safely add a column if it doesn't already exist.

        Args:
            table_name: Name of the table
            column: SQLAlchemy Column object
            schema: Schema name (default: 'public')

        Returns:
            True if column was added, False if it already existed
        """
        if not self.table_exists(table_name, schema):
            raise Exception(
                f"Cannot add column '{column.name}' to non-existent table '{table_name}'.\n"
                f"Ensure table creation migrations have been applied first."
            )

        if self.column_exists(table_name, column.name, schema):
            print(f"Column '{column.name}' already exists in table '{table_name}' - skipping")
            return False

        with op.batch_alter_table(table_name, schema=schema) as batch_op:
            batch_op.add_column(column)

        print(f"Successfully added column '{column.name}' to table '{table_name}'")
        return True

    def safe_create_index(
        self,
        index_name: str,
        table_name: str,
        columns: List[str],
        unique: bool = False,
        schema: str = 'public',
        **kwargs
    ) -> bool:
        """Safely create an index if it doesn't already exist.

        Args:
            index_name: Name of the index
            table_name: Name of the table
            columns: List of column names
            unique: Whether index should be unique
            schema: Schema name (default: 'public')
            **kwargs: Additional arguments for create_index

        Returns:
            True if index was created, False if it already existed
        """
        # First check if table exists
        if not self.table_exists(table_name, schema):
            print(f"WARNING: Table '{table_name}' does not exist - skipping index '{index_name}'")
            return False

        # Check if all columns exist
        column_status = self.columns_exist(table_name, columns, schema)
        missing_columns = [col for col, exists in column_status.items() if not exists]

        if missing_columns:
            print(f"WARNING: Cannot create index '{index_name}' - missing columns in '{table_name}': {missing_columns}")
            return False

        # Check if index already exists
        if self.index_exists(index_name, table_name):
            print(f"Index '{index_name}' already exists on table '{table_name}' - skipping")
            return False

        # Create the index
        op.create_index(index_name, table_name, columns, unique=unique, schema=schema, **kwargs)
        print(f"Successfully created index '{index_name}' on table '{table_name}'")
        return True

    def safe_create_check_constraint(
        self,
        constraint_name: str,
        table_name: str,
        condition: str,
        schema: str = 'public'
    ) -> bool:
        """Safely create a check constraint if it doesn't already exist.

        Args:
            constraint_name: Name of the constraint
            table_name: Name of the table
            condition: SQL condition for the check
            schema: Schema name (default: 'public')

        Returns:
            True if constraint was created, False if it already existed
        """
        # Check if table exists
        if not self.table_exists(table_name, schema):
            print(f"WARNING: Table '{table_name}' does not exist - skipping constraint '{constraint_name}'")
            return False

        # Check if constraint already exists
        if self.constraint_exists(constraint_name, table_name, schema):
            print(f"Constraint '{constraint_name}' already exists on table '{table_name}' - skipping")
            return False

        # Create the constraint
        op.create_check_constraint(constraint_name, table_name, condition, schema=schema)
        print(f"Successfully created constraint '{constraint_name}' on table '{table_name}'")
        return True

    def safe_drop_index(self, index_name: str, table_name: str) -> bool:
        """Safely drop an index if it exists.

        Args:
            index_name: Name of the index
            table_name: Name of the table

        Returns:
            True if index was dropped, False if it didn't exist
        """
        if not self.index_exists(index_name, table_name):
            print(f"Index '{index_name}' does not exist - skipping drop")
            return False

        try:
            op.drop_index(index_name, table_name=table_name)
            print(f"Successfully dropped index '{index_name}'")
            return True
        except (ProgrammingError, OperationalError) as e:
            print(f"WARNING: Could not drop index '{index_name}': {e}")
            return False

    def safe_drop_constraint(
        self,
        constraint_name: str,
        table_name: str,
        schema: str = 'public'
    ) -> bool:
        """Safely drop a constraint if it exists.

        Args:
            constraint_name: Name of the constraint
            table_name: Name of the table
            schema: Schema name (default: 'public')

        Returns:
            True if constraint was dropped, False if it didn't exist
        """
        if not self.constraint_exists(constraint_name, table_name, schema):
            print(f"Constraint '{constraint_name}' does not exist - skipping drop")
            return False

        try:
            op.drop_constraint(constraint_name, table_name, schema=schema)
            print(f"Successfully dropped constraint '{constraint_name}'")
            return True
        except (ProgrammingError, OperationalError) as e:
            print(f"WARNING: Could not drop constraint '{constraint_name}': {e}")
            return False

    def get_migration_status(self) -> Dict[str, Any]:
        """Get comprehensive migration status information.

        Returns:
            Dictionary with migration status details
        """
        # Get current revision
        query = sa.text("SELECT version_num FROM alembic_version")
        try:
            result = self.connection.execute(query)
            current_revision = result.scalar()
        except (ProgrammingError, OperationalError):
            current_revision = None

        # Get all tables
        query = sa.text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        result = self.connection.execute(query)
        tables = [row[0] for row in result.fetchall()]

        # Get all indexes
        query = sa.text("""
            SELECT tablename, indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        result = self.connection.execute(query)
        indexes = {}
        for table, index in result.fetchall():
            if table not in indexes:
                indexes[table] = []
            indexes[table].append(index)

        return {
            'current_revision': current_revision,
            'tables': tables,
            'indexes': indexes,
            'table_count': len(tables),
            'total_indexes': sum(len(idx_list) for idx_list in indexes.values())
        }

    def print_migration_status(self) -> None:
        """Print a formatted migration status report."""
        status = self.get_migration_status()

        print("\n" + "="*60)
        print("MIGRATION STATUS REPORT")
        print("="*60)
        print(f"Current Revision: {status['current_revision'] or 'No migrations applied'}")
        print(f"Total Tables: {status['table_count']}")
        print(f"Total Indexes: {status['total_indexes']}")
        print("\nTables Present:")
        for table in status['tables']:
            index_count = len(status['indexes'].get(table, []))
            print(f"  - {table} ({index_count} indexes)")
        print("="*60 + "\n")


def get_validator() -> MigrationValidator:
    """Get a configured MigrationValidator instance.

    Returns:
        MigrationValidator instance
    """
    return MigrationValidator()


def fail_fast(message: str, instructions: List[str] = None) -> None:
    """Fail immediately with a clear error message and instructions.

    Args:
        message: The error message
        instructions: Optional list of instruction lines

    Raises:
        Exception: Always raises with formatted message
    """
    error_lines = [
        "\n" + "="*60,
        "MIGRATION ERROR",
        "="*60,
        message,
    ]

    if instructions:
        error_lines.extend([
            "",
            "ACTION REQUIRED:",
        ])
        error_lines.extend([f"  {i+1}. {inst}" for i, inst in enumerate(instructions)])

    error_lines.append("="*60 + "\n")

    raise Exception("\n".join(error_lines))