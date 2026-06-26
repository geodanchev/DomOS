"""API endpoints за управление на задължения (Obligation).

Актуализирано за account-based система.
При създаване на задължение се дебитира сметката на апартамента.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.obligation import ObligationType
from app.schemas.obligation import (
    ObligationCreate,
    ObligationUpdate,
    ObligationResponse,
    ObligationSummary,
    MonthlyObligationsSummary,
)
from app.services.obligation_service import ObligationService
from app.models.user import User
from app.api.auth import get_current_user, require_admin, require_cashier_or_admin

router = APIRouter(prefix="/obligations", tags=["obligations"])


# ==================== CRUD Endpoints ====================

@router.post("/", response_model=ObligationResponse, status_code=201)
def create_obligation(
    data: ObligationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cashier_or_admin),  # RBAC: Admin or Cashier
):
    """Създава ново задължение и дебитира сметката на апартамента.
    
    SECURITY: Администратори и касиери могат да създават задължения.
    """
    service = ObligationService(db)
    return service.create(data)


@router.get("/", response_model=list[ObligationResponse])
def list_obligations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: Optional[ObligationType] = None,
    apartment_id: Optional[int] = None,
    month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Връща списък със задължения с филтриране."""
    service = ObligationService(db)
    return service.list_all(
        skip=skip,
        limit=limit,
        obligation_type=type,
        apartment_id=apartment_id,
        month=month,
    )


@router.get("/{obligation_id}", response_model=ObligationResponse)
def get_obligation(
    obligation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Връща задължение по ID."""
    service = ObligationService(db)
    obligation = service.get(obligation_id)
    if not obligation:
        raise HTTPException(status_code=404, detail="Задължението не е намерено")
    return obligation


@router.patch("/{obligation_id}", response_model=ObligationResponse)
def update_obligation(
    obligation_id: int,
    data: ObligationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # RBAC: Admin only
):
    """Актуализира задължение.
    
    SECURITY: Само администратори могат да редактират задължения.
    """
    service = ObligationService(db)
    obligation = service.update(obligation_id, data)
    if not obligation:
        raise HTTPException(status_code=404, detail="Задължението не е намерено")
    return obligation


@router.delete("/{obligation_id}", status_code=204)
def delete_obligation(
    obligation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # RBAC: Admin only
):
    """Изтрива задължение и кредитира обратно сметката.
    
    SECURITY: Само администратори могат да изтриват задължения.
    """
    service = ObligationService(db)
    if not service.delete(obligation_id):
        raise HTTPException(status_code=404, detail="Задължението не е намерено")


# ==================== Apartment Obligations ====================

@router.get("/apartment/{apartment_id}", response_model=list[ObligationResponse])
def list_apartment_obligations(
    apartment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Връща всички задължения за апартамент."""
    service = ObligationService(db)
    return service.list_by_apartment(apartment_id)


@router.get("/apartment/{apartment_id}/balance")
def get_apartment_balance(
    apartment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Връща текущия баланс на апартамент."""
    service = ObligationService(db)
    balance = service.get_apartment_balance(apartment_id)
    return {"apartment_id": apartment_id, "balance": balance}


# ==================== Monthly Generation ====================

@router.post("/generate-monthly", response_model=list[ObligationResponse])
def generate_monthly_obligations(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$", description="Месец (YYYY-MM)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # RBAC: Admin only
):
    """Генерира месечни задължения за всички апартаменти.
    
    SECURITY: Само администратори могат да генерират месечни задължения.
    При генериране се дебитира сметката на всеки апартамент.
    """
    service = ObligationService(db)
    return service.generate_monthly_obligations(month)


# ==================== Statistics ====================

@router.get("/stats/summary", response_model=ObligationSummary)
def get_obligations_summary(
    apartment_id: Optional[int] = None,
    month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    type: Optional[ObligationType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Връща обобщена статистика за задълженията."""
    service = ObligationService(db)
    return service.get_summary(
        apartment_id=apartment_id,
        month=month,
        obligation_type=type,
    )


@router.get("/stats/monthly/{month}", response_model=MonthlyObligationsSummary)
def get_monthly_summary(
    month: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Връща обобщена статистика за месец."""
    service = ObligationService(db)
    return service.get_monthly_summary(month)
