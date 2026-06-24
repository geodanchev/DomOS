"""Expenses API endpoints - управление на разходи от фонда.

CRUD операции за разходи:
- Създаване на разход
- Списък с разходи
- Детайли за разход
- Редакция на разход
- Маркиране като платен
- Анулиране
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.expense import Expense, ExpenseType, ExpenseStatus
from app.models.user import User
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    ExpenseList,
    ExpenseSummary,
)
from app.api.auth import get_current_user

router = APIRouter()


def build_expense_response(expense: Expense) -> ExpenseResponse:
    """Build ExpenseResponse with display fields."""
    return ExpenseResponse(
        id=expense.id,
        description=expense.description,
        amount=float(expense.amount),
        expense_type=expense.expense_type,
        expense_date=expense.expense_date,
        vendor=expense.vendor,
        invoice_number=expense.invoice_number,
        notes=expense.notes,
        status=expense.status,
        paid_date=expense.paid_date,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
        created_by=expense.created_by,
        status_display=ExpenseResponse.get_status_display(expense.status),
        type_display=ExpenseResponse.get_type_display(expense.expense_type),
    )


@router.post("", response_model=ExpenseResponse, status_code=201)
async def create_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new expense.
    
    Създава нов разход във фонда.
    """
    expense = Expense(
        description=expense_data.description,
        amount=Decimal(str(expense_data.amount)),
        expense_type=expense_data.expense_type,
        expense_date=expense_data.expense_date,
        vendor=expense_data.vendor,
        invoice_number=expense_data.invoice_number,
        notes=expense_data.notes,
        status=ExpenseStatus.PENDING,
        created_by=current_user.id,
    )
    
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    return build_expense_response(expense)


@router.get("", response_model=ExpenseList)
async def list_expenses(
    status: Optional[ExpenseStatus] = Query(None, description="Филтър по статус"),
    expense_type: Optional[ExpenseType] = Query(None, description="Филтър по тип"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all expenses with optional filters.
    
    Списък с всички разходи.
    """
    query = db.query(Expense)
    
    if status:
        query = query.filter(Expense.status == status)
    if expense_type:
        query = query.filter(Expense.expense_type == expense_type)
    
    total_count = query.count()
    expenses = query.order_by(Expense.expense_date.desc()).offset(skip).limit(limit).all()
    
    # Calculate totals
    total_amount = db.query(func.sum(Expense.amount)).filter(
        Expense.status != ExpenseStatus.CANCELLED
    ).scalar() or Decimal("0")
    
    total_paid = db.query(func.sum(Expense.amount)).filter(
        Expense.status == ExpenseStatus.PAID
    ).scalar() or Decimal("0")
    
    total_pending = db.query(func.sum(Expense.amount)).filter(
        Expense.status == ExpenseStatus.PENDING
    ).scalar() or Decimal("0")
    
    return ExpenseList(
        expenses=[build_expense_response(e) for e in expenses],
        total_count=total_count,
        total_amount=float(total_amount),
        total_paid=float(total_paid),
        total_pending=float(total_pending),
    )


@router.get("/summary", response_model=list[ExpenseSummary])
async def get_expenses_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get summary of expenses by type.
    
    Обобщение на разходите по тип.
    """
    results = db.query(
        Expense.expense_type,
        func.count(Expense.id).label("count"),
        func.sum(Expense.amount).label("total_amount"),
    ).filter(
        Expense.status != ExpenseStatus.CANCELLED
    ).group_by(
        Expense.expense_type
    ).all()
    
    return [
        ExpenseSummary(
            expense_type=r.expense_type,
            type_display=ExpenseResponse.get_type_display(r.expense_type),
            count=r.count,
            total_amount=float(r.total_amount or 0),
        )
        for r in results
    ]


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get expense by ID.
    
    Детайли за конкретен разход.
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Разходът не е намерен")
    
    return build_expense_response(expense)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update expense.
    
    Редакция на разход.
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Разходът не е намерен")
    
    # Cannot edit cancelled expenses
    if expense.status == ExpenseStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Не може да редактирате анулиран разход")
    
    update_data = expense_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "amount" and value is not None:
            value = Decimal(str(value))
        setattr(expense, field, value)
    
    db.commit()
    db.refresh(expense)
    
    return build_expense_response(expense)


@router.post("/{expense_id}/pay", response_model=ExpenseResponse)
async def mark_expense_paid(
    expense_id: int,
    paid_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark expense as paid.
    
    Маркиране на разход като платен.
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Разходът не е намерен")
    
    if expense.status == ExpenseStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Не може да платите анулиран разход")
    
    if expense.status == ExpenseStatus.PAID:
        raise HTTPException(status_code=400, detail="Разходът вече е платен")
    
    expense.status = ExpenseStatus.PAID
    expense.paid_date = paid_date or datetime.utcnow()
    
    db.commit()
    db.refresh(expense)
    
    return build_expense_response(expense)


@router.post("/{expense_id}/cancel", response_model=ExpenseResponse)
async def cancel_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel expense.
    
    Анулиране на разход.
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Разходът не е намерен")
    
    if expense.status == ExpenseStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Разходът вече е анулиран")
    
    expense.status = ExpenseStatus.CANCELLED
    
    db.commit()
    db.refresh(expense)
    
    return build_expense_response(expense)
