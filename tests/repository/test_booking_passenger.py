import pytest
from datetime import date
from decimal import Decimal

from app.repository.booking_passenger import BookingPassengerRepository
from app.models import FlightBooking, BookingPassenger
from app.enums import BookingStatus
from tests.conftest import ClientFactory

@pytest.fixture
def repo():
    return BookingPassengerRepository()

@pytest.mark.integration
class TestBookingPassengerRepository:
    def test_passenger_queries(self, repo, db_session):
        c = ClientFactory.create()
        b = FlightBooking(
            reference_number="P1", status=BookingStatus.CONFIRMED, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", origin_iata="A", destination_iata="B",
            departure_date=date(2025, 5, 20)
        )
        db_session.add(b)
        db_session.flush()

        p1 = BookingPassenger(
            booking_id=str(b.id),
            first_name="Lead", last_name="Passenger",
            is_lead_passenger=True, passport_number="PASS1"
        )
        p2 = BookingPassenger(
            booking_id=str(b.id),
            first_name="Child", last_name="Passenger",
            is_lead_passenger=False, passport_number="PASS2"
        )
        db_session.add_all([p1, p2])
        db_session.flush()

        passengers = repo.find_by_booking(str(b.id))
        assert len(passengers) == 2
        # ordered by lead
        assert passengers[0] == p1

        lead = repo.find_lead(str(b.id))
        assert lead == p1

        by_passport = repo.find_by_passport("PASS2")
        assert len(by_passport) == 1
        assert by_passport[0] == p2
