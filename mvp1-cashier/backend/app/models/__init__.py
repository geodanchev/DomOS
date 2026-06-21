"""MVP 1: Digital Cashier - Database Models.

Актуализирано: Account-based система.
- ApartmentAccount: сметка на апартамент с баланс
- AccountTransaction: одит на транзакции
- Obligation: опростен (без amount_paid и status)
"""

from app.models.apartment import Apartment
from app.models.payment import Payment
from app.models.obligation import Obligation, ObligationType
from app.models.account import ApartmentAccount, AccountTransaction, TransactionType, TransactionReference
from app.models.user import User
from app.models.receipt import Receipt

__all__ = [
    "Apartment",
    "Payment",
    "Obligation",
    "ObligationType",
    "ApartmentAccount",
    "AccountTransaction",
    "TransactionType",
    "TransactionReference",
    "User",
    "Receipt",
]
