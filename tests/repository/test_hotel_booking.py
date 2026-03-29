import pytest
from datetime import date
from decimal import Decimal

from app.repository.hotel_booking import HotelBookingRepository
from app.models import HotelBooking
from app.enums import BookingStatus, RoomType
from tests.conftest import ClientFactory

@pytest.fixture
def repo():
    return HotelBookingRepository()

@pytest.mark.integration
class TestHotelBookingRepository:
    def test_find_checking_in_on_and_city(self, repo, db_session):
        c = ClientFactory.create()
        b1 = HotelBooking(
            reference_number="H1", status=BookingStatus.CONFIRMED, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", 
            hotel_name="Grand Hyatt", hotel_city="New York", hotel_country="US",
            room_type=RoomType.STANDARD, num_rooms=1, num_guests=1,
            check_in_date=date(2025, 1, 1), check_out_date=date(2025, 1, 5)
        )
        b2 = HotelBooking(
            reference_number="H2", status=BookingStatus.CONFIRMED, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", 
            hotel_name="Hilton", hotel_city="London", hotel_country="UK",
            room_type=RoomType.STANDARD, num_rooms=1, num_guests=1,
            check_in_date=date(2025, 2, 1), check_out_date=date(2025, 2, 5)
        )
        db_session.add_all([b1, b2])
        db_session.flush()

        assert b1 in repo.find_checking_in_on(date(2025, 1, 1))
        assert b2 not in repo.find_checking_in_on(date(2025, 1, 1))

        ny_hotels = repo.find_by_city("York")
        assert b1 in ny_hotels
        assert b2 not in ny_hotels
