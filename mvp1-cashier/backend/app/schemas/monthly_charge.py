"""MonthlyCharge schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from app.models.monthly_charge import ChargeStatus


class MonthlyChargeBase(BaseModel):
    """Base monthly charge fields."""
    apartment_id: int = Field(..., description="ID на апартамента")
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Месец (YYYY-MM)")
    amount_due: float = Field(..., gt=0, description="Дължима сума в лева")


class MonthlyChargeCreate(MonthlyChargeBase):
    """Schema for creating a monthly charge."""
    pass


class ChargeStatusUpdate(BaseModel):
    """Schema for updating charge payment status."""
    amount_paid: float = Field(..., ge=0, description="Платена сума")


class MonthlyChargeResponse(MonthlyChargeBase):
    """Schema for monthly charge response."""
    id: int
    amount_paid: float
    status: ChargeStatus
    created_at: datetime
    updated_at: datetime
    
    # Nested info
    apartment_number: str | None = None
    owner_name: str | None = None
    
    class Config:
        from_attributes = True


class MonthlyChargeList(BaseModel):
    """Schema for list of monthly charges."""
    items: list[MonthlyChargeResponse]
    total: int
