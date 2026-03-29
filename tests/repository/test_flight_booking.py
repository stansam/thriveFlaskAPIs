import pytest
from datetime import date
from decimal import Decimal

from app.repository.flight_booking import FlightBookingRepository
from app.models import FlightBooking
from app.enums import BookingStatus
from tests.conftest import ClientFactory

@pytest.fixture
def repo():
    return FlightBookingRepository()

@pytest.mark.integration
class TestFlightBookingRepository:
    def test_find_by_pnr(self, repo, db_session):
        c = ClientFactory.create()
        b = FlightBooking(
            reference_number="F1", status=BookingStatus.CONFIRMED, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", origin_iata="A", destination_iata="B",
            departure_date=date.today(), pnr="XY123Z"
        )
        db_session.add(b)
        db_session.flush()

        assert repo.find_by_pnr("xy123z ") == b
        assert repo.find_by_pnr("NOPE") is None

    def test_find_departing_on(self, repo, db_session):
        c = ClientFactory.create()
        b = FlightBooking(
            reference_number="F2", status=BookingStatus.CONFIRMED, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", origin_iata="A", destination_iata="B",
            departure_date=date(2025, 5, 20)
        )
        db_session.add(b)
        db_session.flush()

        assert b in repo.find_departing_on(date(2025, 5, 20))
        assert b not in repo.find_departing_on(date(2025, 5, 21))

    def test_find_upcoming_departures(self, repo, db_session):
        c = ClientFactory.create()
        b = FlightBooking(
            reference_number="F3", status=BookingStatus.CONFIRMED, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", origin_iata="A", destination_iata="B",
            departure_date=date(2025, 6, 1)
        )
        b_pending = FlightBooking(
            reference_number="F4", status=BookingStatus.PENDING_PAYMENT, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", origin_iata="A", destination_iata="B",
            departure_date=date(2025, 6, 1)
        )
        db_session.add_all([b, b_pending])
        db_session.flush()

        results = repo.find_upcoming_departures(date(2025, 5, 1), date(2025, 7, 1))
        assert b in results
        assert b_pending not in results
