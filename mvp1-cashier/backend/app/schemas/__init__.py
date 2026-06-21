"""Pydantic schemas for API request/response models.

Актуализирано: Account-based система.
- Добавени Account и Transaction схеми
- Премахнати ObligationStatus и ObligationPayment (не са нужни)
"""

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
from app.schemas.obligation import (
    ObligationType,
    ObligationBase,
    ObligationCreate,
    ObligationUpdate,
    ObligationResponse,
    ObligationWithApartment,
    ObligationSummary,
    MonthlyObligationsSummary,
)
from app.schemas.account import (
    TransactionType,
    TransactionReference,
    AccountBase,
    AccountResponse,
    TransactionBase,
    TransactionResponse,
    AccountWithTransactions,
    AdjustmentCreate,
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
    # Obligation
    "ObligationType",
    "ObligationBase",
    "ObligationCreate",
    "ObligationUpdate",
    "ObligationResponse",
    "ObligationWithApartment",
    "ObligationSummary",
    "MonthlyObligationsSummary",
    # Account
    "TransactionType",
    "TransactionReference",
    "AccountBase",
    "AccountResponse",
    "TransactionBase",
    "TransactionResponse",
    "AccountWithTransactions",
    "AdjustmentCreate",
    # User
    "UserCreate",
    "UserResponse",
    "UserLogin",
    "Token",
    # Statistics
    "CashierDashboard",
    "ApartmentStatus",
]
