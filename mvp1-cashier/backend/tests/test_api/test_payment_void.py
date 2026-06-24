"""Tests for payment void (soft delete) functionality.

Тестове за анулиране на плащания - audit-compliant soft delete.
Плащанията НИКОГА не се изтриват физически.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.apartment import Apartment
from app.models.payment import Payment, PaymentStatus
from app.models.account import ApartmentAccount, AccountTransaction, TransactionType, TransactionReference
from app.models.audit_log import AuditLog, AuditAction
from app.models.user import User


class TestVoidPayment:
    """Tests for POST /api/payments/{payment_id}/void endpoint."""
    
    def test_void_payment_success(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Should void a payment successfully."""
        # First create a payment
        create_response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 50.00,
                "month": "2027-01",
                "payment_method": "cash",
            },
        )
        assert create_response.status_code == 201
        payment_id = create_response.json()["id"]
        
        # Get initial balance
        account = test_db.query(ApartmentAccount).filter(
            ApartmentAccount.apartment_id == sample_apartment.id
        ).first()
        initial_balance = float(account.balance)
        
        # Void the payment
        void_response = client.post(
            f"/api/payments/{payment_id}/void",
            headers=cashier_headers,
            json={
                "reason": "Грешно въведена сума - трябва да е 60 лв вместо 50 лв"
            },
        )
        
        assert void_response.status_code == 200
        data = void_response.json()
        
        # Verify response
        assert data["success"] is True
        assert data["payment_id"] == payment_id
        assert data["void_reason"] == "Грешно въведена сума - трябва да е 60 лв вместо 50 лв"
        assert data["balance_adjustment"] == -50.0
        assert data["new_balance"] == initial_balance - 50.0
        assert "voided_at" in data
        assert "voided_by_id" in data
    
    def test_void_payment_updates_payment_status(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Should update payment status to voided."""
        # Create payment
        create_response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 30.00,
                "month": "2027-02",
            },
        )
        payment_id = create_response.json()["id"]
        
        # Void payment
        client.post(
            f"/api/payments/{payment_id}/void",
            headers=cashier_headers,
            json={"reason": "Тест за анулиране на плащане"},
        )
        
        # Verify payment status in database
        payment = test_db.query(Payment).filter(Payment.id == payment_id).first()
        test_db.refresh(payment)
        
        assert payment.status == PaymentStatus.VOIDED
        assert payment.voided_at is not None
        assert payment.voided_by_id is not None
        assert payment.void_reason == "Тест за анулиране на плащане"
    
    def test_void_payment_adjusts_account_balance(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Should subtract payment amount from account balance."""
        # Get or create account and record initial balance
        from app.api.payments import get_or_create_account
        account = get_or_create_account(test_db, sample_apartment.id)
        test_db.commit()
        initial_balance = Decimal(str(account.balance))
        
        # Create payment
        create_response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 100.00,
                "month": "2027-03",
            },
        )
        payment_id = create_response.json()["id"]
        
        # Balance should have increased
        test_db.refresh(account)
        balance_after_payment = Decimal(str(account.balance))
        assert balance_after_payment == initial_balance + Decimal("100.00")
        
        # Void payment
        client.post(
            f"/api/payments/{payment_id}/void",
            headers=cashier_headers,
            json={"reason": "Тестово анулиране за баланс"},
        )
        
        # Balance should be back to initial
        test_db.refresh(account)
        assert Decimal(str(account.balance)) == initial_balance
    
    def test_void_payment_creates_debit_transaction(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Should create a DEBIT transaction with VOID reference."""
        # Create payment
        create_response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 75.00,
                "month": "2027-04",
            },
        )
        payment_id = create_response.json()["id"]
        
        # Void payment
        client.post(
            f"/api/payments/{payment_id}/void",
            headers=cashier_headers,
            json={"reason": "Тест за транзакция"},
        )
        
        # Check for void transaction
        void_transaction = test_db.query(AccountTransaction).filter(
            AccountTransaction.reference_type == TransactionReference.VOID,
            AccountTransaction.reference_id == payment_id,
        ).first()
        
        assert void_transaction is not None
        assert void_transaction.type == TransactionType.DEBIT
        assert float(void_transaction.amount) == 75.00
        assert "Анулиране" in void_transaction.description
    
    def test_void_payment_creates_audit_log(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
        test_db: Session,
    ):
        """Should create an audit log entry for void operation."""
        # Create payment
        create_response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 25.00,
                "month": "2027-05",
            },
        )
        payment_id = create_response.json()["id"]
        
        # Count audit logs before void
        audit_count_before = test_db.query(AuditLog).filter(
            AuditLog.action == AuditAction.PAYMENT_VOIDED.value
        ).count()
        
        # Void payment
        client.post(
            f"/api/payments/{payment_id}/void",
            headers=cashier_headers,
            json={"reason": "Audit log test"},
        )
        
        # Verify audit log was created
        audit_count_after = test_db.query(AuditLog).filter(
            AuditLog.action == AuditAction.PAYMENT_VOIDED.value
        ).count()
        assert audit_count_after == audit_count_before + 1
        
        # Check audit log details
        audit_entry = test_db.query(AuditLog).filter(
            AuditLog.action == AuditAction.PAYMENT_VOIDED.value,
            AuditLog.entity_id == payment_id,
        ).first()
        
        assert audit_entry is not None
        assert audit_entry.entity_type == "payment"
        assert audit_entry.is_critical is True
        assert audit_entry.state_before is not None
        assert audit_entry.state_after is not None
        assert audit_entry.state_after["status"] == "voided"
    
    def test_void_payment_not_found(
        self,
        client: TestClient,
        cashier_headers: dict,
    ):
        """Should return 404 for non-existent payment."""
        response = client.post(
            "/api/payments/99999/void",
            headers=cashier_headers,
            json={"reason": "Test reason for non-existent payment"},
        )
        
        assert response.status_code == 404
        assert "не е намерено" in response.json()["detail"]
    
    def test_void_payment_already_voided(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Should return 400 when trying to void already voided payment."""
        # Create payment
        create_response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 40.00,
                "month": "2027-06",
            },
        )
        payment_id = create_response.json()["id"]
        
        # Void payment first time
        first_void = client.post(
            f"/api/payments/{payment_id}/void",
            headers=cashier_headers,
            json={"reason": "First void attempt"},
        )
        assert first_void.status_code == 200
        
        # Try to void again
        second_void = client.post(
            f"/api/payments/{payment_id}/void",
            headers=cashier_headers,
            json={"reason": "Second void attempt"},
        )
        
        assert second_void.status_code == 400
        assert "вече е анулирано" in second_void.json()["detail"]
    
    def test_void_payment_requires_reason(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Should return 422 when reason is missing or too short."""
        # Create payment
        create_response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 20.00,
                "month": "2027-07",
            },
        )
        payment_id = create_response.json()["id"]
        
        # Try to void without reason
        response_no_reason = client.post(
            f"/api/payments/{payment_id}/void",
            headers=cashier_headers,
            json={},
        )
        assert response_no_reason.status_code == 422
        
        # Try to void with too short reason
        response_short_reason = client.post(
            f"/api/payments/{payment_id}/void",
            headers=cashier_headers,
            json={"reason": "кратко"},
        )
        assert response_short_reason.status_code == 422
    
    def test_void_payment_unauthenticated(
        self,
        client: TestClient,
        sample_apartment: Apartment,
    ):
        """Should return 401 without authentication."""
        response = client.post(
            "/api/payments/1/void",
            json={"reason": "Unauthenticated test"},
        )
        assert response.status_code == 401


class TestListPaymentsWithVoided:
    """Tests for list payments with voided filter."""
    
    def test_list_payments_excludes_voided_by_default(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Should exclude voided payments by default."""
        # Create two payments
        for i in range(2):
            client.post(
                "/api/payments",
                headers=cashier_headers,
                json={
                    "apartment_id": sample_apartment.id,
                    "amount": 10.00 + i,
                    "month": f"2027-0{8+i}",
                },
            )
        
        # Get list (should have 2)
        response = client.get("/api/payments", headers=cashier_headers)
        initial_count = response.json()["total"]
        
        # Void one payment
        payments = response.json()["items"]
        void_id = payments[0]["id"]
        
        client.post(
            f"/api/payments/{void_id}/void",
            headers=cashier_headers,
            json={"reason": "Test void for filtering"},
        )
        
        # Get list again (should have 1 less)
        response_after = client.get("/api/payments", headers=cashier_headers)
        assert response_after.json()["total"] == initial_count - 1
    
    def test_list_payments_includes_voided_with_flag(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Should include voided payments when include_voided=true."""
        # Create payment
        create_response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 15.00,
                "month": "2027-10",
            },
        )
        payment_id = create_response.json()["id"]
        
        # Void it
        client.post(
            f"/api/payments/{payment_id}/void",
            headers=cashier_headers,
            json={"reason": "Test void for include flag"},
        )
        
        # Without flag - should not include voided
        response_without = client.get("/api/payments", headers=cashier_headers)
        voided_ids_without = [p["id"] for p in response_without.json()["items"] if p["status"] == "voided"]
        assert payment_id not in voided_ids_without
        
        # With flag - should include voided
        response_with = client.get("/api/payments?include_voided=true", headers=cashier_headers)
        all_ids = [p["id"] for p in response_with.json()["items"]]
        assert payment_id in all_ids


class TestReceiptForVoidedPayment:
    """Tests for receipt generation with voided payments."""
    
    def test_receipt_not_allowed_for_voided_payment(
        self,
        client: TestClient,
        cashier_headers: dict,
        sample_apartment: Apartment,
    ):
        """Should return 400 when trying to get receipt for voided payment."""
        # Create payment
        create_response = client.post(
            "/api/payments",
            headers=cashier_headers,
            json={
                "apartment_id": sample_apartment.id,
                "amount": 35.00,
                "month": "2027-11",
            },
        )
        payment_id = create_response.json()["id"]
        
        # Void it
        client.post(
            f"/api/payments/{payment_id}/void",
            headers=cashier_headers,
            json={"reason": "Test void for receipt restriction"},
        )
        
        # Try to get receipt
        receipt_response = client.get(
            f"/api/payments/{payment_id}/receipt",
            headers=cashier_headers,
        )
        
        assert receipt_response.status_code == 400
        assert "анулирано" in receipt_response.json()["detail"]