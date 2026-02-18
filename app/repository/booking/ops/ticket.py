from app.models import Booking, FlightBooking
from app.models.enums import BookingStatus
from app.extensions import db
from sqlalchemy.orm import Session
from app.repository.booking.exceptions import BookingServiceError, BookingNotFound
import logging

logger = logging.getLogger(__name__)

class UploadTicket:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, booking_id: str, ticket_url: str) -> Booking:
        try:
            booking = self.db.get(Booking, booking_id)
            if not booking:
                raise BookingNotFound(f"Booking {booking_id} not found")

            # Update Booking Status
            booking.status = BookingStatus.TICKETED
            
            # Save ticket URL. 
            # Where? app/models/flight_booking.py has eticket_number.
            # app/models/booking.py has no specific ticket_url field for the file itself.
            # In Reference Document 05: "Ticket Path: uploads/tickets/{booking_ref}.pdf"
            # It seems we might want to store this URL.
            # app/models/flight_booking.py is the best place if it's a flight ticket.
            # Does FlightBooking have a file path field?
            # Checked in Step 516: pnr_reference, eticket_number, cabin_class.
            # It does NOT have a ticket_file_url.
            # We can use `eticket_number` if it's just the number, but for a file URL...
            # Maybe `notes`? Or add a field?
            # Or maybe `PackageBooking` has it?
            # Let's check `Invoice` has pdf_url.
            # I will add `ticket_url` to `FlightBooking` model as it seems necessary.
            
            if booking.flight_booking:
                booking.flight_booking.ticket_url = ticket_url
            
            self.db.commit()
            self.db.refresh(booking)
            return booking

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error uploading ticket: {e}")
            raise BookingServiceError(f"Failed to upload ticket: {str(e)}")
