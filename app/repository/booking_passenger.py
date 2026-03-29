from sqlalchemy import select
from app.models import BookingPassenger
from .base import BaseRepository

from app.core.logging import get_logger

logger = get_logger(__name__)


class BookingPassengerRepository(BaseRepository[BookingPassenger]):
    model = BookingPassenger

    def find_by_booking(self, booking_id: str) -> list[BookingPassenger]:
        stmt = (
            select(BookingPassenger)
            .where(BookingPassenger.booking_id == booking_id)
            .order_by(BookingPassenger.is_lead_passenger.desc(), BookingPassenger.last_name)
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_lead(self, booking_id: str) -> BookingPassenger | None:
        stmt = select(BookingPassenger).where(
            BookingPassenger.booking_id == booking_id,
            BookingPassenger.is_lead_passenger.is_(True),
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def find_by_passport(self, passport_number: str) -> list[BookingPassenger]:
        stmt = select(BookingPassenger).where(
            BookingPassenger.passport_number == passport_number
        )
        return list(self._session.execute(stmt).scalars().all())
