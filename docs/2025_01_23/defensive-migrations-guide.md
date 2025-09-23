# Defensive Database Migration Guide

## Overview

This guide documents the defensive migration patterns implemented to prevent the "whack-a-mole" deployment issues where missing prerequisites surface one column at a time, causing endless deployment failures.

## Problem Statement

The original migrations assumed prerequisites existed without validation, leading to:
- Migrations failing one column/table at a time
- Partial schema states that are difficult to repair
- Deployment failures that require manual intervention
- Unclear error messages that don't indicate root causes

## Solution: Defensive Migration Patterns

### 1. Migration Utilities Module (`database/migrations/utils.py`)

A comprehensive utility module providing:

#### Core Validator Class
```python
from database.migrations.utils import get_validator

validator = get_validator()
```

#### Key Methods

- **`table_exists(table_name)`** - Check if a table exists
- **`column_exists(table_name, column_name)`** - Check if a column exists
- **`columns_exist(table_name, column_names)`** - Check multiple columns
- **`index_exists(index_name, table_name)`** - Check if an index exists
- **`constraint_exists(constraint_name, table_name)`** - Check if a constraint exists
- **`validate_prerequisites(...)`** - Comprehensive validation with fail-fast behavior
- **`safe_add_column(...)`** - Add column only if it doesn't exist
- **`safe_create_index(...)`** - Create index only if needed
- **`safe_create_check_constraint(...)`** - Create constraint safely
- **`safe_drop_index(...)`** - Drop index if it exists
- **`safe_drop_constraint(...)`** - Drop constraint if it exists

### 2. Fail-Fast Validation Pattern

Migrations now validate ALL prerequisites upfront and fail immediately with clear error messages:

```python
def upgrade():
    from database.migrations.utils import get_validator, fail_fast

    validator = get_validator()

    # Define all prerequisites
    required_tables = {'users', 'organisations', 'audit_logs'}
    required_columns = {
        'users': ['id', 'email', 'organisation_id'],
        'audit_logs': ['id', 'user_id', 'action']
    }

    # Validate everything upfront
    try:
        validator.validate_prerequisites(
            required_tables=required_tables,
            required_columns=required_columns,
            migration_id='004'
        )
    except Exception as e:
        # Clear error message with recovery instructions
        print(e)
        raise
```

### 3. Safe Operation Pattern

All operations now check prerequisites before attempting changes:

```python
# Instead of blind operations that might fail
op.create_index('idx_users_email', 'users', ['email'])

# Use safe operations that check first
validator.safe_create_index(
    'idx_users_email',
    'users',
    ['email']
)
```

### 4. Enhanced Error Messages

When migrations fail, they now provide:
- Clear description of what's missing
- Diagnostic information about current state
- Specific commands to run for recovery
- References to repair tools

Example error output:
```
============================================================
MIGRATION ERROR
============================================================
Migration 004: Prerequisites validation FAILED!

MISSING PREREQUISITES:
  - Missing required tables: ['audit_logs', 'feature_flags']
  - Table 'users' is missing columns: ['organisation_id', 'role']

ACTION REQUIRED:
  1. Check if previous migrations completed successfully:
     alembic current

  2. If migrations are out of order, create a repair migration:
     python database/create_repair_migration.py

  3. For missing base schema, run:
     python database/validate_schema.py --fix

  4. To apply all pending migrations:
     alembic upgrade head
============================================================
```

## Updated Migration Files

