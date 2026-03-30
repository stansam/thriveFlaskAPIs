import pytest
from datetime import date
from decimal import Decimal

from app.repository.package_booking import PackageBookingRepository
from app.models import PackageBooking, TravelPackage
from app.enums import BookingStatus, PackageStatus
from tests.conftest import ClientFactory

@pytest.fixture
def repo():
    return PackageBookingRepository()

@pytest.mark.integration
class TestPackageBookingRepository:
    def test_queries(self, repo, db_session):
        c = ClientFactory.create()
        p = TravelPackage(
            title="T", slug="t", status=PackageStatus.ACTIVE,
            destination_country="US", duration_days=1, duration_nights=1,
            base_price_usd=Decimal("1"), price_per="p", min_participants=1,
            flights_includable=False, insurance_includable=False, is_featured=False
        )
        db_session.add(p)
        db_session.flush()

        b1 = PackageBooking(
            reference_number="PB1", status=BookingStatus.CONFIRMED, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", package_id=str(p.id),
            travel_date=date.today(), num_participants=2, add_flights=False,
            add_insurance=False, price_per_person_usd=Decimal("100"),
            total_package_cost_usd=Decimal("200")
        )
        b2 = PackageBooking(
            reference_number="PB2", status=BookingStatus.PENDING_PAYMENT, client_id=c.id,
            total_service_fee_usd=Decimal("1"), currency="USD", package_id=str(p.id),
            travel_date=date.today(), num_participants=3, add_flights=False,
            add_insurance=False, price_per_person_usd=Decimal("100"),
            total_package_cost_usd=Decimal("300")
        )
        db_session.add_all([b1, b2])
        db_session.flush()

        bookings = repo.find_by_package(str(p.id))
        assert len(bookings) == 2

        confirmed = repo.find_by_package(str(p.id), status=BookingStatus.CONFIRMED)
        assert len(confirmed) == 1
        assert b1 in confirmed

        count = repo.participant_count_for_package(str(p.id))
        assert count == 2  # b1 is Confirmed(2), b2 is Pending(3) which doesn't count towards it
