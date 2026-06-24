"""Comprehensive tests for Obligation API and Service.

Tests cover:
- CRUD operations via API
- ObligationService business logic
- Account integration (debit/credit on create/update/delete)
- Monthly obligation generation
- Statistics and summaries
- Filtering and pagination
- Validation and edge cases
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.obligation import Obligation, ObligationType
from app.models.account import ApartmentAccount, AccountTransaction, TransactionType, TransactionReference
from app.models.apartment import Apartment
from app.services.obligation_service import ObligationService
from app.schemas.obligation import ObligationCreate, ObligationUpdate
from tests.conftest import get_current_month


# ============== ObligationService Unit Tests ==============

class TestObligationServiceCreate:
    """Tests for ObligationService.create() method."""
    
    def test_create_obligation_creates_record(self, test_db: Session, sample_apartment: Apartment):
        """Test that create() creates an obligation record."""
        service = ObligationService(test_db)
        data = ObligationCreate(
            type=ObligationType.MONTHLY,
            apartment_id=sample_apartment.id,
            month="2026-01",
            amount=15.0,
            description="Месечна такса",
        )
        
        obligation = service.create(data)
        
        assert obligation.id is not None
        assert obligation.type == ObligationType.MONTHLY
        assert obligation.apartment_id == sample_apartment.id
        assert obligation.month == "2026-01"
        assert float(obligation.amount) == 15.0
        assert obligation.description == "Месечна такса"
    
    def test_create_obligation_debits_account(self, test_db: Session, sample_apartment: Apartment):
        """Test that creating an obligation debits the apartment account."""
        service = ObligationService(test_db)
        
        # Get initial balance (may already exist from other operations)
        initial_account = test_db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == sample_apartment.id
        ).first()
        initial_balance = float(initial_account.balance) if initial_account else 0.0
        
        data = ObligationCreate(
            type=ObligationType.MONTHLY,
            apartment_id=sample_apartment.id,
            month="2026-01",
            amount=15.0,
        )
        
        obligation = service.create(data)
        
        # Check account was created/updated and debited by 15.0
        account = test_db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == sample_apartment.id
        ).first()
        assert account is not None
        assert float(account.balance) == initial_balance - 15.0
        
        # Check transaction was recorded
        transaction = test_db.query(AccountTransaction).filter(
            AccountTransaction.reference_id == obligation.id,
            AccountTransaction.reference_type == TransactionReference.OBLIGATION
        ).first()
        assert transaction is not None
        assert transaction.type == TransactionType.DEBIT
        assert float(transaction.amount) == 15.0
    
    def test_create_obligation_uses_existing_account(self, test_db: Session, sample_apartment_no_account: Apartment):
        """Test that create uses existing account if present."""
        # Create account with positive balance (using apartment without pre-existing account)
        existing_account = ApartmentAccount(
            apartment_id=sample_apartment_no_account.id,
            balance=Decimal("50.00"),
        )
        test_db.add(existing_account)
        test_db.commit()
        
        service = ObligationService(test_db)
        data = ObligationCreate(
            type=ObligationType.MONTHLY,
            apartment_id=sample_apartment_no_account.id,
            month="2026-01",
            amount=15.0,
        )
        
        service.create(data)
        
        test_db.refresh(existing_account)
        assert float(existing_account.balance) == 35.0  # 50 - 15
    
    def test_create_penalty_obligation(self, test_db: Session, sample_apartment: Apartment):
        """Test creating a penalty obligation."""
        service = ObligationService(test_db)
        data = ObligationCreate(
            type=ObligationType.PENALTY,
            apartment_id=sample_apartment.id,
            month=None,
            amount=50.0,
            description="Глоба за нарушение",
        )
        
        obligation = service.create(data)
        
        assert obligation.type == ObligationType.PENALTY
        assert obligation.month is None
        assert float(obligation.amount) == 50.0
    
    def test_create_repair_obligation(self, test_db: Session, sample_apartment: Apartment):
        """Test creating a repair obligation."""
        service = ObligationService(test_db)
        data = ObligationCreate(
            type=ObligationType.REPAIR,
            apartment_id=sample_apartment.id,
            month=None,
            amount=200.0,
            description="Ремонт на покрив",
        )
        
        obligation = service.create(data)
        
        assert obligation.type == ObligationType.REPAIR
        assert float(obligation.amount) == 200.0


class TestObligationServiceGet:
    """Tests for ObligationService get methods."""
    
    def test_get_obligation_returns_record(self, test_db: Session, sample_obligation: Obligation):
        """Test that get() returns the correct obligation."""
        service = ObligationService(test_db)
        
        result = service.get(sample_obligation.id)
        
        assert result is not None
        assert result.id == sample_obligation.id
        assert result.type == sample_obligation.type
    
    def test_get_obligation_returns_none_for_invalid_id(self, test_db: Session):
        """Test that get() returns None for non-existent ID."""
        service = ObligationService(test_db)
        
        result = service.get(99999)
        
        assert result is None
    
    def test_get_by_apartment_and_month(self, test_db: Session, sample_obligation: Obligation):
        """Test get_by_apartment_and_month() returns correct record."""
        service = ObligationService(test_db)
        
        result = service.get_by_apartment_and_month(
            apartment_id=sample_obligation.apartment_id,
            month=sample_obligation.month,
            obligation_type=ObligationType.MONTHLY,
        )
        
        assert result is not None
        assert result.id == sample_obligation.id
    
    def test_get_by_apartment_and_month_returns_none(self, test_db: Session, sample_apartment: Apartment):
        """Test get_by_apartment_and_month() returns None when not found."""
        service = ObligationService(test_db)
        
        result = service.get_by_apartment_and_month(
            apartment_id=sample_apartment.id,
            month="2099-01",
            obligation_type=ObligationType.MONTHLY,
        )
        
        assert result is None


class TestObligationServiceList:
    """Tests for ObligationService list methods."""
    
    def test_list_all_returns_obligations(self, test_db: Session, multiple_obligations: list[Obligation]):
        """Test that list_all() returns all obligations."""
        service = ObligationService(test_db)
        
        result = service.list_all()
        
        assert len(result) == len(multiple_obligations)
    
    def test_list_all_filters_by_type(self, test_db: Session, various_obligations: list[Obligation]):
        """Test list_all() filtering by obligation type."""
        service = ObligationService(test_db)
        
        monthly = service.list_all(obligation_type=ObligationType.MONTHLY)
        penalties = service.list_all(obligation_type=ObligationType.PENALTY)
        
        assert len(monthly) == 2  # Two monthly obligations in fixtures
        assert len(penalties) == 1  # One penalty in fixtures
    
    def test_list_all_filters_by_apartment(self, test_db: Session, multiple_obligations: list[Obligation]):
        """Test list_all() filtering by apartment."""
        service = ObligationService(test_db)
        apt_id = multiple_obligations[0].apartment_id
        
        result = service.list_all(apartment_id=apt_id)
        
        assert len(result) == 1
        assert result[0].apartment_id == apt_id
    
    def test_list_all_filters_by_month(self, test_db: Session, various_obligations: list[Obligation]):
        """Test list_all() filtering by month."""
        service = ObligationService(test_db)
        
        result = service.list_all(month="2026-01")
        
        assert len(result) == 1
        assert result[0].month == "2026-01"
    
    def test_list_all_pagination(self, test_db: Session, various_obligations: list[Obligation]):
        """Test list_all() pagination with skip and limit."""
        service = ObligationService(test_db)
        
        page1 = service.list_all(skip=0, limit=3)
        page2 = service.list_all(skip=3, limit=3)
        
        assert len(page1) == 3
        assert len(page2) <= 3
    
    def test_list_by_apartment(self, test_db: Session, sample_apartment: Apartment, various_obligations: list[Obligation]):
        """Test list_by_apartment() returns correct records."""
        service = ObligationService(test_db)
        
        result = service.list_by_apartment(sample_apartment.id)
        
        assert len(result) == len(various_obligations)
        for obl in result:
            assert obl.apartment_id == sample_apartment.id


class TestObligationServiceUpdate:
    """Tests for ObligationService.update() method."""
    
    def test_update_obligation_changes_description(self, test_db: Session, sample_obligation: Obligation):
        """Test that update() changes the obligation description."""
        service = ObligationService(test_db)
        data = ObligationUpdate(description="Обновено описание")
        
        result = service.update(sample_obligation.id, data)
        
        assert result is not None
        assert result.description == "Обновено описание"
    
    def test_update_obligation_returns_none_for_invalid_id(self, test_db: Session):
        """Test that update() returns None for non-existent ID."""
        service = ObligationService(test_db)
        data = ObligationUpdate(description="Test")
        
        result = service.update(99999, data)
        
        assert result is None
    
    def test_update_obligation_amount_increase_debits_account(self, test_db: Session, sample_apartment: Apartment):
        """Test that increasing amount debits the account."""
        service = ObligationService(test_db)
        
        # Get initial balance
        initial_account = test_db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == sample_apartment.id
        ).first()
        initial_balance = float(initial_account.balance) if initial_account else 0.0
        
        # Create obligation
        create_data = ObligationCreate(
            type=ObligationType.MONTHLY,
            apartment_id=sample_apartment.id,
            month="2026-07",  # Unique month to avoid conflicts
            amount=15.0,
        )
        obligation = service.create(create_data)
        
        # Balance after create should be initial - 15
        account = test_db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == sample_apartment.id
        ).first()
        balance_after_create = float(account.balance)
        assert balance_after_create == initial_balance - 15.0
        
        # Update amount to higher value
        update_data = ObligationUpdate(amount=25.0)
        service.update(obligation.id, update_data)
        
        # Check account balance decreased by additional 10
        test_db.refresh(account)
        assert float(account.balance) == balance_after_create - 10.0  # Debited 10 more
    
    def test_update_obligation_amount_decrease_credits_account(self, test_db: Session, sample_apartment: Apartment):
        """Test that decreasing amount credits the account."""
        service = ObligationService(test_db)
        
        # Get initial balance
        initial_account = test_db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == sample_apartment.id
        ).first()
        initial_balance = float(initial_account.balance) if initial_account else 0.0
        
        # Create obligation
        create_data = ObligationCreate(
            type=ObligationType.MONTHLY,
            apartment_id=sample_apartment.id,
            month="2026-08",  # Unique month to avoid conflicts
            amount=25.0,
        )
        obligation = service.create(create_data)
        
        # Balance after create should be initial - 25
        account = test_db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == sample_apartment.id
        ).first()
        balance_after_create = float(account.balance)
        assert balance_after_create == initial_balance - 25.0
        
        # Update amount to lower value
        update_data = ObligationUpdate(amount=15.0)
        service.update(obligation.id, update_data)
        
        # Check account balance increased by 10 (credited back)
        test_db.refresh(account)
        assert float(account.balance) == balance_after_create + 10.0  # Credited 10 back


class TestObligationServiceDelete:
    """Tests for ObligationService.delete() method."""
    
    def test_delete_obligation_removes_record(self, test_db: Session, sample_obligation: Obligation):
        """Test that delete() removes the obligation."""
        service = ObligationService(test_db)
        obl_id = sample_obligation.id
        
        result = service.delete(obl_id)
        
        assert result is True
        assert service.get(obl_id) is None
    
    def test_delete_obligation_credits_account(self, test_db: Session, sample_apartment: Apartment):
        """Test that deleting an obligation credits the account."""
        service = ObligationService(test_db)
        
        # Get initial balance
        initial_account = test_db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == sample_apartment.id
        ).first()
        initial_balance = float(initial_account.balance) if initial_account else 0.0
        
        # Create obligation
        create_data = ObligationCreate(
            type=ObligationType.MONTHLY,
            apartment_id=sample_apartment.id,
            month="2026-09",  # Unique month to avoid conflicts
            amount=15.0,
        )
        obligation = service.create(create_data)
        
        # Balance after create should be initial - 15
        account = test_db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == sample_apartment.id
        ).first()
        balance_after_create = float(account.balance)
        assert balance_after_create == initial_balance - 15.0
        
        # Delete obligation
        service.delete(obligation.id)
        
        # Check account balance is back to initial (credited back)
        test_db.refresh(account)
        assert float(account.balance) == initial_balance
    
    def test_delete_returns_false_for_invalid_id(self, test_db: Session):
        """Test that delete() returns False for non-existent ID."""
        service = ObligationService(test_db)
        
        result = service.delete(99999)
        
        assert result is False


class TestMonthlyObligationGeneration:
    """Tests for monthly obligation generation."""
    
    def test_generate_monthly_creates_for_all_apartments(self, test_db: Session, multiple_apartments: list[Apartment]):
        """Test that generate_monthly_obligations creates for all apartments."""
        service = ObligationService(test_db)
        month = "2026-03"
        
        created = service.generate_monthly_obligations(month)
        
        assert len(created) == len(multiple_apartments)
        for obl in created:
            assert obl.type == ObligationType.MONTHLY
            assert obl.month == month
    
    def test_generate_monthly_uses_apartment_fee(self, test_db: Session, multiple_apartments: list[Apartment]):
        """Test that generation uses each apartment's monthly fee."""
        service = ObligationService(test_db)
        month = "2026-03"
        
        created = service.generate_monthly_obligations(month)
        
        for obl in created:
            apt = test_db.get(Apartment, obl.apartment_id)
            assert float(obl.amount) == float(apt.monthly_fee)
    
    def test_generate_monthly_skips_existing(self, test_db: Session, sample_apartment: Apartment):
        """Test that generation skips apartments with existing obligations."""
        service = ObligationService(test_db)
        month = "2026-03"
        
        # First generation
        first_result = service.generate_monthly_obligations(month)
        assert len(first_result) == 1
        
        # Second generation should skip
        second_result = service.generate_monthly_obligations(month)
        assert len(second_result) == 0
    
    def test_generate_monthly_debits_accounts(self, test_db: Session, multiple_apartments: list[Apartment]):
        """Test that generation debits all apartment accounts."""
        service = ObligationService(test_db)
        month = "2026-10"  # Unique month to avoid conflicts
        
        # Get initial balances
        initial_balances = {}
        for apt in multiple_apartments:
            account = test_db.query(ApartmentAccount).filter(
                ApartmentAccount.apartment_id == apt.id
            ).first()
            initial_balances[apt.id] = float(account.balance) if account else 0.0
        
        service.generate_monthly_obligations(month)
        
        # Verify each apartment's account was debited by its monthly fee
        for apt in multiple_apartments:
            account = test_db.query(ApartmentAccount).filter(
                ApartmentAccount.apartment_id == apt.id
            ).first()
            assert account is not None
            expected_balance = initial_balances[apt.id] - float(apt.monthly_fee)
            assert float(account.balance) == expected_balance


