from sqlalchemy import String, Boolean, ForeignKey, Enum, Integer, Text, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base
from .database_types import CompatibleUUID
from datetime import datetime
import enum
import uuid


class ImportStatus(str, enum.Enum):
    """Import batch status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImportBatch(Base):
    """Track CSV import batches"""
    __tablename__ = "import_batches"
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(Enum(ImportStatus), default=ImportStatus.PENDING, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Import configuration
    organisation_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("organisations.id"), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    
    # Processing details
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relationships
    organisation = relationship("Organisation")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    import_errors = relationship("ImportError", back_populates="import_batch", cascade="all, delete-orphan")


class ImportError(Base):
    """Track individual row errors during import"""
    __tablename__ = "import_errors"
    
    import_batch_id: Mapped[uuid.UUID] = mapped_column(CompatibleUUID(), ForeignKey("import_batches.id"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    row_data: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string of the row data
    
    # Relationships
    import_batch = relationship("ImportBatch", back_populates="import_errors")