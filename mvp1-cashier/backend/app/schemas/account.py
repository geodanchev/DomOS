"""Pydantic schemas за Account модела.

Account-based система за управление на баланси.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TransactionType(str, Enum):
    """Тип на транзакцията."""
    CREDIT = "credit"    # Плащане (добавя към баланса)
    DEBIT = "debit"      # Задължение (изважда от баланса)


class TransactionReference(str, Enum):
    """Референция към източника на транзакцията."""
    PAYMENT = "payment"
    OBLIGATION = "obligation"
    ADJUSTMENT = "adjustment"
    MIGRATION = "migration"


class AccountBase(BaseModel):
    """Базова схема за сметка."""
    apartment_id: int
    balance: float = Field(default=0.0, description="Текущ баланс (отрицателен = дължи)")


class AccountResponse(AccountBase):
    """Схема за отговор с данни за сметка."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @property
    def is_paid(self) -> bool:
        """Дали апартаментът е изплатен."""
        return self.balance >= 0
    
    @property
    def amount_owed(self) -> float:
        """Дължима сума (0 ако няма дълг)."""
        return abs(self.balance) if self.balance < 0 else 0.0


class TransactionBase(BaseModel):
    """Базова схема за транзакция."""
    type: TransactionType
    amount: float = Field(..., ge=0, description="Сума на транзакцията")
    reference_type: TransactionReference
    reference_id: Optional[int] = None
    description: Optional[str] = None


class TransactionResponse(TransactionBase):
    """Схема за отговор с данни за транзакция."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    balance_after: float
    created_at: datetime


class AccountWithTransactions(AccountResponse):
    """Схема за сметка с транзакции."""
    transactions: list[TransactionResponse] = []


class AdjustmentCreate(BaseModel):
    """Схема за ръчна корекция на баланс."""
    apartment_id: int
    amount: float = Field(..., description="Сума (положителна = кредит, отрицателна = дебит)")
    description: str = Field(..., description="Причина за корекцията")
