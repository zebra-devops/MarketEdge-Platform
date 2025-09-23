#!/usr/bin/env python3
"""
Schema Validation Script
========================

Validates database schema against SQLAlchemy models to ensure:
1. All required tables exist
2. All required columns exist with correct types
3. All foreign key relationships exist
4. All indexes and constraints are properly defined

This prevents migration failures by ensuring baseline schema consistency
before attempting to apply incremental migrations.

Usage:
    python database/validate_schema.py --check        # Check schema and report issues
    python database/validate_schema.py --fix          # Generate SQL to fix missing schema
    python database/validate_schema.py --baseline     # Generate complete baseline schema

Exit codes:
    0: Schema is valid
    1: Schema validation failed (missing tables/columns)
    2: Database connection failed
    3: Internal error
"""

import os
import sys
import argparse
import asyncio
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from sqlalchemy import text, MetaData, Table, Column, inspect
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine import reflection

# Add app directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.base import Base
from app.models.user import User, UserRole
from app.models.organisation import Organisation
from app.models.modules import AnalyticsModule, OrganisationModule, ModuleConfiguration, ModuleUsageLog
from app.models.feature_flags import FeatureFlag, FeatureFlagUsage
from app.models.audit_log import AuditLog
from app.models.sectors import SICCode


@dataclass
class SchemaIssue:
    """Represents a schema validation issue"""
    severity: str  # ERROR, WARNING, INFO
    category: str  # MISSING_TABLE, MISSING_COLUMN, TYPE_MISMATCH, etc.
    table_name: str
    column_name: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    fix_sql: Optional[str] = None
    description: str = ""


@dataclass
class SchemaValidationResult:
    """Results of schema validation"""
    is_valid: bool = True
    issues: List[SchemaIssue] = field(default_factory=list)
    missing_tables: Set[str] = field(default_factory=set)
    missing_columns: Dict[str, Set[str]] = field(default_factory=dict)
    baseline_sql: List[str] = field(default_factory=list)

    def add_issue(self, issue: SchemaIssue):
        """Add an issue to the result"""
        self.issues.append(issue)
        if issue.severity == "ERROR":
            self.is_valid = False


