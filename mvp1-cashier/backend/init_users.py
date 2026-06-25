"""Initialize database users for demo/testing.

SECURITY NOTES:
- This script should ONLY be used for initial setup or development.
- In production, set INIT_DEMO_DATA=false to skip demo user creation.
- Demo user passwords are read from environment variables, not hardcoded.
- Generate secure passwords before deploying to production.
"""

import os
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
    """Create demo users if INIT_DEMO_DATA is enabled.
    
    SECURITY: Reads passwords from environment variables.
    Set INIT_DEMO_DATA=false in production to skip this entirely.
    """
    # SECURITY: Check if demo data initialization is enabled
    init_demo_data = os.getenv('INIT_DEMO_DATA', 'true').lower() in ('true', '1', 'yes')
    
    if not init_demo_data:
        print("\n" + "="*50)
        print("INIT_DEMO_DATA is disabled - skipping demo user creation.")
        print("This is the expected behavior for production environments.")
        print("="*50)
        return
    
    # SECURITY: Read passwords from environment variables
    admin_password = os.getenv('DEMO_ADMIN_PASSWORD')
    cashier_password = os.getenv('DEMO_CASHIER_PASSWORD')
    
    # Check if we're in production mode (DEBUG=false)
    is_production = os.getenv('DEBUG', 'true').lower() not in ('true', '1', 'yes')
    
    if is_production:
        print("\n" + "!"*50)
        print("WARNING: Running in production mode with INIT_DEMO_DATA=true")
        print("This is NOT recommended for production environments!")
        print("Set INIT_DEMO_DATA=false in your .env file.")
        print("!"*50 + "\n")
    
    # Validate passwords are provided via environment variables
    if not admin_password:
        if is_production:
            print("ERROR: DEMO_ADMIN_PASSWORD not set. Cannot create demo users in production without explicit passwords.")
            print("Either set INIT_DEMO_DATA=false or provide DEMO_ADMIN_PASSWORD.")
            return
        else:
            # Development fallback - use weak password but warn
            admin_password = 'admin123'
            print("WARNING: Using default admin password for development. Set DEMO_ADMIN_PASSWORD in production.")
    
    if not cashier_password:
        if is_production:
            print("ERROR: DEMO_CASHIER_PASSWORD not set. Cannot create demo users in production without explicit passwords.")
            print("Either set INIT_DEMO_DATA=false or provide DEMO_CASHIER_PASSWORD.")
            return
        else:
            # Development fallback - use weak password but warn
            cashier_password = 'cashier123'
            print("WARNING: Using default cashier password for development. Set DEMO_CASHIER_PASSWORD in production.")
    
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
            password_hash=get_password_hash(admin_password),
            display_name="Администратор",
            role=UserRole.ADMIN,
        )
        db.add(admin)
        
        # Create cashier
        cashier = User(
            username="cashier",
            password_hash=get_password_hash(cashier_password),
            display_name="Касиер",
            role=UserRole.CASHIER,
        )
        db.add(cashier)
        
        db.commit()
        
        print("\n" + "="*50)
        print("Demo users created successfully!")
        print("="*50)
        if not is_production:
            print("\nLogin credentials (DEVELOPMENT ONLY):")
            print("  Admin:   username=admin")
            print("  Cashier: username=cashier")
            print("\nPasswords are set via environment variables:")
            print("  DEMO_ADMIN_PASSWORD, DEMO_CASHIER_PASSWORD")
        else:
            print("\nCredentials created from environment variables.")
            print("Passwords are not displayed for security reasons.")
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
