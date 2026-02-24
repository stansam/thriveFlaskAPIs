from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.flight_booking import FlightBooking
from app.models.enums import BookingStatus, PaymentStatus
from app.repository.flight.exceptions import DatabaseError

class AdminCheckPaymentProof:
    def __init__(self, db: Session) -> None:
        self.db = db
        
    def confirm_payment(self, booking_id: str) -> Booking:
        try:
            booking = self.db.query(Booking).filter_by(id=booking_id).first()
            if not booking:
                raise ValueError("Booking not found")
                
            payment = self.db.query(Payment).filter_by(booking_id=booking_id).first()
            if payment:
                payment.status = PaymentStatus.PAID
                
            booking.status = BookingStatus.PROCESSING_TICKET
            
            self.db.commit()
            self.db.refresh(booking)
            return booking
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while confirming payment: {str(e)}") from e

class AdminFulfillTicket:
    def __init__(self, db: Session) -> None:
        self.db = db
        
    def fulfill(self, booking_id: str, pnr: str, eticket: str, ticket_url: str) -> FlightBooking:
        try:
            booking = self.db.query(Booking).filter_by(id=booking_id).first()
            if not booking:
                raise ValueError("Booking not found")
                
            flight_booking = self.db.query(FlightBooking).filter_by(booking_id=booking_id).first()
            if not flight_booking:
                raise ValueError("Flight booking not found")
                
            flight_booking.pnr_reference = pnr
            flight_booking.eticket_number = eticket
            if ticket_url:
                flight_booking.ticket_url = ticket_url
                
            booking.status = BookingStatus.COMPLETED
            
            self.db.commit()
            self.db.refresh(flight_booking)
            return flight_booking
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while fulfilling ticket: {str(e)}") from e
