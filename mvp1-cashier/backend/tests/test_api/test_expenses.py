"""Tests for Expenses API endpoints.

Тестове за CRUD операции с разходи от фонда:
- Създаване на разход
- Списък с разходи
- Детайли за разход
- Редакция на разход
- Маркиране като платен
- Анулиране
- Баланс на фонда с разходи
"""

import pytest
from decimal import Decimal
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.expense import Expense, ExpenseType, ExpenseStatus
from app.models.payment import Payment


class TestCreateExpense:
    """Tests for POST /api/expenses endpoint."""
    
    def test_create_expense_success(self, client: TestClient, cashier_headers: dict):
        """Test creating a new expense."""
        expense_data = {
            "description": "Ремонт на входна врата",
            "amount": 350.00,
            "expense_type": "repair",
            "vendor": "Врати ЕООД",
            "invoice_number": "INV-2026-001",
        }
        
        response = client.post("/api/expenses", json=expense_data, headers=cashier_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Ремонт на входна врата"
        assert data["amount"] == 350.00
        assert data["expense_type"] == "repair"
        assert data["status"] == "pending"
        assert data["vendor"] == "Врати ЕООД"
        assert data["invoice_number"] == "INV-2026-001"
        assert data["status_display"] == "Очаква плащане"
        assert data["type_display"] == "Ремонт"
        assert data["id"] is not None
    
    def test_create_expense_minimal(self, client: TestClient, cashier_headers: dict):
        """Test creating expense with minimal required fields."""
        expense_data = {
            "description": "Тестов разход",
            "amount": 100.00,
        }
        
        response = client.post("/api/expenses", json=expense_data, headers=cashier_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Тестов разход"
        assert data["amount"] == 100.00
        assert data["expense_type"] == "other"  # default
        assert data["status"] == "pending"
    
    def test_create_expense_invalid_amount(self, client: TestClient, cashier_headers: dict):
        """Test creating expense with invalid amount."""
        expense_data = {
            "description": "Невалиден разход",
            "amount": -50.00,  # negative amount
        }
        
        response = client.post("/api/expenses", json=expense_data, headers=cashier_headers)
        
        assert response.status_code == 422  # validation error
    
    def test_create_expense_empty_description(self, client: TestClient, cashier_headers: dict):
        """Test creating expense with empty description."""
        expense_data = {
            "description": "",
            "amount": 100.00,
        }
        
        response = client.post("/api/expenses", json=expense_data, headers=cashier_headers)
        
        assert response.status_code == 422  # validation error
    
    def test_create_expense_unauthorized(self, client: TestClient):
        """Test creating expense without authentication."""
        expense_data = {
            "description": "Тест",
            "amount": 100.00,
        }
        
        response = client.post("/api/expenses", json=expense_data)
        
        assert response.status_code == 401


class TestListExpenses:
    """Tests for GET /api/expenses endpoint."""
    
    def test_list_expenses_empty(self, client: TestClient, cashier_headers: dict):
        """Test listing expenses when none exist."""
        response = client.get("/api/expenses", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["expenses"] == []
        assert data["total_count"] == 0
        assert data["total_amount"] == 0.0
    
    def test_list_expenses_with_data(
        self, client: TestClient, cashier_headers: dict, multiple_expenses: list[Expense]
    ):
        """Test listing expenses with data."""
        response = client.get("/api/expenses", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 5
        assert len(data["expenses"]) == 5
        # total_amount excludes cancelled (1500 + 150 + 800 + 300 = 2750)
        assert data["total_amount"] == 2750.0
        # total_paid = 1500 + 150 = 1650
        assert data["total_paid"] == 1650.0
        # total_pending = 800 + 300 = 1100
        assert data["total_pending"] == 1100.0
    
    def test_list_expenses_filter_by_status(
        self, client: TestClient, cashier_headers: dict, multiple_expenses: list[Expense]
    ):
        """Test filtering expenses by status."""
        response = client.get("/api/expenses?status=paid", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2  # 2 paid expenses
        for expense in data["expenses"]:
            assert expense["status"] == "paid"
    
    def test_list_expenses_filter_by_type(
        self, client: TestClient, cashier_headers: dict, multiple_expenses: list[Expense]
    ):
        """Test filtering expenses by type."""
        response = client.get("/api/expenses?expense_type=utility", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["expenses"][0]["expense_type"] == "utility"


class TestGetExpense:
    """Tests for GET /api/expenses/{expense_id} endpoint."""
    
    def test_get_expense_success(
        self, client: TestClient, cashier_headers: dict, sample_expense: Expense
    ):
        """Test getting expense by ID."""
        response = client.get(f"/api/expenses/{sample_expense.id}", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_expense.id
        assert data["description"] == "Ремонт на покрив"
        assert data["amount"] == 500.00
        assert data["vendor"] == "Строител ООД"
    
    def test_get_expense_not_found(self, client: TestClient, cashier_headers: dict):
        """Test getting non-existent expense."""
        response = client.get("/api/expenses/99999", headers=cashier_headers)
        
        assert response.status_code == 404
        assert "не е намерен" in response.json()["detail"]


class TestUpdateExpense:
    """Tests for PATCH /api/expenses/{expense_id} endpoint."""
    
    def test_update_expense_success(
        self, client: TestClient, cashier_headers: dict, sample_expense: Expense
    ):
        """Test updating expense."""
        update_data = {
            "description": "Ремонт на покрив - актуализирано",
            "amount": 550.00,
        }
        
        response = client.patch(
            f"/api/expenses/{sample_expense.id}",
            json=update_data,
            headers=cashier_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Ремонт на покрив - актуализирано"
        assert data["amount"] == 550.00
    
    def test_update_expense_partial(
        self, client: TestClient, cashier_headers: dict, sample_expense: Expense
    ):
        """Test partial update of expense."""
        update_data = {
            "vendor": "Нов Строител ООД",
        }
        
        response = client.patch(
            f"/api/expenses/{sample_expense.id}",
            json=update_data,
            headers=cashier_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["vendor"] == "Нов Строител ООД"
        assert data["description"] == "Ремонт на покрив"  # unchanged
    
    def test_update_cancelled_expense_fails(
        self, client: TestClient, cashier_headers: dict, test_db: Session, sample_expense: Expense
    ):
        """Test that cancelled expenses cannot be updated."""
        sample_expense.status = ExpenseStatus.CANCELLED
        test_db.commit()
        
        update_data = {"description": "Опит за редакция"}
        
        response = client.patch(
            f"/api/expenses/{sample_expense.id}",
            json=update_data,
            headers=cashier_headers
        )
        
        assert response.status_code == 400
        assert "анулиран" in response.json()["detail"]


class TestMarkExpensePaid:
    """Tests for POST /api/expenses/{expense_id}/pay endpoint."""
    
    def test_mark_expense_paid_success(
        self, client: TestClient, cashier_headers: dict, sample_expense: Expense
    ):
        """Test marking expense as paid."""
        response = client.post(
            f"/api/expenses/{sample_expense.id}/pay",
            headers=cashier_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paid"
        assert data["status_display"] == "Платен"
        assert data["paid_date"] is not None
    
    def test_mark_already_paid_fails(
        self, client: TestClient, cashier_headers: dict, paid_expense: Expense
    ):
        """Test that already paid expenses cannot be marked as paid again."""
        response = client.post(
            f"/api/expenses/{paid_expense.id}/pay",
            headers=cashier_headers
        )
        
        assert response.status_code == 400
        assert "вече е платен" in response.json()["detail"]
    
    def test_mark_cancelled_as_paid_fails(
        self, client: TestClient, cashier_headers: dict, test_db: Session, sample_expense: Expense
    ):
        """Test that cancelled expenses cannot be marked as paid."""
        sample_expense.status = ExpenseStatus.CANCELLED
        test_db.commit()
        
        response = client.post(
            f"/api/expenses/{sample_expense.id}/pay",
            headers=cashier_headers
        )
        
        assert response.status_code == 400
        assert "анулиран" in response.json()["detail"]


class TestCancelExpense:
    """Tests for POST /api/expenses/{expense_id}/cancel endpoint."""
    
    def test_cancel_expense_success(
        self, client: TestClient, cashier_headers: dict, sample_expense: Expense
    ):
        """Test cancelling expense."""
        response = client.post(
            f"/api/expenses/{sample_expense.id}/cancel",
            headers=cashier_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["status_display"] == "Анулиран"
    
    def test_cancel_already_cancelled_fails(
        self, client: TestClient, cashier_headers: dict, test_db: Session, sample_expense: Expense
    ):
        """Test that already cancelled expenses cannot be cancelled again."""
        sample_expense.status = ExpenseStatus.CANCELLED
        test_db.commit()
        
        response = client.post(
            f"/api/expenses/{sample_expense.id}/cancel",
            headers=cashier_headers
        )
        
        assert response.status_code == 400
        assert "вече е анулиран" in response.json()["detail"]


class TestExpensesSummary:
    """Tests for GET /api/expenses/summary endpoint."""
    
    def test_expenses_summary(
        self, client: TestClient, cashier_headers: dict, multiple_expenses: list[Expense]
    ):
        """Test getting expenses summary by type."""
        response = client.get("/api/expenses/summary", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        for summary in data:
            assert "expense_type" in summary
            assert "type_display" in summary
            assert "count" in summary
            assert "total_amount" in summary


class TestFundBalanceWithExpenses:
    """Tests for GET /api/dashboard/fund endpoint with expenses."""
    
    def test_fund_balance_no_expenses(
        self, client: TestClient, cashier_headers: dict, test_db: Session, sample_apartment
    ):
        """Test fund balance with payments but no expenses."""
        # Create a payment
        payment = Payment(
            apartment_id=sample_apartment.id,
            amount=Decimal("100.00"),
            month="2026-06",
        )
        test_db.add(payment)
        test_db.commit()
        
        response = client.get("/api/dashboard/fund", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_collected_all_time"] == 100.00
        assert data["total_expenses"] == 0.0
        assert data["current_balance"] == 100.00
    
    def test_fund_balance_with_paid_expenses(
        self, client: TestClient, cashier_headers: dict, test_db: Session,
        sample_apartment, paid_expense: Expense
    ):
        """Test fund balance calculation with paid expenses."""
        # Create a payment
        payment = Payment(
            apartment_id=sample_apartment.id,
            amount=Decimal("500.00"),
            month="2026-06",
        )
        test_db.add(payment)
        test_db.commit()
        
        response = client.get("/api/dashboard/fund", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_collected_all_time"] == 500.00
        assert data["total_expenses"] == 200.00  # paid_expense amount
        assert data["current_balance"] == 300.00  # 500 - 200
    
    def test_fund_balance_excludes_pending_expenses(
        self, client: TestClient, cashier_headers: dict, test_db: Session,
        sample_apartment, sample_expense: Expense
    ):
        """Test that pending expenses are NOT subtracted from fund balance."""
        # sample_expense is PENDING, not PAID
        payment = Payment(
            apartment_id=sample_apartment.id,
            amount=Decimal("1000.00"),
            month="2026-06",
        )
        test_db.add(payment)
        test_db.commit()
        
        response = client.get("/api/dashboard/fund", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_collected_all_time"] == 1000.00
        assert data["total_expenses"] == 0.0  # pending not counted
        assert data["current_balance"] == 1000.00
    
    def test_fund_balance_excludes_cancelled_expenses(
        self, client: TestClient, cashier_headers: dict, test_db: Session,
        sample_apartment, sample_expense: Expense
    ):
        """Test that cancelled expenses are NOT subtracted from fund balance."""
        sample_expense.status = ExpenseStatus.CANCELLED
        test_db.commit()
        
        payment = Payment(
            apartment_id=sample_apartment.id,
            amount=Decimal("800.00"),
            month="2026-06",
        )
        test_db.add(payment)
        test_db.commit()
        
        response = client.get("/api/dashboard/fund", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_collected_all_time"] == 800.00
        assert data["total_expenses"] == 0.0  # cancelled not counted
        assert data["current_balance"] == 800.00