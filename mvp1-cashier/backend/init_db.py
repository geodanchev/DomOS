"""Initialize database with tables and sample data.

Актуализирано за Account-based система.
Създава:
- Таблици
- Потребители (admin, cecka)
- Апартаменти със сметки
- Начални задължения
- Примерни плащания и транзакции
"""

import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, '.')

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import (
    Apartment, 
    Payment, 
    Obligation, 
    ObligationType,
    ApartmentAccount,
    AccountTransaction,
    TransactionType,
    TransactionReference,
    User,
    Receipt,
)
from app.models.user import UserRole
from app.core.security import get_password_hash


def init_db():
    """Create all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def create_users(db) -> tuple:
    """Create demo users. Returns (admin, cashier)."""
    # Check if users exist
    existing = db.query(User).first()
    if existing:
        print("Users already exist, fetching...")
        admin = db.query(User).filter(User.username == "admin").first()
        cashier = db.query(User).filter(User.username == "cecka").first()
        return admin, cashier
    
    print("Creating users...")
    
    # Create admin
    admin = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        display_name="Администратор",
        role=UserRole.ADMIN,
    )
    db.add(admin)
    
    # Create cashier (Цецка)
    cashier = User(
        username="cecka",
        password_hash=get_password_hash("1234"),
        display_name="Цецка",
        role=UserRole.CASHIER,
    )
    db.add(cashier)
    
    db.commit()
    print(f"  ✓ Created: admin (password: admin123)")
    print(f"  ✓ Created: cecka (password: 1234)")
    
    return admin, cashier


def create_apartments_with_accounts(db) -> list:
    """Create apartments with their accounts. Returns list of apartments."""
    # Check if apartments exist
    existing = db.query(Apartment).first()
    if existing:
        print("Apartments already exist, fetching...")
        return db.query(Apartment).all()
    
    print("Creating apartments with accounts...")
    
    apartments_data = [
        {"number": "1", "floor": 1, "owner_name": "Иван Петров", "residents_count": 2, "monthly_fee": Decimal("15.00")},
        {"number": "2", "floor": 1, "owner_name": "Мария Георгиева", "residents_count": 4, "monthly_fee": Decimal("30.00")},
        {"number": "3", "floor": 1, "owner_name": "Петър Стоянов", "residents_count": 3, "monthly_fee": Decimal("22.50")},
        {"number": "4", "floor": 2, "owner_name": "Елена Димитрова", "residents_count": 1, "monthly_fee": Decimal("10.00")},
        {"number": "5", "floor": 2, "owner_name": "Георги Иванов", "residents_count": 5, "monthly_fee": Decimal("35.00")},
        {"number": "6", "floor": 2, "owner_name": "Анна Николова", "residents_count": 2, "monthly_fee": Decimal("15.00")},
        {"number": "7", "floor": 3, "owner_name": "Стефан Тодоров", "residents_count": 3, "monthly_fee": Decimal("22.50")},
        {"number": "8", "floor": 3, "owner_name": "Катя Василева", "residents_count": 2, "monthly_fee": Decimal("15.00")},
        {"number": "9", "floor": 3, "owner_name": "Димитър Колев", "residents_count": 4, "monthly_fee": Decimal("30.00")},
        {"number": "10", "floor": 4, "owner_name": "Росица Атанасова", "residents_count": 2, "monthly_fee": Decimal("15.00")},
    ]
    
    apartments = []
    for data in apartments_data:
        apt = Apartment(**data)
        db.add(apt)
        db.flush()  # Get the ID
        
        # Create account for this apartment (starting balance 0)
        account = ApartmentAccount(
            apartment_id=apt.id,
            balance=Decimal("0.00")
        )
        db.add(account)
        apartments.append(apt)
    
    db.commit()
    print(f"  ✓ Created {len(apartments)} apartments with accounts")
    
    return apartments


def create_monthly_obligations(db, apartments: list) -> list:
    """Create monthly obligations for current month."""
    current_month = f"{date.today().year}-{date.today().month:02d}"
    
    # Check if obligations exist for this month
    existing = db.query(Obligation).filter(
        Obligation.month == current_month,
        Obligation.type == ObligationType.MONTHLY
    ).first()
    
    if existing:
        print(f"Obligations for {current_month} already exist, skipping...")
        return []
    
    print(f"Creating monthly obligations for {current_month}...")
    
    obligations = []
    for apt in apartments:
        db.refresh(apt)
        
        # Create obligation
        obligation = Obligation(
            type=ObligationType.MONTHLY,
            apartment_id=apt.id,
            month=current_month,
            amount=apt.monthly_fee,
            description=f"Месечна такса за {current_month}"
        )
        db.add(obligation)
        db.flush()
        
        # Get the apartment account
        account = db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == apt.id
        ).first()
        
        if account:
            # Debit the account (subtract from balance)
            account.balance -= apt.monthly_fee
            
            # Record the transaction
            transaction = AccountTransaction(
                account_id=account.id,
                type=TransactionType.DEBIT,
                amount=apt.monthly_fee,
                reference_type=TransactionReference.OBLIGATION,
                reference_id=obligation.id,
                balance_after=account.balance,
                description=f"Месечна такса {current_month}"
            )
            db.add(transaction)
        
        obligations.append(obligation)
    
    db.commit()
    print(f"  ✓ Created {len(obligations)} monthly obligations")
    
    return obligations


def create_sample_payments(db, apartments: list, cashier) -> list:
    """Create sample payments for some apartments."""
    current_month = f"{date.today().year}-{date.today().month:02d}"
    
    # Check if payments exist
    existing = db.query(Payment).filter(Payment.month == current_month).first()
    if existing:
        print("Payments already exist for this month, skipping...")
        return []
    
    print("Creating sample payments...")
    
    # Payment scenarios:
    # Apt 1 - fully paid
    # Apt 3 - partially paid (10 of 22.50)
    # Apt 5 - fully paid
    # Apt 7 - overpaid (30 instead of 22.50)
    
    payment_scenarios = [
        {"apt_index": 0, "amount": Decimal("15.00"), "note": "Платено изцяло"},
        {"apt_index": 2, "amount": Decimal("10.00"), "note": "Частично плащане"},
        {"apt_index": 4, "amount": Decimal("35.00"), "note": "Платено изцяло"},
        {"apt_index": 6, "amount": Decimal("30.00"), "note": "Надплатено"},
    ]
    
    payments = []
    for scenario in payment_scenarios:
        apt = apartments[scenario["apt_index"]]
        db.refresh(apt)
        
        # Create payment
        payment = Payment(
            apartment_id=apt.id,
            amount=float(scenario["amount"]),
            month=current_month,
            payment_date=date.today(),
            payment_method="cash",
            collected_by_id=cashier.id if cashier else None,
            notes=scenario["note"]
        )
        db.add(payment)
        db.flush()
        
        # Get the apartment account
        account = db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == apt.id
        ).first()
        
        if account:
            # Credit the account (add to balance)
            account.balance += scenario["amount"]
            
            # Record the transaction
            transaction = AccountTransaction(
                account_id=account.id,
                type=TransactionType.CREDIT,
                amount=scenario["amount"],
                reference_type=TransactionReference.PAYMENT,
                reference_id=payment.id,
                balance_after=account.balance,
                description=f"Плащане за {current_month}"
            )
            db.add(transaction)
        
        payments.append(payment)
        print(f"  ✓ Apt {apt.number}: {scenario['amount']} лв - {scenario['note']}")
    
    db.commit()
    
    return payments


def print_summary(db):
    """Print summary of database state."""
    print("\n" + "="*60)
    print("DATABASE INITIALIZED SUCCESSFULLY!")
    print("="*60)
    
    # Users
    users = db.query(User).all()
    print(f"\n📋 Users ({len(users)}):")
    for u in users:
        print(f"   - {u.username} ({u.display_name}) - {u.role.value}")
    print("   Passwords: admin=admin123, cecka=1234")
    
    # Apartments
    apartments = db.query(Apartment).all()
    print(f"\n🏠 Apartments ({len(apartments)}):")
    
    # Account balances
    print("\n💰 Account Balances:")
    print(f"   {'Ап.':<5} {'Собственик':<20} {'Такса':>8} {'Баланс':>10} {'Статус':<15}")
    print("   " + "-"*58)
    
    for apt in apartments:
        db.refresh(apt)
        account = apt.account
        if account:
            balance = account.balance
            if balance > 0:
                status = "✅ Надплатено"
            elif balance == 0:
                status = "✅ Изравнен"
            else:
                status = f"⚠️ Дължи {abs(balance):.2f}"
            print(f"   {apt.number:<5} {apt.owner_name:<20} {apt.monthly_fee:>8.2f} {balance:>10.2f} {status}")
    
    # Transactions count
    tx_count = db.query(AccountTransaction).count()
    print(f"\n📊 Total transactions: {tx_count}")
    
    print("\n" + "="*60)


def main():
    """Main entry point."""
    print("\n🚀 DomOS MVP1 Database Initialization")
    print("="*60 + "\n")
    
    # Create tables
    init_db()
    
    # Create data
    db = SessionLocal()
    try:
        admin, cashier = create_users(db)
        apartments = create_apartments_with_accounts(db)
        create_monthly_obligations(db, apartments)
        create_sample_payments(db, apartments, cashier)
        
        print_summary(db)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
