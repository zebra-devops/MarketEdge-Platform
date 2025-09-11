from sqlalchemy import String, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from .base import Base
from .database_types import CompatibleUUID
import enum
import uuid
from datetime import datetime


class ApplicationType(str, enum.Enum):
    """Available applications in the platform"""
    MARKET_EDGE = "MARKET_EDGE"
    CAUSAL_EDGE = "CAUSAL_EDGE"
    VALUE_EDGE = "VALUE_EDGE"
    # Temporary lowercase aliases for database migration
    market_edge = "market_edge"
    causal_edge = "causal_edge"
    value_edge = "value_edge"


class InvitationStatus(str, enum.Enum):
    """User invitation status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"


class UserApplicationAccess(Base):
    """Manages per-user application access permissions"""
    __tablename__ = "user_application_access"
    
    user_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    application: Mapped[str] = mapped_column("application", String(50), nullable=False)
    has_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    granted_by: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="application_access")
    granted_by_user: Mapped["User"] = relationship("User", foreign_keys=[granted_by])
    
    # Composite unique constraint on user_id + application
    __table_args__ = (
        {"extend_existing": True}
    )


class UserInvitation(Base):
    """Manages user invitation workflow"""
    __tablename__ = "user_invitations"
    
    user_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    invitation_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[InvitationStatus] = mapped_column(Enum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False)
    invited_by: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    invited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="invitations")
    invited_by_user: Mapped["User"] = relationship("User", foreign_keys=[invited_by])