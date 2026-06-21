"""AuditLog model - immutable audit trail for legal compliance."""
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditAction(str, Enum):
    """Types of auditable actions in the system."""
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    
    # Building actions
    BUILDING_CREATED = "building.created"
    BUILDING_UPDATED = "building.updated"
    BUILDING_DELETED = "building.deleted"
    
    # Unit actions
    UNIT_CREATED = "unit.created"
    UNIT_UPDATED = "unit.updated"
    UNIT_DELETED = "unit.deleted"
    
    # Meeting actions
    MEETING_CREATED = "meeting.created"
    MEETING_UPDATED = "meeting.updated"
    MEETING_ANNOUNCED = "meeting.announced"
    MEETING_STARTED = "meeting.started"
    MEETING_ENDED = "meeting.ended"
    MEETING_CANCELLED = "meeting.cancelled"
    MEETING_QUORUM_CHECKED = "meeting.quorum_checked"
    MEETING_PROTOCOL_GENERATED = "meeting.protocol_generated"
    
    # Decision actions
    DECISION_CREATED = "decision.created"
    DECISION_PROPOSED = "decision.proposed"
    DECISION_VOTED = "decision.voted"
    DECISION_APPROVED = "decision.approved"
    DECISION_REJECTED = "decision.rejected"
    DECISION_IMPLEMENTATION_STARTED = "decision.implementation_started"
    DECISION_IMPLEMENTATION_COMPLETED = "decision.implementation_completed"
    
    # Vote actions
    VOTE_CAST = "vote.cast"
    VOTE_CHANGED = "vote.changed"
    
    # Financial actions
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_REFUNDED = "payment.refunded"
    OBLIGATION_CREATED = "obligation.created"
    
    # Document actions
    DOCUMENT_GENERATED = "document.generated"
    DOCUMENT_DOWNLOADED = "document.downloaded"
    DOCUMENT_DELETED = "document.deleted"
    
    # System actions
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"
    SYSTEM_MIGRATION = "system.migration"


class AuditLog(Base):
    """Immutable audit log entry.
    
    Records all critical actions in the system for legal compliance.
    Once created, audit log entries MUST NEVER be modified or deleted.
    This provides court-admissible evidence of all system actions.
    """
    
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Timestamp (immutable, set on creation)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Exact timestamp when action occurred (immutable)"
    )
    
    # Action details
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction),
        nullable=False,
        index=True,
        comment="Type of action performed"
    )
    
    # Actor (who performed the action)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who performed the action (null for system actions)"
    )
    
    user_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Email of user at time of action (denormalized for persistence)"
    )
    
    # Target entity (what was affected)
    entity_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Type of entity affected (e.g., 'building', 'meeting', 'decision')"
    )
    
    entity_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="ID of affected entity"
    )
    
    # Building context (for multi-tenancy and filtering)
    building_id: Mapped[int | None] = mapped_column(
        ForeignKey("buildings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Building context if applicable"
    )
    
    # Action details
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable description of what happened"
    )
    
    # State snapshot (before and after)
    state_before: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="State of entity before action (if applicable)"
    )
    
    state_after: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="State of entity after action (if applicable)"
    )
    
    # Additional metadata
    metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional context (IP address, user agent, etc.)"
    )
    
    # Request context
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="IP address of request origin"
    )
    
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="User agent string"
    )
    
    # Severity/importance
    is_critical: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
        comment="Whether this is a critical action requiring special attention"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    building: Mapped["Building"] = relationship(foreign_keys=[building_id])
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id}, timestamp='{self.timestamp}')>"
    
    @property
    def formatted_timestamp(self) -> str:
        """Get formatted timestamp for display."""
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
    
    @property
    def actor_description(self) -> str:
        """Get description of who performed the action."""
        if self.user_email:
            return f"User: {self.user_email}"
        elif self.user_id:
            return f"User ID: {self.user_id}"
        else:
            return "System"
    
    @property
    def target_description(self) -> str:
        """Get description of what was affected."""
        if self.entity_type and self.entity_id:
            return f"{self.entity_type} #{self.entity_id}"
        return "N/A"
