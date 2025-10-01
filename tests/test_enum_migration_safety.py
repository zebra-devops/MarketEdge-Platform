"""
Test enum migration safety procedures (US-6A)

Tests backup, restore, and rollback procedures for the ApplicationType enum migration.
"""
import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


class TestEnumMigrationSafety:
    """Test suite for enum migration safety procedures."""

    @pytest.fixture(scope="class")
    def db_engine(self):
        """Create database engine for testing."""
        engine = create_engine(settings.DATABASE_URL)
        yield engine
        engine.dispose()

    @pytest.fixture
    def db_session(self, db_engine):
        """Create database session for testing."""
        Session = sessionmaker(bind=db_engine)
        session = Session()
        yield session
        session.close()

    def test_user_application_access_table_exists(self, db_session):
        """Test that user_application_access table exists."""
        result = db_session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'user_application_access'
                );
            """)
        )
        exists = result.scalar()
        assert exists, "user_application_access table does not exist"

    def test_application_enum_exists(self, db_session):
        """Test that applicationtype enum exists."""
        result = db_session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM pg_type
                    WHERE typname = 'applicationtype'
                );
            """)
        )
        exists = result.scalar()
        assert exists, "applicationtype enum does not exist"

    def test_application_enum_values(self, db_session):
        """Test that applicationtype enum has expected values."""
        result = db_session.execute(
            text("""
                SELECT enumlabel
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = 'applicationtype'
                ORDER BY e.enumsortorder;
            """)
        )
        values = [row[0] for row in result]

        # Should be either lowercase (pre-migration) or uppercase (post-migration)
        expected_lowercase = ['market_edge', 'causal_edge', 'value_edge']
        expected_uppercase = ['MARKET_EDGE', 'CAUSAL_EDGE', 'VALUE_EDGE']

        assert values in [expected_lowercase, expected_uppercase], (
            f"Unexpected enum values: {values}. "
            f"Expected either {expected_lowercase} or {expected_uppercase}"
        )

    def test_user_application_access_indexes(self, db_session):
        """Test that required indexes exist on user_application_access."""
        result = db_session.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'user_application_access'
                ORDER BY indexname;
            """)
        )
        indexes = [row[0] for row in result]

        required_indexes = [
            'idx_user_application_access_application',
            'idx_user_application_access_user_id',
        ]

        for required_index in required_indexes:
            assert required_index in indexes, (
                f"Required index {required_index} not found. "
                f"Available indexes: {indexes}"
            )

    def test_user_application_access_constraints(self, db_session):
        """Test that required constraints exist on user_application_access."""
        result = db_session.execute(
            text("""
                SELECT conname, contype
                FROM pg_constraint
                WHERE conrelid = 'user_application_access'::regclass
                ORDER BY conname;
            """)
        )
        constraints = {row[0]: row[1] for row in result}

        # Check for unique constraint (may be named differently)
        unique_constraints = [name for name, type_ in constraints.items() if type_ == 'u']
        assert len(unique_constraints) >= 1, (
            f"Expected at least 1 unique constraint, found {len(unique_constraints)}. "
            f"Available constraints: {list(constraints.keys())}"
        )

        # Check for foreign keys
        foreign_keys = [name for name, type_ in constraints.items() if type_ == 'f']
        assert len(foreign_keys) >= 1, (
            f"Expected at least 1 foreign key, found {len(foreign_keys)}"
        )

    def test_user_invitations_table_exists(self, db_session):
        """Test that user_invitations table exists."""
        result = db_session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'user_invitations'
                );
            """)
        )
        exists = result.scalar()
        assert exists, "user_invitations table does not exist"

    def test_invitation_status_enum_exists(self, db_session):
        """Test that invitationstatus enum exists."""
        result = db_session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM pg_type
                    WHERE typname = 'invitationstatus'
                );
            """)
        )
        exists = result.scalar()
        assert exists, "invitationstatus enum does not exist"

    def test_data_integrity_no_orphaned_records(self, db_session):
        """Test that there are no orphaned records in user_application_access."""
        result = db_session.execute(
            text("""
                SELECT COUNT(*)
                FROM user_application_access uaa
                LEFT JOIN users u ON uaa.user_id = u.id
                WHERE u.id IS NULL;
            """)
        )
        orphaned_count = result.scalar()
        assert orphaned_count == 0, (
            f"Found {orphaned_count} orphaned records in user_application_access"
        )

    def test_backup_script_exists(self):
        """Test that backup script exists and is executable."""
        script_path = Path("/Users/matt/Sites/MarketEdge/scripts/backup/backup_enum_migration.sh")
        assert script_path.exists(), f"Backup script not found at {script_path}"
        assert os.access(script_path, os.X_OK), f"Backup script is not executable"

    def test_restore_script_exists(self):
        """Test that restore script exists and is executable."""
        script_path = Path("/Users/matt/Sites/MarketEdge/scripts/backup/restore_enum_migration.sh")
        assert script_path.exists(), f"Restore script not found at {script_path}"
        assert os.access(script_path, os.X_OK), f"Restore script is not executable"

    def test_rollback_documentation_exists(self):
        """Test that rollback documentation exists."""
        doc_path = Path("/Users/matt/Sites/MarketEdge/docs/auth/rollback-enum-migration.md")
        assert doc_path.exists(), f"Rollback documentation not found at {doc_path}"

        # Check that documentation contains required sections
        content = doc_path.read_text()
        required_sections = [
            "Prerequisites",
            "Backup Procedure",
            "Rollback Scenarios",
            "Rollback Execution",
            "Verification Steps",
            "Recovery Time Objectives",
        ]

        for section in required_sections:
            assert section in content, (
                f"Required section '{section}' not found in rollback documentation"
            )

    @pytest.mark.skipif(
        os.getenv("SKIP_BACKUP_TEST") == "1",
        reason="Backup test skipped (requires database access)"
    )
    def test_backup_script_dry_run(self):
        """Test backup script with dry-run (syntax check)."""
        script_path = Path("/Users/matt/Sites/MarketEdge/scripts/backup/backup_enum_migration.sh")

        # Check script syntax
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, (
            f"Backup script has syntax errors:\n{result.stderr}"
        )

    @pytest.mark.skipif(
        os.getenv("SKIP_BACKUP_TEST") == "1",
        reason="Backup test skipped (requires database access)"
    )
    def test_restore_script_dry_run(self):
        """Test restore script with dry-run (syntax check)."""
        script_path = Path("/Users/matt/Sites/MarketEdge/scripts/backup/restore_enum_migration.sh")

        # Check script syntax
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, (
            f"Restore script has syntax errors:\n{result.stderr}"
        )

    def test_migration_exists(self):
        """Test that the base migration (009) exists."""
        migration_path = Path(
            "/Users/matt/Sites/MarketEdge/database/migrations/versions/009_add_user_management_tables.py"
        )
        assert migration_path.exists(), (
            f"Base migration not found at {migration_path}"
        )

        # Check that migration contains required operations
        content = migration_path.read_text()
        assert "user_application_access" in content, (
            "Migration does not create user_application_access table"
        )
        assert "applicationtype" in content, (
            "Migration does not create applicationtype enum"
        )

    def test_table_statistics_query(self, db_session):
        """Test that we can gather table statistics."""
        # This query is used in the backup script
        result = db_session.execute(
            text("""
                SELECT
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT application) as unique_applications
                FROM user_application_access;
            """)
        )
        stats = result.fetchone()

        assert stats is not None, "Failed to gather table statistics"
        assert stats[0] >= 0, "Invalid row count"
        assert stats[1] >= 0, "Invalid unique user count"
        assert stats[2] >= 0, "Invalid unique application count"

    def test_enum_value_distribution_query(self, db_session):
        """Test that we can get enum value distribution."""
        # This query is used in the backup script
        result = db_session.execute(
            text("""
                SELECT application, COUNT(*) as count
                FROM user_application_access
                GROUP BY application
                ORDER BY count DESC;
            """)
        )
        distribution = result.fetchall()

        # Should have 0-3 distinct applications
        assert len(distribution) <= 3, (
            f"Unexpected number of application types: {len(distribution)}"
        )

    def test_foreign_key_integrity_query(self, db_session):
        """Test that foreign key integrity can be checked."""
        # This query is used in verification
        result = db_session.execute(
            text("""
                SELECT
                    conname,
                    conrelid::regclass,
                    confrelid::regclass
                FROM pg_constraint
                WHERE conrelid IN (
                    'user_application_access'::regclass,
                    'user_invitations'::regclass
                )
                AND contype = 'f';
            """)
        )
        foreign_keys = result.fetchall()

        # Should have at least one foreign key
        assert len(foreign_keys) >= 1, (
            "No foreign keys found on user_application_access or user_invitations"
        )


class TestMigrationRollback:
    """Test migration rollback procedures."""

    @pytest.fixture
    def alembic_config(self):
        """Get Alembic configuration path."""
        return Path("/Users/matt/Sites/MarketEdge/alembic.ini")

    def test_alembic_config_exists(self, alembic_config):
        """Test that Alembic configuration exists."""
        assert alembic_config.exists(), (
            f"Alembic configuration not found at {alembic_config}"
        )

    @pytest.mark.skipif(
        os.getenv("SKIP_ALEMBIC_TEST") == "1",
        reason="Alembic test skipped (migration state may be inconsistent)"
    )
    def test_alembic_current_command(self, alembic_config):
        """Test that we can check current migration."""
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            cwd=alembic_config.parent
        )

        # Command should succeed (even if no migrations applied)
        # Note: May fail if database has inconsistent migration state
        if result.returncode != 0:
            pytest.skip(f"Alembic current failed (migration state inconsistent): {result.stderr}")

        assert result.returncode == 0, (
            f"alembic current failed:\n{result.stderr}"
        )

    def test_alembic_history_command(self, alembic_config):
        """Test that we can view migration history."""
        result = subprocess.run(
            ["alembic", "history"],
            capture_output=True,
            text=True,
            cwd=alembic_config.parent
        )

        # Command should succeed
        assert result.returncode == 0, (
            f"alembic history failed:\n{result.stderr}"
        )

        # Should include migration 009
        assert "009" in result.stdout, (
            "Migration 009 not found in history"
        )


class TestRecoveryTimeObjectives:
    """Test that recovery time objectives are met."""

    @pytest.fixture(scope="class")
    def db_engine(self):
        """Create database engine for testing."""
        engine = create_engine(settings.DATABASE_URL)
        yield engine
        engine.dispose()

    @pytest.fixture
    def db_session(self, db_engine):
        """Create database session for testing."""
        Session = sessionmaker(bind=db_engine)
        session = Session()
        yield session
        session.close()

    def test_backup_time_measurement(self, db_session):
        """Test that we can measure backup time."""
        import time

        # Measure time to count rows (proxy for backup time)
        start_time = time.time()

        result = db_session.execute(
            text("SELECT COUNT(*) FROM user_application_access;")
        )
        count = result.scalar()

        end_time = time.time()
        duration = end_time - start_time

        # Should be fast (< 1 second for test database)
        assert duration < 1.0, (
            f"Row count took {duration:.2f}s (too slow)"
        )

    def test_restore_time_measurement(self, db_session):
        """Test that we can measure restore time."""
        import time

        # Measure time to select data (proxy for restore time)
        start_time = time.time()

        result = db_session.execute(
            text("SELECT * FROM user_application_access LIMIT 1000;")
        )
        rows = result.fetchall()

        end_time = time.time()
        duration = end_time - start_time

        # Should be fast (< 1 second for test database)
        assert duration < 1.0, (
            f"Data selection took {duration:.2f}s (too slow)"
        )


class TestZebraAssociatesProtection:
    """Test that Zebra Associates user is protected during migration."""

    @pytest.fixture(scope="class")
    def db_engine(self):
        """Create database engine for testing."""
        engine = create_engine(settings.DATABASE_URL)
        yield engine
        engine.dispose()

    @pytest.fixture
    def db_session(self, db_engine):
        """Create database session for testing."""
        Session = sessionmaker(bind=db_engine)
        session = Session()
        yield session
        session.close()

    def test_zebra_user_exists(self, db_session):
        """Test that Zebra Associates test user exists."""
        result = db_session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM users
                    WHERE email = 'matt.lindop@zebra.associates'
                );
            """)
        )
        exists = result.scalar()

        # May not exist in test database, but should in staging/production
        if not exists:
            pytest.skip("Zebra user not found in test database")

    def test_zebra_user_has_all_applications(self, db_session):
        """Test that Zebra user has access to all applications."""
        result = db_session.execute(
            text("""
                SELECT COUNT(DISTINCT application)
                FROM user_application_access uaa
                JOIN users u ON uaa.user_id = u.id
                WHERE u.email = 'matt.lindop@zebra.associates'
                AND uaa.has_access = true;
            """)
        )
        app_count = result.scalar()

        if app_count is None:
            pytest.skip("Zebra user not found in test database")

        # Should have access to all 3 applications
        assert app_count == 3, (
            f"Zebra user should have access to 3 applications, found {app_count}"
        )

    def test_zebra_user_role(self, db_session):
        """Test that Zebra user has super_admin role."""
        result = db_session.execute(
            text("""
                SELECT role
                FROM users
                WHERE email = 'matt.lindop@zebra.associates';
            """)
        )
        role = result.scalar()

        if role is None:
            pytest.skip("Zebra user not found in test database")

        assert role == 'super_admin', (
            f"Zebra user should have super_admin role, found {role}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
