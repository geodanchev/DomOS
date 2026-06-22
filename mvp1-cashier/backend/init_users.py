"""Initialize database users for demo/testing."""

import sys
sys.path.insert(0, '.')

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def init_db():
    """Create all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def create_users():
    """Create demo users."""
    db = SessionLocal()
    
    try:
        # Check if users already exist
        existing_count = db.query(User).count()
        if existing_count > 0:
            print(f"Users already exist ({existing_count} users found), skipping...")
            return
        
        print("Creating demo users...")
        
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
        
        print("\n" + "="*50)
        print("Demo users created successfully!")
        print("="*50)
        print("\nLogin credentials:")
        print("  Admin:   username=admin, password=admin123")
        print("  Cashier: username=cecka, password=1234")
        print("="*50)
        
    except Exception as e:
        print(f"Error creating users: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    create_users()
