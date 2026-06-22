"""Reset database completely and create fresh demo data.

ВНИМАНИЕ: Това изтрива ВСИЧКИ данни в базата!

Използване:
    python reset_db.py          # Изисква потвърждение
    python reset_db.py --force  # Без потвърждение
"""

import sys
sys.path.insert(0, '.')

from app.db.base import Base
from app.db.session import engine, SessionLocal


def drop_all_tables():
    """Drop all tables in the database."""
    print("\n⚠️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("   ✓ All tables dropped")


def main():
    """Main entry point."""
    # Check for --force flag
    force = "--force" in sys.argv or "-f" in sys.argv
    
    print("\n" + "="*60)
    print("⚠️  DATABASE RESET SCRIPT")
    print("="*60)
    print("\nТова ще ИЗТРИЕ всички данни в базата и ще създаде")
    print("нови демо данни!")
    print("\n" + "="*60)
    
    if not force:
        response = input("\nСигурни ли сте? Въведете 'YES' за да продължите: ")
        if response != "YES":
            print("\n❌ Операцията е отказана.")
            return
    
    # Drop all tables
    drop_all_tables()
    
    # Run init_db to create fresh data
    print("\n🔄 Creating fresh database...\n")
    
    # Import and run init_db
    from init_db import main as init_main
    init_main()
    
    print("\n" + "="*60)
    print("✅ DATABASE RESET COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
