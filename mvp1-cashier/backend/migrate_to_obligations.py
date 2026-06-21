"""Скрипт за миграция на данни от MonthlyCharge и CustomCharge към Obligation.

Използване:
    cd /a0/usr/projects/domos/mvp1-cashier/backend
    source venv/bin/activate
    python migrate_to_obligations.py

Този скрипт:
1. Чете всички записи от monthly_charges
2. Чете всички записи от custom_charges  
3. Създава съответни записи в obligations таблицата
4. НЕ изтрива старите данни (за безопасност)
"""

import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Add app to path
sys.path.insert(0, '.')

from app.db.base import Base
from app.models.monthly_charge import MonthlyCharge, ChargeStatus
from app.models.custom_charge import CustomCharge, CustomChargeStatus
from app.models.obligation import Obligation, ObligationType, ObligationStatus
from app.core.config import settings


def map_charge_status_to_obligation(status: ChargeStatus | CustomChargeStatus) -> ObligationStatus:
    """Map old status enum to new ObligationStatus."""
    if status.value == "paid":
        return ObligationStatus.PAID
    elif status.value == "partial":
        return ObligationStatus.PARTIAL
    else:
        return ObligationStatus.UNPAID


def migrate_monthly_charges(session: Session) -> int:
    """Migrate MonthlyCharge records to Obligation."""
    monthly_charges = session.execute(select(MonthlyCharge)).scalars().all()
    migrated = 0
    
    for mc in monthly_charges:
        # Check if already migrated
        existing = session.execute(
            select(Obligation).where(
                Obligation.type == ObligationType.MONTHLY,
                Obligation.apartment_id == mc.apartment_id,
                Obligation.month == mc.month
            )
        ).scalar_one_or_none()
        
        if existing:
            print(f"  Skipping MonthlyCharge {mc.id} - already migrated")
            continue
        
        obligation = Obligation(
            type=ObligationType.MONTHLY,
            apartment_id=mc.apartment_id,
            month=mc.month,
            amount_due=float(mc.amount_due),
            amount_paid=float(mc.amount_paid),
            description=f"Месечна такса за {mc.month}",
            status=map_charge_status_to_obligation(mc.status),
        )
        session.add(obligation)
        migrated += 1
        print(f"  Migrated MonthlyCharge {mc.id} -> Obligation (apartment={mc.apartment_id}, month={mc.month})")
    
    return migrated


def migrate_custom_charges(session: Session) -> int:
    """Migrate CustomCharge records to Obligation."""
    custom_charges = session.execute(select(CustomCharge)).scalars().all()
    migrated = 0
    
    for cc in custom_charges:
        # Determine obligation type based on description
        # Default to INITIAL for backward compatibility
        obligation_type = ObligationType.INITIAL
        description = cc.description or "Произволно задължение"
        
        # Try to detect type from description
        desc_lower = description.lower()
        if "глоба" in desc_lower or "санкция" in desc_lower or "нарушение" in desc_lower:
            obligation_type = ObligationType.PENALTY
        elif "ремонт" in desc_lower:
            obligation_type = ObligationType.REPAIR
        elif "фонд" in desc_lower:
            obligation_type = ObligationType.FUND
        elif "начално" in desc_lower or "преди" in desc_lower:
            obligation_type = ObligationType.INITIAL
        
        # Check if similar obligation exists (by apartment, type and amount)
        existing = session.execute(
            select(Obligation).where(
                Obligation.type == obligation_type,
                Obligation.apartment_id == cc.apartment_id,
                Obligation.amount_due == float(cc.amount_due),
                Obligation.month.is_(None)  # Non-monthly
            )
        ).scalar_one_or_none()
        
        if existing:
            print(f"  Skipping CustomCharge {cc.id} - similar obligation exists")
            continue
        
        obligation = Obligation(
            type=obligation_type,
            apartment_id=cc.apartment_id,
            month=None,  # Custom charges don't have month
            amount_due=float(cc.amount_due),
            amount_paid=float(cc.amount_paid),
            description=description,
            status=map_charge_status_to_obligation(cc.status),
        )
        session.add(obligation)
        migrated += 1
        print(f"  Migrated CustomCharge {cc.id} -> Obligation (apartment={cc.apartment_id}, type={obligation_type.value})")
    
    return migrated


def main():
    """Run migration."""
    print("="*60)
    print("Миграция на данни към унифициран Obligation модел")
    print("="*60)
    
    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        print("\n[1/2] Мигриране на MonthlyCharge записи...")
        monthly_count = migrate_monthly_charges(session)
        
        print("\n[2/2] Мигриране на CustomCharge записи...")
        custom_count = migrate_custom_charges(session)
        
        # Commit all changes
        session.commit()
        
        print("\n" + "="*60)
        print("РЕЗУЛТАТ:")
        print(f"  - Мигрирани MonthlyCharge записи: {monthly_count}")
        print(f"  - Мигрирани CustomCharge записи: {custom_count}")
        print(f"  - Общо нови Obligation записи: {monthly_count + custom_count}")
        print("="*60)
        
        # Verify migration
        total_obligations = session.execute(
            select(Obligation)
        ).scalars().all()
        print(f"\nВерификация: {len(total_obligations)} записа в obligations таблицата")
        
        # Show breakdown by type
        for otype in ObligationType:
            count = len([o for o in total_obligations if o.type == otype])
            if count > 0:
                print(f"  - {otype.value}: {count}")


if __name__ == "__main__":
    main()
