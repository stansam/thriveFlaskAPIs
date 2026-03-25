from sqlalchemy import select
from app.models import CarBooking
from .base import BaseRepository

class CarBookingRepository(BaseRepository[CarBooking]):
    model = CarBooking

    def find_picking_up_on(self, pickup_date: date) -> list[CarBooking]:
        from sqlalchemy import cast, Date
        stmt = (
            select(CarBooking)
            .where(cast(CarBooking.pickup_datetime, Date) == pickup_date)
            .order_by(CarBooking.pickup_datetime)
        )
        return list(self._session.execute(stmt).scalars().all())