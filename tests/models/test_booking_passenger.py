import pytest
from app.models.booking_passenger import BookingPassenger
from app.models.booking import Booking
from app.models.client import Client
from app.enums import BookingStatus, BookingServiceType, ClientType
from decimal import Decimal

def test_booking_passenger_creation(db_session):
    """Test BookingPassenger creation and relationship."""
    client = Client(
        first_name="Jane",
        last_name="Doe",
        email="jane.passenger@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    booking = Booking(
        reference_number="TG-2024-PAX",
        service_type=BookingServiceType.FLIGHT,
        status=BookingStatus.PENDING_PAYMENT,
        client_id=client.id,
        total_service_fee_usd=Decimal("25.00")
    )
    db_session.add(booking)
    db_session.flush()

    passenger = BookingPassenger(
        booking_id=booking.id,
        first_name="Jane",
        last_name="Doe",
        is_lead_passenger=True
    )
    db_session.add(passenger)
    db_session.commit()

    assert passenger.id is not None
    assert passenger.full_name == "Jane Doe"
    assert passenger.booking.reference_number == "TG-2024-PAX"
