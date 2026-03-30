from datetime import date
from sqlalchemy import select
from app.models import HotelBooking
from .base import BaseRepository

from app.core.logging import get_logger

logger = get_logger(__name__)


class HotelBookingRepository(BaseRepository[HotelBooking]):
    model = HotelBooking

    def find_checking_in_on(self, check_in_date: date) -> list[HotelBooking]:
        stmt = (
            select(HotelBooking)
            .where(HotelBooking.check_in_date == check_in_date)
            .order_by(HotelBooking.hotel_name)
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_by_city(self, city: str) -> list[HotelBooking]:
        stmt = (
            select(HotelBooking)
            .where(HotelBooking.hotel_city.ilike(f"%{city}%"))
            .order_by(HotelBooking.check_in_date.desc())
        )
        return list(self._session.execute(stmt).scalars().all())