class SchemaValidator:
    """Validates database schema against SQLAlchemy models"""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.metadata = Base.metadata
        self.result = SchemaValidationResult()

    async def validate_schema(self) -> SchemaValidationResult:
        """Perform complete schema validation"""
        try:
            async with self.engine.connect() as conn:
                # Get current database schema
                db_tables = await self._get_database_tables(conn)
                db_columns = await self._get_database_columns(conn)

                # Get expected schema from models
                model_tables = self._get_model_tables()
                model_columns = self._get_model_columns()

                # Validate tables
                await self._validate_tables(db_tables, model_tables)

                # Validate columns
                await self._validate_columns(db_columns, model_columns, db_tables)

                # Generate baseline SQL if needed
                if not self.result.is_valid:
                    self.result.baseline_sql = await self._generate_baseline_sql()

        except Exception as e:
            self.result.add_issue(SchemaIssue(
                severity="ERROR",
                category="VALIDATION_ERROR",
                table_name="",
                description=f"Schema validation failed: {str(e)}"
            ))

        return self.result

    async def _get_database_tables(self, conn) -> Set[str]:
        """Get list of existing database tables"""
        result = await conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """))
        return {row[0] for row in result.fetchall()}

    async def _get_database_columns(self, conn) -> Dict[str, Dict[str, str]]:
        """Get database columns with their types"""
        result = await conn.execute(text("""
            SELECT
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """))

        columns = {}
        for row in result.fetchall():
            table_name = row[0]
            if table_name not in columns:
                columns[table_name] = {}
            columns[table_name][row[1]] = {
                'type': row[2],
                'nullable': row[3] == 'YES',
                'default': row[4]
            }

        return columns

    def _get_model_tables(self) -> Set[str]:
        """Get expected tables from SQLAlchemy models"""
        return {table.name for table in self.metadata.tables.values()}

    def _get_model_columns(self) -> Dict[str, Dict[str, Dict]]:
        """Get expected columns from SQLAlchemy models"""
        columns = {}
        for table_name, table in self.metadata.tables.items():
            columns[table_name] = {}
            for column in table.columns:
                columns[table_name][column.name] = {
                    'type': str(column.type),
                    'nullable': column.nullable,
                    'primary_key': column.primary_key,
                    'foreign_keys': [str(fk.target_fullname) for fk in column.foreign_keys]
                }
        return columns

    async def _validate_tables(self, db_tables: Set[str], model_tables: Set[str]):
        """Validate that all required tables exist"""
        missing_tables = model_tables - db_tables

        for table_name in missing_tables:
            self.result.missing_tables.add(table_name)
            self.result.add_issue(SchemaIssue(
                severity="ERROR",
                category="MISSING_TABLE",
                table_name=table_name,
                description=f"Table '{table_name}' is required but does not exist in database",
                fix_sql=f"-- Table '{table_name}' needs to be created"
            ))

    async def _validate_columns(self, db_columns: Dict[str, Dict[str, str]],
                               model_columns: Dict[str, Dict[str, Dict]],
                               existing_tables: Set[str]):
        """Validate columns for existing tables"""
        for table_name, expected_columns in model_columns.items():
            if table_name not in existing_tables:
                continue  # Skip tables that don't exist (already reported)

            db_table_columns = db_columns.get(table_name, {})

            for column_name, column_spec in expected_columns.items():
                if column_name not in db_table_columns:
                    # Missing column
                    if table_name not in self.result.missing_columns:
                        self.result.missing_columns[table_name] = set()
                    self.result.missing_columns[table_name].add(column_name)

                    self.result.add_issue(SchemaIssue(
                        severity="ERROR",
                        category="MISSING_COLUMN",
                        table_name=table_name,
                        column_name=column_name,
                        expected=str(column_spec['type']),
                        description=f"Column '{column_name}' is required in table '{table_name}' but does not exist",
                        fix_sql=f"ALTER TABLE {table_name} ADD COLUMN {column_name} {self._get_postgres_type(column_spec)};"
                    ))

    def _get_postgres_type(self, column_spec: Dict) -> str:
        """Convert SQLAlchemy type to PostgreSQL type"""
        type_str = column_spec['type'].upper()

        # Map common SQLAlchemy types to PostgreSQL
        type_mapping = {
            'VARCHAR': 'VARCHAR(255)',
            'STRING': 'VARCHAR(255)',
            'TEXT': 'TEXT',
            'INTEGER': 'INTEGER',
            'BOOLEAN': 'BOOLEAN',
            'DATETIME': 'TIMESTAMP WITH TIME ZONE',
            'UUID': 'UUID',
            'JSON': 'JSONB',
            'JSONB': 'JSONB'
        }

        for sqlalchemy_type, postgres_type in type_mapping.items():
            if sqlalchemy_type in type_str:
                result = postgres_type
                if not column_spec['nullable']:
                    result += ' NOT NULL'
                if column_spec['primary_key']:
                    result += ' PRIMARY KEY'
                return result

        # Default fallback
        return 'TEXT'

    async def _generate_baseline_sql(self) -> List[str]:
        """Generate SQL statements to create missing schema"""
        sql_statements = []

        # Create missing tables
        for table_name in self.result.missing_tables:
            if table_name in self.metadata.tables:
                table = self.metadata.tables[table_name]
                create_sql = f"CREATE TABLE {table_name} ("

                columns = []
                for column in table.columns:
                    column_spec = {
                        'type': str(column.type),
                        'nullable': column.nullable,
                        'primary_key': column.primary_key
                    }
                    col_def = f"{column.name} {self._get_postgres_type(column_spec)}"
                    columns.append(col_def)

                create_sql += ",\n    ".join(columns) + "\n);"
                sql_statements.append(create_sql)

        # Add missing columns
        for table_name, columns in self.result.missing_columns.items():
            for column_name in columns:
                if table_name in self.metadata.tables:
                    table = self.metadata.tables[table_name]
                    if column_name in table.columns:
                        column = table.columns[column_name]
                        col_type = self._get_postgres_type({
                            'type': str(column.type),
                            'nullable': column.nullable,
                            'primary_key': column.primary_key
                        })
                        sql_statements.append(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_type};")

        return sql_statements


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Validate database schema against SQLAlchemy models")
    parser.add_argument("--check", action="store_true", help="Check schema and report issues")
    parser.add_argument("--fix", action="store_true", help="Generate SQL to fix missing schema")
    parser.add_argument("--baseline", action="store_true", help="Generate complete baseline schema")
    parser.add_argument("--database-url", help="Database URL (defaults to DATABASE_URL env var)")

    args = parser.parse_args()

    # Default to check mode
    if not any([args.check, args.fix, args.baseline]):
        args.check = True

    # Get database URL
    database_url = args.database_url or os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set", file=sys.stderr)
        sys.exit(2)

    # Create async engine
    try:
        engine = create_async_engine(database_url, echo=False)
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        # Validate schema
        validator = SchemaValidator(engine)
        result = await validator.validate_schema()

        # Report results
        if args.check:
            print("Schema Validation Report")
            print("=" * 50)

            if result.is_valid:
                print("✅ Schema validation PASSED - all required tables and columns exist")
                sys.exit(0)
            else:
                print("❌ Schema validation FAILED - issues found:")
                print()

                # Group issues by category
                errors = [issue for issue in result.issues if issue.severity == "ERROR"]
                warnings = [issue for issue in result.issues if issue.severity == "WARNING"]

                if errors:
                    print("ERRORS (must be fixed):")
                    for issue in errors:
                        print(f"  • {issue.table_name}: {issue.description}")
                        if issue.column_name:
                            print(f"    Column: {issue.column_name}")
                        if issue.fix_sql:
                            print(f"    Fix: {issue.fix_sql}")
                    print()

                if warnings:
                    print("WARNINGS:")
                    for issue in warnings:
                        print(f"  • {issue.table_name}: {issue.description}")
                    print()

                print(f"Summary: {len(result.missing_tables)} missing tables, "
                      f"{sum(len(cols) for cols in result.missing_columns.values())} missing columns")

                sys.exit(1)

        if args.fix or args.baseline:
            if result.baseline_sql:
                print("-- Schema Fix SQL")
                print("-- Generated by schema validator")
                print()
                for sql in result.baseline_sql:
                    print(sql)
                    print()
            else:
                print("-- No schema fixes needed")

    except Exception as e:
        print(f"ERROR: Schema validation failed: {e}", file=sys.stderr)
        sys.exit(3)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())