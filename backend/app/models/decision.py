"""Decision model - tracks resolutions from meetings."""
from datetime import datetime, date
from enum import Enum
from sqlalchemy import String, Text, Integer, Date, Boolean, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, AuditMixin


class DecisionStatus(str, Enum):
    """Status of a decision throughout its lifecycle."""
    DRAFT = "draft"  # Decision draft, not yet voted
    PROPOSED = "proposed"  # Proposed at meeting
    APPROVED = "approved"  # Voted and approved
    REJECTED = "rejected"  # Voted and rejected
    IN_PROGRESS = "in_progress"  # Being implemented
    COMPLETED = "completed"  # Implementation completed
    CANCELLED = "cancelled"  # Cancelled before implementation


class VoteResult(str, Enum):
    """Result of voting on a decision."""
    APPROVED = "approved"  # Majority voted in favor
    REJECTED = "rejected"  # Majority voted against
    NO_QUORUM = "no_quorum"  # No quorum to vote
    TIE = "tie"  # Equal votes (rare, depends on voting rules)


class Decision(Base, TimestampMixin, AuditMixin):
    """Decision/Resolution from a general meeting.
    
    Tracks proposals, voting results, and implementation status.
    All decisions must be linked to a valid meeting with quorum.
    """
    
    __tablename__ = "decisions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Meeting relationship
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Meeting where this decision was made"
    )
    
    # Building relationship (denormalized for easier queries)
    building_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Building this decision applies to"
    )
    
    # Decision info
    decision_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Official decision number (e.g., 'D-2024-001')"
    )
    
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Decision title/summary"
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full description of the decision"
    )
    
    # Voting
    vote_result: Mapped[VoteResult | None] = mapped_column(
        SQLEnum(VoteResult),
        nullable=True,
        comment="Result of the vote"
    )
    
    votes_for: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total ideal parts voted FOR"
    )
    
    votes_against: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total ideal parts voted AGAINST"
    )
    
    votes_abstain: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total ideal parts ABSTAINED"
    )
    
    voted_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="When the vote was taken"
    )
    
    # Implementation
    status: Mapped[DecisionStatus] = mapped_column(
        SQLEnum(DecisionStatus),
        default=DecisionStatus.DRAFT,
        nullable=False,
        index=True,
        comment="Current status of the decision"
    )
    
    implementation_deadline: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Deadline for implementing the decision"
    )
    
    implementation_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Notes about implementation progress"
    )
    
    completed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="When implementation was completed"
    )
    
    # Financial impact
    estimated_cost: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="Estimated cost of implementing decision (in BGN)"
    )
    
    actual_cost: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="Actual cost after implementation (in BGN)"
    )
    
    # Assigned responsibility
    assigned_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User assigned to implement this decision"
    )
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional structured metadata"
    )
    
    # Legal validity
    is_legally_binding: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Whether decision is legally binding (depends on valid quorum)"
    )
    
    # Relationships
    meeting: Mapped["Meeting"] = relationship(back_populates="decisions")
    building: Mapped["Building"] = relationship(back_populates="decisions")
    assigned_to: Mapped["User"] = relationship(foreign_keys=[assigned_to_user_id])
    # votes: Mapped[list["Vote"]] = relationship(back_populates="decision")
    
    def __repr__(self) -> str:
        return f"<Decision(id={self.id}, number='{self.decision_number}', status='{self.status}', result='{self.vote_result}')>"
    
    @property
    def total_votes(self) -> int:
        """Calculate total votes cast."""
        return (self.votes_for or 0) + (self.votes_against or 0) + (self.votes_abstain or 0)
    
    @property
    def approval_percentage(self) -> float | None:
        """Calculate percentage of votes in favor."""
        total = self.total_votes
        if total == 0:
            return None
        return ((self.votes_for or 0) / total) * 100
    
    @property
    def is_approved(self) -> bool:
        """Check if decision was approved."""
        return self.vote_result == VoteResult.APPROVED
    
    @property
    def is_overdue(self) -> bool:
        """Check if implementation is overdue."""
        if not self.implementation_deadline:
            return False
        if self.status in [DecisionStatus.COMPLETED, DecisionStatus.CANCELLED]:
            return False
        return date.today() > self.implementation_deadline
    
    @property
    def requires_action(self) -> bool:
        """Check if decision requires action."""
        return (
            self.is_approved and 
            self.status in [DecisionStatus.APPROVED, DecisionStatus.IN_PROGRESS] and
            not self.completed_at
        )
