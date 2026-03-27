import pytest
from datetime import date
from decimal import Decimal
from app.models.hotel_booking import HotelBooking
from app.models.client import Client
from app.enums import BookingStatus, BookingServiceType, ClientType, RoomType

def test_hotel_booking_creation(db_session):
    """Test HotelBooking model creation."""
    client = Client(
        first_name="Hotel",
        last_name="Tester",
        email="hotel.test@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    hotel_booking = HotelBooking(
        reference_number="TG-HTL-999",
        service_type=BookingServiceType.HOTEL,
        status=BookingStatus.PENDING_PAYMENT,
        client_id=client.id,
        total_service_fee_usd=Decimal("20.00"),
        hotel_name="Grand Hyatt",
        hotel_city="Dubai",
        hotel_country="UAE",
        check_in_date=date(2024, 6, 1),
        check_out_date=date(2024, 6, 5),
        room_type=RoomType.STANDARD,
        num_rooms=1
    )
    db_session.add(hotel_booking)
    db_session.commit()

    assert hotel_booking.id is not None
    assert hotel_booking.hotel_name == "Grand Hyatt"
    assert hotel_booking.service_type == BookingServiceType.HOTEL
