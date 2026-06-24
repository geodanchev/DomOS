"""Dashboard API endpoints - табло за касиера.

Актуализирано за account-based система.
Статусът на апартамент се определя от баланса на сметката.
"""

from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.apartment import Apartment
from app.models.account import ApartmentAccount
from app.models.obligation import Obligation
from app.models.payment import Payment
from app.models.user import User
from app.models.expense import Expense, ExpenseStatus
from app.schemas.statistics import CashierDashboard, ApartmentStatus, FundBalance
from app.api.auth import get_current_user

router = APIRouter()


def get_current_month() -> str:
    """Get current month in YYYY-MM format."""
    today = date.today()
    return f"{today.year}-{today.month:02d}"


def get_status_from_balance(balance: Decimal) -> tuple[str, str]:
    """Get status and display text from balance.
    
    Returns:
        tuple: (status, status_display)
        - status: "paid", "owes", "credit"
        - status_display: Bulgarian text for display
    """
    if balance > 0:
        return "credit", f"Авансово {float(balance):.2f} лв"
    elif balance < 0:
        return "owes", f"Дължи {abs(float(balance)):.2f} лв"
    else:
        return "paid", "Изплатен"


@router.get("", response_model=CashierDashboard)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cashier dashboard data.
    
    Това е основният екран за касиера.
    Показва:
    - Колко апартамента има
    - Баланс на всеки апартамент
    - Кой е платил, кой дължи
    - Процент събираемост
    """
    current_month = get_current_month()
    
    # Get all apartments with their accounts
    apartments = db.query(Apartment).order_by(Apartment.number).all()
    total_apartments = len(apartments)
    
    # Build apartment statuses
    apartment_statuses = []
    total_collected = Decimal("0")
    total_owed = Decimal("0")
    paid_count = 0
    owes_count = 0
    
    for apt in apartments:
        # Get or create account for apartment
        account = apt.account
        
        if account:
            balance = Decimal(str(account.balance))
        else:
            # No account yet - calculate from payments and obligations
            total_payments = db.query(func.sum(Payment.amount)).filter(
                Payment.apartment_id == apt.id
            ).scalar() or Decimal("0")
            
            total_obligations = db.query(func.sum(Obligation.amount)).filter(
                Obligation.apartment_id == apt.id
            ).scalar() or Decimal("0")
            
            balance = Decimal(str(total_payments)) - Decimal(str(total_obligations))
            
            # Create account for this apartment
            account = ApartmentAccount(
                apartment_id=apt.id,
                balance=balance
            )
            db.add(account)
            db.commit()
        
        # Calculate totals for this apartment
        apt_total_payments = db.query(func.sum(Payment.amount)).filter(
            Payment.apartment_id == apt.id
        ).scalar() or Decimal("0")
        
        apt_total_obligations = db.query(func.sum(Obligation.amount)).filter(
            Obligation.apartment_id == apt.id
        ).scalar() or Decimal("0")
        
        # Get status from balance
        status, status_display = get_status_from_balance(balance)
        
        # Track totals
        total_collected += Decimal(str(apt_total_payments))
        if balance < 0:
            total_owed += abs(balance)
            owes_count += 1
        else:
            paid_count += 1
        
        apartment_statuses.append(ApartmentStatus(
            apartment_id=apt.id,
            apartment_number=apt.number,
            owner_name=apt.owner_name,
            balance=float(balance),
            total_obligations=float(apt_total_obligations),
            total_payments=float(apt_total_payments),
            status=status,
            status_display=status_display,
        ))
    
    # Calculate collection rate
    total_obligations_all = total_collected + total_owed
    collection_rate = (float(total_collected) / float(total_obligations_all) * 100) if total_obligations_all > 0 else 100.0
    
    return CashierDashboard(
        total_apartments=total_apartments,
        total_collected=round(float(total_collected), 2),
        total_owed=round(float(total_owed), 2),
        collection_rate=round(collection_rate, 1),
        paid_count=paid_count,
        owes_count=owes_count,
        current_month=current_month,
        apartments=apartment_statuses,
    )


@router.get("/fund", response_model=FundBalance)
async def get_fund_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get building fund balance.
    
    Колко пари има във фонда:
    - total_collected_all_time: общо събрани от всички плащания
    - total_expenses: общо платени разходи (само със статус PAID)
    - current_balance: налично салдо = събрани - разходи
    """
    # Sum all payments (income)
    total_collected = db.query(func.sum(Payment.amount)).scalar() or Decimal("0")
    
    # Sum all paid expenses (outcome)
    total_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.status == ExpenseStatus.PAID
    ).scalar() or Decimal("0")
    
    # Current balance = income - expenses
    current_balance = Decimal(str(total_collected)) - Decimal(str(total_expenses))
    
    return FundBalance(
        total_collected_all_time=float(total_collected),
        total_expenses=float(total_expenses),
        current_balance=float(current_balance),
    )
