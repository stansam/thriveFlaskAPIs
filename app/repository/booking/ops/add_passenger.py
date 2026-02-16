from app.models import Booking, Passenger
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.booking.exceptions import BookingNotFound, DatabaseError
from app.models.enums import Gender

class AddPassengerToBooking:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, booking_id: str, passenger_data: dict) -> Passenger:
        try:
            booking = self.db.query(Booking).filter_by(id=booking_id).first()
            if not booking:
                raise BookingNotFound(f"Booking with ID {booking_id} not found")
            
            # TODO: Validate passenger count against max capacity if applicable
            
            # Map string gender to Enum if necessary
            if 'gender' in passenger_data and isinstance(passenger_data['gender'], str):
                 passenger_data['gender'] = Gender(passenger_data['gender'])

            new_passenger = Passenger(booking_id=booking_id, **passenger_data)
            
            self.db.add(new_passenger)
            self.db.commit()
            self.db.refresh(new_passenger)
            return new_passenger
            
        except ValueError:
            raise ValueError("Invalid passenger data (e.g. invalid gender enum)")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while adding passenger: {str(e)}") from e
