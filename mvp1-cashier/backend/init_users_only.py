"""Initialize database users only (no demo data).

Idempotent script that creates only essential users:
- admin (administrator role)
- cecka (cashier role)

Can be run multiple times safely - skips if users already exist.
"""

import sys
sys.path.insert(0, '.')

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_users_only():
    """Create only essential users without any demo data.
    
    This function is idempotent - it will skip creation if users already exist.
    """
    db = SessionLocal()
    
    try:
        # Check if users already exist
        existing_count = db.query(User).count()
        if existing_count > 0:
            print(f"✓ Users already exist ({existing_count} users found), skipping creation...")
            
            # Show existing users
            users = db.query(User).all()
            print("\nExisting users:")
            for user in users:
                print(f"  - {user.username} ({user.role.value})")
            return
        
        print("Creating users...")
        
        # Create admin user
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            display_name="Администратор",
            role=UserRole.ADMIN,
        )
        db.add(admin)
        print("  ✓ Created admin user")
        
        # Create cashier (Цецка)
        cashier = User(
            username="cecka",
            password_hash=get_password_hash("1234"),
            display_name="Цецка",
            role=UserRole.CASHIER,
        )
        db.add(cashier)
        print("  ✓ Created cashier user (Цецка)")
        
        db.commit()
        
        print("\n" + "="*60)
        print("✅ Users created successfully!")
        print("="*60)
        print("\nLogin credentials:")
        print("  Admin:   username=admin, password=admin123")
        print("  Cashier: username=cecka, password=1234")
        print("="*60)
        print("\nℹ️  No apartments, obligations, or payments created.")
        print("   Use init_users.py or setup-db.sh --with-demo-data for full demo data.")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("DomOS - User Initialization (Users Only)\n")
    create_users_only()
