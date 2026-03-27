import pytest
from decimal import Decimal
from app.models.fee_snapshot import ServiceFeeSnapshot
from app.models.booking import Booking
from app.models.client import Client
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

    booking = Booking(
        reference_number="TG-SNAP-001",
        service_type=BookingServiceType.FLIGHT,
        status=BookingStatus.PENDING_PAYMENT,
        client_id=client.id,
        total_service_fee_usd=Decimal("50.00")
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
    db_session.commit()

    assert snapshot.id is not None
    assert snapshot.booking.reference_number == "TG-SNAP-001"
    assert snapshot.applied_amount_usd == Decimal("50.00")
