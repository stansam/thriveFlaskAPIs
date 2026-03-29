import pytest
from decimal import Decimal
from app.models import Booking, FlightBooking, Client
from app.enums import BookingStatus, BookingServiceType, ClientType

def test_booking_base_creation(db_session):
    """Test basic Booking model creation via a subclass."""
    # Create a client first
    client = Client(
        first_name="John",
        last_name="Doe",
        email="john.booking@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    # Use a specific subclass to avoid SAWarning: polymorphic_identity mismatch
    booking = FlightBooking(
        reference_number="TG-2024-TEST",
        status=BookingStatus.PENDING_PAYMENT,
        client_id=client.id,
        total_service_fee_usd=Decimal("50.00"),
        currency="USD",
        origin_iata="JFK",
        destination_iata="DXB",
        departure_date=__import__("datetime").date(2024, 6, 1)
    )
    db_session.add(booking)
    db_session.flush()

    assert booking.id is not None
    assert booking.reference_number == "TG-2024-TEST"
    assert booking.amount_due == Decimal("50.00")
