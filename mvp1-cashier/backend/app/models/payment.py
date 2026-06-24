"""Payment model - плащания.

Audit-compliant: Плащанията не се изтриват физически.
Вместо това се маркират като анулирани (voided) или грешни (erroneous).
"""

from datetime import date, datetime
from enum import Enum
from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.apartment import Apartment
    from app.models.user import User
    from app.models.receipt import Receipt


class PaymentStatus(str, Enum):
    """Статус на плащане.
    
    ACTIVE - нормално активно плащане
    VOIDED - анулирано плащане (грешно въведено)
    REFUNDED - върнато плащане
    """
    ACTIVE = "active"
    VOIDED = "voided"
    REFUNDED = "refunded"


class Payment(Base, TimestampMixin):
    """Плащане от апартамент.
    
    Пример:
        Апартамент | Месец    | Сума
        1          | 01.2027  | 15
        2          | 01.2027  | 30
    
    ВАЖНО: Плащанията НИКОГА не се изтриват физически!
    При грешка се използва void операция, която:
    - Маркира плащането като voided
    - Записва причината за анулиране
    - Записва кой и кога е анулирал
    - Създава audit log запис
    - Коригира баланса на сметката
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
    
    # === VOID/STATUS FIELDS (Audit-compliant) ===
    
    # Статус на плащането
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, name="payment_status", native_enum=False),
        default=PaymentStatus.ACTIVE,
        nullable=False,
        index=True,
        comment="Статус: active, voided, refunded"
    )
    
    # Дата и час на анулиране
    voided_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="Кога е анулирано плащането"
    )
    
    # Кой е анулирал
    voided_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID на потребителя анулирал плащането"
    )
    
    # Причина за анулиране (задължително при void)
    void_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Причина за анулиране (задължително)"
    )
    
    # Relationships
    apartment: Mapped["Apartment"] = relationship(back_populates="payments")
    collected_by: Mapped["User"] = relationship(
        back_populates="collected_payments",
        foreign_keys=[collected_by_id]
    )
    voided_by: Mapped["User"] = relationship(
        foreign_keys=[voided_by_id]
    )
    receipts: Mapped[list["Receipt"]] = relationship(back_populates="payment")
    
    @property
    def is_active(self) -> bool:
        """Дали плащането е активно (не е анулирано)."""
        return self.status == PaymentStatus.ACTIVE
    
    @property
    def is_voided(self) -> bool:
        """Дали плащането е анулирано."""
        return self.status == PaymentStatus.VOIDED
    
    def __repr__(self) -> str:
        status_str = f", status='{self.status.value}'" if self.status != PaymentStatus.ACTIVE else ""
        return f"<Payment(id={self.id}, apartment_id={self.apartment_id}, amount={self.amount}, month='{self.month}'{status_str})>"
