"""Pydantic schemas for API request/response models."""

from app.schemas.apartment import (
    ApartmentCreate,
    ApartmentUpdate,
    ApartmentResponse,
    ApartmentList,
)
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentList,
)
from app.schemas.monthly_charge import (
    MonthlyChargeCreate,
    MonthlyChargeResponse,
    MonthlyChargeList,
    ChargeStatusUpdate,
)
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
)
from app.schemas.statistics import (
    CashierDashboard,
    ApartmentStatus,
)

__all__ = [
    # Apartment
    "ApartmentCreate",
    "ApartmentUpdate",
    "ApartmentResponse",
    "ApartmentList",
    # Payment
    "PaymentCreate",
    "PaymentResponse",
    "PaymentList",
    # MonthlyCharge
    "MonthlyChargeCreate",
    "MonthlyChargeResponse",
    "MonthlyChargeList",
    "ChargeStatusUpdate",
    # User
    "UserCreate",
    "UserResponse",
    "UserLogin",
    "Token",
    # Statistics
    "CashierDashboard",
    "ApartmentStatus",
]
