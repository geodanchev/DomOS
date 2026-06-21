"""MonthlyCharge model - месечни задължения."""

from enum import Enum
from sqlalchemy import String, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.apartment import Apartment


class ChargeStatus(str, Enum):
    """Статус на задължението."""
    PAID = "paid"          # Платено изцяло
    PARTIAL = "partial"    # Частично платено
    UNPAID = "unpaid"      # Неплатено


class MonthlyCharge(Base, TimestampMixin):
    """Месечно задължение за апартамент.
    
    Системата автоматично генерира задължение всеки месец.
    
    Пример:
        Ап. | Собственик | Дължи | Платил
        1   | Иван       | 15    | Да
        2   | Мария      | 30    | Не
        3   | Петър      | 20    | Частично
    """
    
    __tablename__ = "monthly_charges"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Връзка с апартамент
    apartment_id: Mapped[int] = mapped_column(
        ForeignKey("apartments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID на апартамента"
    )
    
    # Месец (формат: YYYY-MM)
    month: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        index=True,
        comment="Месец на задължението (YYYY-MM)"
    )
    
    # Дължима сума
    amount_due: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Дължима сума в лева"
    )
    
    # Платена сума
    amount_paid: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False,
        comment="Платена сума в лева"
    )
    
    # Статус
    status: Mapped[ChargeStatus] = mapped_column(
        SQLEnum(ChargeStatus),
        default=ChargeStatus.UNPAID,
        nullable=False,
        comment="Статус на задължението"
    )
    
    # Relationships
    apartment: Mapped["Apartment"] = relationship(back_populates="monthly_charges")
    
    def __repr__(self) -> str:
        return f"<MonthlyCharge(id={self.id}, apartment_id={self.apartment_id}, month='{self.month}', status={self.status.value})>"
    
    @property
    def amount_remaining(self) -> float:
        """Оставаща дължима сума."""
        return float(self.amount_due) - float(self.amount_paid)
    
    def update_status(self) -> None:
        """Актуализира статуса спрямо платената сума."""
        if self.amount_paid >= self.amount_due:
            self.status = ChargeStatus.PAID
        elif self.amount_paid > 0:
            self.status = ChargeStatus.PARTIAL
        else:
            self.status = ChargeStatus.UNPAID