class TestObligationStatistics:
    """Tests for obligation statistics methods."""
    
    def test_get_apartment_balance_returns_zero_for_new(self, test_db: Session, sample_apartment: Apartment):
        """Test balance is zero for apartment without obligations."""
        service = ObligationService(test_db)
        
        balance = service.get_apartment_balance(sample_apartment.id)
        
        assert balance == 0.0
    
    def test_get_apartment_balance_negative_with_obligations(self, test_db: Session, sample_apartment: Apartment):
        """Test balance decreases when obligations are created."""
        service = ObligationService(test_db)
        
        # Get initial balance
        initial_balance = service.get_apartment_balance(sample_apartment.id)
        
        data = ObligationCreate(
            type=ObligationType.MONTHLY,
            apartment_id=sample_apartment.id,
            month="2026-11",  # Unique month to avoid conflicts
            amount=15.0,
        )
        service.create(data)
        
        balance = service.get_apartment_balance(sample_apartment.id)
        
        # Balance should have decreased by 15 from initial
        assert balance == initial_balance - 15.0
    
    def test_get_summary_totals(self, test_db: Session, various_obligations: list[Obligation]):
        """Test get_summary() calculates correct totals."""
        service = ObligationService(test_db)
        
        summary = service.get_summary()
        
        expected_total = sum(float(obl.amount) for obl in various_obligations)
        assert summary.total_obligations == expected_total
        assert summary.count_obligations == len(various_obligations)
    
    def test_get_summary_filters_by_apartment(self, test_db: Session, sample_apartment: Apartment, various_obligations: list[Obligation]):
        """Test get_summary() filters by apartment."""
        service = ObligationService(test_db)
        
        summary = service.get_summary(apartment_id=sample_apartment.id)
        
        expected_total = sum(float(obl.amount) for obl in various_obligations)
        assert summary.total_obligations == expected_total
    
    def test_get_monthly_summary(self, test_db: Session, sample_apartment: Apartment):
        """Test get_monthly_summary() returns correct data."""
        service = ObligationService(test_db)
        month = "2026-05"
        
        # Create monthly obligation
        data = ObligationCreate(
            type=ObligationType.MONTHLY,
            apartment_id=sample_apartment.id,
            month=month,
            amount=15.0,
        )
        service.create(data)
        
        summary = service.get_monthly_summary(month)
        
        assert summary.month == month
        assert summary.total_obligations == 15.0
        assert summary.count_obligations == 1


