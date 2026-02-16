from sqlalchemy.orm import Session
from app.models import Flight, FlightBooking
from app.repository.flight.ops import (
    SearchFlights,
    GetFlightByID,
    ReserveSeat
)

class FlightService:
    def __init__(self, db: Session):
        self.db = db
    
    def search_flights(self, origin: str, destination: str, date: str) -> list[dict]:
        return SearchFlights().execute(origin, destination, date)

    def get_flight_by_id(self, flight_id: str) -> Flight:
        return GetFlightByID(self.db).execute(flight_id)

    def reserve_seat(self, booking_id: str, flight_data: dict, seat_number: str) -> FlightBooking:
        return ReserveSeat(self.db).execute(booking_id, flight_data, seat_number)
