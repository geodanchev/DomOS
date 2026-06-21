"""Tests for MonthlyCharge model."""

import pytest
from sqlalchemy.orm import Session

from app.models.monthly_charge import MonthlyCharge, ChargeStatus
from app.models.apartment import Apartment


class TestChargeStatus:
    """Tests for ChargeStatus enum."""
    
    def test_status_values(self):
        """Should have correct status values."""
        assert ChargeStatus.PAID.value == "paid"
        assert ChargeStatus.PARTIAL.value == "partial"
        assert ChargeStatus.UNPAID.value == "unpaid"
    
    def test_status_is_string_enum(self):
        """Status should be string enum."""
        assert isinstance(ChargeStatus.PAID, str)
        assert ChargeStatus.PAID == "paid"


class TestMonthlyChargeModel:
    """Tests for MonthlyCharge model."""
    
    def test_create_charge(self, test_db: Session, sample_apartment: Apartment):
        """Should create charge with correct fields."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=0,
            status=ChargeStatus.UNPAID,
        )
        test_db.add(charge)
        test_db.commit()
        test_db.refresh(charge)
        
        assert charge.id is not None
        assert charge.apartment_id == sample_apartment.id
        assert charge.month == "2027-01"
        assert float(charge.amount_due) == 15.00
        assert float(charge.amount_paid) == 0
        assert charge.status == ChargeStatus.UNPAID
    
    def test_charge_repr(self, test_db: Session, sample_apartment: Apartment):
        """Should have useful __repr__."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            status=ChargeStatus.UNPAID,
        )
        test_db.add(charge)
        test_db.commit()
        
        repr_str = repr(charge)
        assert "MonthlyCharge" in repr_str
        assert "2027-01" in repr_str
        assert "unpaid" in repr_str
    
    def test_charge_apartment_relationship(self, test_db: Session, sample_apartment: Apartment):
        """Should have correct apartment relationship."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
        )
        test_db.add(charge)
        test_db.commit()
        test_db.refresh(charge)
        
        assert charge.apartment is not None
        assert charge.apartment.id == sample_apartment.id
        assert charge.apartment.number == "1"


class TestAmountRemaining:
    """Tests for amount_remaining property."""
    
    def test_amount_remaining_unpaid(self, test_db: Session, sample_apartment: Apartment):
        """Should return full amount when unpaid."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=0,
        )
        
        assert charge.amount_remaining == 15.00
    
    def test_amount_remaining_partial(self, test_db: Session, sample_apartment: Apartment):
        """Should return difference when partial."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=10.00,
        )
        
        assert charge.amount_remaining == 5.00
    
    def test_amount_remaining_paid(self, test_db: Session, sample_apartment: Apartment):
        """Should return zero when fully paid."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=15.00,
        )
        
        assert charge.amount_remaining == 0
    
    def test_amount_remaining_overpaid(self, test_db: Session, sample_apartment: Apartment):
        """Should return negative when overpaid."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=20.00,
        )
        
        assert charge.amount_remaining == -5.00


class TestUpdateStatus:
    """Tests for update_status() method - core business logic."""
    
    def test_update_status_to_paid(self, test_db: Session, sample_apartment: Apartment):
        """Should set PAID when amount_paid >= amount_due."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=15.00,
            status=ChargeStatus.UNPAID,
        )
        
        charge.update_status()
        
        assert charge.status == ChargeStatus.PAID
    
    def test_update_status_to_paid_overpayment(self, test_db: Session, sample_apartment: Apartment):
        """Should set PAID when overpaid."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=20.00,
            status=ChargeStatus.UNPAID,
        )
        
        charge.update_status()
        
        assert charge.status == ChargeStatus.PAID
    
    def test_update_status_to_partial(self, test_db: Session, sample_apartment: Apartment):
        """Should set PARTIAL when 0 < amount_paid < amount_due."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=7.50,
            status=ChargeStatus.UNPAID,
        )
        
        charge.update_status()
        
        assert charge.status == ChargeStatus.PARTIAL
    
    def test_update_status_to_partial_minimal(self, test_db: Session, sample_apartment: Apartment):
        """Should set PARTIAL even for tiny payment."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=0.01,
            status=ChargeStatus.UNPAID,
        )
        
        charge.update_status()
        
        assert charge.status == ChargeStatus.PARTIAL
    
    def test_update_status_to_unpaid(self, test_db: Session, sample_apartment: Apartment):
        """Should set UNPAID when amount_paid == 0."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=0,
            status=ChargeStatus.PAID,  # Start as paid
        )
        
        charge.update_status()
        
        assert charge.status == ChargeStatus.UNPAID
    
    def test_update_status_from_paid_to_partial(self, test_db: Session, sample_apartment: Apartment):
        """Should transition from PAID to PARTIAL correctly."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=15.00,
            status=ChargeStatus.PAID,
        )
        
        # Simulate refund/correction
        charge.amount_paid = 10.00
        charge.update_status()
        
        assert charge.status == ChargeStatus.PARTIAL
    
    def test_update_status_idempotent(self, test_db: Session, sample_apartment: Apartment):
        """Calling update_status() multiple times should be safe."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=15.00,
        )
        
        charge.update_status()
        charge.update_status()
        charge.update_status()
        
        assert charge.status == ChargeStatus.PAID
    
    def test_update_status_exact_boundary(self, test_db: Session, sample_apartment: Apartment):
        """Should handle exact payment amount."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=15.00,
            amount_paid=14.99,
        )
        charge.update_status()
        assert charge.status == ChargeStatus.PARTIAL
        
        charge.amount_paid = 15.00
        charge.update_status()
        assert charge.status == ChargeStatus.PAID


class TestChargeWithPaymentFlow:
    """Integration tests simulating real payment flow."""
    
    def test_incremental_payments(
        self,
        test_db: Session,
        sample_apartment: Apartment,
    ):
        """Simulating multiple small payments."""
        charge = MonthlyCharge(
            apartment_id=sample_apartment.id,
            month="2027-01",
            amount_due=30.00,
            amount_paid=0,
            status=ChargeStatus.UNPAID,
        )
        test_db.add(charge)
        test_db.commit()
        
        # First payment: 10 лв
        charge.amount_paid = float(charge.amount_paid) + 10.00
        charge.update_status()
        assert charge.status == ChargeStatus.PARTIAL
        assert charge.amount_remaining == 20.00
        
        # Second payment: 10 лв
        charge.amount_paid = float(charge.amount_paid) + 10.00
        charge.update_status()
        assert charge.status == ChargeStatus.PARTIAL
        assert charge.amount_remaining == 10.00
        
        # Final payment: 10 лв
        charge.amount_paid = float(charge.amount_paid) + 10.00
        charge.update_status()
        assert charge.status == ChargeStatus.PAID
        assert charge.amount_remaining == 0
        
        test_db.commit()
