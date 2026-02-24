from app.models import Booking
from app.models.enums import BookingStatus
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.booking.exceptions import BookingNotFound, DatabaseError, InvalidBookingStatus

class UpdateBookingStatus:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, booking_id: str, new_status: str) -> Booking:
        try:
            booking = self.db.query(Booking).filter_by(id=booking_id).first()
            if not booking:
                raise BookingNotFound(f"Booking with ID {booking_id} not found")
            
            status_enum = BookingStatus(new_status)
            
            # TODO: Add state transition logic validation here
            # e.g., cannot go from CANCELLED to CONFIRMED
            
            booking.status = status_enum
            self.db.commit()
            self.db.refresh(booking)
            return booking
            
        except ValueError:
             raise InvalidBookingStatus(f"Invalid status: {new_status}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while updating booking status: {str(e)}") from e
