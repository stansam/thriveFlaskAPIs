import pytest
from datetime import date
from decimal import Decimal
from app.repository.payment import PaymentRepository
from app.models import Payment, FlightBooking
from app.enums import BookingStatus, PaymentStatus, PaymentMethod
from tests.conftest import ClientFactory

@pytest.fixture
def repo():
    return PaymentRepository()

@pytest.mark.integration
class TestPaymentRepository:
    def test_queries(self, repo, db_session):
        c = ClientFactory.create()
        b = FlightBooking(
            reference_number="TG", status=BookingStatus.PENDING_PAYMENT,
            client_id=str(c.id), total_service_fee_usd=Decimal("50"),
            origin_iata="A", destination_iata="B", departure_date=date(2025, 1, 1),
            currency="USD"
        )
        db_session.add(b)
        db_session.flush()
        bid = str(b.id)

        p1 = Payment(
            booking_id=bid, amount_usd=Decimal("50.00"),
            method=PaymentMethod.BANK_TRANSFER, status=PaymentStatus.CONFIRMED
        )
        p2 = Payment(
            booking_id=bid, amount_usd=Decimal("10.00"),
            method=PaymentMethod.ZELLE, status=PaymentStatus.PENDING
        )
        db_session.add_all([p1, p2])
        db_session.flush()

        by_booking = repo.find_by_booking(bid)
        assert len(by_booking) == 2

        total = repo.total_confirmed_for_booking(bid)
        assert total == Decimal("50.00")

        pending = repo.find_pending()
        assert p2 in pending
        assert p1 not in pending

        page = repo.paginate_payments(booking_id=bid, status=PaymentStatus.CONFIRMED)
        assert len(page.items) == 1
        assert page.items[0] == p1
