from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Dict, List, Any
from .base import Base
from .database_types import CompatibleUUID, CompatibleJSON
import uuid


class OrganisationToolAccess(Base):
    __tablename__ = "organisation_tool_access"
    
    organisation_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("organisations.id"), nullable=False)
    tool_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("tools.id"), nullable=False)
    subscription_tier: Mapped[str] = mapped_column(String(50), nullable=False)
    features_enabled: Mapped[List[Any]] = mapped_column(CompatibleJSON(), default=list)
    usage_limits: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON(), default=dict)
    
    organisation: Mapped["Organisation"] = relationship("Organisation", back_populates="tool_access")
    tool: Mapped["Tool"] = relationship("Tool", back_populates="organisation_access")