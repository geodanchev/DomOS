"""Payment model - плащания."""

from datetime import date
from sqlalchemy import String, Integer, Numeric, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.apartment import Apartment
    from app.models.user import User


class Payment(Base, TimestampMixin):
    """Плащане от апартамент.
    
    Пример:
        Апартамент | Месец    | Сума
        1          | 01.2027  | 15
        2          | 01.2027  | 30
    """
    
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Връзка с апартамент
    apartment_id: Mapped[int] = mapped_column(
        ForeignKey("apartments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID на апартамента"
    )
    
    # Сума на плащането
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Платена сума в лева"
    )
    
    # Месец за който е плащането (формат: YYYY-MM)
    month: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="Месец за плащането (YYYY-MM)"
    )
    
    # Дата на плащане
    payment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        comment="Дата на плащане"
    )
    
    # Метод на плащане
    payment_method: Mapped[str] = mapped_column(
        String(50),
        default="cash",
        nullable=False,
        comment="Метод на плащане (cash, bank, card)"
    )
    
    # Кой е приел плащането
    collected_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID на касиера приел плащането"
    )
    
    # Бележки
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Допълнителни бележки"
    )
    
    # Relationships
    apartment: Mapped["Apartment"] = relationship(back_populates="payments")
    collected_by: Mapped["User"] = relationship(back_populates="collected_payments")
    
    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, apartment_id={self.apartment_id}, amount={self.amount}, month='{self.month}')>"
