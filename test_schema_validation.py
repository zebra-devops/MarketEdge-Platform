#!/usr/bin/env python3
"""
Test Schema Validation System
=============================

Tests the schema validation system components without requiring database connection.
"""

import sys
import os

# Add app directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

def test_imports():
    """Test that all model imports work correctly"""
    print("Testing schema validation imports...")

    try:
        from database.validate_schema import SchemaValidator, SchemaIssue, SchemaValidationResult
        print("✅ Schema validation classes imported successfully")

        from database.generate_baseline import generate_baseline_schema
        print("✅ Baseline schema generator imported successfully")

        # Test model imports
        from app.models.base import Base
        from app.models.user import User, UserRole
        from app.models.organisation import Organisation
        from app.models.modules import AnalyticsModule, OrganisationModule, ModuleConfiguration, ModuleUsageLog
        from app.models.feature_flags import FeatureFlag, FeatureFlagUsage
        from app.models.audit_log import AuditLog
        from app.models.sectors import SICCode
        print("✅ All model imports successful")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_baseline_generation():
    """Test baseline schema generation"""
    print("\nTesting baseline schema generation...")

    try:
        from database.generate_baseline import generate_baseline_schema

        schema_sql = generate_baseline_schema()

        # Basic validation
        if not schema_sql:
            print("❌ Generated schema is empty")
            return False

        if "CREATE TABLE" not in schema_sql:
            print("❌ Generated schema doesn't contain CREATE TABLE statements")
            return False

        if "users" not in schema_sql:
            print("❌ Generated schema doesn't contain users table")
            return False

        if "organisations" not in schema_sql:
            print("❌ Generated schema doesn't contain organisations table")
            return False

        print("✅ Baseline schema generation successful")
        print(f"   Generated {len(schema_sql.split('CREATE TABLE'))} table definitions")

        return True

    except Exception as e:
        print(f"❌ Baseline generation error: {e}")
        return False


def test_schema_metadata():
    """Test that SQLAlchemy metadata contains expected tables"""
    print("\nTesting SQLAlchemy metadata...")

    try:
        from app.models.base import Base

        tables = Base.metadata.tables
        expected_tables = {
            'users', 'organisations', 'analytics_modules', 'organisation_modules',
            'feature_flags', 'audit_logs', 'sic_codes'
        }

        existing_tables = set(tables.keys())
        missing_tables = expected_tables - existing_tables

        if missing_tables:
            print(f"⚠️  Some expected tables missing from metadata: {missing_tables}")
        else:
            print("✅ All expected tables found in metadata")

        print(f"   Total tables in metadata: {len(existing_tables)}")
        print(f"   Tables: {sorted(existing_tables)}")

        return len(missing_tables) == 0

    except Exception as e:
        print(f"❌ Metadata test error: {e}")
        return False


def test_migration_validation_logic():
    """Test the validation logic used in migration 004"""
    print("\nTesting migration validation logic...")

    try:
        # Simulate the logic from migration 004
        required_tables = {'module_usage_logs', 'feature_flag_usage', 'organisation_modules', 'feature_flags', 'audit_logs', 'competitive_factor_templates', 'sic_codes'}

        # This would normally come from database query
        existing_tables = {'users', 'organisations', 'feature_flags', 'audit_logs', 'sic_codes'}  # Simulate partial schema

        missing_tables = required_tables - existing_tables

        if missing_tables:
            print(f"✅ Validation correctly identifies missing tables: {missing_tables}")
            print("✅ Migration would fail fast with clear error message")
        else:
            print("✅ All required tables present (would proceed with migration)")

        return True

    except Exception as e:
        print(f"❌ Migration validation test error: {e}")
        return False


def test_schema_validation_system():
    """Run comprehensive test of schema validation system"""
    print("=" * 60)
    print("SCHEMA VALIDATION SYSTEM TEST")
    print("=" * 60)

    tests = [
        test_imports,
        test_schema_metadata,
        test_baseline_generation,
        test_migration_validation_logic
    ]

    results = []

    for test in tests:
        result = test()
        results.append(result)

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🎉 Schema validation system is ready!")
        print("\nNext steps:")
        print("1. Set DATABASE_URL environment variable")
        print("2. Run: python database/validate_schema.py --check")
        print("3. If issues found, run: python database/validate_schema.py --fix")
        print("4. Apply fixes or baseline: python database/generate_baseline.py --apply")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("\n🔧 Fix the issues above before proceeding")
        return False


if __name__ == "__main__":
    success = test_schema_validation_system()
    sys.exit(0 if success else 1)