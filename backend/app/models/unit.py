"""Unit model - represents individual apartments/units in a building."""
from enum import Enum
from sqlalchemy import String, Text, Integer, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, AuditMixin, SoftDeleteMixin


class UnitType(str, Enum):
    """Type of unit in the building."""
    APARTMENT = "apartment"  # Жилище
    GARAGE = "garage"  # Гараж
    STORAGE = "storage"  # Избено помещение
    COMMERCIAL = "commercial"  # Търговски обект
    OFFICE = "office"  # Офис
    OTHER = "other"  # Друго


class Unit(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Individual unit (apartment, garage, etc.) in a building.
    
    Each unit has ownership shares (ideal parts) that determine voting power.
    Multiple owners can share ownership of a single unit.
    """
    
    __tablename__ = "units"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Building relationship
    building_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Building this unit belongs to"
    )
    
    # Unit identification
    unit_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Unit number (e.g., 'А12', '5', 'Г-3')"
    )
    
    entrance: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Entrance identifier (e.g., 'А', 'Б', '1')"
    )
    
    floor: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Floor number (0 for ground floor, negative for basement)"
    )
    
    # Unit details
    unit_type: Mapped[UnitType] = mapped_column(
        SQLEnum(UnitType),
        default=UnitType.APARTMENT,
        nullable=False,
        comment="Type of unit"
    )
    
    area_sqm: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Unit area in square meters"
    )
    
    rooms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of rooms (for apartments)"
    )
    
    # Ownership shares (идеални части)
    ideal_parts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Ideal parts (ownership share) - determines voting power"
    )
    
    # Legal information
    cadastral_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
        comment="Cadastral number from property registry"
    )
    
    # Additional info
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional description or notes"
    )
    
    # Status
    is_occupied: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Whether unit is currently occupied"
    )
    
    # Relationships
    building: Mapped["Building"] = relationship(back_populates="units")
    # ownerships: Mapped[list["Ownership"]] = relationship(back_populates="unit")
    # residencies: Mapped[list["Residency"]] = relationship(back_populates="unit")
    # obligations: Mapped[list["FinancialObligation"]] = relationship(back_populates="unit")
    
    def __repr__(self) -> str:
        return f"<Unit(id={self.id}, building_id={self.building_id}, number='{self.unit_number}', ideal_parts={self.ideal_parts})>"
    
    @property
    def full_identifier(self) -> str:
        """Get full unit identifier with entrance and floor."""
        parts = []
        if self.entrance:
            parts.append(f"вх. {self.entrance}")
        if self.floor is not None:
            parts.append(f"ет. {self.floor}")
        parts.append(f"ап. {self.unit_number}")
        return ", ".join(parts)
    
    @property
    def ownership_percentage(self) -> float:
        """Calculate ownership percentage based on ideal parts.
        
        Assumes building.total_ideal_parts = 1000 for percentage calculation.
        """
        # This will need access to building.total_ideal_parts in actual implementation
        return (self.ideal_parts / 1000) * 100
