import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.booking import Booking
from app.models.flight_booking import FlightBooking, Flight
from app.models.payment import Payment
from app.models.enums import BookingStatus, BookingType, PaymentStatus, PaymentMethod
from app.repository.flight.exceptions import DatabaseError

class CreateManualBookingRequest:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, user_id: str, flight_data: dict, amount: float, currency: str = 'USD') -> Booking:
        try:
            reference_code = uuid.uuid4().hex[:12].upper()
            booking = Booking(
                reference_code=reference_code,
                user_id=user_id,
                status=BookingStatus.PAYMENT_PENDING,
                booking_type=BookingType.FLIGHT,
                total_amount=amount,
                currency=currency
            )
            self.db.add(booking)
            self.db.flush()

            flight_booking = FlightBooking(
                booking_id=booking.id,
                pnr_reference="PENDING",
                eticket_number="PENDING"
            )
            self.db.add(flight_booking)
            self.db.flush()

            new_flight = Flight(
                flight_booking_id=flight_booking.id,
                carrier_code=flight_data.get('carrier_code', 'UNK'),
                flight_number=flight_data.get('flight_number', '000'),
                departure_airport_code=flight_data.get('departure_airport', 'UNK'),
                arrival_airport_code=flight_data.get('arrival_airport', 'UNK'),
                departure_time=flight_data.get('departure_time', datetime.now(timezone.utc)), 
                arrival_time=flight_data.get('arrival_time', datetime.now(timezone.utc))
            )
            self.db.add(new_flight)

            payment = Payment(
                booking_id=booking.id,
                user_id=user_id,
                amount=amount,
                currency=currency,
                payment_method=PaymentMethod.MANUAL_TRANSFER,
                status=PaymentStatus.PENDING
            )
            self.db.add(payment)

            self.db.commit()
            self.db.refresh(booking)
            return booking

        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while creating manual booking: {str(e)}") from e
