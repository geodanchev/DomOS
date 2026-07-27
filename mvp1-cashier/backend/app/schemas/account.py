"""Pydantic schemas за Account модела.

АРХИТЕКТУРА БЕЗ КЕШИРАН БАЛАНС:
Account е контейнер за audit транзакции.
Балансът се изчислява динамично, не се съхранява.
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
    VOID = "void"


class AccountBase(BaseModel):
    """Базова схема за сметка.
    
    Забележка: balance вече НЕ е поле в модела.
    Изчислява се динамично от payments и obligations.
    """
    apartment_id: int


class AccountResponse(AccountBase):
    """Схема за отговор с данни за сметка.
    
    balance се предоставя като изчислено поле, не от DB.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Balance is now computed, provided externally
    balance: Optional[float] = Field(
        default=None,
        description="Изчислен баланс (отрицателен = дължи). Подава се отделно."
    )


class TransactionBase(BaseModel):
    """Базова схема за транзакция."""
    type: TransactionType
    amount: float = Field(..., ge=0, description="Сума на транзакцията")
    reference_type: TransactionReference
    reference_id: Optional[int] = None
    description: Optional[str] = None


class TransactionResponse(TransactionBase):
    """Схема за отговор с данни за транзакция.
    
    balance_after вече е optional (legacy поле за одит).
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    balance_after: Optional[float] = Field(
        default=None,
        description="Legacy поле - баланс след транзакцията (вече не се изчислява)"
    )
    created_at: datetime


class AccountWithTransactions(AccountResponse):
    """Схема за сметка с транзакции."""
    transactions: list[TransactionResponse] = []


class AdjustmentCreate(BaseModel):
    """Схема за ръчна корекция.
    
    Забележка: С новата архитектура, корекциите се записват
    като транзакции само за одит. Не обновяват кеширан баланс.
    """
    apartment_id: int
    amount: float = Field(..., description="Сума (положителна = кредит, отрицателна = дебит)")
    description: str = Field(..., description="Причина за корекцията")
