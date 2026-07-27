"""ApartmentAccount model - сметка на апартамент.

АРХИТЕКТУРА БЕЗ КЕШИРАН БАЛАНС:
Балансът се изчислява динамично като:
  balance = sum(payments) - sum(obligations)

Това елиминира проблемите със sync при директни DB операции.
"""

from enum import Enum
from decimal import Decimal
from sqlalchemy import String, Numeric, Text, ForeignKey, Enum as SQLEnum, select, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from typing import Optional, TYPE_CHECKING

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.apartment import Apartment
    from app.models.payment import Payment
    from app.models.obligation import Obligation


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
    
    Балансът се изчислява ДИНАМИЧНО от payments и obligations.
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
    
    # ПРЕМАХНАТ: Кеширан баланс - вече се изчислява динамично
    # balance: Mapped[Decimal] - REMOVED
    
    # Relationships
    apartment: Mapped["Apartment"] = relationship(back_populates="account")
    transactions: Mapped[list["AccountTransaction"]] = relationship(
        back_populates="account",
        order_by="AccountTransaction.created_at.desc()"
    )
    
    def __repr__(self) -> str:
        return f"<ApartmentAccount(id={self.id}, apartment_id={self.apartment_id})>"
    
    def calculate_balance(self, db_session) -> Decimal:
        """Изчислява баланса в реално време.
        
        balance = sum(payments) - sum(obligations)
        
        Args:
            db_session: SQLAlchemy session за заявки
            
        Returns:
            Decimal: Текущ баланс (отрицателен = дължи)
        """
        from app.models.payment import Payment, PaymentStatus
        from app.models.obligation import Obligation
        
        # Sum active payments (exclude voided)
        total_payments = db_session.query(func.sum(Payment.amount)).filter(
            Payment.apartment_id == self.apartment_id,
            Payment.status == PaymentStatus.ACTIVE
        ).scalar() or Decimal("0")
        
        # Sum all obligations
        total_obligations = db_session.query(func.sum(Obligation.amount)).filter(
            Obligation.apartment_id == self.apartment_id
        ).scalar() or Decimal("0")
        
        return Decimal(str(total_payments)) - Decimal(str(total_obligations))
    
    @property
    def is_paid(self) -> bool:
        """Дали апартаментът е изплатен (баланс >= 0).
        
        ВНИМАНИЕ: Този property изисква db session за изчисление.
        Използвайте calculate_balance(db) за точен резултат.
        """
        # This property cannot work without session
        # It's kept for backwards compatibility but should use calculate_balance
        raise NotImplementedError(
            "Use calculate_balance(db_session) >= 0 instead. "
            "The is_paid property requires a database session."
        )
    
    @property
    def amount_owed(self) -> Decimal:
        """Дължима сума.
        
        ВНИМАНИЕ: Този property изисква db session за изчисление.
        Използвайте calculate_balance(db) за точен резултат.
        """
        raise NotImplementedError(
            "Use abs(min(calculate_balance(db_session), 0)) instead. "
            "The amount_owed property requires a database session."
        )
    
    @property
    def amount_credit(self) -> Decimal:
        """Авансова сума.
        
        ВНИМАНИЕ: Този property изисква db session за изчисление.
        Използвайте calculate_balance(db) за точен резултат.
        """
        raise NotImplementedError(
            "Use max(calculate_balance(db_session), 0) instead. "
            "The amount_credit property requires a database session."
        )


class AccountTransaction(Base, TimestampMixin):
    """Транзакция по сметка на апартамент.
    
    Записва всяка промяна за ОДИТ цели.
    balance_after е nullable за обратна съвместимост.
    
    Пример:
        ID | Сметка | Тип    | Сума   | Референция | Описание
        1  | 1      | credit | 50.00  | payment:5  | Плащане #5
        2  | 1      | debit  | 30.00  | obligation:3 | Задължение #3
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
    
    # Баланс след транзакцията - ВЕЧЕ Е OPTIONAL (само за одит история)
    balance_after: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,  # Changed from False to True
        comment="Баланс на сметката след транзакцията (legacy, за одит)"
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
