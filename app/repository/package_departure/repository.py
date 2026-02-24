from typing import Optional, List
from datetime import date
from sqlalchemy.orm.exc import StaleDataError
from app.extensions import db
from app.models.package_departure import PackageDeparture
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.package_departure.utils import CapacityExceededError, ConcurrentUpdateError

class PackageDepartureRepository(BaseRepository[PackageDeparture]):
    """
    PackageDepartureRepository enforcing strict inventory bounds
    using SQLAlchemy Optimistic Locking (`version_id`).
    """

    def __init__(self):
        super().__init__(PackageDeparture)

    @handle_db_exceptions
    def get_available_departures(self, package_id: str, start_date: date, end_date: date) -> List[PackageDeparture]:
        """Fetch all dates for a package that still have positive booking capability."""
        return self.model.query.filter(
            self.model.package_id == package_id,
            self.model.departure_date >= start_date,
            self.model.departure_date <= end_date,
            self.model.available_capacity > 0
        ).order_by(self.model.departure_date.asc()).all()

    @handle_db_exceptions
    def decrement_capacity(self, departure_id: str, count: int, current_version: int) -> PackageDeparture:
        """
        Atomically lowers inventory boundaries. Traps underlying DB Exceptions if
        the `version_id` mismatch happens (StaleDataError) signaling a race-condition.
        """
        departure = self.get_by_id(departure_id)
        if not departure:
            raise ValueError(f"Departure {departure_id} not found.")

        # Guard against fundamental overbooking
        if departure.available_capacity < count:
            raise CapacityExceededError("Not enough seats/capacity remaining for this departure.")

        # Enforce exact version matching. If someone else bought a ticket since we loaded
        # this model into memory, `current_version` will be outdated relative to the DB.
        if departure.version_id != current_version:
             raise ConcurrentUpdateError("This departure was updated by another booking. Please refresh and try again.")
             
        try:
            departure.available_capacity -= count
            db.session.commit()
            return departure
        except StaleDataError:
            # Failsafe: SQLAlchemy interception if optimistic lock fails directly at commit phase
            db.session.rollback()
            raise ConcurrentUpdateError("Capacity was just modified by another process. Please retry.")

    @handle_db_exceptions
    def increment_capacity(self, departure_id: str, count: int) -> Optional[PackageDeparture]:
        """Restores inventory boundaries (e.g. after a booking cancellation or refund)."""
        departure = self.get_by_id(departure_id)
        if not departure:
            return None
            
        # Hard db constraints should ensure this never surpasses max_capacity natively
        departure.available_capacity += count
        db.session.commit()
        return departure