### Migration 004: Security Constraints
- Full prerequisite validation for all tables and columns
- Safe index creation with column existence checks
- Optional column handling (doesn't fail if optional columns missing)
- Comprehensive error reporting with recovery instructions

### Migration 005: Row Level Security
- Graceful handling of missing tables
- Column validation before applying RLS
- Partial success reporting (shows what worked and what didn't)
- Clear warnings for skipped operations

## Repair Migration Generator

The `create_repair_migration.py` script automatically generates migrations to fix missing prerequisites:

### Usage
```bash
# Analyze database and create repair migration
python database/create_repair_migration.py

# Preview without saving
python database/create_repair_migration.py --dry-run

# Custom migration name
python database/create_repair_migration.py --name fix_missing_tables
```

### Features
- Analyzes current database state
- Identifies all missing tables, columns, and indexes
- Generates a complete repair migration
- Provides clear next steps

## Migration Best Practices

### 1. Always Use the Validator
```python
def upgrade():
    from database.migrations.utils import get_validator
    validator = get_validator()

    # Use validator for all operations
    validator.safe_create_index(...)
    validator.safe_add_column(...)
```

### 2. Define Prerequisites Upfront
```python
# At the start of upgrade()
required_tables = {...}
required_columns = {...}
optional_columns = {...}  # Won't fail if missing

validator.validate_prerequisites(
    required_tables=required_tables,
    required_columns=required_columns,
    migration_id='my_migration'
)
```

### 3. Handle Partial Failures Gracefully
```python
successful_operations = []
failed_operations = []

for table in tables_to_modify:
    try:
        # Attempt operation
        op.alter_table(...)
        successful_operations.append(table)
    except Exception as e:
        print(f"WARNING: Failed to modify {table}: {e}")
        failed_operations.append(table)

# Report summary at the end
if failed_operations:
    print(f"Some operations failed: {failed_operations}")
```

### 4. Provide Clear Downgrade Paths
```python
def downgrade():
    validator = get_validator()

    # Use safe drop operations
    validator.safe_drop_index('idx_name', 'table_name')
    validator.safe_drop_constraint('constraint_name', 'table_name')
```

## Deployment Process

### Standard Deployment
1. Run migrations with defensive patterns
2. Review output for any warnings
3. If failures occur, follow provided instructions

### Recovery from Failures
1. Check current migration state: `alembic current`
2. Review migration history: `alembic history`
3. Generate repair migration if needed: `python database/create_repair_migration.py`
4. Apply repair: `alembic upgrade head`
5. Verify success: `python database/validate_schema.py --check`

### Emergency Procedures
If migrations are severely broken:

1. **Generate comprehensive repair:**
   ```bash
   python database/create_repair_migration.py
   ```

2. **Review generated migration:**
   Check the repair migration file for accuracy

3. **Apply repair:**
   ```bash
   alembic upgrade head
   ```

4. **Validate schema:**
   ```bash
   python database/validate_schema.py --check
   ```

## Benefits of Defensive Patterns

1. **Fail Fast:** Issues are caught immediately, not one at a time
2. **Clear Errors:** Developers know exactly what's wrong and how to fix it
3. **Safe Operations:** No partial failures or corrupted states
4. **Easy Recovery:** Automated tools for generating repairs
5. **Maintainability:** Future migrations are more resilient

## Common Issues and Solutions

### Issue: Migration fails with missing table
**Solution:** Use validator to check table existence first:
```python
if validator.table_exists('my_table'):
    # Perform operations
else:
    print("WARNING: Table 'my_table' not found - skipping")
```

### Issue: Index creation fails on missing column
**Solution:** Validate columns before creating index:
```python
validator.safe_create_index(
    'idx_name',
    'table_name',
    ['column1', 'column2']  # Will check columns exist
)
```

### Issue: Constraint fails on incompatible data
**Solution:** Add data validation before constraint:
```python
# Check data compatibility
result = connection.execute(
    "SELECT COUNT(*) FROM table WHERE condition"
)
if result.scalar() == 0:
    validator.safe_create_check_constraint(...)
else:
    print("WARNING: Data not compatible with constraint")
```

## Testing Migrations

### Local Testing
```bash
# Reset to clean state
alembic downgrade base

# Apply migrations one by one
alembic upgrade +1
alembic upgrade +1
# ... continue until all applied

# Verify final state
python database/validate_schema.py --check
```

### Staging Testing
1. Clone production database to staging
2. Apply migrations with verbose output
3. Review all warnings and errors
4. Test application functionality
5. Generate repair migration if needed

## Summary

The defensive migration patterns transform fragile, assumption-based migrations into robust, self-validating operations that:
- Fail fast with clear error messages
- Provide specific recovery instructions
- Handle partial failures gracefully
- Make deployments more reliable

This approach prevents the cascade of deployment failures and makes database schema management predictable and maintainable.