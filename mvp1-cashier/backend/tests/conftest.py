"""Pytest fixtures for DomOS Cashier MVP tests."""

import pytest
from datetime import date
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.apartment import Apartment
from app.models.payment import Payment
from app.models.monthly_charge import MonthlyCharge, ChargeStatus
from app.core.security import get_password_hash, create_access_token


# Test database URL - in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """Create test client with overridden database dependency."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============== User Fixtures ==============

@pytest.fixture
def admin_user(test_db: Session) -> User:
    """Create admin user for tests."""
    user = User(
        username="test_admin",
        password_hash=get_password_hash("admin123"),
        display_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def cashier_user(test_db: Session) -> User:
    """Create cashier user (Цецка) for tests."""
    user = User(
        username="cecka",
        password_hash=get_password_hash("1234"),
        display_name="Цецка",
        role=UserRole.CASHIER,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def inactive_user(test_db: Session) -> User:
    """Create inactive user for tests."""
    user = User(
        username="inactive",
        password_hash=get_password_hash("pass123"),
        display_name="Inactive User",
        role=UserRole.VIEWER,
        is_active=False,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create JWT token for admin user."""
    return create_access_token(data={"sub": admin_user.id})


@pytest.fixture
def cashier_token(cashier_user: User) -> str:
    """Create JWT token for cashier user."""
    return create_access_token(data={"sub": cashier_user.id})


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Auth headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def cashier_headers(cashier_token: str) -> dict:
    """Auth headers for cashier user."""
    return {"Authorization": f"Bearer {cashier_token}"}


# ============== Apartment Fixtures ==============

@pytest.fixture
def sample_apartment(test_db: Session) -> Apartment:
    """Create sample apartment for tests."""
    apartment = Apartment(
        number="1",
        floor=1,
        owner_name="Иван Петров",
        residents_count=2,
        monthly_fee=15.00,
        notes="Тестов апартамент",
    )
    test_db.add(apartment)
    test_db.commit()
    test_db.refresh(apartment)
    return apartment


@pytest.fixture
def multiple_apartments(test_db: Session) -> list[Apartment]:
    """Create multiple apartments for tests."""
    apartments_data = [
        {"number": "1", "floor": 1, "owner_name": "Иван Петров", "residents_count": 2, "monthly_fee": 15.00},
        {"number": "2", "floor": 1, "owner_name": "Мария Георгиева", "residents_count": 4, "monthly_fee": 30.00},
        {"number": "3", "floor": 2, "owner_name": "Петър Стоянов", "residents_count": 3, "monthly_fee": 22.50},
        {"number": "4", "floor": 2, "owner_name": "Елена Димитрова", "residents_count": 1, "monthly_fee": 10.00},
        {"number": "5", "floor": 3, "owner_name": "Георги Иванов", "residents_count": 5, "monthly_fee": 35.00},
    ]
    apartments = []
    for data in apartments_data:
        apt = Apartment(**data)
        test_db.add(apt)
        apartments.append(apt)
    test_db.commit()
    for apt in apartments:
        test_db.refresh(apt)
    return apartments


# ============== Monthly Charge Fixtures ==============

def get_current_month() -> str:
    """Get current month in YYYY-MM format."""
    today = date.today()
    return f"{today.year}-{today.month:02d}"


@pytest.fixture
def sample_charge(test_db: Session, sample_apartment: Apartment) -> MonthlyCharge:
    """Create sample monthly charge for tests."""
    charge = MonthlyCharge(
        apartment_id=sample_apartment.id,
        month=get_current_month(),
        amount_due=sample_apartment.monthly_fee,
        amount_paid=0,
        status=ChargeStatus.UNPAID,
    )
    test_db.add(charge)
    test_db.commit()
    test_db.refresh(charge)
    return charge


@pytest.fixture
def paid_charge(test_db: Session, sample_apartment: Apartment) -> MonthlyCharge:
    """Create fully paid monthly charge."""
    charge = MonthlyCharge(
        apartment_id=sample_apartment.id,
        month="2027-01",
        amount_due=sample_apartment.monthly_fee,
        amount_paid=sample_apartment.monthly_fee,
        status=ChargeStatus.PAID,
    )
    test_db.add(charge)
    test_db.commit()
    test_db.refresh(charge)
    return charge


@pytest.fixture
def partial_charge(test_db: Session, sample_apartment: Apartment) -> MonthlyCharge:
    """Create partially paid monthly charge."""
    charge = MonthlyCharge(
        apartment_id=sample_apartment.id,
        month="2027-02",
        amount_due=sample_apartment.monthly_fee,
        amount_paid=sample_apartment.monthly_fee / 2,
        status=ChargeStatus.PARTIAL,
    )
    test_db.add(charge)
    test_db.commit()
    test_db.refresh(charge)
    return charge


@pytest.fixture
def multiple_charges(test_db: Session, multiple_apartments: list[Apartment]) -> list[MonthlyCharge]:
    """Create monthly charges for all apartments."""
    current_month = get_current_month()
    charges = []
    for apt in multiple_apartments:
        charge = MonthlyCharge(
            apartment_id=apt.id,
            month=current_month,
            amount_due=apt.monthly_fee,
            amount_paid=0,
            status=ChargeStatus.UNPAID,
        )
        test_db.add(charge)
        charges.append(charge)
    test_db.commit()
    for charge in charges:
        test_db.refresh(charge)
    return charges


# ============== Payment Fixtures ==============

@pytest.fixture
def sample_payment(test_db: Session, sample_apartment: Apartment, cashier_user: User) -> Payment:
    """Create sample payment for tests."""
    payment = Payment(
        apartment_id=sample_apartment.id,
        amount=15.00,
        month=get_current_month(),
        payment_date=date.today(),
        payment_method="cash",
        collected_by_id=cashier_user.id,
        notes="Тестово плащане",
    )
    test_db.add(payment)
    test_db.commit()
    test_db.refresh(payment)
    return payment


# ============== Helper Functions ==============

def create_apartment(db: Session, number: str, owner: str, fee: float) -> Apartment:
    """Helper to create apartment in tests."""
    apt = Apartment(
        number=number,
        floor=1,
        owner_name=owner,
        residents_count=1,
        monthly_fee=fee,
    )
    db.add(apt)
    db.commit()
    db.refresh(apt)
    return apt


def create_charge(db: Session, apartment_id: int, month: str, amount: float) -> MonthlyCharge:
    """Helper to create monthly charge in tests."""
    charge = MonthlyCharge(
        apartment_id=apartment_id,
        month=month,
        amount_due=amount,
        amount_paid=0,
        status=ChargeStatus.UNPAID,
    )
    db.add(charge)
    db.commit()
    db.refresh(charge)
    return charge
