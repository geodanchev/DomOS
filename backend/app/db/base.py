"""Database base configuration and mixins."""
from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class AuditMixin:
    """Mixin for audit trail tracking.
    
    Records who created/modified the record.
    Note: Actual detailed audit logs are in separate AuditLog table.
    """
    
    created_by_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="User ID who created this record"
    )
    
    updated_by_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="User ID who last updated this record"
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality.
    
    Instead of deleting records, we mark them as deleted.
    This is important for legal compliance and audit trails.
    """
    
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when record was soft-deleted"
    )
    
    deleted_by_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="User ID who deleted this record"
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None
