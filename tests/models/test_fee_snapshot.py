import pytest
import datetime
from decimal import Decimal
from app.models import ServiceFeeSnapshot, FlightBooking, Client
from app.enums import BookingStatus, BookingServiceType, ClientType, FeeType, BookingChannel

def test_service_fee_snapshot_creation(db_session):
    """Test ServiceFeeSnapshot and its 1:1 link to Booking."""
    client = Client(
        first_name="Snapshot",
        last_name="User",
        email="snap@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    booking = FlightBooking(
        reference_number="TG-2024-FEE",
        status=BookingStatus.PENDING_PAYMENT,
        client_id=client.id,
        total_service_fee_usd=Decimal("50.00"),
        origin_iata="JFK",
        destination_iata="DXB",
        departure_date=datetime.date(2024, 6, 1)
    )
    db_session.add(booking)
    db_session.flush()

    snapshot = ServiceFeeSnapshot(
        booking_id=booking.id,
        fee_type=FeeType.DOMESTIC_FLIGHT,
        fee_label="Domestic Flight Fee",
        base_amount_usd=Decimal("50.00"),
        applied_amount_usd=Decimal("50.00"),
        channel=BookingChannel.WHATSAPP
    )
    db_session.add(snapshot)
    db_session.flush()

    assert snapshot.id is not None
    assert snapshot.booking.reference_number == "TG-2024-FEE"
    assert snapshot.applied_amount_usd == Decimal("50.00")
