"""Payment schemas."""

from pydantic import BaseModel, Field
from datetime import date, datetime


class PaymentBase(BaseModel):
    """Base payment fields."""
    apartment_id: int = Field(..., description="ID на апартамента")
    amount: float = Field(..., gt=0, description="Платена сума в лева")
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Месец (YYYY-MM)")
    payment_method: str = Field("cash", description="Метод на плащане")
    notes: str | None = Field(None, description="Бележки")


class PaymentCreate(PaymentBase):
    """Schema for creating a payment."""
    payment_date: date | None = Field(None, description="Дата на плащане (default: днес)")


class PaymentResponse(PaymentBase):
    """Schema for payment response."""
    id: int
    payment_date: date
    collected_by_id: int | None
    created_at: datetime
    updated_at: datetime
    
    # Nested info
    apartment_number: str | None = None
    owner_name: str | None = None
    collected_by_name: str | None = None
    
    class Config:
        from_attributes = True


class PaymentList(BaseModel):
    """Schema for list of payments."""
    items: list[PaymentResponse]
    total: int


class ReceiptData(BaseModel):
    """Data for printing a receipt."""
    apartment_number: str
    amount: float
    month: str
    payment_date: date
    receipt_number: int | None = None


class RecentPayment(BaseModel):
    """Schema for recent payment in summary."""
    id: int
    amount: float
    month: str
    payment_date: date
    payment_method: str
    
    class Config:
        from_attributes = True


class ApartmentPaymentSummary(BaseModel):
    """Schema for apartment payment dialog.
    
    Показва информация за апартамент при въвеждане на плащане:
    - Информация за апартамента
    - Последни 3 плащания
    - Текущ баланс (положителен = дължи, отрицателен = предплатил)
    """
    apartment_id: int
    apartment_number: str
    owner_name: str
    
    # Последни 3 плащания
    recent_payments: list[RecentPayment]
    
    # Текущ баланс: положителен = дължи, отрицателен = предплатил
    current_balance: float = Field(..., description="Текущ баланс (+ дължи, - предплатил)")
    
    # Допълнителна информация
    total_due: float = Field(..., description="Общо дължимо")
    total_paid: float = Field(..., description="Общо платено")
