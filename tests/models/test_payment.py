import pytest
from decimal import Decimal
from app.models.payment import Payment
from app.models.booking import Booking
from app.models.client import Client
from app.enums import BookingStatus, BookingServiceType, ClientType, PaymentStatus, PaymentMethod

def test_payment_creation(db_session):
    """Test Payment model creation linked to a Booking."""
    client = Client(
        first_name="Pay",
        last_name="Tester",
        email="pay@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    booking = Booking(
        reference_number="TG-PAY-123",
        service_type=BookingServiceType.FLIGHT,
        status=BookingStatus.PENDING_PAYMENT,
        client_id=client.id,
        total_service_fee_usd=Decimal("50.00")
    )
    db_session.add(booking)
    db_session.flush()

    payment = Payment(
        booking_id=booking.id,
        amount_usd=Decimal("50.00"),
        method=PaymentMethod.BANK_TRANSFER,
        status=PaymentStatus.CONFIRMED
    )
    db_session.add(payment)
    db_session.commit()

    assert payment.id is not None
    assert payment.booking.reference_number == "TG-PAY-123"
    assert payment.amount_usd == Decimal("50.00")
