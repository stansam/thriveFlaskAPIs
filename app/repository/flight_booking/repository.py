from typing import Optional
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models.flight_booking import FlightBooking
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.flight_booking.utils import normalize_pnr

class FlightBookingRepository(BaseRepository[FlightBooking]):
    """
    FlightBookingRepository handles airline flight reservations, loading nested
    segment data and managing downstream ticketing components.
    """

    def __init__(self):
        super().__init__(FlightBooking)

    @handle_db_exceptions
    def get_flight_booking_with_segments(self, booking_id: str) -> Optional[FlightBooking]:
        """Eagerly loads all sequentially linked Flight segments associated with this booking."""
        return self.model.query.options(
            joinedload(self.model.flights)
        ).filter_by(id=booking_id).first()

    @handle_db_exceptions
    def find_by_pnr(self, pnr_reference: str) -> Optional[FlightBooking]:
        """Looks up a specific booking strictly by its airline-issued PNR code."""
        cln_pnr = normalize_pnr(pnr_reference)
        return self.model.query.filter_by(pnr=cln_pnr).first()

    @handle_db_exceptions
    def update_eticket_info(self, booking_id: str, eticket_number: str, ticket_url: str) -> Optional[FlightBooking]:
        """Secures post-fulfillment eticket metadata to the respective booking record."""
        booking = self.get_by_id(booking_id)
        if not booking:
            return None
            
        booking.eticket_number = eticket_number
        booking.ticket_url = ticket_url
        db.session.commit()
        return booking
