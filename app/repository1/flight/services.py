from sqlalchemy.orm import Session
from app.models import Flight, FlightBooking, Booking
from app.repository.flight.ops import (
    SearchFlights,
    GetFlightByID,
    GetFlightDetails
)
from app.repository.flight.ops.create_booking import CreateManualBookingRequest
from app.repository.flight.ops.admin_ops import AdminCheckPaymentProof, AdminFulfillTicket
from app.repository.flight.requestDTO import FlightSearchRequestDTO

class FlightService:
    def __init__(self, db: Session):
        self.db = db
    
    def search_flights(self, params: FlightSearchRequestDTO) -> list[dict]:
        return SearchFlights().execute(params)

    def get_flight_by_id(self, flight_id: str) -> Flight:
        return GetFlightByID(self.db).execute(flight_id)

    def create_manual_booking(self, user_id: str, flight_data: dict, amount: float, currency: str = 'USD') -> Booking:
        return CreateManualBookingRequest(self.db).execute(user_id, flight_data, amount, currency)

    def admin_confirm_payment(self, booking_id: str) -> Booking:
        return AdminCheckPaymentProof(self.db).confirm_payment(booking_id)
        
    def admin_fulfill_ticket(self, booking_id: str, pnr: str, eticket: str, ticket_url: str) -> FlightBooking:
        return AdminFulfillTicket(self.db).fulfill(booking_id, pnr, eticket, ticket_url)

    def get_flight_details(self, flight_id: str, params: dict = None) -> dict:
        return GetFlightDetails().execute(flight_id, params)
