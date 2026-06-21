"""Building model - core entity representing a residential building."""
from sqlalchemy import String, Text, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, AuditMixin, SoftDeleteMixin


class Building(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Residential building (етажна собственост).
    
    Represents a single building managed under ЗУЕС.
    This is the primary tenant entity in the multi-tenant architecture.
    """
    
    __tablename__ = "buildings"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Basic Information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Building name or identifier"
    )
    
    # Address
    address_street: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Street address"
    )
    
    address_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Building number"
    )
    
    address_city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="City"
    )
    
    address_postal_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Postal code"
    )
    
    address_district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="District/Region"
    )
    
    # Building Details
    total_floors: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total number of floors"
    )
    
    total_entrances: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total number of entrances"
    )
    
    year_built: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Year of construction"
    )
    
    # Legal Information
    registration_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
        comment="Legal registration number (from cadastre)"
    )
    
    tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Tax identification number (ЕИК/БУЛСТАТ)"
    )
    
    # Financial
    bank_account: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Building's bank account (IBAN)"
    )
    
    # Ownership shares
    total_ideal_parts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000,
        comment="Total ideal parts (default 1000 for percentage-based calculation)"
    )
    
    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes about the building"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Whether building is actively managed"
    )
    
    # Relationships
    # entrances: Mapped[list["Entrance"]] = relationship(back_populates="building")
    # units: Mapped[list["Unit"]] = relationship(back_populates="building")
    # meetings: Mapped[list["Meeting"]] = relationship(back_populates="building")
    # managers: Mapped[list["BuildingManager"]] = relationship(back_populates="building")
    
    def __repr__(self) -> str:
        return f"<Building(id={self.id}, name='{self.name}', address='{self.full_address}')>"
    
    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [
            f"ул. {self.address_street}",
            f"№ {self.address_number}",
            self.address_city
        ]
        if self.address_postal_code:
            parts.append(self.address_postal_code)
        return ", ".join(parts)
