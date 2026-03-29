from sqlalchemy import select, func
from app.models import PackageBooking
from app.enums import BookingStatus
from .base import BaseRepository

from app.core.logging import get_logger

logger = get_logger(__name__)


class PackageBookingRepository(BaseRepository[PackageBooking]):
    model = PackageBooking

    def find_by_package(
        self,
        package_id: str,
        status: BookingStatus | None = None,
    ) -> list[PackageBooking]:
        stmt = select(PackageBooking).where(
            PackageBooking.package_id == package_id
        )
        if status:
            stmt = stmt.where(PackageBooking.status == status)
        stmt = stmt.order_by(PackageBooking.travel_date)
        return list(self._session.execute(stmt).scalars().all())

    def participant_count_for_package(self, package_id: str) -> int:
        """Total confirmed participants across all bookings for a package."""
        stmt = (
            select(func.sum(PackageBooking.num_participants))
            .where(
                PackageBooking.package_id == package_id,
                PackageBooking.status.in_([
                    BookingStatus.CONFIRMED,
                    BookingStatus.PAYMENT_RECEIVED,
                    BookingStatus.ON_HOLD,
                ]),
            )
        )
        result = self._session.execute(stmt).scalar_one_or_none()
        return result or 0