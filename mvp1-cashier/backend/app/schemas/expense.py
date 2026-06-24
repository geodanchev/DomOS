"""Expense schemas for building fund expenses.

Pydantic схеми за разходи от фонда.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.expense import ExpenseType, ExpenseStatus


class ExpenseBase(BaseModel):
    """Base expense schema."""
    description: str = Field(..., min_length=1, max_length=500, description="Описание на разхода")
    amount: float = Field(..., gt=0, description="Сума (лв)")
    expense_type: ExpenseType = Field(default=ExpenseType.OTHER, description="Тип разход")
    expense_date: datetime = Field(default_factory=datetime.utcnow, description="Дата на разхода")
    vendor: Optional[str] = Field(None, max_length=255, description="Доставчик/Изпълнител")
    invoice_number: Optional[str] = Field(None, max_length=100, description="Номер на фактура")
    notes: Optional[str] = Field(None, description="Бележки")


class ExpenseCreate(ExpenseBase):
    """Schema for creating an expense."""
    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense."""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    amount: Optional[float] = Field(None, gt=0)
    expense_type: Optional[ExpenseType] = None
    expense_date: Optional[datetime] = None
    status: Optional[ExpenseStatus] = None
    paid_date: Optional[datetime] = None
    vendor: Optional[str] = Field(None, max_length=255)
    invoice_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class ExpenseResponse(ExpenseBase):
    """Schema for expense response."""
    id: int
    status: ExpenseStatus
    paid_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    
    # Display fields
    status_display: str = Field(default="", description="Статус на български")
    type_display: str = Field(default="", description="Тип на български")
    
    class Config:
        from_attributes = True
    
    @staticmethod
    def get_status_display(status: ExpenseStatus) -> str:
        """Get Bulgarian display text for status."""
        displays = {
            ExpenseStatus.PENDING: "Очаква плащане",
            ExpenseStatus.PAID: "Платен",
            ExpenseStatus.CANCELLED: "Анулиран",
        }
        return displays.get(status, str(status.value))
    
    @staticmethod
    def get_type_display(expense_type: ExpenseType) -> str:
        """Get Bulgarian display text for type."""
        displays = {
            ExpenseType.REPAIR: "Ремонт",
            ExpenseType.MAINTENANCE: "Поддръжка",
            ExpenseType.UTILITY: "Комунални",
            ExpenseType.ADMINISTRATIVE: "Административни",
            ExpenseType.CLEANING: "Почистване",
            ExpenseType.ELEVATOR: "Асансьор",
            ExpenseType.SECURITY: "Охрана",
            ExpenseType.INSURANCE: "Застраховка",
            ExpenseType.OTHER: "Други",
        }
        return displays.get(expense_type, str(expense_type.value))


class ExpenseList(BaseModel):
    """Schema for list of expenses with summary."""
    expenses: list[ExpenseResponse]
    total_count: int
    total_amount: float = Field(..., description="Обща сума на разходите")
    total_paid: float = Field(..., description="Сума на платените разходи")
    total_pending: float = Field(..., description="Сума на очакващите плащане")


class ExpenseSummary(BaseModel):
    """Summary of expenses by type."""
    expense_type: ExpenseType
    type_display: str
    count: int
    total_amount: float
