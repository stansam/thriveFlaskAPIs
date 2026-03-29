import pytest
from datetime import date, datetime
from decimal import Decimal

from app.repository.car_booking import CarBookingRepository
from app.models import CarBooking
from app.enums import BookingStatus, CarCategory
from tests.conftest import ClientFactory

@pytest.fixture
def repo():
    return CarBookingRepository()

@pytest.mark.integration
class TestCarBookingRepository:
    def test_find_picking_up_on(self, repo, db_session):
        c = ClientFactory.create()
        b = CarBooking(
            reference_number="C1", status=BookingStatus.CONFIRMED, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD",
            pickup_location="JFK Airport", dropoff_location="JFK Airport",
            pickup_datetime=datetime(2025, 4, 1, 10, 0),
            dropoff_datetime=datetime(2025, 4, 5, 10, 0),
            rental_company="Hertz", car_category=CarCategory.ECONOMY, num_passengers=1
        )
        db_session.add(b)
        db_session.flush()

        assert b in repo.find_picking_up_on(date(2025, 4, 1))
        assert b not in repo.find_picking_up_on(date(2025, 4, 2))
