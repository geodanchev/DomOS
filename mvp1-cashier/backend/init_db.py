"""Initialize database with tables and real building data.

Създава:
- Таблици
- Потребители (Gosh, Cvetelina, Ani)
- Апартаменти със сметки (реални данни от сградата)

НЕ създава задължения и плащания - базата започва празна.
"""

import sys
from decimal import Decimal

sys.path.insert(0, '.')

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import (
    Apartment,
    ApartmentAccount,
    User,
)
from app.models.user import UserRole
from app.core.security import get_password_hash


def init_db():
    """Create all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def create_users(db) -> dict:
    """Create users. Returns dict of users."""
    # Check if users exist
    existing = db.query(User).first()
    if existing:
        print("Users already exist, fetching...")
        return {
            'admin': db.query(User).filter(User.username == "Gosh").first(),
            'cashier': db.query(User).filter(User.username == "Cvetelina").first(),
            'viewer': db.query(User).filter(User.username == "Ani").first(),
        }
    
    print("Creating users...")
    
    users = {}
    
    # Create admin - Gosh
    users['admin'] = User(
        username="Gosh",
        password_hash=get_password_hash("Adidas2002802"),
        display_name="Гош",
        role=UserRole.ADMIN,
    )
    db.add(users['admin'])
    
    # Create cashier - Cvetelina
    users['cashier'] = User(
        username="Cvetelina",
        password_hash=get_password_hash("Sony5Mouse"),
        display_name="Цветелина",
        role=UserRole.CASHIER,
    )
    db.add(users['cashier'])
    
    # Create viewer - Ani
    users['viewer'] = User(
        username="Ani",
        password_hash=get_password_hash("Book4Me"),
        display_name="Ани",
        role=UserRole.VIEWER,
    )
    db.add(users['viewer'])
    
    db.commit()
    print(f"  ✓ Created: Gosh (admin)")
    print(f"  ✓ Created: Cvetelina (cashier)")
    print(f"  ✓ Created: Ani (viewer)")
    
    return users


def create_apartments_with_accounts(db) -> list:
    """Create apartments with their accounts. Returns list of apartments."""
    # Check if apartments exist
    existing = db.query(Apartment).first()
    if existing:
        print("Apartments already exist, fetching...")
        return db.query(Apartment).all()
    
    print("Creating apartments with accounts...")
    
    # Real building data
    # Format: number, floor, owner_name, residents_count, monthly_fee, notes
    apartments_data = [
        # Етаж 1
        {"number": "1", "floor": 1, "owner_name": "Драгана", "residents_count": 1, "monthly_fee": Decimal("9.00"), "notes": None},
        {"number": "2", "floor": 1, "owner_name": "Огнян", "residents_count": 2, "monthly_fee": Decimal("11.00"), "notes": None},
        {"number": "3", "floor": 1, "owner_name": "Стоянка Гълабова", "residents_count": 0, "monthly_fee": Decimal("7.00"), "notes": None},
        {"number": "4", "floor": 1, "owner_name": "Георги", "residents_count": 2, "monthly_fee": Decimal("11.00"), "notes": None},
        
        # Етаж 2
        {"number": "9", "floor": 2, "owner_name": "Цветослава Василева Ботева", "residents_count": 0, "monthly_fee": Decimal("7.00"), "notes": None},
        {"number": "10", "floor": 2, "owner_name": "Петия", "residents_count": 1, "monthly_fee": Decimal("9.00"), "notes": None},
        {"number": "11", "floor": 2, "owner_name": "Венета", "residents_count": 1, "monthly_fee": Decimal("9.00"), "notes": None},
        {"number": "12", "floor": 2, "owner_name": "Петър Спасов", "residents_count": 1, "monthly_fee": Decimal("9.00"), "notes": None},
        
        # Етаж 3
        {"number": "17", "floor": 3, "owner_name": "Ивка", "residents_count": 1, "monthly_fee": Decimal("9.50"), "notes": "0.5 за куче"},
        {"number": "18", "floor": 3, "owner_name": "Надка Чуканова", "residents_count": 2, "monthly_fee": Decimal("11.00"), "notes": None},
        {"number": "19", "floor": 3, "owner_name": "Цецка Бенчева", "residents_count": 0, "monthly_fee": Decimal("7.00"), "notes": None},
        {"number": "20", "floor": 3, "owner_name": "Ивайло Крумов", "residents_count": 3, "monthly_fee": Decimal("13.00"), "notes": None},
        
        # Етаж 4
        {"number": "25", "floor": 4, "owner_name": "Радослав", "residents_count": 2, "monthly_fee": Decimal("11.00"), "notes": None},
        {"number": "26", "floor": 4, "owner_name": "Георги Данчев", "residents_count": 2, "monthly_fee": Decimal("13.50"), "notes": "+ 2 деца + куче"},
        {"number": "27", "floor": 4, "owner_name": "Диляна Чипилова", "residents_count": 1, "monthly_fee": Decimal("9.00"), "notes": None},
        {"number": "28", "floor": 4, "owner_name": "Николай", "residents_count": 1, "monthly_fee": Decimal("9.00"), "notes": None},
        
        # Етаж 5
        {"number": "33", "floor": 5, "owner_name": "Цветелина Григорова", "residents_count": 1, "monthly_fee": Decimal("9.00"), "notes": None},
        {"number": "34", "floor": 5, "owner_name": "Тодорка", "residents_count": 1, "monthly_fee": Decimal("11.00"), "notes": "+ 2 деца"},
        {"number": "35", "floor": 5, "owner_name": "Бисерка", "residents_count": 1, "monthly_fee": Decimal("9.50"), "notes": "+ куче"},
        {"number": "36", "floor": 5, "owner_name": "Мирослава", "residents_count": 1, "monthly_fee": Decimal("9.00"), "notes": None},
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
    print("\n   Passwords:")
    print("   - Gosh: Adidas2002802 (admin)")
    print("   - Cvetelina: Sony5Mouse (cashier)")
    print("   - Ani: Book4Me (viewer)")
    
    # Apartments
    apartments = db.query(Apartment).order_by(Apartment.number).all()
    print(f"\n🏠 Apartments ({len(apartments)}):")
    print(f"   {'Ап.':<5} {'Етаж':<5} {'Собственик':<25} {'Живущи':>6} {'Такса':>8} {'Бележки'}")
    print("   " + "-"*70)
    
    total_fee = Decimal("0.00")
    for apt in apartments:
        notes = apt.notes or ""
        print(f"   {apt.number:<5} {apt.floor:<5} {apt.owner_name:<25} {apt.residents_count:>6} {apt.monthly_fee:>8.2f} {notes}")
        total_fee += apt.monthly_fee
    
    print("   " + "-"*70)
    print(f"   {'ОБЩО:':<37} {'':<6} {total_fee:>8.2f} лв/месец")
    
    print("\n" + "="*60)
    print("Базата данни е готова за работа!")
    print("Задълженията и плащанията са празни - започвате на чисто.")
    print("="*60)


def main():
    """Main entry point."""
    print("\n🚀 DomOS MVP1 Database Initialization")
    print("="*60 + "\n")
    
    # Create tables
    init_db()
    
    # Create data
    db = SessionLocal()
    try:
        create_users(db)
        create_apartments_with_accounts(db)
        
        print_summary(db)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
