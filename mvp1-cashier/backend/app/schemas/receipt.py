"""Receipt schemas - Pydantic схеми за разписки.

Спринт 3: Схеми за създаване, четене и отговор на разписки.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# === Request Schemas ===

class ReceiptCreate(BaseModel):
    """Схема за създаване на нова разписка."""
    payment_id: int


class ReceiptCopyCreate(BaseModel):
    """Схема за създаване на копие (празна - само receipt_id от URL)."""
    pass


# === Response Schemas ===

class ReceiptBase(BaseModel):
    """Базова схема за разписка."""
    id: int
    receipt_number: str
    payment_id: int
    is_copy: bool
    original_receipt_id: Optional[int] = None
    issued_at: datetime
    issued_by_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class ReceiptResponse(ReceiptBase):
    """Пълна схема за отговор с разписка."""
    pass


class ReceiptWithDetails(ReceiptBase):
    """Разписка с допълнителни детайли за PDF генериране."""
    # Payment details
    amount: float
    month: str
    payment_method: str
    payment_date: datetime
    
    # Apartment details
    apartment_number: str
    owner_name: str
    
    # Issuer details
    issued_by_name: Optional[str] = None


# === List Response ===

class ReceiptListResponse(BaseModel):
    """Схема за списък с разписки с пагинация."""
    items: list[ReceiptResponse]
    total: int
    page: int = 1
    limit: int = 50
