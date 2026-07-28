"""CRUD услуга за управление на задължения (Obligation).

АРХИТЕКТУРА БЕЗ КЕШИРАН БАЛАНС:
Задълженията се записват директно. Балансът се изчислява динамично.
AccountTransaction се използва само за одит цели.
"""

from typing import Optional
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.obligation import Obligation, ObligationType
from app.models.apartment import Apartment
from app.models.account import ApartmentAccount, AccountTransaction, TransactionType, TransactionReference
from app.models.payment import Payment, PaymentStatus
from app.schemas.obligation import (
    ObligationCreate,
    ObligationUpdate,
    ObligationSummary,
    MonthlyObligationsSummary,
)


class ObligationService:
    """Услуга за CRUD операции със задължения.
    
    С новата архитектура без кеширан баланс, услугата:
    - Записва задължения директно в базата
    - Записва audit транзакции (без balance_after)
    - НЕ обновява кеширан баланс
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Helper functions ====================
    
    def _calculate_balance(self, apartment_id: int) -> Decimal:
        """Calculate balance dynamically from payments and obligations.
        
        balance = sum(active payments) - sum(obligations)
        """
        total_payments = self.db.query(func.sum(Payment.amount)).filter(
            Payment.apartment_id == apartment_id,
            Payment.status == PaymentStatus.ACTIVE
        ).scalar() or Decimal("0")
        
        total_obligations = self.db.query(func.sum(Obligation.amount)).filter(
            Obligation.apartment_id == apartment_id
        ).scalar() or Decimal("0")
        
        return Decimal(str(total_payments)) - Decimal(str(total_obligations))
    
    def _get_or_create_account(self, apartment_id: int) -> ApartmentAccount:
        """Get or create account for apartment.
        
        Account is now just a container for audit transactions.
        Balance is calculated dynamically, not stored.
        """
        account = self.db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == apartment_id
        ).first()
        
        if not account:
            # Simply create account without balance calculation
            account = ApartmentAccount(apartment_id=apartment_id)
            self.db.add(account)
            self.db.flush()
        
        return account
    
    def _record_transaction(
        self,
        account: ApartmentAccount,
        transaction_type: TransactionType,
        amount: Decimal,
        reference_type: TransactionReference,
        reference_id: int,
        description: str | None = None
    ) -> AccountTransaction:
        """Record a transaction for audit purposes.
        
        Note: balance_after is no longer calculated/stored.
        Transactions are purely for audit trail.
        """
        transaction = AccountTransaction(
            account_id=account.id,
            type=transaction_type,
            amount=amount,
            reference_type=reference_type,
            reference_id=reference_id,
            balance_after=None,  # No longer storing cached balance
            description=description
        )
        self.db.add(transaction)
        return transaction
    
    # ==================== CRUD операции ====================
    
    def create(self, data: ObligationCreate) -> Obligation:
        """Създава ново задължение.
        
        С новата архитектура:
        - Записва задължението директно
        - Записва audit транзакция
        - НЕ обновява кеширан баланс
        """
        obligation = Obligation(
            type=data.type,
            apartment_id=data.apartment_id,
            month=data.month,
            amount=data.amount,
            description=data.description,
        )
        self.db.add(obligation)
        self.db.flush()  # Get obligation ID
        
        # Record audit transaction (no balance update)
        account = self._get_or_create_account(data.apartment_id)
        self._record_transaction(
            account=account,
            transaction_type=TransactionType.DEBIT,
            amount=Decimal(str(data.amount)),
            reference_type=TransactionReference.OBLIGATION,
            reference_id=obligation.id,
            description=data.description or f"{data.type.value} задължение"
        )
        
        self.db.commit()
        self.db.refresh(obligation)
        return obligation
    
    def get(self, obligation_id: int) -> Optional[Obligation]:
        """Връща задължение по ID."""
        return self.db.get(Obligation, obligation_id)
    
    def get_by_apartment_and_month(
        self,
        apartment_id: int,
        month: str,
        obligation_type: ObligationType = ObligationType.MONTHLY
    ) -> Optional[Obligation]:
        """Връща задължение по апартамент, месец и тип."""
        stmt = select(Obligation).where(
            Obligation.apartment_id == apartment_id,
            Obligation.month == month,
            Obligation.type == obligation_type
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        obligation_type: Optional[ObligationType] = None,
        apartment_id: Optional[int] = None,
        month: Optional[str] = None,
    ) -> list[Obligation]:
        """Връща списък със задължения с филтриране."""
        stmt = select(Obligation)
        
        if obligation_type:
            stmt = stmt.where(Obligation.type == obligation_type)
        if apartment_id:
            stmt = stmt.where(Obligation.apartment_id == apartment_id)
        if month:
            stmt = stmt.where(Obligation.month == month)
        
        stmt = stmt.order_by(Obligation.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
    
    def list_by_apartment(self, apartment_id: int) -> list[Obligation]:
        """Връща всички задължения за апартамент."""
        stmt = select(Obligation).where(
            Obligation.apartment_id == apartment_id
        ).order_by(Obligation.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())
    
    def update(self, obligation_id: int, data: ObligationUpdate) -> Optional[Obligation]:
        """Актуализира задължение.
        
        С новата архитектура:
        - Обновява задължението директно
        - Записва audit транзакция при промяна на сумата
        - НЕ обновява кеширан баланс
        """
        obligation = self.get(obligation_id)
        if not obligation:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        old_amount = Decimal(str(obligation.amount))
        
        for field, value in update_data.items():
            setattr(obligation, field, value)
        
        # If amount changed, record adjustment transaction for audit
        if "amount" in update_data:
            new_amount = Decimal(str(update_data["amount"]))
            amount_diff = new_amount - old_amount
            
            if amount_diff != 0:
                account = self._get_or_create_account(obligation.apartment_id)
                if amount_diff > 0:
                    # Increased - record debit transaction
                    self._record_transaction(
                        account=account,
                        transaction_type=TransactionType.DEBIT,
                        amount=amount_diff,
                        reference_type=TransactionReference.ADJUSTMENT,
                        reference_id=obligation.id,
                        description=f"Увеличение на задължение #{obligation.id}"
                    )
                else:
                    # Decreased - record credit transaction
                    self._record_transaction(
                        account=account,
                        transaction_type=TransactionType.CREDIT,
                        amount=abs(amount_diff),
                        reference_type=TransactionReference.ADJUSTMENT,
                        reference_id=obligation.id,
                        description=f"Намаление на задължение #{obligation.id}"
                    )
        
        self.db.commit()
        self.db.refresh(obligation)
        return obligation
    
    def delete(self, obligation_id: int) -> bool:
        """Изтрива задължение.
        
        С новата архитектура:
        - Изтрива задължението директно
        - Записва audit транзакция
        - НЕ обновява кеширан баланс
        """
        obligation = self.get(obligation_id)
        if not obligation:
            return False
        
        # Record credit transaction for audit
        account = self._get_or_create_account(obligation.apartment_id)
        self._record_transaction(
            account=account,
            transaction_type=TransactionType.CREDIT,
            amount=Decimal(str(obligation.amount)),
            reference_type=TransactionReference.ADJUSTMENT,
            reference_id=obligation.id,
            description=f"Изтрито задължение: {obligation.description or obligation.type.value}"
        )
        
        self.db.delete(obligation)
        self.db.commit()
        return True
    
    # ==================== Генериране на месечни задължения ====================
    
    def generate_monthly_obligations(self, month: str) -> list[Obligation]:
        """Генерира месечни задължения за всички апартаменти.
        
        Args:
            month: Месец във формат YYYY-MM
            
        Returns:
            Списък със създадените задължения
        """
        # Вземаме всички апартаменти
        apartments = list(self.db.execute(select(Apartment)).scalars().all())
        created = []
        
        for apt in apartments:
            # Проверяваме дали вече има задължение за този месец
            existing = self.get_by_apartment_and_month(
                apt.id, month, ObligationType.MONTHLY
            )
            if existing:
                continue
            
            # Създаваме ново месечно задължение
            obligation = Obligation(
                type=ObligationType.MONTHLY,
                apartment_id=apt.id,
                month=month,
                amount=Decimal(str(apt.monthly_fee)),
                description=f"Месечна такса за {month}",
            )
            self.db.add(obligation)
            self.db.flush()  # Get obligation ID
            
            # Record audit transaction (no balance update)
            account = self._get_or_create_account(apt.id)
            self._record_transaction(
                account=account,
                transaction_type=TransactionType.DEBIT,
                amount=Decimal(str(apt.monthly_fee)),
                reference_type=TransactionReference.OBLIGATION,
                reference_id=obligation.id,
                description=f"Месечна такса за {month}"
            )
            
            created.append(obligation)
        
        if created:
            self.db.commit()
            for obl in created:
                self.db.refresh(obl)
        
        return created
    
    # ==================== Статистики ====================
    
    def get_apartment_balance(self, apartment_id: int) -> float:
        """Връща текущия баланс на апартамент (изчислен динамично)."""
        return float(self._calculate_balance(apartment_id))
    
    def get_summary(
        self,
        apartment_id: Optional[int] = None,
        month: Optional[str] = None,
        obligation_type: Optional[ObligationType] = None,
    ) -> ObligationSummary:
        """Връща обобщена статистика за задълженията."""
        # Build filters
        obl_filters = []
        payment_filters = [Payment.status == PaymentStatus.ACTIVE]  # Only active payments
        
        if apartment_id:
            obl_filters.append(Obligation.apartment_id == apartment_id)
            payment_filters.append(Payment.apartment_id == apartment_id)
        if month:
            obl_filters.append(Obligation.month == month)
            payment_filters.append(Payment.month == month)
        if obligation_type:
            obl_filters.append(Obligation.type == obligation_type)
        
        # Get totals
        obl_query = self.db.query(func.sum(Obligation.amount))
        if obl_filters:
            obl_query = obl_query.filter(*obl_filters)
        total_obligations = obl_query.scalar() or Decimal("0")
        
        payment_query = self.db.query(func.sum(Payment.amount))
        if payment_filters:
            payment_query = payment_query.filter(*payment_filters)
        total_payments = payment_query.scalar() or Decimal("0")
        
        balance = float(Decimal(str(total_payments)) - Decimal(str(total_obligations)))
        
        # Count obligations
        count_query = self.db.query(func.count(Obligation.id))
        if obl_filters:
            count_query = count_query.filter(*obl_filters)
        count = count_query.scalar() or 0
        
        return ObligationSummary(
            total_obligations=float(total_obligations),
            total_payments=float(total_payments),
            balance=balance,
            count_obligations=count,
        )
    
    def get_monthly_summary(self, month: str) -> MonthlyObligationsSummary:
        """Връща обобщена статистика за месец."""
        summary = self.get_summary(month=month, obligation_type=ObligationType.MONTHLY)
        return MonthlyObligationsSummary(
            month=month,
            total_obligations=summary.total_obligations,
            total_payments=summary.total_payments,
            balance=summary.balance,
            count_obligations=summary.count_obligations,
        )