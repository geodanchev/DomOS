"""Tests for custom charges API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.custom_charge import CustomCharge, CustomChargeStatus
from app.models.apartment import Apartment


class TestCustomChargesAPI:
    """Test suite for custom charges API."""

    def test_create_custom_charge(self, client: TestClient, cashier_headers: dict, sample_apartment: Apartment):
        """Test creating a new custom charge."""
        payload = {
            "apartment_id": sample_apartment.id,
            "amount_due": 120.00,
            "description": "начално задължение преди старта"
        }
        
        response = client.post(
            "/api/custom-charges",
            json=payload,
            headers=cashier_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["apartment_id"] == sample_apartment.id
        assert data["amount_due"] == 120.00
        assert data["description"] == "начално задължение преди старта"
        assert data["amount_paid"] == 0
        assert data["status"] == "unpaid"
        assert data["apartment_number"] == sample_apartment.number
        assert data["owner_name"] == sample_apartment.owner_name
        assert "id" in data

    def test_create_custom_charge_minimal(self, client: TestClient, cashier_headers: dict, sample_apartment: Apartment):
        """Test creating a custom charge with minimal data (no description)."""
        payload = {
            "apartment_id": sample_apartment.id,
            "amount_due": 50.00
        }
        
        response = client.post(
            "/api/custom-charges",
            json=payload,
            headers=cashier_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["apartment_id"] == sample_apartment.id
        assert data["amount_due"] == 50.00
        assert data["description"] is None

    def test_create_custom_charge_invalid_amount(self, client: TestClient, cashier_headers: dict, sample_apartment: Apartment):
        """Test that creating a charge with invalid amount fails."""
        payload = {
            "apartment_id": sample_apartment.id,
            "amount_due": -10.00  # Negative amount
        }
        
        response = client.post(
            "/api/custom-charges",
            json=payload,
            headers=cashier_headers
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_custom_charge_invalid_apartment(self, client: TestClient, cashier_headers: dict):
        """Test that creating a charge with non-existent apartment fails."""
        payload = {
            "apartment_id": 99999,
            "amount_due": 100.00
        }
        
        response = client.post(
            "/api/custom-charges",
            json=payload,
            headers=cashier_headers
        )
        
        assert response.status_code == 404
        assert "не е намерен" in response.json()["detail"]

    def test_list_custom_charges(self, client: TestClient, cashier_headers: dict, test_db: Session, sample_apartment: Apartment):
        """Test listing all custom charges."""
        # Create some test charges
        charge1 = CustomCharge(
            apartment_id=sample_apartment.id,
            amount_due=100.00,
            description="Тестово задължение 1"
        )
        charge2 = CustomCharge(
            apartment_id=sample_apartment.id,
            amount_due=200.00,
            description="Тестово задължение 2"
        )
        test_db.add(charge1)
        test_db.add(charge2)
        test_db.commit()
        
        response = client.get("/api/custom-charges", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2

    def test_list_custom_charges_filter_by_apartment(self, client: TestClient, cashier_headers: dict, test_db: Session, multiple_apartments: list):
        """Test listing custom charges filtered by apartment."""
        apt1, apt2 = multiple_apartments[0], multiple_apartments[1]
        
        # Create charges for different apartments
        charge1 = CustomCharge(apartment_id=apt1.id, amount_due=100.00)
        charge2 = CustomCharge(apartment_id=apt2.id, amount_due=200.00)
        test_db.add(charge1)
        test_db.add(charge2)
        test_db.commit()
        
        response = client.get(
            f"/api/custom-charges?apartment_id={apt1.id}",
            headers=cashier_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["apartment_id"] == apt1.id

    def test_list_custom_charges_filter_by_status(self, client: TestClient, cashier_headers: dict, test_db: Session, sample_apartment: Apartment):
        """Test listing custom charges filtered by status."""
        # Create a paid charge
        paid_charge = CustomCharge(
            apartment_id=sample_apartment.id,
            amount_due=50.00,
            amount_paid=50.00,
            status=CustomChargeStatus.PAID
        )
        test_db.add(paid_charge)
        test_db.commit()
        
        response = client.get(
            "/api/custom-charges?status_filter=paid",
            headers=cashier_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "paid"

    def test_get_custom_charge(self, client: TestClient, cashier_headers: dict, test_db: Session, sample_apartment: Apartment):
        """Test getting a specific custom charge."""
        charge = CustomCharge(
            apartment_id=sample_apartment.id,
            amount_due=75.00,
            description="Тест за детайли"
        )
        test_db.add(charge)
        test_db.commit()
        test_db.refresh(charge)
        
        response = client.get(f"/api/custom-charges/{charge.id}", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == charge.id
        assert data["apartment_id"] == sample_apartment.id
        assert data["amount_due"] == 75.00
        assert data["apartment_number"] == sample_apartment.number
        assert data["owner_name"] == sample_apartment.owner_name

    def test_get_custom_charge_not_found(self, client: TestClient, cashier_headers: dict):
        """Test getting a non-existent custom charge."""
        response = client.get("/api/custom-charges/99999", headers=cashier_headers)
        
        assert response.status_code == 404
        assert "не е намерено" in response.json()["detail"]

    def test_update_custom_charge(self, client: TestClient, cashier_headers: dict, test_db: Session, sample_apartment: Apartment):
        """Test updating a custom charge."""
        charge = CustomCharge(
            apartment_id=sample_apartment.id,
            amount_due=100.00,
            description="Оригинално описание"
        )
        test_db.add(charge)
        test_db.commit()
        test_db.refresh(charge)
        
        update_payload = {
            "amount_due": 150.00,
            "description": "Обновено описание"
        }
        
        response = client.put(
            f"/api/custom-charges/{charge.id}",
            json=update_payload,
            headers=cashier_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount_due"] == 150.00
        assert data["description"] == "Обновено описание"

    def test_update_custom_charge_partial(self, client: TestClient, cashier_headers: dict, test_db: Session, sample_apartment: Apartment):
        """Test partial update of a custom charge."""
        charge = CustomCharge(
            apartment_id=sample_apartment.id,
            amount_due=100.00,
            description="Оригинално"
        )
        test_db.add(charge)
        test_db.commit()
        test_db.refresh(charge)
        
        # Update only the description
        update_payload = {"description": "Само описание"}
        
        response = client.put(
            f"/api/custom-charges/{charge.id}",
            json=update_payload,
            headers=cashier_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount_due"] == 100.00  # Unchanged
        assert data["description"] == "Само описание"

    def test_delete_custom_charge(self, client: TestClient, cashier_headers: dict, test_db: Session, sample_apartment: Apartment):
        """Test deleting a custom charge."""
        charge = CustomCharge(
            apartment_id=sample_apartment.id,
            amount_due=25.00
        )
        test_db.add(charge)
        test_db.commit()
        test_db.refresh(charge)
        charge_id = charge.id
        
        response = client.delete(f"/api/custom-charges/{charge_id}", headers=cashier_headers)
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/api/custom-charges/{charge_id}", headers=cashier_headers)
        assert get_response.status_code == 404

    def test_record_payment(self, client: TestClient, cashier_headers: dict, test_db: Session, sample_apartment: Apartment):
        """Test recording a payment for a custom charge."""
        charge = CustomCharge(
            apartment_id=sample_apartment.id,
            amount_due=100.00,
            amount_paid=0,
            status=CustomChargeStatus.UNPAID
        )
        test_db.add(charge)
        test_db.commit()
        test_db.refresh(charge)
        
        payment_payload = {"amount": 50.00}
        
        response = client.post(
            f"/api/custom-charges/{charge.id}/payment",
            json=payment_payload,
            headers=cashier_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount_paid"] == 50.00
        assert data["status"] == "partial"

    def test_record_full_payment(self, client: TestClient, cashier_headers: dict, test_db: Session, sample_apartment: Apartment):
        """Test recording a full payment that marks charge as paid."""
        charge = CustomCharge(
            apartment_id=sample_apartment.id,
            amount_due=100.00,
            amount_paid=0,
            status=CustomChargeStatus.UNPAID
        )
        test_db.add(charge)
        test_db.commit()
        test_db.refresh(charge)
        
        payment_payload = {"amount": 100.00}
        
        response = client.post(
            f"/api/custom-charges/{charge.id}/payment",
            json=payment_payload,
            headers=cashier_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount_paid"] == 100.00
        assert data["status"] == "paid"

    def test_record_multiple_payments(self, client: TestClient, cashier_headers: dict, test_db: Session, sample_apartment: Apartment):
        """Test recording multiple payments for a custom charge."""
        charge = CustomCharge(
            apartment_id=sample_apartment.id,
            amount_due=100.00,
            amount_paid=0,
            status=CustomChargeStatus.UNPAID
        )
        test_db.add(charge)
        test_db.commit()
        test_db.refresh(charge)
        
        # First payment
        response1 = client.post(
            f"/api/custom-charges/{charge.id}/payment",
            json={"amount": 30.00},
            headers=cashier_headers
        )
        assert response1.status_code == 200
        assert response1.json()["amount_paid"] == 30.00
        assert response1.json()["status"] == "partial"
        
        # Second payment
        response2 = client.post(
            f"/api/custom-charges/{charge.id}/payment",
            json={"amount": 70.00},
            headers=cashier_headers
        )
        assert response2.status_code == 200
        assert response2.json()["amount_paid"] == 100.00
        assert response2.json()["status"] == "paid"

    def test_create_charge_unauthorized(self, client: TestClient, sample_apartment: Apartment):
        """Test that creating a charge without auth fails."""
        payload = {
            "apartment_id": sample_apartment.id,
            "amount_due": 100.00
        }
        
        response = client.post("/api/custom-charges", json=payload)
        
        assert response.status_code == 401