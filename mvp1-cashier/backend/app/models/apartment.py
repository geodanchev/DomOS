"""Apartment model - домова книга."""

from sqlalchemy import String, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.monthly_charge import MonthlyCharge


class Apartment(Base, TimestampMixin):
    """Апартамент в сградата.
    
    Пример:
        Апартамент | Собственик | Живущи | Такса
        1          | Иван       | 2      | 15 лв
        2          | Мария      | 4      | 30 лв
    """
    
    __tablename__ = "apartments"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Номер на апартамента
    number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        comment="Номер на апартамента (напр. '1', '12А')"
    )
    
    # Етаж
    floor: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Етаж (0 за партер, отрицателни за сутерен)"
    )
    
    # Собственик
    owner_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Име на собственика"
    )
    
    # Брой живущи
    residents_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Брой живущи в апартамента"
    )
    
    # Месечна такса (в лева)
    monthly_fee: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Месечна такса в лева"
    )
    
    # Бележки
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Допълнителни бележки"
    )
    
    # Relationships
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="apartment",
        cascade="all, delete-orphan"
    )
    
    monthly_charges: Mapped[list["MonthlyCharge"]] = relationship(
        back_populates="apartment",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Apartment(id={self.id}, number='{self.number}', owner='{self.owner_name}')>"
