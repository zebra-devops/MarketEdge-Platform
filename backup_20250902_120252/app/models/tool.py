from sqlalchemy import String, Boolean, Text
from .database_types import CompatibleJSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional, Dict, Any
from .base import Base


class Tool(Base):
    __tablename__ = "tools"
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(CompatibleJSON)
    pricing_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(CompatibleJSON)
    
    organisation_access: Mapped[List["OrganisationToolAccess"]] = relationship("OrganisationToolAccess", back_populates="tool")