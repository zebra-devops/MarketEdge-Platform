"""Database type compatibility layer for different database engines."""

from sqlalchemy import TypeDecorator, JSON, Text, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.sql.type_api import UserDefinedType
import json
import uuid


class CompatibleJSON(TypeDecorator):
    """A JSON type that works with both PostgreSQL and SQLite."""
    
    impl = Text
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(Text())
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value  # PostgreSQL handles JSON natively
        else:
            return json.dumps(value)  # For SQLite, serialize to string
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value  # PostgreSQL returns JSON directly
        else:
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return value


class CompatibleUUID(TypeDecorator):
    """A UUID type that works with both PostgreSQL and SQLite."""
    
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value  # PostgreSQL handles UUID natively
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            elif isinstance(value, str):
                # Validate it's a proper UUID
                try:
                    uuid.UUID(value)
                    return value
                except ValueError:
                    return value
            return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value  # PostgreSQL returns UUID directly
        else:
            if isinstance(value, str):
                try:
                    return uuid.UUID(value)
                except ValueError:
                    return value
            return value