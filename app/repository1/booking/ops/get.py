from app.models import Booking
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.booking.exceptions import BookingNotFound, DatabaseError

class GetBookingByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, booking_id: str) -> Booking:
        try:
            booking = self.db.query(Booking).filter_by(id=booking_id).first()
            if not booking:
                raise BookingNotFound(f"Booking with ID {booking_id} not found")
            return booking
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching booking: {str(e)}") from e

class GetBookingByReference:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, reference_code: str) -> Booking:
        try:
            booking = self.db.query(Booking).filter_by(reference_code=reference_code).first()
            if not booking:
                raise BookingNotFound(f"Booking with reference {reference_code} not found")
            return booking
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching booking: {str(e)}") from e

class GetUserBookings:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_id: str) -> list[Booking]:
        try:
            bookings = self.db.query(Booking).filter_by(user_id=user_id).all()
            return bookings
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching user bookings: {str(e)}") from e
