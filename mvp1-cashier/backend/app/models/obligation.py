"""Obligation model - задължения.

Актуализирано: Account-based система.
- Премахнати: amount_paid, status (балансът се следи в ApartmentAccount)
- Полето amount_due е преименувано на amount
- При създаване на Obligation, сумата автоматично се дебитира от сметката
"""

from enum import Enum
from decimal import Decimal
from sqlalchemy import String, Numeric, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.apartment import Apartment


class ObligationType(str, Enum):
    """Тип на задължението."""
    MONTHLY = "monthly"          # Месечна такса
    INITIAL = "initial"          # Начално задължение (преди старт на системата)
    PENALTY = "penalty"          # Глоба/санкция
    REPAIR = "repair"            # Ремонт
    FUND = "fund"                # Вноска във фонд
    OTHER = "other"              # Друго


class Obligation(Base, TimestampMixin):
    """Задължение за апартамент.
    
    Всяко задължение е дебит от сметката на апартамента.
    При създаване автоматично се изважда от баланса.
    
    Примери:
        Тип     | Ап. | Собственик | Месец   | Сума  | Описание
        monthly | 1   | Иван       | 2024-01 | 15.00 | Месечна такса
        monthly | 2   | Мария      | 2024-01 | 30.00 | Месечна такса
        initial | 3   | Петър      | -       | 120.00| Начално задължение
        penalty | 1   | Иван       | -       | 50.00 | Глоба за нарушение
    """
    
    __tablename__ = "obligations"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Тип на задължението
    type: Mapped[ObligationType] = mapped_column(
        SQLEnum(ObligationType),
        nullable=False,
        index=True,
        comment="Тип на задължението"
    )
    
    # Връзка с апартамент
    apartment_id: Mapped[int] = mapped_column(
        ForeignKey("apartments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID на апартамента"
    )
    
    # Месец (само за MONTHLY тип, формат: YYYY-MM)
    month: Mapped[Optional[str]] = mapped_column(
        String(7),
        nullable=True,
        index=True,
        comment="Месец на задължението (YYYY-MM), само за месечни такси"
    )
    
    # Сума на задължението
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Сума на задължението в лева"
    )
    
    # Описание/информация за задължението
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Описание на задължението"
    )
    
    # Relationships
    apartment: Mapped["Apartment"] = relationship(back_populates="obligations")
    
    def __repr__(self) -> str:
        month_str = f", month='{self.month}'" if self.month else ""
        return f"<Obligation(id={self.id}, type={self.type.value}, apartment_id={self.apartment_id}{month_str}, amount={self.amount})>"
    
    @property
    def is_monthly(self) -> bool:
        """Дали е месечно задължение."""
        return self.type == ObligationType.MONTHLY
