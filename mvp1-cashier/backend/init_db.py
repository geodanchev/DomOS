"""Initialize database with tables and sample data."""

import sys
sys.path.insert(0, '.')

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import Apartment, Payment, MonthlyCharge, User
from app.core.security import get_password_hash
from app.models.monthly_charge import ChargeStatus
from app.models.user import UserRole


def init_db():
    """Create all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def create_sample_data():
    """Create sample data for testing."""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(User).first():
            print("Sample data already exists, skipping...")
            return
        
        print("Creating sample data...")
        
        # Create admin user
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
        print(f"Created users: admin (password: admin123), cecka (password: 1234)")
        
        # Create sample apartments
        apartments_data = [
            {"number": "1", "floor": 1, "owner_name": "Иван Петров", "residents_count": 2, "monthly_fee": 15.00},
            {"number": "2", "floor": 1, "owner_name": "Мария Георгиева", "residents_count": 4, "monthly_fee": 30.00},
            {"number": "3", "floor": 1, "owner_name": "Петър Стоянов", "residents_count": 3, "monthly_fee": 22.50},
            {"number": "4", "floor": 2, "owner_name": "Елена Димитрова", "residents_count": 1, "monthly_fee": 10.00},
            {"number": "5", "floor": 2, "owner_name": "Георги Иванов", "residents_count": 5, "monthly_fee": 35.00},
            {"number": "6", "floor": 2, "owner_name": "Анна Николова", "residents_count": 2, "monthly_fee": 15.00},
            {"number": "7", "floor": 3, "owner_name": "Стефан Тодоров", "residents_count": 3, "monthly_fee": 22.50},
            {"number": "8", "floor": 3, "owner_name": "Катя Василева", "residents_count": 2, "monthly_fee": 15.00},
            {"number": "9", "floor": 3, "owner_name": "Димитър Колев", "residents_count": 4, "monthly_fee": 30.00},
            {"number": "10", "floor": 4, "owner_name": "Росица Атанасова", "residents_count": 2, "monthly_fee": 15.00},
        ]
        
        apartments = []
        for data in apartments_data:
            apt = Apartment(**data)
            db.add(apt)
            apartments.append(apt)
        
        db.commit()
        print(f"Created {len(apartments)} apartments")
        
        # Create monthly charges for current month
        from datetime import date
        current_month = f"{date.today().year}-{date.today().month:02d}"
        
        for apt in apartments:
            db.refresh(apt)
            charge = MonthlyCharge(
                apartment_id=apt.id,
                month=current_month,
                amount_due=float(apt.monthly_fee),
                amount_paid=0,
                status=ChargeStatus.UNPAID,
            )
            db.add(charge)
        
        db.commit()
        print(f"Created monthly charges for {current_month}")
        
        # Create some sample payments
        from datetime import date
        
        # Apartment 1 - fully paid
        payment1 = Payment(
            apartment_id=apartments[0].id,
            amount=15.00,
            month=current_month,
            payment_date=date.today(),
            payment_method="cash",
            collected_by_id=cashier.id,
        )
        db.add(payment1)
        
        # Update charge
        charge1 = db.query(MonthlyCharge).filter(
            MonthlyCharge.apartment_id == apartments[0].id,
            MonthlyCharge.month == current_month
        ).first()
        charge1.amount_paid = 15.00
        charge1.status = ChargeStatus.PAID
        
        # Apartment 3 - partially paid
        payment3 = Payment(
            apartment_id=apartments[2].id,
            amount=10.00,
            month=current_month,
            payment_date=date.today(),
            payment_method="cash",
            collected_by_id=cashier.id,
        )
        db.add(payment3)
        
        charge3 = db.query(MonthlyCharge).filter(
            MonthlyCharge.apartment_id == apartments[2].id,
            MonthlyCharge.month == current_month
        ).first()
        charge3.amount_paid = 10.00
        charge3.status = ChargeStatus.PARTIAL
        
        # Apartment 5 - fully paid
        payment5 = Payment(
            apartment_id=apartments[4].id,
            amount=35.00,
            month=current_month,
            payment_date=date.today(),
            payment_method="cash",
            collected_by_id=cashier.id,
        )
        db.add(payment5)
        
        charge5 = db.query(MonthlyCharge).filter(
            MonthlyCharge.apartment_id == apartments[4].id,
            MonthlyCharge.month == current_month
        ).first()
        charge5.amount_paid = 35.00
        charge5.status = ChargeStatus.PAID
        
        db.commit()
        print("Created sample payments")
        
        print("\n" + "="*50)
        print("Sample data created successfully!")
        print("="*50)
        print("\nLogin credentials:")
        print("  Admin:   username=admin, password=admin123")
        print("  Cashier: username=cecka, password=1234")
        print("\n10 apartments created with monthly charges.")
        print("3 apartments have payments (1-paid, 3-partial, 5-paid)")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    create_sample_data()
