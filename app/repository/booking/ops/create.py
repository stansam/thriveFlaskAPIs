from app.models import Booking, FlightBooking, Passenger
from app.models.enums import BookingStatus, BookingType, Gender, TravelClass
from app.extensions import db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import uuid
from app.repository.booking.exceptions import BookingAlreadyExists, DatabaseError

class CreateBooking:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_id: str, booking_type: str, total_amount: float = 0.0, currency: str = "USD", notes: str = None, booking_details: dict = None) -> Booking:
        try:
            reference_code = f"THRIVE-{uuid.uuid4().hex[:8].upper()}" # TODO: Implement booking reference code generator util
            
            new_booking = Booking(
                reference_code=reference_code,
                user_id=user_id,
                booking_type=BookingType(booking_type),
                total_amount=total_amount,
                currency=currency,
                notes=notes,
                status=BookingStatus.PENDING
            )
            
            self.db.add(new_booking)
            self.db.flush() # Flush to populate new_booking.id

            if booking_details and booking_type == BookingType.FLIGHT.value:
                # Create FlightBooking
                
                # Retrieve cabin_class string, default to economy
                try:
                    cabin_enum = TravelClass(booking_details.get('cabin_class', 'economy'))
                except ValueError:
                    cabin_enum = TravelClass.ECONOMY

                flight_booking = FlightBooking(
                    booking_id=new_booking.id,
                    pnr_reference=booking_details.get('pnr_reference'),
                    eticket_number=None, 
                    cabin_class=cabin_enum
                )
                self.db.add(flight_booking)

                # Create Passengers
                for p_data in booking_details.get('passengers', []):
                    new_passenger = Passenger(
                        booking_id=new_booking.id,
                        first_name=p_data['first_name'],
                        last_name=p_data['last_name'],
                        date_of_birth=p_data['dob'],
                        gender=Gender(p_data['gender']),
                        passport_number=p_data['passport_number'],
                        passport_expiry=p_data['passport_expiry'] # Correct field name
                    )
                    self.db.add(new_passenger)

            self.db.commit()
            self.db.refresh(new_booking)
            return new_booking
            
        except ValueError as e:
            self.db.rollback()
            raise 
        except IntegrityError:
            self.db.rollback()
            raise BookingAlreadyExists("Booking reference already exists.")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while creating booking: {str(e)}") from e
