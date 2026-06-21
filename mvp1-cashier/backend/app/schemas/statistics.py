"""Statistics schemas for cashier dashboard."""

from pydantic import BaseModel, Field
from app.models.monthly_charge import ChargeStatus


class ApartmentStatus(BaseModel):
    """Status of an apartment for the cashier view.
    
    Пример:
        Ап. | Собственик | Дължи | Платил
        1   | Иван       | 15    | Да
        2   | Мария      | 30    | Не
        3   | Петър      | 20    | Частично
    """
    apartment_id: int
    apartment_number: str
    owner_name: str
    amount_due: float
    amount_paid: float
    status: ChargeStatus
    status_display: str  # "Да", "Не", "Частично"


class CashierDashboard(BaseModel):
    """Dashboard data for the cashier.
    
    Показва:
        - Брой апартаменти
        - Общо събрани
        - Неплатени
        - Процент събираемост
        - Списък със статус на апартаменти
    """
    # Statistics
    total_apartments: int = Field(..., description="Брой апартаменти")
    total_collected: float = Field(..., description="Общо събрани (лв)")
    total_unpaid: float = Field(..., description="Неплатени (лв)")
    collection_rate: float = Field(..., description="Процент събираемост (%)")
    
    # Counts by status
    paid_count: int = Field(..., description="Брой платили изцяло")
    partial_count: int = Field(..., description="Брой частично платили")
    unpaid_count: int = Field(..., description="Брой неплатили")
    
    # Current month
    current_month: str = Field(..., description="Текущ месец (YYYY-MM)")
    
    # Apartment statuses
    apartments: list[ApartmentStatus] = Field(default_factory=list)


class FundBalance(BaseModel):
    """Building fund balance."""
    total_collected_all_time: float = Field(..., description="Общо събрани от началото")
    total_expenses: float = Field(0, description="Общо разходи")
    current_balance: float = Field(..., description="Текущо салдо във фонда")
