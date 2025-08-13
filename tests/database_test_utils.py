"""
Database-agnostic test utilities for multi-tenant testing.

Provides utilities that work with both PostgreSQL (with RLS) and SQLite (for testing).
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, create_engine
import os


class DatabaseTestContext:
    """Context manager for database-agnostic tenant context setting."""
    
    def __init__(self, session: Session, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id
        self.is_postgresql = self._is_postgresql()
        self._original_context = None
        
    def _is_postgresql(self) -> bool:
        """Check if we're using PostgreSQL or SQLite."""
        return self.session.bind.dialect.name == 'postgresql'
    
    def __enter__(self):
        """Set tenant context for the session."""
        if self.is_postgresql:
            # PostgreSQL: Use set_config for RLS
            try:
                self.session.execute(
                    text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
                    {"tenant_id": self.tenant_id}
                )
                self.session.commit()
            except Exception:
                # If RLS settings fail, continue but note it
                pass
        else:
            # SQLite: Store in a mock context (since RLS isn't supported)
            # This allows tests to verify the context setting pattern works
            self._original_context = getattr(self.session, '_test_tenant_id', None)
            self.session._test_tenant_id = self.tenant_id
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up tenant context."""
        if self.is_postgresql:
            try:
                # Reset PostgreSQL settings
                self.session.execute(text("SELECT set_config('app.current_tenant_id', '', true)"))
                self.session.commit()
            except Exception:
                pass
        else:
            # SQLite: Restore original context
            if self._original_context is not None:
                self.session._test_tenant_id = self._original_context
            else:
                if hasattr(self.session, '_test_tenant_id'):
                    delattr(self.session, '_test_tenant_id')
    
    def get_current_tenant_id(self) -> Optional[str]:
        """Get the current tenant ID in a database-agnostic way."""
        if self.is_postgresql:
            try:
                result = self.session.execute(
                    text("SELECT current_setting('app.current_tenant_id', true)")
                ).scalar()
                return result if result and result != '' else None
            except Exception:
                return None
        else:
            # SQLite: Return mock context
            return getattr(self.session, '_test_tenant_id', None)


def set_tenant_context(session: Session, tenant_id: str) -> DatabaseTestContext:
    """Set tenant context for database-agnostic testing."""
    return DatabaseTestContext(session, tenant_id)


def is_postgresql_session(session: Session) -> bool:
    """Check if the session is using PostgreSQL."""
    return session.bind.dialect.name == 'postgresql'


def skip_rls_tests_for_sqlite(session: Session) -> bool:
    """Check if RLS-specific tests should be skipped (i.e., for SQLite)."""
    return not is_postgresql_session(session)


def create_rls_policy_if_postgresql(session: Session, table_name: str, policy_name: str, policy_sql: str):
    """Create RLS policy only if using PostgreSQL."""
    if is_postgresql_session(session):
        try:
            session.execute(text(f"""
                CREATE POLICY IF NOT EXISTS {policy_name} ON {table_name}
                {policy_sql}
            """))
            session.commit()
        except Exception as e:
            # Policy might already exist
            session.rollback()


def enable_rls_if_postgresql(session: Session, table_name: str):
    """Enable Row Level Security only if using PostgreSQL."""
    if is_postgresql_session(session):
        try:
            session.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
            session.commit()
        except Exception as e:
            # RLS might already be enabled
            session.rollback()


def simulate_rls_for_sqlite(session: Session, model_class, tenant_id: str):
    """
    Simulate RLS behavior for SQLite by manually filtering queries.
    
    This is a testing utility to verify that the application logic
    would work correctly with RLS in PostgreSQL.
    """
    if not is_postgresql_session(session):
        # For SQLite testing, we can manually filter by organisation_id
        # This simulates what RLS would do automatically in PostgreSQL
        if hasattr(model_class, 'organisation_id'):
            return session.query(model_class).filter(
                model_class.organisation_id == tenant_id
            )
        else:
            return session.query(model_class)
    else:
        # PostgreSQL: Let RLS handle filtering automatically
        return session.query(model_class)