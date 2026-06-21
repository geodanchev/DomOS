"""Receipts API endpoints - разписки/квитанции.

Спринт 3: API за създаване, четене и PDF генериране на разписки.
"""

from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from io import BytesIO

from app.db.session import get_db
from app.models.receipt import Receipt
from app.models.payment import Payment
from app.models.user import User
from app.schemas.receipt import (
    ReceiptCreate,
    ReceiptResponse,
    ReceiptListResponse,
    ReceiptWithDetails,
)
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/receipts", tags=["receipts"])


def generate_receipt_number(db: Session) -> str:
    """Генерира следващ номер на разписка за текущата година.
    
    Формат: YYYY-NNNNNN (напр. 2026-000001)
    """
    current_year = date.today().year
    year_prefix = f"{current_year}-"
    
    # Намираме последния номер за тази година (само оригинали)
    last_receipt = db.query(Receipt).filter(
        Receipt.receipt_number.like(f"{year_prefix}%"),
        Receipt.is_copy == False
    ).order_by(Receipt.id.desc()).first()
    
    if last_receipt:
        # Извличаме номера и увеличаваме
        last_num = int(last_receipt.receipt_number.split("-")[1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"{year_prefix}{next_num:06d}"


@router.post("", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
def create_receipt(
    data: ReceiptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Създава нова оригинална разписка за плащане.
    
    - Едно плащане може да има само една оригинална разписка
    - За допълнителни копия използвайте POST /api/receipts/{id}/copy
    """
    # Проверяваме дали плащането съществува
    payment = db.query(Payment).filter(Payment.id == data.payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with id {data.payment_id} not found"
        )
    
    # Проверяваме дали вече има оригинална разписка за това плащане
    existing = db.query(Receipt).filter(
        Receipt.payment_id == data.payment_id,
        Receipt.is_copy == False
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt already exists for this payment. Use copy endpoint instead."
        )
    
    # Генерираме номер и създаваме разписката
    receipt_number = generate_receipt_number(db)
    
    receipt = Receipt(
        receipt_number=receipt_number,
        payment_id=data.payment_id,
        is_copy=False,
        original_receipt_id=None,
        issued_at=datetime.utcnow(),
        issued_by_id=current_user.id,
    )
    
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    
    return receipt


@router.post("/{receipt_id}/copy", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
def create_receipt_copy(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Създава копие на съществуваща разписка.
    
    - Копието има същия receipt_number като оригинала
    - Копие на копие сочи към оригинала, не към копието
    - Няма лимит на копията
    """
    # Намираме разписката
    source_receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not source_receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with id {receipt_id} not found"
        )
    
    # Определяме оригинала (ако source е копие, вземаме неговия оригинал)
    if source_receipt.is_copy:
        original_id = source_receipt.original_receipt_id
        receipt_number = source_receipt.receipt_number
    else:
        original_id = source_receipt.id
        receipt_number = source_receipt.receipt_number
    
    # Създаваме копието
    copy = Receipt(
        receipt_number=receipt_number,
        payment_id=source_receipt.payment_id,
        is_copy=True,
        original_receipt_id=original_id,
        issued_at=datetime.utcnow(),
        issued_by_id=current_user.id,
    )
    
    db.add(copy)
    db.commit()
    db.refresh(copy)
    
    return copy


@router.get("/{receipt_id}", response_model=ReceiptResponse)
def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Връща разписка по ID."""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with id {receipt_id} not found"
        )
    return receipt


@router.get("", response_model=ReceiptListResponse)
def list_receipts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    apartment_id: Optional[int] = Query(None, description="Филтър по апартамент"),
    is_copy: Optional[bool] = Query(None, description="Филтър по тип (оригинал/копие)"),
    from_date: Optional[date] = Query(None, description="От дата"),
    to_date: Optional[date] = Query(None, description="До дата"),
    page: int = Query(1, ge=1, description="Страница"),
    limit: int = Query(50, ge=1, le=100, description="Брой на страница"),
):
    """Връща списък с разписки с пагинация и филтри."""
    query = db.query(Receipt)
    
    # Филтър по апартамент (през Payment)
    if apartment_id is not None:
        query = query.join(Payment).filter(Payment.apartment_id == apartment_id)
    
    # Филтър по тип (оригинал/копие)
    if is_copy is not None:
        query = query.filter(Receipt.is_copy == is_copy)
    
    # Филтър по дата
    if from_date:
        query = query.filter(Receipt.issued_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        query = query.filter(Receipt.issued_at <= datetime.combine(to_date, datetime.max.time()))
    
    # Общ брой
    total = query.count()
    
    # Пагинация
    offset = (page - 1) * limit
    receipts = query.order_by(Receipt.issued_at.desc()).offset(offset).limit(limit).all()
    
    return ReceiptListResponse(
        items=receipts,
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{receipt_id}/pdf")
def get_receipt_pdf(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Генерира и връща PDF на разписката."""
    # Намираме разписката с всички връзки
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with id {receipt_id} not found"
        )
    
    # Зареждаме payment и apartment
    payment = receipt.payment
    apartment = payment.apartment
    issuer = receipt.issued_by
    
    # Генерираме PDF
    from app.services.pdf_generator import generate_receipt_pdf
    
    pdf_buffer = generate_receipt_pdf(
        receipt_number=receipt.receipt_number,
        is_copy=receipt.is_copy,
        issued_at=receipt.issued_at,
        amount=float(payment.amount),
        month=payment.month,
        payment_method=payment.payment_method,
        payment_date=payment.payment_date,
        apartment_number=apartment.number,
        owner_name=apartment.owner_name,
        issued_by_name=issuer.display_name if issuer else None,
    )
    
    # Връщаме като StreamingResponse
    filename = f"receipt_{receipt.receipt_number}.pdf"
    if receipt.is_copy:
        filename = f"receipt_{receipt.receipt_number}_copy.pdf"
    
    return StreamingResponse(
        BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
