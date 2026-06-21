"""API routers.

Актуализирано: Премахнати legacy routers за monthly_charges и custom_charges.
"""

from app.api import apartments, payments, auth, dashboard, obligations

__all__ = ["apartments", "payments", "auth", "dashboard", "obligations"]
