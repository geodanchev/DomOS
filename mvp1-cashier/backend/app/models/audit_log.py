"""AuditLog model - immutable audit trail for legal compliance.

Simplified version for MVP1-Cashier.
Всички критични действия се записват и НИКОГА не се изтриват.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditAction(str, Enum):
    """Types of auditable actions."""
    # Payment actions
    PAYMENT_CREATED = "payment.created"
    PAYMENT_VOIDED = "payment.voided"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # Obligation actions
    OBLIGATION_CREATED = "obligation.created"
    OBLIGATION_UPDATED = "obligation.updated"
    OBLIGATION_DELETED = "obligation.deleted"
    
    # Expense actions
    EXPENSE_CREATED = "expense.created"
    EXPENSE_UPDATED = "expense.updated"
    EXPENSE_DELETED = "expense.deleted"
    
    # Account actions
    ACCOUNT_CREDIT = "account.credit"
    ACCOUNT_DEBIT = "account.debit"
    ACCOUNT_ADJUSTMENT = "account.adjustment"
    
    # Receipt actions
    RECEIPT_GENERATED = "receipt.generated"
    RECEIPT_PRINTED = "receipt.printed"
    
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    
    # System actions
    SYSTEM_BACKUP = "system.backup"


class AuditLog(Base):
    """Immutable audit log entry.
    
    Records all critical actions for legal compliance.
    Once created, entries MUST NEVER be modified or deleted.
    """
    
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Timestamp (immutable)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Exact timestamp when action occurred"
    )
    
    # Action type
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of action performed"
    )
    
    # Actor (who performed the action)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who performed the action"
    )
    
    user_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Email at time of action (denormalized)"
    )
    
    # Target entity
    entity_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Type of entity affected (payment, obligation, etc.)"
    )
    
    entity_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="ID of affected entity"
    )
    
    # Apartment context (for filtering)
    apartment_id: Mapped[int | None] = mapped_column(
        ForeignKey("apartments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Apartment context if applicable"
    )
    
    # Description
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable description"
    )
    
    # State snapshots (before/after for changes)
    state_before: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="State before action"
    )
    
    state_after: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="State after action"
    )
    
    # Additional metadata
    extra_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional context (reason, IP, etc.)"
    )
    
    # Request context
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="IP address"
    )
    
    # Critical flag
    is_critical: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
        comment="Critical action flag"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', timestamp='{self.timestamp}')>"


# === Audit Service Functions ===

def create_audit_log(
    db,
    action: str | AuditAction,
    description: str,
    user_id: int | None = None,
    user_email: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    apartment_id: int | None = None,
    state_before: dict | None = None,
    state_after: dict | None = None,
    extra_data: dict | None = None,
    ip_address: str | None = None,
    is_critical: bool = False,
) -> AuditLog:
    """Create an immutable audit log entry.
    
    Args:
        db: Database session
        action: Action type (string or AuditAction enum)
        description: Human-readable description
        user_id: ID of user who performed action
        user_email: Email (denormalized for persistence)
        entity_type: Type of affected entity
        entity_id: ID of affected entity
        apartment_id: Apartment context
        state_before: State before action
        state_after: State after action
        metadata: Additional context
        ip_address: Request IP address
        is_critical: Whether this is a critical action
    
    Returns:
        Created AuditLog entry
    """
    action_str = action.value if isinstance(action, AuditAction) else action
    
    audit_entry = AuditLog(
        timestamp=datetime.utcnow(),
        action=action_str,
        user_id=user_id,
        user_email=user_email,
        entity_type=entity_type,
        entity_id=entity_id,
        apartment_id=apartment_id,
        description=description,
        state_before=state_before,
        state_after=state_after,
        extra_data=extra_data,
        ip_address=ip_address,
        is_critical=is_critical,
    )
    
    db.add(audit_entry)
    # Note: Caller should commit the transaction
    
    return audit_entry
