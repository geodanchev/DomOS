"""Dashboard API endpoints - табло за касиера."""

from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.apartment import Apartment
from app.models.monthly_charge import MonthlyCharge, ChargeStatus
from app.models.payment import Payment
from app.models.user import User
from app.schemas.statistics import CashierDashboard, ApartmentStatus, FundBalance
from app.api.auth import get_current_user

router = APIRouter()


def get_current_month() -> str:
    """Get current month in YYYY-MM format."""
    today = date.today()
    return f"{today.year}-{today.month:02d}"


def status_to_display(status: ChargeStatus) -> str:
    """Convert status enum to Bulgarian display text."""
    mapping = {
        ChargeStatus.PAID: "Да",
        ChargeStatus.PARTIAL: "Частично",
        ChargeStatus.UNPAID: "Не",
    }
    return mapping.get(status, "?")


@router.get("", response_model=CashierDashboard)
async def get_dashboard(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cashier dashboard data.
    
    Това е основният екран за касиера.
    Показва за 2 минути:
    - Колко апартамента има
    - Колко дължи всеки
    - Кой е платил
    - Кой не е платил
    - Колко пари има във фонда
    """
    target_month = month or get_current_month()
    
    # Get all apartments
    apartments = db.query(Apartment).order_by(Apartment.number).all()
    total_apartments = len(apartments)
    
    # Get charges for this month
    charges_map = {}
    charges = db.query(MonthlyCharge).filter(
        MonthlyCharge.month == target_month
    ).all()
    for c in charges:
        charges_map[c.apartment_id] = c
    
    # Build apartment statuses
    apartment_statuses = []
    total_due = 0.0
    total_paid = 0.0
    paid_count = 0
    partial_count = 0
    unpaid_count = 0
    
    for apt in apartments:
        charge = charges_map.get(apt.id)
        
        if charge:
            amount_due = float(charge.amount_due)
            amount_paid = float(charge.amount_paid)
            status = charge.status
        else:
            # No charge yet - use apartment's monthly fee
            amount_due = float(apt.monthly_fee)
            amount_paid = 0.0
            status = ChargeStatus.UNPAID
        
        total_due += amount_due
        total_paid += amount_paid
        
        if status == ChargeStatus.PAID:
            paid_count += 1
        elif status == ChargeStatus.PARTIAL:
            partial_count += 1
        else:
            unpaid_count += 1
        
        apartment_statuses.append(ApartmentStatus(
            apartment_id=apt.id,
            apartment_number=apt.number,
            owner_name=apt.owner_name,
            amount_due=amount_due,
            amount_paid=amount_paid,
            status=status,
            status_display=status_to_display(status),
        ))
    
    # Calculate collection rate
    collection_rate = (total_paid / total_due * 100) if total_due > 0 else 0.0
    
    return CashierDashboard(
        total_apartments=total_apartments,
        total_collected=round(total_paid, 2),
        total_unpaid=round(total_due - total_paid, 2),
        collection_rate=round(collection_rate, 1),
        paid_count=paid_count,
        partial_count=partial_count,
        unpaid_count=unpaid_count,
        current_month=target_month,
        apartments=apartment_statuses,
    )


@router.get("/fund", response_model=FundBalance)
async def get_fund_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get building fund balance.
    
    Колко пари има във фонда (общо събрани от началото).
    """
    # Sum all payments
    total = db.query(func.sum(Payment.amount)).scalar() or 0
    
    return FundBalance(
        total_collected_all_time=float(total),
        total_expenses=0,  # TODO: implement expenses tracking
        current_balance=float(total),
    )
