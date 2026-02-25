from typing import Optional, List
from datetime import date
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from app.extensions import db
from app.models.booking import Booking
from app.models.booking import BookingLineItem
from app.models.enums import BookingStatus
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.booking.utils import generate_reference

class BookingRepository(BaseRepository[Booking]):
    """
    BookingRepository managing high-volume transaction aggregations
    and fetching deeply nested ledger-like structures.
    """

    def __init__(self):
        super().__init__(Booking)

    @handle_db_exceptions
    def create_booking(self, user_id: str, data: dict) -> Booking:
        """Injects custom unique reference codes during creation."""
        data['reference_code'] = generate_reference()
        data['user_id'] = user_id
        return super().create(data, commit=False)

    @handle_db_exceptions
    def find_by_reference(self, reference_code: str) -> Optional[Booking]:
        return self.model.query.filter_by(reference_code=reference_code.upper()).first()

    @handle_db_exceptions
    def get_user_bookings_history(self, user_id: str, page: int = 1, limit: int = 50) -> dict:
        """Paginates a single user's bookings securely, ordered most recent first."""
        pagination = self.model.query.filter_by(user_id=user_id)\
            .order_by(self.model.created_at.desc())\
            .paginate(page=page, per_page=limit, error_out=False)
            
        return {
            "items": pagination.items,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }

    @handle_db_exceptions
    def get_booking_with_line_items(self, booking_id: str) -> Optional[Booking]:
        """Eagerly loads the immutable financial line-items associated with this booking."""
        return self.model.query.options(
            joinedload(self.model.line_items)
        ).filter_by(id=booking_id).first()

    @handle_db_exceptions
    def get_bookings_by_status(self, status: BookingStatus) -> List[Booking]:
        return self.model.query.filter_by(status=status).all()

    @handle_db_exceptions
    def update_booking_status(self, booking_id: str, new_status: BookingStatus) -> Optional[Booking]:
        booking = self.get_by_id(booking_id)
        if not booking:
            return None
            
        booking.status = new_status
        db.session.commit()
        return booking
        
    @handle_db_exceptions
    def calculate_total_revenue_by_period(self, start_date: date, end_date: date) -> float:
        """
        Database-level scalar aggregation of total cost fields across CONFIRMED 
        transactions bounded by date. Performs SUM operations entirely server-side.
        """
        total = db.session.query(func.sum(self.model.total_amount)).filter(
            self.model.status == BookingStatus.CONFIRMED,
            self.model.created_at >= start_date,
            self.model.created_at <= end_date
        ).scalar()
        
        return float(total) if total is not None else 0.0
