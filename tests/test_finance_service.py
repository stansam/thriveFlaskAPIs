import pytest
from app.repository.finance.services import FinanceService
from app.models import ServiceFeeRule
from app.models.enums import PaymentStatus, InvoiceStatus, FeeType, BookingStatus
from app.repository.finance.exceptions import InvalidAmount
from datetime import datetime

def test_process_payment(db_session, booking_factory):
    service = FinanceService(db_session)
    booking = booking_factory(status=BookingStatus.PENDING)
    
    payment = service.process_payment(booking.id, 100.0, "credit_card", "TXN-123")
    
    assert payment.id is not None
    assert payment.status == PaymentStatus.PAID
    assert payment.amount == 100.0
    
    # Check if booking status updated
    db_session.refresh(booking)
    assert booking.status == BookingStatus.CONFIRMED

def test_process_payment_negative_amount(db_session, booking_factory):
    service = FinanceService(db_session)
    booking = booking_factory()
    
    with pytest.raises(InvalidAmount):
        service.process_payment(booking.id, -50.0, "credit_card")

def test_generate_invoice(db_session, booking_factory):
    service = FinanceService(db_session)
    booking = booking_factory()
    
    invoice = service.generate_invoice(booking.id, 500.0)
    
    assert invoice.id is not None
    assert invoice.total_amount == 500.0
    # In DB it stores Date, so datetime comparison might need care if using ==
    # We just check properties
    assert invoice.status == InvoiceStatus.ISSUED
    assert invoice.invoice_number.startswith("INV-")

def test_calculate_fees(db_session):
    service = FinanceService(db_session)
    
    # Setup rules
    rule1 = ServiceFeeRule(
        name="Booking Fee %",
        fee_type=FeeType.FLIGHT_DOMESTIC,
        amount_percent=10.0,
        currency="USD"
    )
    rule2 = ServiceFeeRule(
        name="Fixed Fee",
        fee_type=FeeType.FLIGHT_DOMESTIC,
        amount_fixed=5.0,
        currency="USD"
    )
    db_session.add_all([rule1, rule2])
    db_session.commit()
    
    fees = service.calculate_fees("flight_domestic", 100.0)
    
    assert len(fees) == 2
    # 10% of 100 = 10.0
    # Fixed 5.0
    fee_amounts = sorted([f['amount'] for f in fees])
    assert fee_amounts == [5.0, 10.0]

def test_process_refund(db_session, booking_factory):
    service = FinanceService(db_session)
    booking = booking_factory()
    
    # Create original payment
    original_payment = service.process_payment(booking.id, 100.0, "credit_card")
    
    refund = service.process_refund(original_payment.id, 50.0)
    
    assert refund.id is not None
    assert refund.status == PaymentStatus.REFUNDED
    assert refund.amount == 50.0