# ============== API Integration Tests ==============

class TestObligationAPICreate:
    """Tests for POST /api/obligations endpoint."""
    
    def test_create_obligation_success(self, client: TestClient, cashier_headers: dict, sample_apartment: Apartment):
        """Test successful obligation creation via API."""
        response = client.post(
            "/api/obligations/",
            headers=cashier_headers,
            json={
                "type": "monthly",
                "apartment_id": sample_apartment.id,
                "month": "2026-01",
                "amount": 15.0,
                "description": "Месечна такса",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "monthly"
        assert data["apartment_id"] == sample_apartment.id
        assert data["amount"] == 15.0
    
    def test_create_obligation_requires_auth(self, client: TestClient, sample_apartment: Apartment):
        """Test that creating obligation requires authentication."""
        response = client.post(
            "/api/obligations/",
            json={
                "type": "monthly",
                "apartment_id": sample_apartment.id,
                "month": "2026-01",
                "amount": 15.0,
            },
        )
        
        assert response.status_code == 401


class TestObligationAPIList:
    """Tests for GET /api/obligations endpoint."""
    
    def test_list_obligations_success(self, client: TestClient, cashier_headers: dict, multiple_obligations: list[Obligation]):
        """Test listing obligations via API."""
        response = client.get("/api/obligations/", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(multiple_obligations)
    
    def test_list_obligations_filter_by_type(self, client: TestClient, cashier_headers: dict, various_obligations: list[Obligation]):
        """Test filtering obligations by type."""
        response = client.get("/api/obligations/?type=monthly", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(obl["type"] == "monthly" for obl in data)
    
    def test_list_obligations_filter_by_apartment(self, client: TestClient, cashier_headers: dict, multiple_obligations: list[Obligation]):
        """Test filtering obligations by apartment."""
        apt_id = multiple_obligations[0].apartment_id
        response = client.get(f"/api/obligations/?apartment_id={apt_id}", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(obl["apartment_id"] == apt_id for obl in data)


class TestObligationAPIGet:
    """Tests for GET /api/obligations/{id} endpoint."""
    
    def test_get_obligation_success(self, client: TestClient, cashier_headers: dict, sample_obligation: Obligation):
        """Test getting single obligation via API."""
        response = client.get(f"/api/obligations/{sample_obligation.id}", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_obligation.id
    
    def test_get_obligation_not_found(self, client: TestClient, cashier_headers: dict):
        """Test getting non-existent obligation returns 404."""
        response = client.get("/api/obligations/99999", headers=cashier_headers)
        
        assert response.status_code == 404


class TestObligationAPIUpdate:
    """Tests for PATCH /api/obligations/{id} endpoint."""
    
    def test_update_obligation_success(self, client: TestClient, cashier_headers: dict, sample_obligation: Obligation):
        """Test updating obligation via API."""
        response = client.patch(
            f"/api/obligations/{sample_obligation.id}",
            headers=cashier_headers,
            json={"description": "Updated description"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
    
    def test_update_obligation_not_found(self, client: TestClient, cashier_headers: dict):
        """Test updating non-existent obligation returns 404."""
        response = client.patch(
            "/api/obligations/99999",
            headers=cashier_headers,
            json={"description": "Test"},
        )
        
        assert response.status_code == 404


class TestObligationAPIDelete:
    """Tests for DELETE /api/obligations/{id} endpoint."""
    
    def test_delete_obligation_success(self, client: TestClient, cashier_headers: dict, sample_obligation: Obligation):
        """Test deleting obligation via API."""
        response = client.delete(f"/api/obligations/{sample_obligation.id}", headers=cashier_headers)
        
        assert response.status_code == 204
    
    def test_delete_obligation_not_found(self, client: TestClient, cashier_headers: dict):
        """Test deleting non-existent obligation returns 404."""
        response = client.delete("/api/obligations/99999", headers=cashier_headers)
        
        assert response.status_code == 404


class TestObligationAPIApartment:
    """Tests for apartment-specific obligation endpoints."""
    
    def test_list_apartment_obligations(self, client: TestClient, cashier_headers: dict, sample_apartment: Apartment, various_obligations: list[Obligation]):
        """Test listing obligations for specific apartment."""
        response = client.get(f"/api/obligations/apartment/{sample_apartment.id}", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(various_obligations)
    
    def test_get_apartment_balance(self, client: TestClient, cashier_headers: dict, sample_apartment: Apartment):
        """Test getting apartment balance via API."""
        response = client.get(f"/api/obligations/apartment/{sample_apartment.id}/balance", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert data["apartment_id"] == sample_apartment.id


class TestObligationAPIGenerateMonthly:
    """Tests for POST /api/obligations/generate-monthly endpoint."""
    
    def test_generate_monthly_success(self, client: TestClient, cashier_headers: dict, multiple_apartments: list[Apartment]):
        """Test generating monthly obligations via API."""
        response = client.post(
            "/api/obligations/generate-monthly?month=2026-04",
            headers=cashier_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(multiple_apartments)
    
    def test_generate_monthly_invalid_month_format(self, client: TestClient, cashier_headers: dict):
        """Test generating monthly with invalid month format."""
        response = client.post(
            "/api/obligations/generate-monthly?month=invalid",
            headers=cashier_headers,
        )
        
        assert response.status_code == 422  # Validation error


class TestObligationAPIStatistics:
    """Tests for obligation statistics endpoints."""
    
    def test_get_summary(self, client: TestClient, cashier_headers: dict, various_obligations: list[Obligation]):
        """Test getting obligation summary via API."""
        response = client.get("/api/obligations/stats/summary", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_obligations" in data
        assert "count_obligations" in data
    
    def test_get_summary_filter_by_type(self, client: TestClient, cashier_headers: dict, various_obligations: list[Obligation]):
        """Test filtering summary by obligation type."""
        response = client.get("/api/obligations/stats/summary?type=monthly", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_obligations" in data
    
    def test_get_monthly_summary(self, client: TestClient, cashier_headers: dict, sample_apartment: Apartment, test_db: Session):
        """Test getting monthly summary via API."""
        # Create monthly obligation first
        obl = Obligation(
            type=ObligationType.MONTHLY,
            apartment_id=sample_apartment.id,
            month="2026-06",
            amount=Decimal("15.00"),
        )
        test_db.add(obl)
        test_db.commit()
        
        response = client.get("/api/obligations/stats/monthly/2026-06", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["month"] == "2026-06"
        assert data["total_obligations"] == 15.0