"""Tests for dashboard API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.apartment import Apartment
from app.models.payment import Payment
from app.models.monthly_charge import MonthlyCharge, ChargeStatus
from app.models.user import User
from tests.conftest import get_current_month


class TestDashboard:
    """Tests for GET /api/dashboard endpoint."""
    
    def test_dashboard_empty(
        self,
        client: TestClient,
        cashier_headers: dict,
    ):
        """Should return zeros when no data."""
        response = client.get("/api/dashboard", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_apartments"] == 0
        assert data["total_collected"] == 0
        assert data["total_unpaid"] == 0
        assert data["paid_count"] == 0
        assert data["apartments"] == []
    
    def test_dashboard_with_apartments(
        self,
        client: TestClient,
        cashier_headers: dict,
        multiple_apartments: list[Apartment],
    ):
        """Should count apartments correctly."""
        response = client.get("/api/dashboard", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_apartments"] == 5
        assert len(data["apartments"]) == 5
    
    def test_dashboard_with_charges(
        self,
        client: TestClient,
        cashier_headers: dict,
        multiple_charges: list[MonthlyCharge],
        multiple_apartments: list[Apartment],
    ):
        """Should show unpaid status for all apartments with charges."""
        response = client.get("/api/dashboard", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # All should be unpaid initially
        assert data["unpaid_count"] == 5
        assert data["paid_count"] == 0
        assert data["partial_count"] == 0
        
        # Total due should be sum of all monthly fees
        total_due = sum(float(apt.monthly_fee) for apt in multiple_apartments)
        assert data["total_unpaid"] == total_due
        assert data["total_collected"] == 0
    
    def test_dashboard_collection_rate_calculation(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_charge: MonthlyCharge,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Should calculate collection rate correctly."""
        # Pay half
        half_amount = float(sample_apartment.monthly_fee) / 2
        sample_charge.amount_paid = half_amount
        sample_charge.status = ChargeStatus.PARTIAL
        test_db.commit()
        
        response = client.get("/api/dashboard", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # 50% collection rate
        assert data["collection_rate"] == 50.0
        assert data["total_collected"] == half_amount
        assert data["partial_count"] == 1
    
    def test_dashboard_mixed_statuses(
        self,
        client: TestClient,
        cashier_headers: dict,
        multiple_charges: list[MonthlyCharge],
        multiple_apartments: list[Apartment],
        test_db: Session,
    ):
        """Should correctly count mixed payment statuses."""
        # Set up: 2 paid, 1 partial, 2 unpaid
        charges = multiple_charges
        
        # Apartment 1: fully paid
        charges[0].amount_paid = charges[0].amount_due
        charges[0].status = ChargeStatus.PAID
        
        # Apartment 2: fully paid
        charges[1].amount_paid = charges[1].amount_due
        charges[1].status = ChargeStatus.PAID
        
        # Apartment 3: partial
        charges[2].amount_paid = float(charges[2].amount_due) / 2
        charges[2].status = ChargeStatus.PARTIAL
        
        # Apartments 4, 5: remain unpaid
        test_db.commit()
        
        response = client.get("/api/dashboard", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["paid_count"] == 2
        assert data["partial_count"] == 1
        assert data["unpaid_count"] == 2
    
    def test_dashboard_apartment_details(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_charge: MonthlyCharge,
        sample_apartment: Apartment,
    ):
        """Should include apartment details in response."""
        response = client.get("/api/dashboard", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        apt = data["apartments"][0]
        assert apt["apartment_id"] == sample_apartment.id
        assert apt["apartment_number"] == "1"
        assert apt["owner_name"] == "Иван Петров"
        assert apt["amount_due"] == float(sample_apartment.monthly_fee)
        assert apt["amount_paid"] == 0
        assert apt["status"] == "unpaid"
        assert apt["status_display"] == "Не"
    
    def test_dashboard_status_display_bulgarian(
        self,
        client: TestClient,
        cashier_headers: dict,
        multiple_charges: list[MonthlyCharge],
        multiple_apartments: list[Apartment],
        test_db: Session,
    ):
        """Should display status in Bulgarian."""
        # Set different statuses
        multiple_charges[0].status = ChargeStatus.PAID
        multiple_charges[0].amount_paid = multiple_charges[0].amount_due
        
        multiple_charges[1].status = ChargeStatus.PARTIAL
        multiple_charges[1].amount_paid = float(multiple_charges[1].amount_due) / 2
        
        # charges[2] remains UNPAID
        test_db.commit()
        
        response = client.get("/api/dashboard", headers=cashier_headers)
        
        assert response.status_code == 200
        apartments = response.json()["apartments"]
        
        # Find each apartment by number and check display
        status_displays = {apt["apartment_number"]: apt["status_display"] for apt in apartments}
        
        assert status_displays["1"] == "Да"       # PAID
        assert status_displays["2"] == "Частично"  # PARTIAL
        assert status_displays["3"] == "Не"       # UNPAID
    
    def test_dashboard_filter_by_month(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Should filter by specific month."""
        # Create charge for specific month
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-03",
            amount_due=sample_apartment.monthly_fee,
            amount_paid=sample_apartment.monthly_fee,
            status=ChargeStatus.PAID,
        )
        test_db.add(charge)
        test_db.commit()
        
        # Query specific month
        response = client.get(
            "/api/dashboard?month=2027-03",
            headers=cashier_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_month"] == "2027-03"
        assert data["paid_count"] == 1
    
    def test_dashboard_unauthenticated(self, client: TestClient):
        """Should return 401 without authentication."""
        response = client.get("/api/dashboard")
        assert response.status_code == 401
    
    def test_dashboard_apartments_sorted_by_number(
        self,
        client: TestClient,
        cashier_headers: dict,
        multiple_apartments: list[Apartment],
    ):
        """Should return apartments sorted by number."""
        response = client.get("/api/dashboard", headers=cashier_headers)
        
        assert response.status_code == 200
        apartments = response.json()["apartments"]
        numbers = [apt["apartment_number"] for apt in apartments]
        
        assert numbers == sorted(numbers)


class TestFundBalance:
    """Tests for GET /api/dashboard/fund endpoint."""
    
    def test_fund_balance_empty(
        self,
        client: TestClient,
        cashier_headers: dict,
    ):
        """Should return zero balance when no payments."""
        response = client.get("/api/dashboard/fund", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_collected_all_time"] == 0
        assert data["total_expenses"] == 0
        assert data["current_balance"] == 0
    
    def test_fund_balance_with_payments(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_payment: Payment,
    ):
        """Should sum all payments."""
        response = client.get("/api/dashboard/fund", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_collected_all_time"] == 15.0
        assert data["current_balance"] == 15.0
    
    def test_fund_balance_multiple_payments(
        self,
        client: TestClient,
        cashier_headers: dict,
        multiple_apartments: list[Apartment],
        cashier_user: User,
        test_db: Session,
    ):
        """Should sum all payments across apartments."""
        # Create multiple payments
        total = 0
        for i, apt in enumerate(multiple_apartments[:3]):
            amount = 10.0 + i * 5  # 10, 15, 20
            payment = Payment(
                apartment_id=apt.id,
                amount=amount,
                month=get_current_month(),
                payment_method="cash",
                collected_by_id=cashier_user.id,
            )
            test_db.add(payment)
            total += amount
        test_db.commit()
        
        response = client.get("/api/dashboard/fund", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_collected_all_time"] == total
        assert data["current_balance"] == total
    
    def test_fund_balance_unauthenticated(self, client: TestClient):
        """Should return 401 without authentication."""
        response = client.get("/api/dashboard/fund")
        assert response.status_code == 401


class TestDashboardIntegration:
    """Integration tests for dashboard with real payment flow."""
    
    def test_payment_updates_dashboard(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_charge: MonthlyCharge,
        sample_apartment: Apartment,
    ):
        """Dashboard should reflect new payments immediately."""
        # Check initial state
        response1 = client.get("/api/dashboard", headers=cashier_headers)
        assert response1.json()["unpaid_count"] == 1
        assert response1.json()["paid_count"] == 0
        
        # Make payment
        client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": float(sample_apartment.monthly_fee),
                "month": sample_charge.month,
            },
        )
        
        # Check updated state
        response2 = client.get("/api/dashboard", headers=cashier_headers)
        assert response2.json()["unpaid_count"] == 0
        assert response2.json()["paid_count"] == 1
    
    def test_fund_increases_with_payments(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Fund balance should increase with each payment."""
        # Initial balance
        response1 = client.get("/api/dashboard/fund", headers=cashier_headers)
        initial_balance = response1.json()["current_balance"]
        
        # Make payment
        payment_amount = 25.0
        client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": payment_amount,
                "month": "2027-01",
            },
        )
        
        # Check new balance
        response2 = client.get("/api/dashboard/fund", headers=cashier_headers)
        new_balance = response2.json()["current_balance"]
        
        assert new_balance == initial_balance + payment_amount
