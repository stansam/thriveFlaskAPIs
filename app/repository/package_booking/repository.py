from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models.package_booking import PackageBooking
from app.models.package_departure import PackageDeparture
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.package_booking.utils import get_future_cutoff_date

class PackageBookingRepository(BaseRepository[PackageBooking]):
    """
    PackageBookingRepository orchestrates querying nested structures
    associated with bespoke vacation package tracking and upcoming departures.
    """

    def __init__(self):
        super().__init__(PackageBooking)

    @handle_db_exceptions
    def get_package_booking_with_custom_itinerary(self, booking_id: str) -> Optional[PackageBooking]:
        """Eagerly loads deeply nested custom itinerary structures if one was generated."""
        return self.model.query.options(
            joinedload(self.model.custom_itinerary)
        ).filter_by(id=booking_id).first()

    @handle_db_exceptions
    def get_upcoming_package_bookings(self, days_ahead: int) -> List[PackageBooking]:
        """
        Cross-queries against the PackageDeparture bounds evaluating bookings 
        where the departure falls within a specifically constrained near-future window.
        """
        cutoff_date = get_future_cutoff_date(days_ahead)
        now = datetime.now(timezone.utc).date()
        
        return self.model.query.join(
            PackageDeparture, self.model.departure_id == PackageDeparture.id
        ).filter(
            PackageDeparture.departure_date > now,
            PackageDeparture.departure_date <= cutoff_date
        ).order_by(PackageDeparture.departure_date.asc()).all()
