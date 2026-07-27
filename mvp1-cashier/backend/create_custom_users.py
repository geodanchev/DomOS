"""Create custom users in Cloud SQL database.

This script creates specific users as requested:
- Gosh (admin)
- Cecka (cashier)  
- Viewer (viewer)

Run via Cloud Build or with direct database access.
"""

import os
import sys
sys.path.insert(0, '.')

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_custom_users():
    """Create the requested users."""
    
    # Users to create with their passwords
    users_to_create = [
        {
            'username': 'gosh',
            'display_name': 'Gosh',
            'role': UserRole.ADMIN,
            'password': os.getenv('GOSH_PASSWORD', 'gosh123'),
        },
        {
            'username': 'cecka',
            'display_name': 'Cecka',
            'role': UserRole.CASHIER,
            'password': os.getenv('CECKA_PASSWORD', 'cecka123'),
        },
        {
            'username': 'viewer',
            'display_name': 'Viewer',
            'role': UserRole.VIEWER,
            'password': os.getenv('VIEWER_PASSWORD', 'viewer123'),
        },
    ]
    
    # Ensure tables exist
    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        created_count = 0
        skipped_count = 0
        
        for user_data in users_to_create:
            # Check if user already exists
            existing = db.query(User).filter(User.username == user_data['username']).first()
            
            if existing:
                print(f"User '{user_data['username']}' already exists (id={existing.id}), skipping...")
                skipped_count += 1
                continue
            
            # Create new user
            new_user = User(
                username=user_data['username'],
                password_hash=get_password_hash(user_data['password']),
                display_name=user_data['display_name'],
                role=user_data['role'],
                is_active=True,
            )
            db.add(new_user)
            db.flush()  # Get the ID
            
            print(f"Created user '{user_data['display_name']}' (id={new_user.id}, username={user_data['username']}, role={user_data['role'].value})")
            created_count += 1
        
        db.commit()
        
        # List all users
        print("\n" + "="*50)
        print("All users in database:")
        print("="*50)
        all_users = db.query(User).order_by(User.id).all()
        for user in all_users:
            print(f"  ID: {user.id}, Username: {user.username}, Display: {user.display_name}, Role: {user.role.value}, Active: {user.is_active}")
        
        print(f"\nSummary: {created_count} created, {skipped_count} skipped")
        print("="*50)
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_custom_users()
