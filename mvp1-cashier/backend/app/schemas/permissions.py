"""UI Permissions schemas.

Defines the structure for role-based UI permissions.
These permissions are for UI convenience only - backend always validates access.
"""

from pydantic import BaseModel
from app.models.user import UserRole


class ApartmentPermissions(BaseModel):
    """Permissions for apartment management."""
    view: bool = True
    create: bool = False
    edit: bool = False
    delete: bool = False


class PaymentPermissions(BaseModel):
    """Permissions for payment operations."""
    view: bool = True
    create: bool = False
    void: bool = False


class ObligationPermissions(BaseModel):
    """Permissions for obligation management."""
    view: bool = True
    create: bool = False
    edit: bool = False
    delete: bool = False
    generate_monthly: bool = False


class ExpensePermissions(BaseModel):
    """Permissions for expense management."""
    view: bool = True
    create: bool = False
    edit: bool = False
    delete: bool = False


class ReportPermissions(BaseModel):
    """Permissions for reports."""
    view: bool = True
    export: bool = True


class SchedulerPermissions(BaseModel):
    """Permissions for scheduler jobs."""
    manage: bool = False


class UserManagementPermissions(BaseModel):
    """Permissions for user management."""
    manage: bool = False


class UIPermissions(BaseModel):
    """Complete UI permissions object.
    
    This is returned with the login response to help the frontend
    determine which UI elements to show/hide based on user role.
    
    IMPORTANT: These are for UI convenience only.
    Backend always validates permissions on every request.
    """
    apartments: ApartmentPermissions
    payments: PaymentPermissions
    obligations: ObligationPermissions
    expenses: ExpensePermissions
    reports: ReportPermissions
    scheduler: SchedulerPermissions
    users: UserManagementPermissions


def get_permissions_for_role(role: UserRole) -> UIPermissions:
    """Generate UI permissions based on user role.
    
    Permission matrix:
    - ADMIN: Full access to everything
    - CASHIER: View all, create payments/obligations/expenses, no edit/delete/void
    - VIEWER: View only, no write operations
    
    Args:
        role: The user's role
        
    Returns:
        UIPermissions object with appropriate permissions
    """
    if role == UserRole.ADMIN:
        return UIPermissions(
            apartments=ApartmentPermissions(
                view=True,
                create=True,
                edit=True,
                delete=True,
            ),
            payments=PaymentPermissions(
                view=True,
                create=True,
                void=True,
            ),
            obligations=ObligationPermissions(
                view=True,
                create=True,
                edit=True,
                delete=True,
                generate_monthly=True,
            ),
            expenses=ExpensePermissions(
                view=True,
                create=True,
                edit=True,
                delete=True,
            ),
            reports=ReportPermissions(
                view=True,
                export=True,
            ),
            scheduler=SchedulerPermissions(
                manage=True,
            ),
            users=UserManagementPermissions(
                manage=True,
            ),
        )
    
    elif role == UserRole.CASHIER:
        return UIPermissions(
            apartments=ApartmentPermissions(
                view=True,
                create=False,
                edit=False,
                delete=False,
            ),
            payments=PaymentPermissions(
                view=True,
                create=True,
                void=False,
            ),
            obligations=ObligationPermissions(
                view=True,
                create=True,
                edit=False,
                delete=False,
                generate_monthly=False,
            ),
            expenses=ExpensePermissions(
                view=True,
                create=True,
                edit=False,
                delete=False,
            ),
            reports=ReportPermissions(
                view=True,
                export=True,
            ),
            scheduler=SchedulerPermissions(
                manage=False,
            ),
            users=UserManagementPermissions(
                manage=False,
            ),
        )
    
    else:  # VIEWER
        return UIPermissions(
            apartments=ApartmentPermissions(
                view=True,
                create=False,
                edit=False,
                delete=False,
            ),
            payments=PaymentPermissions(
                view=True,
                create=False,
                void=False,
            ),
            obligations=ObligationPermissions(
                view=True,
                create=False,
                edit=False,
                delete=False,
                generate_monthly=False,
            ),
            expenses=ExpensePermissions(
                view=True,
                create=False,
                edit=False,
                delete=False,
            ),
            reports=ReportPermissions(
                view=True,
                export=True,
            ),
            scheduler=SchedulerPermissions(
                manage=False,
            ),
            users=UserManagementPermissions(
                manage=False,
            ),
        )
