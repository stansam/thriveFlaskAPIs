import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from app.models.flight_booking import FlightBooking, FlightSegment
from app.models.client import Client
from app.enums import BookingStatus, BookingServiceType, ClientType, FlightCabin

def test_flight_booking_and_segments(db_session):
    """Test FlightBooking and its child FlightSegments."""
    client = Client(
        first_name="Flight",
        last_name="Tester",
        email="flight.test@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    flight_booking = FlightBooking(
        reference_number="TG-FLT-123",
        service_type=BookingServiceType.FLIGHT,
        status=BookingStatus.PENDING_PAYMENT,
        client_id=client.id,
        total_service_fee_usd=Decimal("50.00"),
        origin_iata="JFK",
        destination_iata="DXB",
        departure_date=date(2024, 6, 1),
        is_round_trip=True,
        cabin_class=FlightCabin.ECONOMY,
        is_international=True
    )
    db_session.add(flight_booking)
    db_session.flush()

    segment = FlightSegment(
        flight_booking_id=flight_booking.id,
        segment_order=1,
        origin_iata="JFK",
        destination_iata="DXB",
        airline_code="EK",
        flight_number="EK202",
        departure_datetime=datetime(2024, 6, 1, 9, 0, tzinfo=timezone.utc),
        arrival_datetime=datetime(2024, 6, 2, 8, 0, tzinfo=timezone.utc),
        duration_minutes=720
    )
    db_session.add(segment)
    db_session.commit()

    assert flight_booking.id is not None
    assert len(flight_booking.segments) == 1
    assert flight_booking.segments[0].flight_number == "EK202"
    assert flight_booking.is_international is True
