"""Payments API endpoints - плащания."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.apartment import Apartment
from app.models.payment import Payment
from app.models.monthly_charge import MonthlyCharge, ChargeStatus
from app.models.user import User
from app.schemas.payment import (
    PaymentCreate, 
    PaymentResponse, 
    PaymentList, 
    ReceiptData,
    ApartmentPaymentSummary,
    RecentPayment,
)
from app.api.auth import get_current_user

router = APIRouter()


@router.get("", response_model=PaymentList)
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    apartment_id: int | None = None,
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List payments with optional filters."""
    query = db.query(Payment).order_by(desc(Payment.payment_date))
    
    if apartment_id:
        query = query.filter(Payment.apartment_id == apartment_id)
    if month:
        query = query.filter(Payment.month == month)
    
    total = query.count()
    payments = query.offset(skip).limit(limit).all()
    
    # Enrich with apartment info
    items = []
    for p in payments:
        item = PaymentResponse.model_validate(p)
        if p.apartment:
            item.apartment_number = p.apartment.number
            item.owner_name = p.apartment.owner_name
        if p.collected_by:
            item.collected_by_name = p.collected_by.display_name
        items.append(item)
    
    return PaymentList(items=items, total=total)


@router.get("/apartment/{apartment_id}/summary", response_model=ApartmentPaymentSummary)
async def get_apartment_payment_summary(
    apartment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment summary for an apartment.
    
    Returns:
        - Apartment info
        - Last 3 payments
        - Current balance (positive = owes, negative = overpaid)
    """
    # Verify apartment exists
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Апартаментът не е намерен",
        )
    
    # Get last 3 payments
    recent_payments = (
        db.query(Payment)
        .filter(Payment.apartment_id == apartment_id)
        .order_by(desc(Payment.payment_date), desc(Payment.id))
        .limit(3)
        .all()
    )
    
    # Calculate totals from monthly charges
    charges = db.query(MonthlyCharge).filter(
        MonthlyCharge.apartment_id == apartment_id
    ).all()
    
    total_due = sum(float(c.amount_due) for c in charges)
    total_paid = sum(float(c.amount_paid) for c in charges)
    
    # Current balance: positive = owes money, negative = overpaid
    current_balance = total_due - total_paid
    
    return ApartmentPaymentSummary(
        apartment_id=apartment.id,
        apartment_number=apartment.number,
        owner_name=apartment.owner_name or "",
        recent_payments=[
            RecentPayment(
                id=p.id,
                amount=float(p.amount),
                month=p.month,
                payment_date=p.payment_date,
                payment_method=p.payment_method,
            )
            for p in recent_payments
        ],
        current_balance=current_balance,
        total_due=total_due,
        total_paid=total_paid,
    )


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a new payment.
    
    This is the main action for Цецка - recording payments from residents.
    """
    # Verify apartment exists
    apartment = db.query(Apartment).filter(Apartment.id == data.apartment_id).first()
    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Апартаментът не е намерен",
        )
    
    # Create payment
    payment = Payment(
        apartment_id=data.apartment_id,
        amount=data.amount,
        month=data.month,
        payment_date=data.payment_date or date.today(),
        payment_method=data.payment_method,
        notes=data.notes,
        collected_by_id=current_user.id,
    )
    
    db.add(payment)
    
    # Update monthly charge if exists
    charge = db.query(MonthlyCharge).filter(
        MonthlyCharge.apartment_id == data.apartment_id,
        MonthlyCharge.month == data.month,
    ).first()
    
    if charge:
        charge.amount_paid = float(charge.amount_paid) + data.amount
        charge.update_status()
    
    db.commit()
    db.refresh(payment)
    
    # Build response
    response = PaymentResponse.model_validate(payment)
    response.apartment_number = apartment.number
    response.owner_name = apartment.owner_name
    response.collected_by_name = current_user.display_name
    
    return response


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment by ID."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Плащането не е намерено",
        )
    
    response = PaymentResponse.model_validate(payment)
    if payment.apartment:
        response.apartment_number = payment.apartment.number
        response.owner_name = payment.apartment.owner_name
    if payment.collected_by:
        response.collected_by_name = payment.collected_by.display_name
    
    return response


@router.get("/{payment_id}/receipt", response_model=ReceiptData)
async def get_receipt(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get receipt data for printing.
    
    Returns data formatted for thermal printer.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Плащането не е намерено",
        )
    
    return ReceiptData(
        apartment_number=payment.apartment.number if payment.apartment else "?",
        amount=float(payment.amount),
        month=payment.month,
        payment_date=payment.payment_date,
        receipt_number=payment.id,
    )


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a payment (admin only, use with caution)."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Плащането не е намерено",
        )
    
    # Update monthly charge
    charge = db.query(MonthlyCharge).filter(
        MonthlyCharge.apartment_id == payment.apartment_id,
        MonthlyCharge.month == payment.month,
    ).first()
    
    if charge:
        charge.amount_paid = max(0, float(charge.amount_paid) - float(payment.amount))
        charge.update_status()
    
    db.delete(payment)
    db.commit()
