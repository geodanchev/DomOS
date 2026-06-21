"""Tests for payments API endpoints."""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.apartment import Apartment
from app.models.payment import Payment
from app.models.monthly_charge import MonthlyCharge, ChargeStatus
from app.models.user import User
from tests.conftest import get_current_month


class TestListPayments:
    """Tests for GET /api/payments endpoint."""
    
    def test_list_payments_empty(self, client: TestClient, cashier_headers: dict):
        """Should return empty list when no payments."""
        response = client.get("/api/payments", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
    
    def test_list_payments_with_data(
        self, 
        client: TestClient, 
        cashier_headers: dict,
        sample_payment: Payment,
    ):
        """Should return list of payments."""
        response = client.get("/api/payments", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["amount"] == 15.0
    
    def test_list_payments_filter_by_apartment(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_payment: Payment,
        sample_apartment: Apartment,
    ):
        """Should filter payments by apartment_id."""
        response = client.get(
            f"/api/payments?apartment_id={sample_apartment.id}",
            headers=cashier_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        
        # Filter by non-existent apartment
        response2 = client.get(
            "/api/payments?apartment_id=9999",
            headers=cashier_headers,
        )
        assert response2.json()["total"] == 0
    
    def test_list_payments_filter_by_month(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_payment: Payment,
    ):
        """Should filter payments by month."""
        current_month = get_current_month()
        
        response = client.get(
            f"/api/payments?month={current_month}",
            headers=cashier_headers,
        )
        
        assert response.status_code == 200
        assert response.json()["total"] == 1
        
        # Filter by different month
        response2 = client.get(
            "/api/payments?month=2020-01",
            headers=cashier_headers,
        )
        assert response2.json()["total"] == 0
    
    def test_list_payments_unauthenticated(self, client: TestClient):
        """Should return 401 without authentication."""
        response = client.get("/api/payments")
        assert response.status_code == 401
    
    def test_list_payments_includes_apartment_info(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_payment: Payment,
    ):
        """Should include apartment number and owner name."""
        response = client.get("/api/payments", headers=cashier_headers)
        
        assert response.status_code == 200
        item = response.json()["items"][0]
        assert item["apartment_number"] == "1"
        assert item["owner_name"] == "Иван Петров"


class TestCreatePayment:
    """Tests for POST /api/payments endpoint."""
    
    def test_create_payment_success(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Should create payment successfully."""
        current_month = get_current_month()
        
        response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 15.00,
                "month": current_month,
                "payment_method": "cash",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 15.0
        assert data["month"] == current_month
        assert data["apartment_id"] == sample_apartment.id
        assert data["payment_method"] == "cash"
    
    def test_create_payment_invalid_apartment(
        self,
        client: TestClient,
        cashier_headers: dict,
    ):
        """Should return 404 for non-existent apartment."""
        response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": 9999,
                "amount": 15.00,
                "month": "2027-01",
            },
        )
        
        assert response.status_code == 404
        assert "не е намерен" in response.json()["detail"]
    
    def test_create_payment_updates_charge_status(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_charge: MonthlyCharge,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Should update monthly charge status after payment."""
        # Verify charge is initially unpaid
        assert sample_charge.status == ChargeStatus.UNPAID
        assert float(sample_charge.amount_paid) == 0
        
        # Pay full amount
        response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": float(sample_apartment.monthly_fee),
                "month": sample_charge.month,
            },
        )
        
        assert response.status_code == 201
        
        # Refresh and check charge status
        test_db.refresh(sample_charge)
        assert sample_charge.status == ChargeStatus.PAID
        assert float(sample_charge.amount_paid) == float(sample_apartment.monthly_fee)
    
    def test_create_payment_partial_updates_status(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_charge: MonthlyCharge,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Should set status to PARTIAL for partial payment."""
        partial_amount = float(sample_apartment.monthly_fee) / 2
        
        response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": partial_amount,
                "month": sample_charge.month,
            },
        )
        
        assert response.status_code == 201
        
        test_db.refresh(sample_charge)
        assert sample_charge.status == ChargeStatus.PARTIAL
        assert float(sample_charge.amount_paid) == partial_amount
    
    def test_create_payment_invalid_month_format(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Should reject invalid month format."""
        invalid_formats = ["01-2027", "2027/01", "January 2027", "2027-1", "27-01"]
        
        for month in invalid_formats:
            response = client.post(
                "/api/payments",
                headers=cashier_headers,
                json={
                    "apartment_id": sample_apartment.id,
                    "amount": 15.00,
                    "month": month,
                },
            )
            assert response.status_code == 422, f"Month format '{month}' should be rejected"
    
    def test_create_payment_negative_amount(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Should reject negative amount."""
        response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": -15.00,
                "month": "2027-01",
            },
        )
        
        assert response.status_code == 422
    
    def test_create_payment_zero_amount(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Should reject zero amount."""
        response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 0,
                "month": "2027-01",
            },
        )
        
        assert response.status_code == 422
    
    def test_create_payment_records_collector(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
        cashier_user: User,
    ):
        """Should record who collected the payment."""
        response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 15.00,
                "month": "2027-01",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["collected_by_id"] == cashier_user.id
        assert data["collected_by_name"] == "Цецка"
    
    def test_create_payment_with_notes(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Should store payment notes."""
        response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 15.00,
                "month": "2027-01",
                "notes": "Платено на ръка",
            },
        )
        
        assert response.status_code == 201
        assert response.json()["notes"] == "Платено на ръка"
    
    def test_create_payment_custom_date(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Should accept custom payment date."""
        response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 15.00,
                "month": "2027-01",
                "payment_date": "2027-01-15",
            },
        )
        
        assert response.status_code == 201
        assert response.json()["payment_date"] == "2027-01-15"


class TestGetPayment:
    """Tests for GET /api/payments/{id} endpoint."""
    
    def test_get_payment_success(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_payment: Payment,
    ):
        """Should return payment by ID."""
        response = client.get(
            f"/api/payments/{sample_payment.id}",
            headers=cashier_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_payment.id
        assert data["amount"] == 15.0
    
    def test_get_payment_not_found(
        self,
        client: TestClient,
        cashier_headers: dict,
    ):
        """Should return 404 for non-existent payment."""
        response = client.get(
            "/api/payments/9999",
            headers=cashier_headers,
        )
        
        assert response.status_code == 404
        assert "не е намерено" in response.json()["detail"]


class TestGetReceipt:
    """Tests for GET /api/payments/{id}/receipt endpoint."""
    
    def test_get_receipt_success(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_payment: Payment,
    ):
        """Should return receipt data."""
        response = client.get(
            f"/api/payments/{sample_payment.id}/receipt",
            headers=cashier_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["apartment_number"] == "1"
        assert data["amount"] == 15.0
        assert data["receipt_number"] == sample_payment.id
    
    def test_get_receipt_not_found(
        self,
        client: TestClient,
        cashier_headers: dict,
    ):
        """Should return 404 for non-existent payment."""
        response = client.get(
            "/api/payments/9999/receipt",
            headers=cashier_headers,
        )
        
        assert response.status_code == 404


class TestDeletePayment:
    """Tests for DELETE /api/payments/{id} endpoint."""
    
    def test_delete_payment_success(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_payment: Payment,
    ):
        """Should delete payment successfully."""
        response = client.delete(
            f"/api/payments/{sample_payment.id}",
            headers=cashier_headers,
        )
        
        assert response.status_code == 204
        
        # Verify payment is deleted
        get_response = client.get(
            f"/api/payments/{sample_payment.id}",
            headers=cashier_headers,
        )
        assert get_response.status_code == 404
    
    def test_delete_payment_not_found(
        self,
        client: TestClient,
        cashier_headers: dict,
    ):
        """Should return 404 for non-existent payment."""
        response = client.delete(
            "/api/payments/9999",
            headers=cashier_headers,
        )
        
        assert response.status_code == 404
    
    def test_delete_payment_reverts_charge_status(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_charge: MonthlyCharge,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Should revert charge status when payment is deleted."""
        # First create a payment that marks charge as paid
        response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": float(sample_apartment.monthly_fee),
                "month": sample_charge.month,
            },
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]
        
        # Verify charge is paid
        test_db.refresh(sample_charge)
        assert sample_charge.status == ChargeStatus.PAID
        
        # Delete the payment
        delete_response = client.delete(
            f"/api/payments/{payment_id}",
            headers=cashier_headers,
        )
        assert delete_response.status_code == 204
        
        # Verify charge status is reverted
        test_db.refresh(sample_charge)
        assert sample_charge.status == ChargeStatus.UNPAID
        assert float(sample_charge.amount_paid) == 0
    
    def test_delete_payment_partial_revert(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_charge: MonthlyCharge,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Should correctly revert partial payment on delete."""
        # Create first payment (partial)
        half_amount = float(sample_apartment.monthly_fee) / 2
        response1 = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": half_amount,
                "month": sample_charge.month,
            },
        )
        payment1_id = response1.json()["id"]
        
        # Create second payment (completes payment)
        response2 = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": half_amount,
                "month": sample_charge.month,
            },
        )
        payment2_id = response2.json()["id"]
        
        # Verify charge is fully paid
        test_db.refresh(sample_charge)
        assert sample_charge.status == ChargeStatus.PAID
        
        # Delete second payment
        client.delete(f"/api/payments/{payment2_id}", headers=cashier_headers)
        
        # Verify charge is now partial
        test_db.refresh(sample_charge)
        assert sample_charge.status == ChargeStatus.PARTIAL
        assert float(sample_charge.amount_paid) == half_amount


class TestMultiplePayments:
    """Tests for multiple payments scenarios."""
    
    def test_multiple_payments_same_month(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_charge: MonthlyCharge,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Multiple payments for same month should accumulate."""
        amount1 = 5.0
        amount2 = 10.0
        
        # First payment
        client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": amount1,
                "month": sample_charge.month,
            },
        )
        
        # Second payment
        client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": amount2,
                "month": sample_charge.month,
            },
        )
        
        # Check accumulated amount
        test_db.refresh(sample_charge)
        assert float(sample_charge.amount_paid) == amount1 + amount2
    
    def test_overpayment(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_charge: MonthlyCharge,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Overpayment should be recorded (amount_paid > amount_due)."""
        overpayment = float(sample_apartment.monthly_fee) + 10.0
        
        response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": overpayment,
                "month": sample_charge.month,
            },
        )
        
        assert response.status_code == 201
        
        test_db.refresh(sample_charge)
        assert float(sample_charge.amount_paid) == overpayment
        assert sample_charge.status == ChargeStatus.PAID