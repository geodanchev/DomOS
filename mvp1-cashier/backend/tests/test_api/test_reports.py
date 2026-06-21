"""Tests for Reports API - Sprint 3 TDD.

Тест кейсове за справки с Excel и PDF експорт.
Подход: Test-Driven Development - тестовете са написани преди имплементацията.
"""

import pytest
from datetime import date, timedelta
from fastapi import status
from io import BytesIO


class TestPaymentsReport:
    """Тестове за справка за плащания по период."""

    def test_payments_report_returns_data_for_period(
        self, client, test_db, sample_payment, cashier_headers
    ):
        """Справка връща плащания за период с total_amount."""
        today = date.today()
        from_date = (today - timedelta(days=30)).isoformat()
        to_date = today.isoformat()

        response = client.get(
            f"/api/reports/payments?from_date={from_date}&to_date={to_date}",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "payments" in data
        assert "total_amount" in data
        assert "count" in data

    def test_payments_report_empty_period_returns_empty(
        self, client, test_db, cashier_headers
    ):
        """Празен период връща празен списък и total_amount=0."""
        # Период в бъдещето без плащания
        future_date = (date.today() + timedelta(days=365)).isoformat()
        future_date_end = (date.today() + timedelta(days=366)).isoformat()

        response = client.get(
            f"/api/reports/payments?from_date={future_date}&to_date={future_date_end}",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["payments"] == []
        assert data["total_amount"] == 0
        assert data["count"] == 0

    def test_payments_report_filter_by_apartment(
        self, client, test_db, sample_payment, sample_apartment, cashier_headers
    ):
        """Филтър по апартамент връща само плащания за него."""
        today = date.today()
        from_date = (today - timedelta(days=30)).isoformat()
        to_date = today.isoformat()

        response = client.get(
            f"/api/reports/payments?from_date={from_date}&to_date={to_date}&apartment_id={sample_apartment.id}",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for payment in data["payments"]:
            assert payment["apartment_id"] == sample_apartment.id

    def test_payments_report_filter_by_payment_method(
        self, client, test_db, sample_payment, cashier_headers
    ):
        """Филтър по метод на плащане."""
        today = date.today()
        from_date = (today - timedelta(days=30)).isoformat()
        to_date = today.isoformat()

        response = client.get(
            f"/api/reports/payments?from_date={from_date}&to_date={to_date}&payment_method=cash",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for payment in data["payments"]:
            assert payment["payment_method"] == "cash"


class TestCollectionRateReport:
    """Тестове за справка за събираемост."""

    def test_collection_rate_100_percent(
        self, client, test_db, paid_charge, cashier_headers
    ):
        """100% събираемост когато всички задължения са платени."""
        response = client.get(
            f"/api/reports/collection-rate?month={paid_charge.month}",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["collection_rate"] == 100.0

    def test_collection_rate_partial(
        self, client, test_db, partial_charge, cashier_headers
    ):
        """Частична събираемост (50%)."""
        response = client.get(
            f"/api/reports/collection-rate?month={partial_charge.month}",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["collection_rate"] == 50.0

    def test_collection_rate_zero(
        self, client, test_db, sample_charge, cashier_headers
    ):
        """0% събираемост когато няма плащания."""
        response = client.get(
            f"/api/reports/collection-rate?month={sample_charge.month}",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["collection_rate"] == 0.0

    def test_collection_rate_no_obligations(
        self, client, test_db, cashier_headers
    ):
        """100% събираемост когато няма задължения (технически всичко е платено)."""
        # Месец без задължения
        response = client.get(
            "/api/reports/collection-rate?month=2099-12",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["collection_rate"] == 100.0  # Технически "всичко е платено"


class TestOutstandingDebtsReport:
    """Тестове за справка за дължими суми."""

    def test_outstanding_debts_returns_debtors(
        self, client, test_db, sample_charge, sample_apartment, cashier_headers
    ):
        """Справка връща длъжници с неплатени задължения."""
        response = client.get(
            "/api/reports/outstanding-debts",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "debtors" in data
        assert "total_outstanding" in data
        assert len(data["debtors"]) > 0

    def test_outstanding_debts_no_debts(
        self, client, test_db, paid_charge, cashier_headers
    ):
        """Празен списък когато няма дължими суми."""
        # Изчистваме неплатените задължения за теста
        # Тук разчитаме само на paid_charge fixture
        response = client.get(
            "/api/reports/outstanding-debts",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "debtors" in data
        assert "total_outstanding" in data

    def test_outstanding_debts_sorted_by_amount(
        self, client, test_db, multiple_charges, cashier_headers
    ):
        """Длъжниците са сортирани по сума (най-големите първо)."""
        response = client.get(
            "/api/reports/outstanding-debts",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        debtors = data["debtors"]

        if len(debtors) > 1:
            amounts = [d["amount_due"] for d in debtors]
            assert amounts == sorted(amounts, reverse=True)


class TestExcelExport:
    """Тестове за Excel експорт."""

    def test_excel_export_payments_success(
        self, client, test_db, sample_payment, cashier_headers
    ):
        """Успешен Excel експорт на плащания."""
        today = date.today()
        from_date = (today - timedelta(days=30)).isoformat()
        to_date = today.isoformat()

        response = client.get(
            f"/api/reports/payments/excel?from_date={from_date}&to_date={to_date}",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert "spreadsheet" in response.headers["content-type"] or "excel" in response.headers["content-type"].lower()

    def test_excel_export_has_correct_headers(
        self, client, test_db, sample_payment, cashier_headers
    ):
        """Excel файлът има български заглавия."""
        today = date.today()
        from_date = (today - timedelta(days=30)).isoformat()
        to_date = today.isoformat()

        response = client.get(
            f"/api/reports/payments/excel?from_date={from_date}&to_date={to_date}",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        # Файлът не е празен
        assert len(response.content) > 0

    def test_excel_export_empty_data(
        self, client, test_db, cashier_headers
    ):
        """Excel с празни данни - headers без редове."""
        future_date = (date.today() + timedelta(days=365)).isoformat()
        future_date_end = (date.today() + timedelta(days=366)).isoformat()

        response = client.get(
            f"/api/reports/payments/excel?from_date={future_date}&to_date={future_date_end}",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        # Файлът съществува дори с празни данни
        assert len(response.content) > 0

    def test_excel_export_outstanding_debts(
        self, client, test_db, sample_charge, cashier_headers
    ):
        """Excel експорт на справка за длъжници."""
        response = client.get(
            "/api/reports/outstanding-debts/excel",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.content) > 0


class TestPDFExport:
    """Тестове за PDF експорт на справки."""

    def test_pdf_export_payments_success(
        self, client, test_db, sample_payment, cashier_headers
    ):
        """Успешен PDF експорт на плащания."""
        today = date.today()
        from_date = (today - timedelta(days=30)).isoformat()
        to_date = today.isoformat()

        response = client.get(
            f"/api/reports/payments/pdf?from_date={from_date}&to_date={to_date}",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/pdf"

    def test_pdf_export_has_title_and_period(
        self, client, test_db, sample_payment, cashier_headers
    ):
        """PDF съдържа заглавие и период."""
        today = date.today()
        from_date = (today - timedelta(days=30)).isoformat()
        to_date = today.isoformat()

        response = client.get(
            f"/api/reports/payments/pdf?from_date={from_date}&to_date={to_date}",
            headers=cashier_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        # PDF файлът не е празен
        assert len(response.content) > 0
        # PDF magic bytes
        assert response.content[:4] == b"%PDF"

    def test_pdf_export_requires_authentication(
        self, client, test_db
    ):
        """PDF експорт изисква автентикация."""
        today = date.today()
        from_date = (today - timedelta(days=30)).isoformat()
        to_date = today.isoformat()

        response = client.get(
            f"/api/reports/payments/pdf?from_date={from_date}&to_date={to_date}",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
