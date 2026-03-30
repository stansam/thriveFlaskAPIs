from datetime import date
from sqlalchemy import select
from app.models import CarBooking
from .base import BaseRepository

from app.core.logging import get_logger

logger = get_logger(__name__)


class CarBookingRepository(BaseRepository[CarBooking]):
    model = CarBooking

    def find_picking_up_on(self, pickup_date: "date") -> list[CarBooking]:
        from datetime import datetime, time
        start = datetime.combine(pickup_date, time.min)
        end = datetime.combine(pickup_date, time.max)
        stmt = (
            select(CarBooking)
            .where(
                CarBooking.pickup_datetime >= start,
                CarBooking.pickup_datetime <= end
            )
            .order_by(CarBooking.pickup_datetime)
        )
        return list(self._session.execute(stmt).scalars().all())