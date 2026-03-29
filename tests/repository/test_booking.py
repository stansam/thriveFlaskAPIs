import pytest
from datetime import date, datetime
from decimal import Decimal
from werkzeug.exceptions import NotFound

from app.repository.booking import BookingRepository
from app.models import FlightBooking, PackageBooking
from app.enums import BookingStatus, BookingServiceType
from tests.conftest import ClientFactory

@pytest.fixture
def repo():
    return BookingRepository()

@pytest.mark.integration
class TestBookingRepository:
    def test_find_by_reference(self, repo, db_session):
        c = ClientFactory.create()
        b = FlightBooking(
            reference_number="REF123", status=BookingStatus.PENDING_PAYMENT,
            client_id=c.id, total_service_fee_usd=Decimal("10.00"),
            currency="USD", origin_iata="O", destination_iata="D",
            departure_date=date(2025, 1, 1)
        )
        db_session.add(b)
        db_session.flush()

        assert repo.find_by_reference("ref123 ") == b
        assert repo.find_by_reference("unknown") is None

    def test_find_by_reference_or_404(self, repo, db_session):
        c = ClientFactory.create()
        b = FlightBooking(
            reference_number="REF404", status=BookingStatus.PENDING_PAYMENT,
            client_id=c.id, total_service_fee_usd=Decimal("10.00"),
            currency="USD", origin_iata="O", destination_iata="D",
            departure_date=date(2025, 1, 1)
        )
        db_session.add(b)
        db_session.flush()

        assert repo.find_by_reference_or_404("REF404") == b
        with pytest.raises(NotFound):
            repo.find_by_reference_or_404("UNKNOWN")

    def test_filters(self, repo, db_session):
        c1 = ClientFactory.create()
        c2 = ClientFactory.create()
        
        b1 = FlightBooking(
            reference_number="B1", status=BookingStatus.PENDING_PAYMENT,
            client_id=c1.id, total_service_fee_usd=Decimal("10.00"),
            currency="USD", origin_iata="O", destination_iata="D",
            departure_date=date(2025, 1, 1)
        )
        b2 = FlightBooking(
            reference_number="B2", status=BookingStatus.CONFIRMED,
            client_id=c1.id, total_service_fee_usd=Decimal("20.00"),
            currency="USD", origin_iata="O", destination_iata="D",
            departure_date=date(2025, 1, 1)
        )
        b3 = FlightBooking(
            reference_number="B3", status=BookingStatus.PENDING_PAYMENT,
            client_id=c2.id, total_service_fee_usd=Decimal("30.00"),
            currency="USD", origin_iata="O", destination_iata="D",
            departure_date=date(2025, 1, 1)
        )
        db_session.add_all([b1, b2, b3])
        db_session.flush()

        c1_bookings = repo.find_by_client(str(c1.id))
        assert len(c1_bookings) == 2
        
        c1_pending = repo.find_by_client(str(c1.id), status=BookingStatus.PENDING_PAYMENT)
        assert len(c1_pending) == 1
        assert c1_pending[0] == b1

        pending_all = repo.find_pending_payment()
        assert b1 in pending_all
        assert b3 in pending_all
        assert b2 not in pending_all

        revenue = repo.total_revenue_by_status(BookingStatus.PENDING_PAYMENT)
        assert revenue == Decimal("40.00")

    def test_find_confirmed_upcoming(self, repo, db_session):
        c = ClientFactory.create()
        b1 = FlightBooking(
            reference_number="F1", status=BookingStatus.CONFIRMED, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", origin_iata="A", destination_iata="B",
            departure_date=date.today()
        )
        b2 = PackageBooking(
            reference_number="P1", status=BookingStatus.CONFIRMED, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", package_id="PKG",
            travel_date=date.today(), num_participants=2, add_flights=False,
            add_insurance=False, price_per_person_usd=Decimal("1.0"),
            total_package_cost_usd=Decimal("1.0")
        )
        db_session.add_all([b1, b2])
        db_session.flush()

        upcoming = repo.find_confirmed_upcoming(cutoff_date=date.today())
        assert b1 in upcoming
        assert b2 in upcoming

    def test_pagination(self, repo, db_session):
        c = ClientFactory.create()
        b = FlightBooking(
            reference_number="PAG2", status=BookingStatus.CONFIRMED, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", origin_iata="A", destination_iata="B",
            departure_date=date.today()
        )
        db_session.add(b)
        db_session.flush()

        page = repo.paginate_bookings(client_id=str(c.id), status=BookingStatus.CONFIRMED)
        assert b in page.items

    def test_transition_status(self, repo, db_session):
        c = ClientFactory.create()
        b = FlightBooking(
            reference_number="TR1", status=BookingStatus.PENDING_PAYMENT, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", origin_iata="A", destination_iata="B",
            departure_date=date.today()
        )
        db_session.add(b)
        db_session.flush()

        updated = repo.transition_status(b, BookingStatus.CONFIRMED)
        assert updated.status == BookingStatus.CONFIRMED
        assert updated.confirmed_at is not None
