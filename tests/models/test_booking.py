import pytest
from decimal import Decimal
from app.models.booking import Booking
from app.models.client import Client
from app.enums import BookingStatus, BookingServiceType, ClientType

def test_booking_base_creation(db_session):
    """Test basic Booking model creation (as parent)."""
    # Create a client first
    client = Client(
        first_name="John",
        last_name="Doe",
        email="john.booking@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    booking = Booking(
        reference_number="TG-2024-TEST",
        service_type=BookingServiceType.FLIGHT,
        status=BookingStatus.PENDING_PAYMENT,
        client_id=client.id,
        total_service_fee_usd=Decimal("50.00"),
        currency="USD"
    )
    db_session.add(booking)
    db_session.commit()

    assert booking.id is not None
    assert booking.reference_number == "TG-2024-TEST"
    assert booking.amount_due == Decimal("50.00")
