"""Tests for UI permissions in login response."""

import pytest
from fastapi.testclient import TestClient

from app.models.user import UserRole
from app.schemas.permissions import (
    get_permissions_for_role,
    UIPermissions,
    ApartmentPermissions,
    PaymentPermissions,
    ObligationPermissions,
    ExpensePermissions,
    ReportPermissions,
    SchedulerPermissions,
    UserManagementPermissions,
)


class TestGetPermissionsForRole:
    """Test the get_permissions_for_role function."""
    
    def test_admin_has_full_permissions(self):
        """Admin should have all permissions enabled."""
        perms = get_permissions_for_role(UserRole.ADMIN)
        
        # Apartments - full access
        assert perms.apartments.view is True
        assert perms.apartments.create is True
        assert perms.apartments.edit is True
        assert perms.apartments.delete is True
        
        # Payments - full access including void
        assert perms.payments.view is True
        assert perms.payments.create is True
        assert perms.payments.void is True
        
        # Obligations - full access including generate_monthly
        assert perms.obligations.view is True
        assert perms.obligations.create is True
        assert perms.obligations.edit is True
        assert perms.obligations.delete is True
        assert perms.obligations.generate_monthly is True
        
        # Expenses - full access
        assert perms.expenses.view is True
        assert perms.expenses.create is True
        assert perms.expenses.edit is True
        assert perms.expenses.delete is True
        
        # Reports - full access
        assert perms.reports.view is True
        assert perms.reports.export is True
        
        # Scheduler - can manage
        assert perms.scheduler.manage is True
        
        # Users - can manage
        assert perms.users.manage is True
    
    def test_cashier_has_limited_permissions(self):
        """Cashier should have view all + create payments/obligations/expenses."""
        perms = get_permissions_for_role(UserRole.CASHIER)
        
        # Apartments - view only
        assert perms.apartments.view is True
        assert perms.apartments.create is False
        assert perms.apartments.edit is False
        assert perms.apartments.delete is False
        
        # Payments - view + create, no void
        assert perms.payments.view is True
        assert perms.payments.create is True
        assert perms.payments.void is False
        
        # Obligations - view + create, no edit/delete/generate
        assert perms.obligations.view is True
        assert perms.obligations.create is True
        assert perms.obligations.edit is False
        assert perms.obligations.delete is False
        assert perms.obligations.generate_monthly is False
        
        # Expenses - view + create, no edit/delete
        assert perms.expenses.view is True
        assert perms.expenses.create is True
        assert perms.expenses.edit is False
        assert perms.expenses.delete is False
        
        # Reports - full access
        assert perms.reports.view is True
        assert perms.reports.export is True
        
        # Scheduler - no access
        assert perms.scheduler.manage is False
        
        # Users - no access
        assert perms.users.manage is False
    
    def test_viewer_has_view_only_permissions(self):
        """Viewer should only have view permissions."""
        perms = get_permissions_for_role(UserRole.VIEWER)
        
        # Apartments - view only
        assert perms.apartments.view is True
        assert perms.apartments.create is False
        assert perms.apartments.edit is False
        assert perms.apartments.delete is False
        
        # Payments - view only
        assert perms.payments.view is True
        assert perms.payments.create is False
        assert perms.payments.void is False
        
        # Obligations - view only
        assert perms.obligations.view is True
        assert perms.obligations.create is False
        assert perms.obligations.edit is False
        assert perms.obligations.delete is False
        assert perms.obligations.generate_monthly is False
        
        # Expenses - view only
        assert perms.expenses.view is True
        assert perms.expenses.create is False
        assert perms.expenses.edit is False
        assert perms.expenses.delete is False
        
        # Reports - view + export (allowed for all)
        assert perms.reports.view is True
        assert perms.reports.export is True
        
        # Scheduler - no access
        assert perms.scheduler.manage is False
        
        # Users - no access
        assert perms.users.manage is False
    
    def test_permissions_returns_ui_permissions_type(self):
        """Function should return UIPermissions instance."""
        for role in UserRole:
            perms = get_permissions_for_role(role)
            assert isinstance(perms, UIPermissions)


