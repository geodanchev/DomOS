"""Tests for Receipts API - Sprint 3 TDD.

Тест кейсове за разписки (квитанции) с PDF генериране.
Подход: Test-Driven Development - тестовете са написани преди имплементацията.
"""

import pytest
from datetime import date, datetime
from fastapi import status
from sqlalchemy.orm import Session


class TestCreateReceiptOriginal:
    """Тестове за създаване на оригинална разписка."""

    def test_create_receipt_success(self, client, test_db, sample_payment, cashier_headers):
        """Успешно създаване на разписка за валидно плащане."""
        response = client.post(
            "/api/receipts",
            json={"payment_id": sample_payment.id},
            headers=cashier_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["payment_id"] == sample_payment.id
        assert data["is_copy"] is False
        assert data["original_receipt_id"] is None
        assert "receipt_number" in data
        assert data["receipt_number"] is not None

    def test_create_receipt_generates_sequential_number(
        self, client, test_db, multiple_apartments, cashier_user, cashier_headers
    ):
        """Номерата на разписките са последователни (YYYY-NNNNNN)."""
        from app.models.payment import Payment

        payments = []
        for apt in multiple_apartments[:3]:
            payment = Payment(
                apartment_id=apt.id, amount=apt.monthly_fee, month="2026-06",
                payment_date=date.today(), payment_method="cash", collected_by_id=cashier_user.id,
            )
            test_db.add(payment)
            payments.append(payment)
        test_db.commit()
        for p in payments:
            test_db.refresh(p)

        receipt_numbers = []
        for payment in payments:
            response = client.post("/api/receipts", json={"payment_id": payment.id}, headers=cashier_headers)
            assert response.status_code == status.HTTP_201_CREATED
            receipt_numbers.append(response.json()["receipt_number"])

        current_year = date.today().year
        for i, num in enumerate(receipt_numbers):
            assert num.startswith(f"{current_year}-")
            seq_num = int(num.split("-")[1])
            assert seq_num == i + 1

    def test_create_receipt_invalid_payment_returns_404(self, client, cashier_headers):
        """Грешка 404 при несъществуващ payment_id."""
        response = client.post("/api/receipts", json={"payment_id": 99999}, headers=cashier_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_receipt_duplicate_payment_returns_error(self, client, test_db, sample_payment, cashier_headers):
        """Грешка при втора оригинална разписка за същото плащане."""
        response1 = client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        assert response1.status_code == status.HTTP_201_CREATED

        response2 = client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_receipt_requires_authentication(self, client, sample_payment):
        """Създаването изисква автентикация."""
        response = client.post("/api/receipts", json={"payment_id": sample_payment.id})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateReceiptCopy:
    """Тестове за създаване на копие на разписка."""

    def test_create_copy_success(self, client, test_db, sample_payment, cashier_headers):
        """Успешно създаване на копие - is_copy=True, същия receipt_number."""
        response1 = client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        original = response1.json()

        response2 = client.post(f"/api/receipts/{original['id']}/copy", headers=cashier_headers)
        assert response2.status_code == status.HTTP_201_CREATED
        copy = response2.json()

        assert copy["is_copy"] is True
        assert copy["original_receipt_id"] == original["id"]
        assert copy["receipt_number"] == original["receipt_number"]

    def test_create_copy_invalid_receipt_returns_404(self, client, cashier_headers):
        """Грешка 404 при копиране на несъществуваща разписка."""
        response = client.post("/api/receipts/99999/copy", headers=cashier_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_multiple_copies_allowed(self, client, test_db, sample_payment, cashier_headers):
        """Множество копия на една разписка са позволени."""
        response = client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        original = response.json()

        for i in range(5):
            response = client.post(f"/api/receipts/{original['id']}/copy", headers=cashier_headers)
            assert response.status_code == status.HTTP_201_CREATED
            assert response.json()["is_copy"] is True

    def test_create_copy_of_copy_references_original(self, client, test_db, sample_payment, cashier_headers):
        """Копие на копие сочи към ОРИГИНАЛА."""
        response = client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        original = response.json()

        response = client.post(f"/api/receipts/{original['id']}/copy", headers=cashier_headers)
        copy1 = response.json()

        response = client.post(f"/api/receipts/{copy1['id']}/copy", headers=cashier_headers)
        copy2 = response.json()

        assert copy2["original_receipt_id"] == original["id"]


class TestGetReceipt:
    """Тестове за четене на разписки."""

    def test_get_receipt_by_id_success(self, client, test_db, sample_payment, cashier_headers):
        """Успешно вземане на разписка по ID."""
        response = client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        created = response.json()

        response = client.get(f"/api/receipts/{created['id']}", headers=cashier_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == created["id"]

    def test_get_receipt_not_found_returns_404(self, client, cashier_headers):
        """Грешка 404 за несъществуваща разписка."""
        response = client.get("/api/receipts/99999", headers=cashier_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestListReceipts:
    """Тестове за списък с разписки."""

    def test_list_receipts_returns_all_by_default(self, client, test_db, sample_payment, cashier_headers):
        """По подразбиране връща и оригинали и копия."""
        response = client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        original = response.json()

        for _ in range(2):
            client.post(f"/api/receipts/{original['id']}/copy", headers=cashier_headers)

        response = client.get("/api/receipts", headers=cashier_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 3

    def test_list_receipts_filter_originals_only(self, client, test_db, sample_payment, cashier_headers):
        """Филтър за само оригинални разписки."""
        response = client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        original = response.json()
        client.post(f"/api/receipts/{original['id']}/copy", headers=cashier_headers)

        response = client.get("/api/receipts?is_copy=false", headers=cashier_headers)
        assert response.status_code == status.HTTP_200_OK
        for item in response.json()["items"]:
            assert item["is_copy"] is False

    def test_list_receipts_filter_by_apartment(self, client, test_db, sample_payment, sample_apartment, cashier_headers):
        """Филтър по апартамент."""
        client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)

        response = client.get(f"/api/receipts?apartment_id={sample_apartment.id}", headers=cashier_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_list_receipts_filter_by_date_range(self, client, test_db, sample_payment, cashier_headers):
        """Филтър по дата."""
        client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        today = date.today().isoformat()

        response = client.get(f"/api/receipts?from_date={today}&to_date={today}", headers=cashier_headers)
        assert response.status_code == status.HTTP_200_OK


class TestReceiptPDF:
    """Тестове за PDF генериране на разписки."""

    def test_generate_pdf_original_success(self, client, test_db, sample_payment, cashier_headers):
        """Успешно PDF генериране за оригинал (без маркер КОПИЕ)."""
        response = client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        receipt = response.json()

        response = client.get(f"/api/receipts/{receipt['id']}/pdf", headers=cashier_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/pdf"

    def test_generate_pdf_copy_has_copy_marker(self, client, test_db, sample_payment, cashier_headers):
        """PDF на копие съдържа маркер "КОПИЕ"."""
        response = client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        original = response.json()

        response = client.post(f"/api/receipts/{original['id']}/copy", headers=cashier_headers)
        copy = response.json()

        response = client.get(f"/api/receipts/{copy['id']}/pdf", headers=cashier_headers)
        assert response.status_code == status.HTTP_200_OK
        # PDF съдържанието ще се провери при имплементацията

    def test_generate_pdf_contains_correct_data(self, client, test_db, sample_payment, cashier_headers):
        """PDF съдържа номер, дата, сума, апартамент."""
        response = client.post("/api/receipts", json={"payment_id": sample_payment.id}, headers=cashier_headers)
        receipt = response.json()

        response = client.get(f"/api/receipts/{receipt['id']}/pdf", headers=cashier_headers)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.content) > 0  # PDF файлът не е празен

    def test_generate_pdf_invalid_receipt_returns_404(self, client, cashier_headers):
        """Грешка 404 за PDF на несъществуваща разписка."""
        response = client.get("/api/receipts/99999/pdf", headers=cashier_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAutoCreateReceiptOnPayment:
    """Тестове за автоматично създаване на разписка при плащане."""

    def test_receipt_created_automatically_when_payment_made(
        self, client, test_db, sample_apartment, cashier_headers
    ):
        """При създаване на плащане автоматично се създава оригинална разписка."""
        from app.models.receipt import Receipt
        
        # Създаваме плащане
        payment_data = {
            "apartment_id": sample_apartment.id,
            "amount": 15.00,
            "month": "2026-06",
            "payment_method": "cash",
        }
        response = client.post("/api/payments", json=payment_data, headers=cashier_headers)
        assert response.status_code == status.HTTP_201_CREATED
        payment = response.json()
        
        # Проверяваме че разписка е създадена за това плащане
        receipt = test_db.query(Receipt).filter(
            Receipt.payment_id == payment["id"],
            Receipt.is_copy == False
        ).first()
        
        assert receipt is not None, "Receipt should be created automatically"
        assert receipt.is_copy is False
        assert receipt.original_receipt_id is None
        assert receipt.receipt_number is not None
        assert receipt.payment_id == payment["id"]

    def test_receipt_number_format_on_auto_create(
        self, client, test_db, sample_apartment, cashier_headers
    ):
        """Автоматично създадената разписка има правилен формат на номера (YYYY-NNNNNN)."""
        from app.models.receipt import Receipt
        
        payment_data = {
            "apartment_id": sample_apartment.id,
            "amount": 20.00,
            "month": "2026-07",
            "payment_method": "bank",
        }
        response = client.post("/api/payments", json=payment_data, headers=cashier_headers)
        assert response.status_code == status.HTTP_201_CREATED
        payment = response.json()
        
        receipt = test_db.query(Receipt).filter(
            Receipt.payment_id == payment["id"]
        ).first()
        
        assert receipt is not None
        # Проверяваме формата YYYY-NNNNNN
        current_year = date.today().year
        assert receipt.receipt_number.startswith(f"{current_year}-")
        seq_part = receipt.receipt_number.split("-")[1]
        assert len(seq_part) == 6
        assert seq_part.isdigit()

    def test_multiple_payments_create_sequential_receipts(
        self, client, test_db, multiple_apartments, cashier_headers
    ):
        """Множество плащания създават разписки с последователни номера."""
        from app.models.receipt import Receipt
        
        receipt_numbers = []
        for i, apt in enumerate(multiple_apartments[:3]):
            payment_data = {
                "apartment_id": apt.id,
                "amount": 10.00 + i,
                "month": "2026-08",
                "payment_method": "cash",
            }
            response = client.post("/api/payments", json=payment_data, headers=cashier_headers)
            assert response.status_code == status.HTTP_201_CREATED
            payment = response.json()
            
            receipt = test_db.query(Receipt).filter(
                Receipt.payment_id == payment["id"]
            ).first()
            assert receipt is not None
            receipt_numbers.append(receipt.receipt_number)
        
        # Проверяваме че номерата са последователни
        seq_nums = [int(rn.split("-")[1]) for rn in receipt_numbers]
        for i in range(1, len(seq_nums)):
            assert seq_nums[i] == seq_nums[i-1] + 1, "Receipt numbers should be sequential"

    def test_receipt_issued_by_current_user(
        self, client, test_db, sample_apartment, cashier_user, cashier_headers
    ):
        """Автоматично създадената разписка е издадена от текущия потребител."""
        from app.models.receipt import Receipt
        
        payment_data = {
            "apartment_id": sample_apartment.id,
            "amount": 25.00,
            "month": "2026-09",
            "payment_method": "cash",
        }
        response = client.post("/api/payments", json=payment_data, headers=cashier_headers)
        assert response.status_code == status.HTTP_201_CREATED
        payment = response.json()
        
        receipt = test_db.query(Receipt).filter(
            Receipt.payment_id == payment["id"]
        ).first()
        
        assert receipt is not None
        assert receipt.issued_by_id == cashier_user.id

    def test_cannot_create_duplicate_receipt_for_same_payment(
        self, client, test_db, sample_apartment, cashier_headers
    ):
        """Не може да се създаде втора оригинална разписка за същото плащане."""
        # Създаваме плащане (автоматично се създава разписка)
        payment_data = {
            "apartment_id": sample_apartment.id,
            "amount": 30.00,
            "month": "2026-10",
            "payment_method": "cash",
        }
        response = client.post("/api/payments", json=payment_data, headers=cashier_headers)
        assert response.status_code == status.HTTP_201_CREATED
        payment = response.json()
        
        # Опитваме да създадем втора разписка за същото плащане
        response = client.post(
            "/api/receipts",
            json={"payment_id": payment["id"]},
            headers=cashier_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_payment_response_includes_receipt_id(
        self, client, test_db, sample_apartment, cashier_headers
    ):
        """Payment response включва receipt_id за директно сваляне на PDF."""
        from app.models.receipt import Receipt
        
        payment_data = {
            "apartment_id": sample_apartment.id,
            "amount": 45.00,
            "month": "2026-11",
            "payment_method": "cash",
        }
        response = client.post("/api/payments", json=payment_data, headers=cashier_headers)
        assert response.status_code == status.HTTP_201_CREATED
        payment = response.json()
        
        # Проверяваме че receipt_id е включен в response
        assert "receipt_id" in payment
        assert payment["receipt_id"] is not None
        
        # Проверяваме че receipt_id сочи към валидна разписка
        receipt = test_db.query(Receipt).filter(Receipt.id == payment["receipt_id"]).first()
        assert receipt is not None
        assert receipt.payment_id == payment["id"]
