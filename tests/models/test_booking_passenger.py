import pytest
import datetime
from decimal import Decimal
from app.models import BookingPassenger, FlightBooking, Client
from app.enums import BookingStatus, BookingServiceType, ClientType

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

    booking = FlightBooking(
        reference_number="TG-2024-PAX",
        status=BookingStatus.PENDING_PAYMENT,
        client_id=client.id,
        total_service_fee_usd=Decimal("25.00"),
        origin_iata="JFK",
        destination_iata="DXB",
        departure_date=datetime.date(2024, 6, 1)
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
    db_session.flush()

    assert passenger.id is not None
    assert passenger.full_name == "Jane Doe"
    assert passenger.booking.reference_number == "TG-2024-PAX"
