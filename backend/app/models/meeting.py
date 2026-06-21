"""Meeting model - represents general assemblies (общи събрания)."""
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, Integer, DateTime, Boolean, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, AuditMixin


class MeetingType(str, Enum):
    """Type of meeting according to ЗУЕС."""
    REGULAR = "regular"  # Редовно общо събрание
    EXTRAORDINARY = "extraordinary"  # Извънредно общо събрание


class MeetingStatus(str, Enum):
    """Current status of a meeting."""
    DRAFT = "draft"  # Draft meeting, not yet announced
    ANNOUNCED = "announced"  # Invitations sent, meeting scheduled
    IN_PROGRESS = "in_progress"  # Meeting is currently happening
    COMPLETED = "completed"  # Meeting finished, protocol generated
    CANCELLED = "cancelled"  # Meeting was cancelled
    NO_QUORUM = "no_quorum"  # Meeting couldn't proceed due to lack of quorum


class QuorumType(str, Enum):
    """Type of quorum calculation."""
    FIRST_CALL = "first_call"  # Първо свикване (requires >50% ideal parts)
    SECOND_CALL = "second_call"  # Второ свикване (any attendance is valid)


class Meeting(Base, TimestampMixin, AuditMixin):
    """General assembly meeting (Общо събрание).
    
    Represents a formal meeting of building owners according to ЗУЕС.
    Tracks full lifecycle from invitation to protocol generation.
    """
    
    __tablename__ = "meetings"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Building relationship
    building_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Building this meeting belongs to"
    )
    
    # Meeting basic info
    meeting_type: Mapped[MeetingType] = mapped_column(
        SQLEnum(MeetingType),
        nullable=False,
        comment="Type of meeting (regular or extraordinary)"
    )
    
    status: Mapped[MeetingStatus] = mapped_column(
        SQLEnum(MeetingStatus),
        default=MeetingStatus.DRAFT,
        nullable=False,
        index=True,
        comment="Current status of the meeting"
    )
    
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Meeting title"
    )
    
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Meeting description or purpose"
    )
    
    # Scheduling - First Call
    scheduled_at_first: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Scheduled date/time for first call"
    )
    
    location_first: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Location for first call meeting"
    )
    
    # Scheduling - Second Call (if needed)
    scheduled_at_second: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Scheduled date/time for second call (if first call has no quorum)"
    )
    
    location_second: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Location for second call meeting"
    )
    
    # Actual meeting time
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Actual start time of the meeting"
    )
    
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Actual end time of the meeting"
    )
    
    # Quorum tracking
    quorum_type: Mapped[QuorumType | None] = mapped_column(
        SQLEnum(QuorumType),
        nullable=True,
        comment="Which call achieved quorum (first or second)"
    )
    
    total_ideal_parts: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total ideal parts in building at meeting time (snapshot)"
    )
    
    present_ideal_parts: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total ideal parts represented at meeting"
    )
    
    quorum_achieved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether quorum was achieved"
    )
    
    # Agenda
    agenda_items: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Structured agenda items in JSON format"
    )
    
    # Protocol
    protocol_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        index=True,
        comment="Official protocol number (auto-generated)"
    )
    
    protocol_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When protocol was generated"
    )
    
    protocol_file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to generated protocol PDF/DOCX"
    )
    
    # Metadata
    invitation_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When invitations were sent to owners"
    )
    
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes or minutes"
    )
    
    # Relationships
    building: Mapped["Building"] = relationship(back_populates="meetings")
    # attendances: Mapped[list["MeetingAttendance"]] = relationship(back_populates="meeting")
    # decisions: Mapped[list["Decision"]] = relationship(back_populates="meeting")
    # votes: Mapped[list["Vote"]] = relationship(back_populates="meeting")
    
    def __repr__(self) -> str:
        return f"<Meeting(id={self.id}, building_id={self.building_id}, type='{self.meeting_type}', status='{self.status}')>"
    
    @property
    def quorum_percentage(self) -> float | None:
        """Calculate quorum percentage if data available."""
        if self.total_ideal_parts and self.present_ideal_parts:
            return (self.present_ideal_parts / self.total_ideal_parts) * 100
        return None
    
    @property
    def has_valid_quorum(self) -> bool:
        """Check if meeting has valid quorum.
        
        First call: requires >50% of ideal parts
        Second call: any attendance is valid
        """
        if not self.quorum_achieved:
            return False
        
        if self.quorum_type == QuorumType.SECOND_CALL:
            return True  # Second call is always valid if there's attendance
        
        if self.quorum_type == QuorumType.FIRST_CALL:
            percentage = self.quorum_percentage
            return percentage is not None and percentage > 50.0
        
        return False
    
    @property
    def is_active(self) -> bool:
        """Check if meeting is currently active/in progress."""
        return self.status == MeetingStatus.IN_PROGRESS
    
    @property
    def is_finalized(self) -> bool:
        """Check if meeting is completed and finalized."""
        return self.status == MeetingStatus.COMPLETED and self.protocol_generated_at is not None
