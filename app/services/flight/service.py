from typing import List
import uuid
from app.models.flight_booking import FlightBooking, Flight
from app.models.enums import BookingStatus
from app.repository import repositories
from app.dto.flight.schemas import BookFlightDTO, SearchFlightDTO
from app.services.flight.adapter import GDSFlightAdapter

class FlightService:
    """
    FlightService abstracts external global distribution systems (GDS) and coordinates
    multi-legged flight segment persistence underneath a unified transactional Booking lock.
    """

    def __init__(self):
        self.flight_booking_repo = repositories.flight_booking
        self.booking_repo = repositories.booking
        self.user_repo = repositories.user
        self.api_adapter = GDSFlightAdapter()
        self.subscription_service = None # Defer importing to prevent circular loops if needed

    def search_locations(self, query: str, type_param: str = "airportonly") -> dict:
        """Proxies geographic queries extracting strictly typed physical coordinates natively."""
        res = self.api_adapter.search_airports(query, type_param)
        return res.model_dump()

    def track_flight(self, flight_number: str, airline_id: str, date: str) -> dict:
        """Proxies real-time radar mapping arrays natively tracking live aircraft."""
        res = self.api_adapter.get_flight_details(flight_number, airline_id, date)
        return res.model_dump()

    def search_flights(self, payload: SearchFlightDTO) -> dict:
        """
        Executes physical flight inventory lookups mapping complex structures 
        strictly across the external GDS aggregators securely.
        """
        adults: int = payload.passengers.adults if payload.passengers else 1
        page: int = payload.page 
        
        # Pydantic model dump parsing
        gds_results = self.api_adapter.search_flights(
            origin=payload.origin,
            destination=payload.destination,
            date=payload.departure_date.strftime("%Y-%m-%d"),
            adults=adults,
            cabin_class=payload.cabin_class.value if hasattr(payload.cabin_class, 'value') else payload.cabin_class,
            page=page
        )
        
        return gds_results.model_dump()

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

    def void_booking(self, booking_id: str, reason: str) -> None:
        """
        Executes a transactional block reversing the physical booking mapping.
        1. Cancels the generic overarching Booking state.
        2. Frees any future segments releasing inventory locks (mocked or external).
        """
        try:
            booking = self.booking_repo.get_by_id(booking_id)
            if not booking:
                raise ValueError("Booking explicitly unseen natively.")
                
            if booking.status == BookingStatus.CANCELLED:
                raise ValueError("Booking already structurally Voided.")
                
            # 1. Base Booking Voiding
            self.booking_repo.update(booking.id, {"status": BookingStatus.CANCELLED}, commit=False)
            
            # 2. FlightBooking Voiding & Inventory Release
            # The relationship `booking.flight_booking` holds the native PNR context
            if booking.flight_booking:
                # In a live GDS environment, physical API triggers routing to Amadeus/Kayak
                # would proactively release the PNR hold bounds here strictly.
                # e.g., self.api_adapter.cancel_pnr(booking.flight_booking.pnr_reference)
                pass
                
            # 3. Commit native block securely
            self.booking_repo.db.session.commit()
        except Exception as e:
            self.booking_repo.db.session.rollback()
            raise RuntimeError(f"Failed cancelling physical booking loop: {str(e)}")
