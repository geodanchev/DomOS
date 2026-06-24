"""MVP 1: Digital Cashier - Database Models.

Актуализирано: Account-based система + Audit Log.
- ApartmentAccount: сметка на апартамент с баланс
- AccountTransaction: одит на транзакции
- Obligation: опростен (без amount_paid и status)
- AuditLog: immutable одит лог за съответствие
- Payment: с поддръжка на void/status (soft delete)
"""

from app.models.apartment import Apartment
from app.models.payment import Payment, PaymentStatus
from app.models.obligation import Obligation, ObligationType
from app.models.account import ApartmentAccount, AccountTransaction, TransactionType, TransactionReference
from app.models.user import User
from app.models.receipt import Receipt
from app.models.expense import Expense, ExpenseType, ExpenseStatus
from app.models.audit_log import AuditLog, AuditAction, create_audit_log

__all__ = [
    # Core entities
    "Apartment",
    "Payment",
    "PaymentStatus",
    "Obligation",
    "ObligationType",
    "User",
    "Receipt",
    "Expense",
    "ExpenseType",
    "ExpenseStatus",
    # Account system
    "ApartmentAccount",
    "AccountTransaction",
    "TransactionType",
    "TransactionReference",
    # Audit system
    "AuditLog",
    "AuditAction",
    "create_audit_log",
]
