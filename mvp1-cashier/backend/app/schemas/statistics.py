"""Statistics schemas for cashier dashboard.

Актуализирано за account-based система.
Статусът се определя от баланса на сметката.
"""

from pydantic import BaseModel, Field


class ApartmentStatus(BaseModel):
    """Status of an apartment for the cashier view.
    
    Пример:
        Ап. | Собственик | Баланс  | Статус
        1   | Иван       | 0.00    | Изплатен
        2   | Мария      | -30.00  | Дължи
        3   | Петър      | 15.00   | Авансово
    """
    apartment_id: int
    apartment_number: str
    owner_name: str
    balance: float  # Баланс на сметката (отрицателен = дължи)
    total_obligations: float  # Общо задължения
    total_payments: float  # Общо плащания
    status: str  # "paid", "owes", "credit"
    status_display: str  # "Изплатен", "Дължи X лв", "Авансово X лв"


class CashierDashboard(BaseModel):
    """Dashboard data for the cashier.
    
    Показва:
        - Брой апартаменти
        - Общо събрани
        - Общо дължимо (сума на отрицателните баланси)
        - Процент събираемост
        - Списък със статус на апартаменти
    """
    # Statistics
    total_apartments: int = Field(..., description="Брой апартаменти")
    total_collected: float = Field(..., description="Общо събрани (лв)")
    total_owed: float = Field(..., description="Общо дължимо (лв)")
    collection_rate: float = Field(..., description="Процент събираемост (%)")
    
    # Counts by status
    paid_count: int = Field(..., description="Брой изплатени (баланс >= 0)")
    owes_count: int = Field(..., description="Брой дължащи (баланс < 0)")
    
    # Current month
    current_month: str = Field(..., description="Текущ месец (YYYY-MM)")
    
    # Apartment statuses
    apartments: list[ApartmentStatus] = Field(default_factory=list)


class FundBalance(BaseModel):
    """Building fund balance."""
    total_collected_all_time: float = Field(..., description="Общо събрани от началото")
    total_expenses: float = Field(0, description="Общо разходи")
    current_balance: float = Field(..., description="Текущо салдо във фонда")
