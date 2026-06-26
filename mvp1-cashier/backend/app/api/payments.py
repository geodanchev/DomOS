"""Payments API endpoints - плащания.

Актуализирано за account-based система + void (soft delete) support.
При плащане се добавя кредит към сметката на апартамента.
Плащанията НИКОГА не се изтриват - само се маркират като voided.
"""

from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.db.session import get_db
from app.models.apartment import Apartment
from app.models.payment import Payment, PaymentStatus
from app.models.obligation import Obligation
from app.models.account import ApartmentAccount, AccountTransaction, TransactionType, TransactionReference
from app.models.user import User
from app.models.audit_log import AuditAction, create_audit_log
from app.models.receipt import Receipt
from app.api.receipts import generate_receipt_number
from app.schemas.payment import (
    PaymentCreate, 
    PaymentResponse, 
    PaymentList, 
    ReceiptData,
    ApartmentPaymentSummary,
    RecentPayment,
    PaymentVoidRequest,
    PaymentVoidResponse,
)
from app.api.auth import get_current_user, require_admin, require_cashier_or_admin

router = APIRouter()


def get_or_create_account(db: Session, apartment_id: int) -> ApartmentAccount:
    """Get or create account for apartment."""
    account = db.query(ApartmentAccount).filter(
        ApartmentAccount.apartment_id == apartment_id
    ).first()
    
    if not account:
        # Calculate initial balance from existing data
        total_payments = db.query(func.sum(Payment.amount)).filter(
            Payment.apartment_id == apartment_id
        ).scalar() or Decimal("0")
        
        total_obligations = db.query(func.sum(Obligation.amount)).filter(
            Obligation.apartment_id == apartment_id
        ).scalar() or Decimal("0")
        
        balance = Decimal(str(total_payments)) - Decimal(str(total_obligations))
        
        account = ApartmentAccount(
            apartment_id=apartment_id,
            balance=balance
        )
        db.add(account)
        db.flush()
    
    return account


def add_credit_to_account(
    db: Session, 
    account: ApartmentAccount, 
    amount: Decimal,
    payment_id: int,
    description: str | None = None
) -> AccountTransaction:
    """Add credit to account and create transaction record."""
    # Update balance
    new_balance = Decimal(str(account.balance)) + amount
    account.balance = new_balance
    
    # Create transaction record
    transaction = AccountTransaction(
        account_id=account.id,
        type=TransactionType.CREDIT,
        amount=amount,
        reference_type=TransactionReference.PAYMENT,
        reference_id=payment_id,
        balance_after=new_balance,
        description=description or f"Плащане #{payment_id}"
    )
    db.add(transaction)
    
    return transaction


def remove_credit_from_account(
    db: Session, 
    account: ApartmentAccount, 
    amount: Decimal,
    payment_id: int,
    description: str | None = None
) -> AccountTransaction:
    """Remove credit from account (for voided payments) and create transaction record."""
    # Update balance (subtract the amount)
    new_balance = Decimal(str(account.balance)) - amount
    account.balance = new_balance
    
    # Create transaction record
    transaction = AccountTransaction(
        account_id=account.id,
        type=TransactionType.DEBIT,
        amount=amount,
        reference_type=TransactionReference.VOID,
        reference_id=payment_id,
        balance_after=new_balance,
        description=description or f"Анулиране на плащане #{payment_id}"
    )
    db.add(transaction)
    
    return transaction


