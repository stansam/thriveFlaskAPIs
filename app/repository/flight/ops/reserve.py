from app.models import FlightBooking, Flight, Booking
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.flight.exceptions import DatabaseError, SeatNotAvailable
import uuid

class ReserveSeat:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, booking_id: str, flight_data: dict, seat_number: str) -> FlightBooking:
        # flight_data expected to contain flight details like carrier, flight_number, times...
        try:
            # 1. Check if booking exists (optional dependency on BookingService or direct DB check)
            # For loose coupling, we assume booking_id is valid or foreign key constraint will fail
            
            # 2. Check seat availability (MOCK)
            if seat_number == "X99": # specific mock unavailable seat
                 raise SeatNotAvailable(f"Seat {seat_number} is already taken")

            # 3. Create FlightBooking container if not exists for this booking?
            # A booking might have one flight booking container? 
            # In models: Booking -> flight_booking (One-to-One)
            
            # Check if FlightBooking exists for this booking
            flight_booking = self.db.query(FlightBooking).filter_by(booking_id=booking_id).first()
            if not flight_booking:
                flight_booking = FlightBooking(
                    booking_id=booking_id,
                    pnr_reference=f"PNR-{uuid.uuid4().hex[:6].upper()}"
                )
                self.db.add(flight_booking)
                self.db.flush() # get ID

            # 4. Create Flight segment
            # Expecting flight_data to map to Flight model fields
            new_flight = Flight(
                flight_booking_id=flight_booking.id,
                carrier_code=flight_data.get('carrier_code'),
                flight_number=flight_data.get('flight_number'),
                departure_airport_code=flight_data.get('departure_airport'),
                arrival_airport_code=flight_data.get('arrival_airport'),
                departure_time=flight_data.get('departure_time'), # Ensure datetime obj or string parser
                arrival_time=flight_data.get('arrival_time'),
                seat_assignment=seat_number
            )
            
            self.db.add(new_flight)
            self.db.commit()
            self.db.refresh(flight_booking)
            return flight_booking

        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while reserving seat: {str(e)}") from e
