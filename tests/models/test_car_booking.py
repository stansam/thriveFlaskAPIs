import pytest
from datetime import datetime, timezone
from decimal import Decimal
from app.models.car_booking import CarBooking
from app.models.client import Client
from app.enums import BookingStatus, BookingServiceType, ClientType, CarCategory

def test_car_booking_creation(db_session):
    """Test CarBooking polymorphic creation."""
    client = Client(
        first_name="Car",
        last_name="Tester",
        email="car.test@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    car_booking = CarBooking(
        reference_number="TG-CAR-123",
        service_type=BookingServiceType.CAR,
        status=BookingStatus.PENDING_PAYMENT,
        client_id=client.id,
        total_service_fee_usd=Decimal("15.00"),
        pickup_location="Airport",
        pickup_datetime=datetime.now(timezone.utc),
        dropoff_datetime=datetime.now(timezone.utc),
        car_category=CarCategory.ECONOMY
    )
    db_session.add(car_booking)
    db_session.commit()

    assert car_booking.id is not None
    assert car_booking.service_type == BookingServiceType.CAR
    assert car_booking.rental_company is None  # Check default/nullable
