from sqlalchemy import select
from app.models import FlightBooking
from .base import BaseRepository
from app.enums import BookingStatus

from app.core.logging import get_logger

logger = get_logger(__name__)


class FlightBookingRepository(BaseRepository[FlightBooking]):
    model = FlightBooking

    def find_by_pnr(self, pnr: str) -> FlightBooking | None:
        stmt = select(FlightBooking).where(
            FlightBooking.pnr == pnr.upper().strip()
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def find_departing_on(self, departure_date: date) -> list[FlightBooking]:
        stmt = (
            select(FlightBooking)
            .where(FlightBooking.departure_date == departure_date)
            .order_by(FlightBooking.origin_iata)
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_upcoming_departures(
        self, from_date: date, to_date: date
    ) -> list[FlightBooking]:
        stmt = (
            select(FlightBooking)
            .where(
                FlightBooking.departure_date >= from_date,
                FlightBooking.departure_date <= to_date,
                FlightBooking.status == BookingStatus.CONFIRMED,
            )
            .order_by(FlightBooking.departure_date)
        )
        return list(self._session.execute(stmt).scalars().all())
