from app.models import Booking
from app.models.enums import BookingStatus, BookingType
from app.extensions import db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import uuid
from app.repository.booking.exceptions import BookingAlreadyExists, DatabaseError

class CreateBooking:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_id: str, booking_type: str, currency: str = "USD", notes: str = None) -> Booking:
        try:
            reference_code = f"THRIVE-{uuid.uuid4().hex[:8].upper()}" # TODO: Implement booking reference code generator util
            
            new_booking = Booking(
                reference_code=reference_code,
                user_id=user_id,
                booking_type=BookingType(booking_type),
                currency=currency,
                notes=notes,
                status=BookingStatus.PENDING
            )
            
            self.db.add(new_booking)
            self.db.commit()
            self.db.refresh(new_booking)
            return new_booking
            
        except ValueError as e:
            raise 
        except IntegrityError:
            self.db.rollback()
            raise BookingAlreadyExists("Booking reference already exists.")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while creating booking: {str(e)}") from e
