"""Expense model for building fund expenses.

Проследяване на разходите от фонда на сградата:
- Ремонти
- Поддръжка (почистване, асансьор, охрана)
- Комунални (ток общи части, вода)
- Административни (застраховки, такси)
"""

import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, Text
from app.db.base import Base


class ExpenseType(str, enum.Enum):
    """Типове разходи."""
    REPAIR = "repair"  # Ремонт
    MAINTENANCE = "maintenance"  # Поддръжка
    UTILITY = "utility"  # Комунални
    ADMINISTRATIVE = "administrative"  # Административни
    CLEANING = "cleaning"  # Почистване
    ELEVATOR = "elevator"  # Асансьор
    SECURITY = "security"  # Охрана
    INSURANCE = "insurance"  # Застраховка
    OTHER = "other"  # Други


class ExpenseStatus(str, enum.Enum):
    """Статус на разхода."""
    PENDING = "pending"  # Очаква плащане
    PAID = "paid"  # Платен
    CANCELLED = "cancelled"  # Анулиран


class Expense(Base):
    """Expense model - разход от фонда на сградата.
    
    Всеки разход се записва тук и намалява баланса на фонда.
    
    Примери:
        - Ремонт на покрив: 5000 лв
        - Месечно почистване: 200 лв
        - Ток общи части: 150 лв
        - Застраховка сграда: 800 лв/год
    """
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Основни данни
    description = Column(String(500), nullable=False)  # Описание на разхода
    amount = Column(Numeric(10, 2), nullable=False)  # Сума
    expense_type = Column(Enum(ExpenseType), nullable=False, default=ExpenseType.OTHER)
    status = Column(Enum(ExpenseStatus), nullable=False, default=ExpenseStatus.PENDING)
    
    # Дати
    expense_date = Column(DateTime, nullable=False, default=datetime.utcnow)  # Дата на разхода
    paid_date = Column(DateTime, nullable=True)  # Дата на плащане (ако е платен)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Допълнителна информация
    vendor = Column(String(255), nullable=True)  # Доставчик/Изпълнител
    invoice_number = Column(String(100), nullable=True)  # Номер на фактура
    notes = Column(Text, nullable=True)  # Бележки
    
    # Audit
    created_by = Column(Integer, nullable=True)  # User ID който е създал записа
    
    def __repr__(self):
        return f"<Expense(id={self.id}, type={self.expense_type.value}, amount={self.amount}, status={self.status.value})>"
