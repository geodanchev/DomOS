"""Monthly charges API endpoints - месечни задължения."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.apartment import Apartment
from app.models.monthly_charge import MonthlyCharge, ChargeStatus
from app.models.user import User
from app.schemas.monthly_charge import (
    MonthlyChargeCreate,
    MonthlyChargeResponse,
    MonthlyChargeList,
)
from app.api.auth import get_current_user

router = APIRouter()


def get_current_month() -> str:
    """Get current month in YYYY-MM format."""
    today = date.today()
    return f"{today.year}-{today.month:02d}"


@router.get("", response_model=MonthlyChargeList)
async def list_charges(
    month: str | None = None,
    status_filter: ChargeStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List monthly charges with optional filters."""
    query = db.query(MonthlyCharge)
    
    if month:
        query = query.filter(MonthlyCharge.month == month)
    if status_filter:
        query = query.filter(MonthlyCharge.status == status_filter)
    
    query = query.order_by(MonthlyCharge.month.desc())
    
    total = query.count()
    charges = query.all()
    
    # Enrich with apartment info
    items = []
    for c in charges:
        item = MonthlyChargeResponse.model_validate(c)
        if c.apartment:
            item.apartment_number = c.apartment.number
            item.owner_name = c.apartment.owner_name
        items.append(item)
    
    return MonthlyChargeList(items=items, total=total)


@router.post("/generate", response_model=MonthlyChargeList)
async def generate_monthly_charges(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate monthly charges for all apartments.
    
    If month is not specified, uses current month.
    Skips apartments that already have charges for the month.
    """
    target_month = month or get_current_month()
    
    # Get all apartments
    apartments = db.query(Apartment).all()
    
    created = []
    for apt in apartments:
        # Check if charge already exists
        existing = db.query(MonthlyCharge).filter(
            MonthlyCharge.apartment_id == apt.id,
            MonthlyCharge.month == target_month,
        ).first()
        
        if existing:
            continue
        
        # Create new charge
        charge = MonthlyCharge(
            apartment_id=apt.id,
            month=target_month,
            amount_due=float(apt.monthly_fee),
            amount_paid=0,
            status=ChargeStatus.UNPAID,
        )
        db.add(charge)
        created.append(charge)
    
    db.commit()
    
    # Refresh and build response
    items = []
    for c in created:
        db.refresh(c)
        item = MonthlyChargeResponse.model_validate(c)
        if c.apartment:
            item.apartment_number = c.apartment.number
            item.owner_name = c.apartment.owner_name
        items.append(item)
    
    return MonthlyChargeList(items=items, total=len(items))


@router.get("/{charge_id}", response_model=MonthlyChargeResponse)
async def get_charge(
    charge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get charge by ID."""
    charge = db.query(MonthlyCharge).filter(MonthlyCharge.id == charge_id).first()
    if not charge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задължението не е намерено",
        )
    
    response = MonthlyChargeResponse.model_validate(charge)
    if charge.apartment:
        response.apartment_number = charge.apartment.number
        response.owner_name = charge.apartment.owner_name
    
    return response


@router.delete("/{charge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_charge(
    charge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a charge (admin only)."""
    charge = db.query(MonthlyCharge).filter(MonthlyCharge.id == charge_id).first()
    if not charge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задължението не е намерено",
        )
    
    db.delete(charge)
    db.commit()
