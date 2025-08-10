from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid
import enum

from .base import Base


class AuditAction(str, enum.Enum):
    """Types of auditable actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ENABLE = "enable"
    DISABLE = "disable"
    CONFIGURE = "configure"
    EXPORT = "export"
    IMPORT = "import"


class AuditSeverity(str, enum.Enum):
    """Severity levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(Base):
    """
    Comprehensive audit logging for all administrative actions
    Tracks who did what, when, and from where
    """
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Who performed the action
    user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    organisation_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("organisations.id"), nullable=True)
    
    # What action was performed
    action: Mapped[AuditAction] = mapped_column(SQLEnum(AuditAction), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)  # feature_flag, module, user, etc.
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Action details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[AuditSeverity] = mapped_column(SQLEnum(AuditSeverity), default=AuditSeverity.LOW)
    
    # Context information
    changes: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)  # Before/after values
    context_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)  # Additional context
    
    # Request information
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Success/failure tracking
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    organisation = relationship("Organisation", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(action={self.action}, resource={self.resource_type}:{self.resource_id}, user={self.user_id})>"


class AdminAction(Base):
    """
    Track specific administrative actions for compliance
    Higher-level tracking than audit logs
    """
    __tablename__ = "admin_actions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Administrator who performed the action
    admin_user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    
    # Action details
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)  # feature_flag_update, module_enable, etc.
    target_organisation_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("organisations.id"), nullable=True)
    target_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    
    # Action summary
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Impact assessment
    affected_users_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    affected_organisations_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Configuration changes
    configuration_changes: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Approval workflow (if implemented)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    executed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    admin_user = relationship("User", foreign_keys=[admin_user_id], back_populates="admin_actions")
    target_organisation = relationship("Organisation", foreign_keys=[target_organisation_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<AdminAction(type='{self.action_type}', admin={self.admin_user_id}, target_org={self.target_organisation_id})>"