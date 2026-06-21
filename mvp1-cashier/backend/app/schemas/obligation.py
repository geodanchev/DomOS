"""Pydantic schemas за Obligation модела.

Актуализирано за account-based система:
- Премахнати amount_paid и status от модела
- Преименувано amount_due на amount
- Статусът се изчислява от баланса на сметката
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class ObligationType(str, Enum):
    """Тип на задължението."""
    MONTHLY = "monthly"
    INITIAL = "initial"
    PENALTY = "penalty"
    REPAIR = "repair"
    FUND = "fund"
    OTHER = "other"


class ObligationBase(BaseModel):
    """Базова схема за задължение."""
    type: ObligationType
    apartment_id: int
    month: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$", description="Месец (YYYY-MM), само за месечни такси")
    amount: float = Field(..., ge=0, description="Сума на задължението в лева")
    description: Optional[str] = Field(None, description="Описание на задължението")


class ObligationCreate(ObligationBase):
    """Схема за създаване на задължение."""
    pass


class ObligationUpdate(BaseModel):
    """Схема за актуализиране на задължение."""
    amount: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None


class ObligationResponse(ObligationBase):
    """Схема за отговор с пълни данни за задължение."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class ObligationWithApartment(ObligationResponse):
    """Схема за задължение с информация за апартамента."""
    apartment_number: str
    owner_name: str


class ObligationSummary(BaseModel):
    """Обобщена статистика за задължения."""
    total_obligations: float = Field(..., description="Общо задължения")
    total_payments: float = Field(..., description="Общо плащания")
    balance: float = Field(..., description="Баланс (отрицателен = дължи)")
    count_obligations: int = Field(..., description="Брой задължения")


class MonthlyObligationsSummary(ObligationSummary):
    """Обобщена статистика за месечни задължения."""
    month: str = Field(..., description="Месец (YYYY-MM)")
