from app.models import Booking
from app.models.enums import BookingStatus
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.booking.exceptions import BookingNotFound, DatabaseError, InvalidBookingStatus

class CancelBooking:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, booking_id: str, reason: str = None) -> Booking:
        try:
            booking = self.db.query(Booking).filter_by(id=booking_id).first()
            if not booking:
                raise BookingNotFound(f"Booking with ID {booking_id} not found")
            
            if booking.status == BookingStatus.CANCELLED:
                 raise InvalidBookingStatus("Booking is already cancelled")
            
            # TODO: Add logic to check cancellation policy and trigger refunds via Finance service
            
            booking.status = BookingStatus.CANCELLED
            # Store reason in notes or audit log if needed
            if reason:
                if booking.notes:
                    booking.notes += f"\nCancelled: {reason}"
                else:
                    booking.notes = f"Cancelled: {reason}"

            self.db.commit()
            self.db.refresh(booking)
            return booking
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while cancelling booking: {str(e)}") from e
