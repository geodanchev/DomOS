"""ApartmentAccount model - сметка на апартамент.

Всеки апартамент има сметка с баланс:
- Плащане → добавя към баланса (кредит)
- Задължение → изважда от баланса (дебит)
- Баланс < 0 → апартаментът дължи
- Баланс >= 0 → всичко е платено
"""

from enum import Enum
from decimal import Decimal
from sqlalchemy import String, Numeric, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.apartment import Apartment


class TransactionType(str, Enum):
    """Тип на транзакцията."""
    CREDIT = "credit"    # Плащане (добавя към баланса)
    DEBIT = "debit"      # Задължение (изважда от баланса)


class TransactionReference(str, Enum):
    """Референция към източника на транзакцията."""
    PAYMENT = "payment"        # От плащане
    OBLIGATION = "obligation"  # От задължение
    ADJUSTMENT = "adjustment"  # Ръчна корекция
    MIGRATION = "migration"    # От миграция на данни
    VOID = "void"              # От анулиране на плащане


class ApartmentAccount(Base, TimestampMixin):
    """Сметка на апартамент.
    
    Съхранява текущия баланс на апартамента.
    Положителен баланс = авансово плащане/надплащане.
    Отрицателен баланс = дължима сума.
    
    Пример:
        Апартамент | Баланс  | Статус
        1          | 50.00   | Платил авансово
        2          | 0.00    | Изравнен
        3          | -120.00 | Дължи 120 лв
    """
    
    __tablename__ = "apartment_accounts"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Връзка с апартамент (1:1)
    apartment_id: Mapped[int] = mapped_column(
        ForeignKey("apartments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="ID на апартамента"
    )
    
    # Текущ баланс (може да е отрицателен)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Текущ баланс в лева (отрицателен = дължи)"
    )
    
    # Relationships
    apartment: Mapped["Apartment"] = relationship(back_populates="account")
    transactions: Mapped[list["AccountTransaction"]] = relationship(
        back_populates="account",
        order_by="AccountTransaction.created_at.desc()"
    )
    
    def __repr__(self) -> str:
        return f"<ApartmentAccount(id={self.id}, apartment_id={self.apartment_id}, balance={self.balance})>"
    
    @property
    def is_paid(self) -> bool:
        """Дали апартаментът е изплатен (баланс >= 0)."""
        return self.balance >= 0
    
    @property
    def amount_owed(self) -> Decimal:
        """Дължима сума (0 ако няма дълг)."""
        return abs(self.balance) if self.balance < 0 else Decimal("0.00")
    
    @property
    def amount_credit(self) -> Decimal:
        """Авансова сума (0 ако няма аванс)."""
        return self.balance if self.balance > 0 else Decimal("0.00")


class AccountTransaction(Base, TimestampMixin):
    """Транзакция по сметка на апартамент.
    
    Записва всяка промяна в баланса за одит.
    
    Пример:
        ID | Сметка | Тип    | Сума   | Референция | Баланс след
        1  | 1      | credit | 50.00  | payment:5  | 50.00
        2  | 1      | debit  | 30.00  | obligation:3 | 20.00
    """
    
    __tablename__ = "account_transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Връзка със сметка
    account_id: Mapped[int] = mapped_column(
        ForeignKey("apartment_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID на сметката"
    )
    
    # Тип транзакция
    type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType),
        nullable=False,
        comment="Тип на транзакцията (credit/debit)"
    )
    
    # Сума (винаги положителна)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Сума на транзакцията в лева"
    )
    
    # Референция към източника
    reference_type: Mapped[TransactionReference] = mapped_column(
        SQLEnum(TransactionReference),
        nullable=False,
        comment="Тип на източника (payment/obligation/adjustment)"
    )
    
    # ID на източника
    reference_id: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="ID на свързания запис (payment_id, obligation_id и т.н.)"
    )
    
    # Баланс след транзакцията
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Баланс на сметката след транзакцията"
    )
    
    # Описание
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Описание на транзакцията"
    )
    
    # Relationships
    account: Mapped["ApartmentAccount"] = relationship(back_populates="transactions")
    
    def __repr__(self) -> str:
        return f"<AccountTransaction(id={self.id}, account_id={self.account_id}, type={self.type.value}, amount={self.amount})>"