@router.get("", response_model=PaymentList)
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    apartment_id: int | None = None,
    month: str | None = None,
    include_voided: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List payments with optional filters.
    
    Args:
        include_voided: If True, includes voided payments. Default False.
    """
    query = db.query(Payment).order_by(desc(Payment.payment_date))
    
    # Filter by status - exclude voided by default
    if not include_voided:
        query = query.filter(Payment.status == PaymentStatus.ACTIVE)
    
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
        # Add receipt_id (first non-copy receipt)
        if p.receipts:
            original_receipt = next((r for r in p.receipts if not r.is_copy), None)
            if original_receipt:
                item.receipt_id = original_receipt.id
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
        - Current balance from account
    """
    # Verify apartment exists
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Апартаментът не е намерен",
        )
    
    # Get or create account
    account = get_or_create_account(db, apartment_id)
    db.commit()
    
    # Get last 3 payments
    recent_payments = (
        db.query(Payment)
        .filter(Payment.apartment_id == apartment_id)
        .order_by(desc(Payment.payment_date), desc(Payment.id))
        .limit(3)
        .all()
    )
    
    # Calculate totals
    total_payments = db.query(func.sum(Payment.amount)).filter(
        Payment.apartment_id == apartment_id
    ).scalar() or Decimal("0")
    
    total_obligations = db.query(func.sum(Obligation.amount)).filter(
        Obligation.apartment_id == apartment_id
    ).scalar() or Decimal("0")
    
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
        balance=float(account.balance),
        total_obligations=float(total_obligations),
        total_payments=float(total_payments),
    )


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cashier_or_admin),  # RBAC: Admin or Cashier
):
    """Record a new payment.
    
    SECURITY: Администратори и касиери могат да регистрират плащания.
    This is the main action for the cashier - recording payments from residents.
    The payment adds credit to the apartment's account.
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
    db.flush()  # Get payment ID
    
    # Get or create account and add credit
    account = get_or_create_account(db, data.apartment_id)
    add_credit_to_account(
        db=db,
        account=account,
        amount=Decimal(str(data.amount)),
        payment_id=payment.id,
        description=f"Плащане за {data.month}" if data.month else None
    )
    
    # Create receipt automatically
    receipt_number = generate_receipt_number(db)
    receipt = Receipt(
        receipt_number=receipt_number,
        payment_id=payment.id,
        is_copy=False,
        original_receipt_id=None,
        issued_at=datetime.utcnow(),
        issued_by_id=current_user.id,
    )
    db.add(receipt)
    
    db.commit()
    db.refresh(payment)
    db.refresh(receipt)
    
    # Build response
    response = PaymentResponse.model_validate(payment)
    response.apartment_number = apartment.number
    response.owner_name = apartment.owner_name
    response.collected_by_name = current_user.display_name
    response.receipt_id = receipt.id
    
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
async def get_payment_receipt(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get receipt data for a payment."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Плащането не е намерено",
        )
    
    apartment = payment.apartment
    
    # Don't allow receipts for voided payments
    if payment.status == PaymentStatus.VOIDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не може да се издаде разписка за анулирано плащане",
        )
    
    return ReceiptData(
        receipt_number=f"R-{payment.id:06d}",
        payment_id=payment.id,
        payment_date=payment.payment_date,
        amount=float(payment.amount),
        payment_method=payment.payment_method,
        apartment_number=apartment.number if apartment else "N/A",
        owner_name=apartment.owner_name if apartment else "N/A",
        month=payment.month,
        collected_by=payment.collected_by.display_name if payment.collected_by else "N/A",
        notes=payment.notes,
    )


@router.post("/{payment_id}/void", response_model=PaymentVoidResponse)
async def void_payment(
    payment_id: int,
    data: PaymentVoidRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # RBAC: Admin only
):
    """Void (soft delete) a payment.
    
    SECURITY: Само администратори могат да анулират плащания.
    ВАЖНО: Плащанията НИКОГА не се изтриват физически!
    Тази операция:
    - Маркира плащането като voided
    - Записва причината за анулиране (задължителна)
    - Записва кой и кога е анулирал
    - Коригира баланса на сметката
    - Създава audit log запис
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Плащането не е намерено",
        )
    
    if payment.status == PaymentStatus.VOIDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Плащането вече е анулирано",
        )
    
    # Store state before void for audit
    state_before = {
        "id": payment.id,
        "amount": float(payment.amount),
        "month": payment.month,
        "apartment_id": payment.apartment_id,
        "status": payment.status.value,
    }
    
    # Update payment status
    voided_at = datetime.utcnow()
    payment.status = PaymentStatus.VOIDED
    payment.voided_at = voided_at
    payment.voided_by_id = current_user.id
    payment.void_reason = data.reason
    
    # Adjust account balance
    account = get_or_create_account(db, payment.apartment_id)
    transaction = remove_credit_from_account(
        db=db,
        account=account,
        amount=Decimal(str(payment.amount)),
        payment_id=payment.id,
        description=f"Анулиране: {data.reason}"
    )
    
    # Create audit log entry
    create_audit_log(
        db=db,
        action=AuditAction.PAYMENT_VOIDED,
        description=f"Анулирано плащане #{payment.id} за {payment.amount} лв. Причина: {data.reason}",
        user_id=current_user.id,
        user_email=current_user.username,
        entity_type="payment",
        entity_id=payment.id,
        apartment_id=payment.apartment_id,
        state_before=state_before,
        state_after={
            "id": payment.id,
            "amount": float(payment.amount),
            "month": payment.month,
            "apartment_id": payment.apartment_id,
            "status": "voided",
            "voided_at": voided_at.isoformat(),
            "voided_by_id": current_user.id,
            "void_reason": data.reason,
        },
        extra_data={"reason": data.reason},
        ip_address=request.client.host if request.client else None,
        is_critical=True,
    )
    
    db.commit()
    db.refresh(payment)
    db.refresh(account)
    
    return PaymentVoidResponse(
        success=True,
        message="Плащането е анулирано успешно",
        payment_id=payment.id,
        voided_at=voided_at,
        voided_by_id=current_user.id,
        void_reason=data.reason,
        balance_adjustment=-float(payment.amount),
        new_balance=float(account.balance),
    )
