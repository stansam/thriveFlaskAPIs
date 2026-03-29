# repositories/booking_repository.py
"""
Repositories for Booking (parent) and all sub-types:
FlightBooking, HotelBooking, CarBooking, PackageBooking, BookingPassenger.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import and_, or_, select, func

from app.enums import (
    BookingStatus, BookingServiceType,
    
)
from app.models import (
    Booking, BookingPassenger,
    FlightBooking, HotelBooking, CarBooking, PackageBooking,
)
from .base import BaseRepository, Page

from app.core.logging import get_logger

logger = get_logger(__name__)


# BookingRepository  (queries across ALL service types via the parent table)
class BookingRepository(BaseRepository[Booking]):
    model = Booking

    def find_by_reference(self, reference_number: str) -> Booking | None:
        stmt = select(Booking).where(
            Booking.reference_number == reference_number.upper().strip()
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def find_by_reference_or_404(self, reference_number: str) -> Booking:
        return self.get_by_or_404(reference_number=reference_number.upper().strip())

    def find_by_client(
        self,
        client_id: str,
        status: BookingStatus | None = None,
    ) -> list[Booking]:
        stmt = select(Booking).where(Booking.client_id == client_id)
        if status:
            stmt = stmt.where(Booking.status == status)
        stmt = stmt.order_by(Booking.created_at.desc())
        return list(self._session.execute(stmt).scalars().all())

    def find_pending_payment(self) -> list[Booking]:
        stmt = (
            select(Booking)
            .where(Booking.status == BookingStatus.PENDING_PAYMENT)
            .order_by(Booking.created_at)
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_confirmed_upcoming(self, cutoff_date: date) -> list[Booking]:
        """
        Return CONFIRMED bookings whose service date is before `cutoff_date`.
        Used by the pre-trip reminder job.  Joins across sub-types for departure dates.
        """
        flight_stmt = (
            select(FlightBooking)
            .where(
                FlightBooking.status == BookingStatus.CONFIRMED,
                FlightBooking.departure_date <= cutoff_date,
                FlightBooking.departure_date >= date.today(),
            )
        )
        package_stmt = (
            select(PackageBooking)
            .where(
                PackageBooking.status == BookingStatus.CONFIRMED,
                PackageBooking.travel_date <= cutoff_date,
                PackageBooking.travel_date >= date.today(),
            )
        )
        flights = list(self._session.execute(flight_stmt).scalars().all())
        packages = list(self._session.execute(package_stmt).scalars().all())
        return flights + packages

    def total_revenue_by_status(self, status: BookingStatus) -> Decimal:
        stmt = (
            select(func.sum(Booking.total_service_fee_usd))
            .where(Booking.status == status)
        )
        result = self._session.execute(stmt).scalar_one_or_none()
        return result or Decimal("0.00")

    def monthly_booking_count(self, year: int, month: int) -> int:
        from sqlalchemy import extract
        stmt = (
            select(func.count(Booking.id))
            .where(
                extract("year", Booking.created_at) == year,
                extract("month", Booking.created_at) == month,
            )
        )
        return self._session.execute(stmt).scalar_one()

    def paginate_bookings(
        self,
        client_id: str | None = None,
        service_type: BookingServiceType | None = None,
        status: BookingStatus | None = None,
        is_emergency: bool | None = None,
        is_group: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[Booking]:
        stmt = select(Booking)
        if client_id:
            stmt = stmt.where(Booking.client_id == client_id)
        if service_type:
            stmt = stmt.where(Booking.service_type == service_type)
        if status:
            stmt = stmt.where(Booking.status == status)
        if is_emergency is not None:
            stmt = stmt.where(Booking.is_emergency.is_(is_emergency))
        if is_group is not None:
            stmt = stmt.where(Booking.is_group.is_(is_group))
        if date_from:
            stmt = stmt.where(Booking.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Booking.created_at <= date_to)
        if search:
            stmt = stmt.where(
                Booking.reference_number.ilike(f"%{search}%")
            )
        stmt = stmt.order_by(Booking.created_at.desc())
        return self.paginate(stmt, page=page, per_page=per_page)

    def transition_status(
        self,
        booking: Booking,
        new_status: BookingStatus,
        actor_id: str | None = None,
    ) -> Booking:
        """Apply a status transition and stamp the relevant timestamp."""
        now = datetime.now()
        extra: dict = {"status": new_status}
        if new_status == BookingStatus.CONFIRMED:
            extra["confirmed_at"] = now
        elif new_status == BookingStatus.CANCELLED:
            extra["cancelled_at"] = now
        elif new_status == BookingStatus.COMPLETED:
            extra["completed_at"] = now
        return self.update(booking, actor_id=actor_id, **extra)