class TestLoginReturnsPermissions:
    """Test that login endpoint returns permissions."""
    
    def test_login_response_includes_permissions(self, client: TestClient, admin_user):
        """Login response should include permissions object."""
        # Login as admin (using fixture credentials)
        response = client.post(
            "/api/auth/login",
            data={"username": "test_admin", "password": "admin123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check permissions is in response
        assert "permissions" in data
        perms = data["permissions"]
        
        # Check structure
        assert "apartments" in perms
        assert "payments" in perms
        assert "obligations" in perms
        assert "expenses" in perms
        assert "reports" in perms
        assert "scheduler" in perms
        assert "users" in perms
    
    def test_admin_login_returns_admin_permissions(self, client: TestClient, admin_user):
        """Admin login should return full permissions."""
        response = client.post(
            "/api/auth/login",
            data={"username": "test_admin", "password": "admin123"}
        )
        
        assert response.status_code == 200
        perms = response.json()["permissions"]
        
        # Admin should have full access
        assert perms["apartments"]["edit"] is True
        assert perms["apartments"]["delete"] is True
        assert perms["payments"]["void"] is True
        assert perms["obligations"]["generate_monthly"] is True
        assert perms["scheduler"]["manage"] is True
        assert perms["users"]["manage"] is True
    
    def test_cashier_login_returns_cashier_permissions(self, client: TestClient, cashier_user):
        """Cashier login should return limited permissions."""
        response = client.post(
            "/api/auth/login",
            data={"username": "cecka", "password": "1234"}
        )
        
        assert response.status_code == 200
        perms = response.json()["permissions"]
        
        # Cashier should have create but not edit/delete
        assert perms["apartments"]["view"] is True
        assert perms["apartments"]["edit"] is False
        assert perms["payments"]["create"] is True
        assert perms["payments"]["void"] is False
        assert perms["obligations"]["create"] is True
        assert perms["obligations"]["edit"] is False
        assert perms["scheduler"]["manage"] is False
    
    def test_viewer_login_returns_viewer_permissions(self, client: TestClient, admin_user, admin_headers):
        """Viewer login should return view-only permissions."""
        # First create a viewer user
        response = client.post(
            "/api/auth/register",
            headers=admin_headers,
            json={
                "username": "viewer_test",
                "password": "viewer123",
                "display_name": "Test Viewer",
                "role": "viewer"
            }
        )
        assert response.status_code == 201
        
        # Login as viewer
        response = client.post(
            "/api/auth/login",
            data={"username": "viewer_test", "password": "viewer123"}
        )
        
        assert response.status_code == 200
        perms = response.json()["permissions"]
        
        # Viewer should only have view access
        assert perms["apartments"]["view"] is True
        assert perms["apartments"]["create"] is False
        assert perms["payments"]["view"] is True
        assert perms["payments"]["create"] is False
        assert perms["obligations"]["view"] is True
        assert perms["obligations"]["create"] is False
        assert perms["scheduler"]["manage"] is False


class TestPermissionsSchemaStructure:
    """Test that permissions schema has correct structure."""
    
    def test_apartment_permissions_fields(self):
        """ApartmentPermissions should have view, create, edit, delete."""
        perms = ApartmentPermissions()
        assert hasattr(perms, 'view')
        assert hasattr(perms, 'create')
        assert hasattr(perms, 'edit')
        assert hasattr(perms, 'delete')
    
    def test_payment_permissions_fields(self):
        """PaymentPermissions should have view, create, void."""
        perms = PaymentPermissions()
        assert hasattr(perms, 'view')
        assert hasattr(perms, 'create')
        assert hasattr(perms, 'void')
    
    def test_obligation_permissions_fields(self):
        """ObligationPermissions should have all required fields."""
        perms = ObligationPermissions()
        assert hasattr(perms, 'view')
        assert hasattr(perms, 'create')
        assert hasattr(perms, 'edit')
        assert hasattr(perms, 'delete')
        assert hasattr(perms, 'generate_monthly')
    
    def test_expense_permissions_fields(self):
        """ExpensePermissions should have view, create, edit, delete."""
        perms = ExpensePermissions()
        assert hasattr(perms, 'view')
        assert hasattr(perms, 'create')
        assert hasattr(perms, 'edit')
        assert hasattr(perms, 'delete')
    
    def test_report_permissions_fields(self):
        """ReportPermissions should have view, export."""
        perms = ReportPermissions()
        assert hasattr(perms, 'view')
        assert hasattr(perms, 'export')
    
    def test_scheduler_permissions_fields(self):
        """SchedulerPermissions should have manage."""
        perms = SchedulerPermissions()
        assert hasattr(perms, 'manage')
    
    def test_user_management_permissions_fields(self):
        """UserManagementPermissions should have manage."""
        perms = UserManagementPermissions()
        assert hasattr(perms, 'manage')
    
    def test_ui_permissions_has_all_categories(self):
        """UIPermissions should have all permission categories."""
        perms = get_permissions_for_role(UserRole.ADMIN)
        assert hasattr(perms, 'apartments')
        assert hasattr(perms, 'payments')
        assert hasattr(perms, 'obligations')
        assert hasattr(perms, 'expenses')
        assert hasattr(perms, 'reports')
        assert hasattr(perms, 'scheduler')
        assert hasattr(perms, 'users')


class TestPermissionsJsonSerialization:
    """Test that permissions serialize correctly to JSON."""
    
    def test_permissions_serializes_to_dict(self):
        """Permissions should serialize to a dictionary."""
        perms = get_permissions_for_role(UserRole.ADMIN)
        perms_dict = perms.model_dump()
        
        assert isinstance(perms_dict, dict)
        assert "apartments" in perms_dict
        assert "payments" in perms_dict
    
    def test_nested_permissions_are_dicts(self):
        """Nested permissions should also be dictionaries."""
        perms = get_permissions_for_role(UserRole.CASHIER)
        perms_dict = perms.model_dump()
        
        assert isinstance(perms_dict["apartments"], dict)
        assert isinstance(perms_dict["payments"], dict)
        assert "view" in perms_dict["apartments"]
        assert "create" in perms_dict["payments"]
