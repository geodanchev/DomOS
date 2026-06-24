"""Pytest configuration and shared fixtures for DomOS Cashier tests.

This file provides all common fixtures used across test modules:
- Database session management (test_db, db)
- Test client with authentication (client)
- User fixtures (cashier_user, admin_user, inactive_user)
- Auth header fixtures (cashier_headers, admin_headers)
- Domain object fixtures (apartments, obligations, payments)
- Helper functions (get_current_month)
"""

import pytest
from datetime import date
from decimal import Decimal
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.apartment import Apartment
from app.models.obligation import Obligation, ObligationType
from app.models.payment import Payment
from app.models.account import ApartmentAccount
from app.core.security import get_password_hash, create_access_token
from app.models.expense import Expense, ExpenseType, ExpenseStatus


# ============== Helper Functions ==============

def get_current_month() -> str:
    """Get current month in YYYY-MM format."""
    today = date.today()
    return f"{today.year}-{today.month:02d}"


def get_previous_month() -> str:
    """Get previous month in YYYY-MM format."""
    today = date.today()
    if today.month == 1:
        return f"{today.year - 1}-12"
    return f"{today.year}-{today.month - 1:02d}"


# ============== Database Fixtures ==============

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a fresh database session for each test.
    
    Alias for 'db' fixture for backward compatibility.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(test_db: Session) -> Session:
    """Alias for test_db fixture."""
    return test_db


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override."""
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

@pytest.fixture(scope="function")
def cashier_user(test_db: Session) -> User:
    """Create a cashier user for testing (Цецка)."""
    user = User(
        username="cecka",
        password_hash=get_password_hash("1234"),
        display_name="Цецка",
        role=UserRole.CASHIER,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(test_db: Session) -> User:
    """Create an admin user for testing."""
    user = User(
        username="test_admin",
        password_hash=get_password_hash("admin123"),
        display_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def inactive_user(test_db: Session) -> User:
    """Create an inactive user for testing."""
    user = User(
        username="inactive",
        password_hash=get_password_hash("pass123"),
        display_name="Inactive User",
        role=UserRole.CASHIER,
        is_active=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


# ============== Auth Header Fixtures ==============

@pytest.fixture(scope="function")
def cashier_headers(cashier_user: User) -> dict:
    """Get auth headers for cashier user."""
    token = create_access_token(data={"sub": cashier_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(admin_user: User) -> dict:
    """Get auth headers for admin user."""
    token = create_access_token(data={"sub": admin_user.id})
    return {"Authorization": f"Bearer {token}"}


# ============== Apartment Fixtures ==============

@pytest.fixture(scope="function")
def sample_apartment_no_account(test_db: Session) -> Apartment:
    """Create a sample apartment WITHOUT an account for tests that need to control account creation."""
    apartment = Apartment(
        number="1",
        floor=1,
        owner_name="Иван Иванов",
        residents_count=2,
        monthly_fee=Decimal("15.00"),
        notes="Test apartment"
    )
    test_db.add(apartment)
    test_db.commit()
    test_db.refresh(apartment)
    return apartment


@pytest.fixture(scope="function")
def sample_apartment(test_db: Session, sample_apartment_no_account: Apartment) -> Apartment:
    """Create a sample apartment WITH an associated account for testing."""
    # Create associated account
    account = ApartmentAccount(
        apartment_id=sample_apartment_no_account.id,
        balance=Decimal("0.00")
    )
    test_db.add(account)
    test_db.commit()
    
    return sample_apartment_no_account


@pytest.fixture(scope="function")
def multiple_apartments(test_db: Session) -> list[Apartment]:
    """Create multiple apartments for testing."""
    apartments = []
    for i in range(1, 6):
        apartment = Apartment(
            number=str(i),
            floor=(i - 1) // 2 + 1,
            owner_name=f"Собственик {i}",
            residents_count=i,
            monthly_fee=Decimal(str(10 + i * 5)),
            notes=f"Apartment {i}"
        )
        test_db.add(apartment)
        test_db.commit()
        test_db.refresh(apartment)
        
        # Create associated account
        account = ApartmentAccount(
            apartment_id=apartment.id,
            balance=Decimal("0.00")
        )
        test_db.add(account)
        test_db.commit()
        
        apartments.append(apartment)
    
    return apartments


# ============== Obligation Fixtures ==============

@pytest.fixture(scope="function")
def sample_obligation(test_db: Session, sample_apartment: Apartment) -> Obligation:
    """Create a sample obligation for testing."""
    obligation = Obligation(
        type=ObligationType.MONTHLY,
        apartment_id=sample_apartment.id,
        month=get_current_month(),
        amount=Decimal("15.00"),
        description="Месечна такса"
    )
    test_db.add(obligation)
    test_db.commit()
    test_db.refresh(obligation)
    return obligation


@pytest.fixture(scope="function")
def multiple_obligations(test_db: Session, multiple_apartments: list[Apartment]) -> list[Obligation]:
    """Create multiple monthly obligations for testing."""
    obligations = []
    current_month = get_current_month()
    
    for apartment in multiple_apartments:
        obligation = Obligation(
            type=ObligationType.MONTHLY,
            apartment_id=apartment.id,
            month=current_month,
            amount=apartment.monthly_fee,
            description="Месечна такса"
        )
        test_db.add(obligation)
        test_db.commit()
        test_db.refresh(obligation)
        obligations.append(obligation)
    
    return obligations


@pytest.fixture(scope="function")
def various_obligations(test_db: Session, sample_apartment: Apartment) -> list[Obligation]:
    """Create obligations of various types for testing.
    
    Includes 2 monthly obligations as expected by test_list_all_filters_by_type.
    """
    obligations = []
    current_month = get_current_month()
    previous_month = get_previous_month()
    
    # Monthly obligation 1 (current month)
    monthly1 = Obligation(
        type=ObligationType.MONTHLY,
        apartment_id=sample_apartment.id,
        month=current_month,
        amount=Decimal("15.00"),
        description="Месечна такса - текущ месец"
    )
    test_db.add(monthly1)
    obligations.append(monthly1)
    
    # Monthly obligation 2 (specific month for filter test)
    monthly2 = Obligation(
        type=ObligationType.MONTHLY,
        apartment_id=sample_apartment.id,
        month="2026-01",
        amount=Decimal("15.00"),
        description="Месечна такса - януари 2026"
    )
    test_db.add(monthly2)
    obligations.append(monthly2)
    
    # Penalty obligation
    penalty = Obligation(
        type=ObligationType.PENALTY,
        apartment_id=sample_apartment.id,
        month=None,
        amount=Decimal("50.00"),
        description="Глоба за нарушение"
    )
    test_db.add(penalty)
    obligations.append(penalty)
    
    # Repair obligation
    repair = Obligation(
        type=ObligationType.REPAIR,
        apartment_id=sample_apartment.id,
        month=None,
        amount=Decimal("100.00"),
        description="Ремонт на покрив"
    )
    test_db.add(repair)
    obligations.append(repair)
    
    # Initial obligation
    initial = Obligation(
        type=ObligationType.INITIAL,
        apartment_id=sample_apartment.id,
        month=None,
        amount=Decimal("200.00"),
        description="Начално задължение"
    )
    test_db.add(initial)
    obligations.append(initial)
    
    test_db.commit()
    for ob in obligations:
        test_db.refresh(ob)
    
    return obligations


# ============== Payment Fixtures ==============

@pytest.fixture(scope="function")
def sample_payment(test_db: Session, sample_apartment: Apartment, cashier_user: User) -> Payment:
    """Create a sample payment for testing."""
    from app.models.payment import PaymentStatus
    payment = Payment(
        apartment_id=sample_apartment.id,
        amount=Decimal("15.00"),
        month=get_current_month(),
        notes="Test payment",
        collected_by_id=cashier_user.id,
        status=PaymentStatus.ACTIVE
    )
    test_db.add(payment)
    test_db.commit()
    test_db.refresh(payment)
    return payment


# ============== Expense Fixtures ==============

@pytest.fixture(scope="function")
def sample_expense(test_db: Session, cashier_user: User) -> Expense:
    """Create a sample expense for testing.
    
    Test expectations: description='Ремонт на покрив', amount=500.00, vendor='Строител ООД'
    """
    expense = Expense(
        description="Ремонт на покрив",
        amount=Decimal("500.00"),
        expense_type=ExpenseType.REPAIR,
        status=ExpenseStatus.PENDING,
        vendor="Строител ООД",
        invoice_number="INV-001",
        notes="Test expense notes",
        created_by=cashier_user.id
    )
    test_db.add(expense)
    test_db.commit()
    test_db.refresh(expense)
    return expense


# ============== Charge/Collection Fixtures for Reports ==============

@pytest.fixture(scope="function")
def paid_charge(test_db: Session, sample_apartment: Apartment, cashier_user: User) -> Obligation:
    """Create a fully paid charge (obligation + matching payment) for collection rate tests."""
    from app.models.payment import PaymentStatus
    current_month = get_current_month()
    
    # Create obligation
    obligation = Obligation(
        type=ObligationType.MONTHLY,
        apartment_id=sample_apartment.id,
        month=current_month,
        amount=Decimal("15.00"),
        description="Месечна такса - платена"
    )
    test_db.add(obligation)
    test_db.commit()
    test_db.refresh(obligation)
    
    # Create matching payment to mark as fully paid
    payment = Payment(
        apartment_id=sample_apartment.id,
        amount=Decimal("15.00"),
        month=current_month,
        notes="Full payment for collection test",
        collected_by_id=cashier_user.id,
        status=PaymentStatus.ACTIVE
    )
    test_db.add(payment)
    test_db.commit()
    
    return obligation


@pytest.fixture(scope="function")
def sample_charge(test_db: Session, sample_apartment: Apartment) -> Obligation:
    """Create an unpaid charge (obligation without payment) for collection rate and outstanding debts tests.
    
    Also updates the apartment account to have negative balance (debt).
    """
    current_month = get_current_month()
    
    # Create obligation without payment - represents unpaid charge
    obligation = Obligation(
        type=ObligationType.MONTHLY,
        apartment_id=sample_apartment.id,
        month=current_month,
        amount=Decimal("15.00"),
        description="Месечна такса - неплатена"
    )
    test_db.add(obligation)
    test_db.commit()
    test_db.refresh(obligation)
    
    # Update account balance to show debt (negative = owes money)
    account = test_db.query(ApartmentAccount).filter(
        ApartmentAccount.apartment_id == sample_apartment.id
    ).first()
    if account:
        account.balance = Decimal("-15.00")
        test_db.commit()
    
    return obligation


@pytest.fixture(scope="function")
def partial_charge(test_db: Session, sample_apartment: Apartment, cashier_user: User) -> Obligation:
    """Create a partially paid charge (50% paid) for collection rate tests."""
    from app.models.payment import PaymentStatus
    current_month = get_current_month()
    
    # Create obligation for 30.00
    obligation = Obligation(
        type=ObligationType.MONTHLY,
        apartment_id=sample_apartment.id,
        month=current_month,
        amount=Decimal("30.00"),
        description="Месечна такса - частично платена"
    )
    test_db.add(obligation)
    test_db.commit()
    test_db.refresh(obligation)
    
    # Create partial payment (50% = 15.00)
    payment = Payment(
        apartment_id=sample_apartment.id,
        amount=Decimal("15.00"),
        month=current_month,
        notes="Partial payment for collection test",
        collected_by_id=cashier_user.id,
        status=PaymentStatus.ACTIVE
    )
    test_db.add(payment)
    test_db.commit()
    
    return obligation


@pytest.fixture(scope="function")
def multiple_charges(test_db: Session, multiple_apartments: list[Apartment]) -> list[Obligation]:
    """Create multiple unpaid charges (obligations) with different amounts for sorting tests."""
    charges = []
    current_month = get_current_month()
    
    # Create different amounts to test sorting
    amounts = [Decimal("100.00"), Decimal("50.00"), Decimal("200.00"), Decimal("25.00"), Decimal("150.00")]
    
    for i, (apartment, amount) in enumerate(zip(multiple_apartments, amounts)):
        charge = Obligation(
            type=ObligationType.MONTHLY,
            apartment_id=apartment.id,
            month=current_month,
            amount=amount,
            description=f"Месечна такса - тест {i+1}"
        )
        test_db.add(charge)
        charges.append(charge)
    
    test_db.commit()
    for c in charges:
        test_db.refresh(c)
    
    return charges


@pytest.fixture(scope="function")
def apartments_with_debts(test_db: Session, cashier_user: User) -> list[Apartment]:
    """Create apartments with outstanding debts for reports testing."""
    apartments = []
    current_month = get_current_month()
    
    # Apartment with large debt
    apt1 = Apartment(
        number="D1",
        floor=1,
        owner_name="Длъжник Голям",
        residents_count=3,
        monthly_fee=Decimal("25.00"),
        notes="Large debt test"
    )
    test_db.add(apt1)
    test_db.commit()
    test_db.refresh(apt1)
    
    # Create account and obligation for apt1
    account1 = ApartmentAccount(
        apartment_id=apt1.id,
        balance=Decimal("-100.00")  # Owes 100
    )
    test_db.add(account1)
    
    obligation1 = Obligation(
        type=ObligationType.MONTHLY,
        apartment_id=apt1.id,
        month=current_month,
        amount=Decimal("100.00"),
        description="Натрупан дълг"
    )
    test_db.add(obligation1)
    apartments.append(apt1)
    
    # Apartment with medium debt
    apt2 = Apartment(
        number="D2",
        floor=2,
        owner_name="Длъжник Среден",
        residents_count=2,
        monthly_fee=Decimal("20.00"),
        notes="Medium debt test"
    )
    test_db.add(apt2)
    test_db.commit()
    test_db.refresh(apt2)
    
    account2 = ApartmentAccount(
        apartment_id=apt2.id,
        balance=Decimal("-50.00")  # Owes 50
    )
    test_db.add(account2)
    
    obligation2 = Obligation(
        type=ObligationType.MONTHLY,
        apartment_id=apt2.id,
        month=current_month,
        amount=Decimal("50.00"),
        description="Среден дълг"
    )
    test_db.add(obligation2)
    apartments.append(apt2)
    
    # Apartment with small debt
    apt3 = Apartment(
        number="D3",
        floor=3,
        owner_name="Длъжник Малък",
        residents_count=1,
        monthly_fee=Decimal("15.00"),
        notes="Small debt test"
    )
    test_db.add(apt3)
    test_db.commit()
    test_db.refresh(apt3)
    
    account3 = ApartmentAccount(
        apartment_id=apt3.id,
        balance=Decimal("-25.00")  # Owes 25
    )
    test_db.add(account3)
    
    obligation3 = Obligation(
        type=ObligationType.MONTHLY,
        apartment_id=apt3.id,
        month=current_month,
        amount=Decimal("25.00"),
        description="Малък дълг"
    )
    test_db.add(obligation3)
    apartments.append(apt3)
    
    test_db.commit()
    return apartments


@pytest.fixture(scope="function")
def multiple_expenses(test_db: Session, cashier_user: User) -> list[Expense]:
    """Create multiple expenses of various types for testing.
    
    Test expectations:
    - total_amount = 2750.0 (excluding cancelled)
    - total_paid = 1650.0 (1500 + 150)
    - total_pending = 1100.0 (800 + 300)
    """
    expenses = []
    
    # Repair expense - paid (1500)
    repair = Expense(
        description="Ремонт на покрив",
        amount=Decimal("1500.00"),
        expense_type=ExpenseType.REPAIR,
        status=ExpenseStatus.PAID,
        vendor="Строителна фирма",
        invoice_number="INV-101",
        created_by=cashier_user.id
    )
    test_db.add(repair)
    expenses.append(repair)
    
    # Maintenance expense - paid (150)
    maintenance = Expense(
        description="Поддръжка асансьор",
        amount=Decimal("150.00"),
        expense_type=ExpenseType.MAINTENANCE,
        status=ExpenseStatus.PAID,
        vendor="Асансьорна компания",
        invoice_number="INV-102",
        created_by=cashier_user.id
    )
    test_db.add(maintenance)
    expenses.append(maintenance)
    
    # Cleaning expense - pending (800)
    cleaning = Expense(
        description="Месечно почистване",
        amount=Decimal("800.00"),
        expense_type=ExpenseType.CLEANING,
        status=ExpenseStatus.PENDING,
        vendor="Чистачка",
        created_by=cashier_user.id
    )
    test_db.add(cleaning)
    expenses.append(cleaning)
    
    # Utility expense - pending (300)
    utility = Expense(
        description="Ток общи части",
        amount=Decimal("300.00"),
        expense_type=ExpenseType.UTILITY,
        status=ExpenseStatus.PENDING,
        vendor="ЕВН",
        invoice_number="INV-103",
        created_by=cashier_user.id
    )
    test_db.add(utility)
    expenses.append(utility)
    
    # Cancelled expense (excluded from totals)
    cancelled = Expense(
        description="Отменен разход",
        amount=Decimal("500.00"),
        expense_type=ExpenseType.OTHER,
        status=ExpenseStatus.CANCELLED,
        created_by=cashier_user.id
    )
    test_db.add(cancelled)
    expenses.append(cancelled)
    
    test_db.commit()
    for exp in expenses:
        test_db.refresh(exp)
    
    return expenses


@pytest.fixture(scope="function")
def paid_expense(test_db: Session, cashier_user: User) -> Expense:
    """Create a paid expense for testing.
    
    Test expects amount=200.00 for fund_balance test.
    """
    from datetime import datetime
    expense = Expense(
        description="Платен разход",
        amount=Decimal("200.00"),
        expense_type=ExpenseType.MAINTENANCE,
        status=ExpenseStatus.PAID,
        paid_date=datetime.utcnow(),
        vendor="Test Vendor",
        invoice_number="INV-PAID-001",
        created_by=cashier_user.id
    )
    test_db.add(expense)
    test_db.commit()
    test_db.refresh(expense)
    return expense


@pytest.fixture(scope="function")
def cancelled_expense(test_db: Session, cashier_user: User) -> Expense:
    """Create a cancelled expense for testing."""
    expense = Expense(
        description="Анулиран разход",
        amount=Decimal("175.00"),
        expense_type=ExpenseType.REPAIR,
        status=ExpenseStatus.CANCELLED,
        created_by=cashier_user.id
    )
    test_db.add(expense)
    test_db.commit()
    test_db.refresh(expense)
    return expense
