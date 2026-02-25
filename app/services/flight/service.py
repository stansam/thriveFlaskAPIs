from typing import List
import uuid
from app.models.flight_booking import FlightBooking, Flight
from app.models.enums import BookingStatus
from app.repository import repositories
from app.dto.flight.schemas import BookFlightDTO

class FlightService:
    """
    FlightService abstracts external global distribution systems (GDS) and coordinates
    multi-legged flight segment persistence underneath a unified transactional Booking lock.
    """

    def __init__(self):
        self.flight_booking_repo = repositories.flight_booking
        self.booking_repo = repositories.booking
        self.user_repo = repositories.user
        self.subscription_service = None # Defer importing to prevent circular loops if needed

    def search_flights(self, origin: str, destination: str, date: str) -> List[dict]:
        """
        Mocks reaching out to external GDS aggregators (like Amadeus/Sabre) 
        returning unified segment arrays ready for parsing.
        """
        # TODO: Concrete API wireup
        return [{
            "carrier_code": "KQ",
            "flight_number": "100",
            "departure_airport_code": origin,
            "arrival_airport_code": destination,
            "duration_minutes": 120,
            "price_usd": 250.00
        }]

    def book_flight(self, data: BookFlightDTO) -> FlightBooking:
        """
        Executes a transactional block:
        1. Confirms the user can book.
        2. Creates the generic overarching `Booking` mapping.
        3. Creates the specific `FlightBooking` holding the PNR.
        4. Writes out the physical segment relationships inherently bound.
        """
        user = self.user_repo.get_by_id(data.user_id)
        if not user or not user.can_book():
            # In production, this proxies out to `SubscriptionService.check_booking_eligibility(user_id)`
            raise PermissionError("User lacks active booking entitlements or has exhausted their tier limit.")

        try:
            # 1. Base Booking
            booking_core = self.booking_repo.create({
                "user_id": user.id,
                "status": BookingStatus.PENDING,
                "company_id": user.company_id # Inherit billing context natively if present
            }, commit=False)
            # 2. FlightBooking Header
            pnr = data.pnr_reference or str(uuid.uuid4()).split('-')[0].upper()
            flight_header = self.flight_booking_repo.create({
                "booking_id": booking_core.id,
                "pnr_reference": pnr,
                "cabin_class": data.cabin_class
            }, commit=False)
            # 3. Flight Segments natively injected against the header
            self.flight_booking_repo.add_flight_segments(flight_header.id, data.segments)
            return flight_header

        except Exception as e:
            raise RuntimeError(f"Flight booking transaction failed cleanly: {str(e)}")
