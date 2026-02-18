from sqlalchemy.orm import Session
from app.models import Booking, Passenger
from app.repository.booking.ops import (
    CreateBooking,
    GetBookingByID,
    GetBookingByReference,
    GetUserBookings,
    UpdateBookingStatus,
    AddPassengerToBooking,
    CancelBooking
)

from app.repository.flight.ops import CheckFlightPrice
from app.repository.booking.exceptions import BookingServiceError

class BookingService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_booking(self, user_id: str, booking_type: str, total_amount: float = 0.0, currency: str = "USD", notes: str = None, booking_details: dict = None) -> Booking:
        return CreateBooking(self.db).execute(user_id, booking_type, total_amount, currency, notes, booking_details)

    def initiate_booking(self, user_id: str, flight_id: str, passengers: list, expected_price: float = None) -> Booking:
        """
        Validates price/availability and creates a draft booking.
        """
        # 1. Live Price Check
        checker = CheckFlightPrice()
        check_result = checker.execute(flight_id, expected_price)
        
        if not check_result['available']:
            raise BookingServiceError("Flight is no longer available.")
        
        # Optional: Fail if price changed significantly
        # if check_result['price_changed']:
        #     raise BookingServiceError(f"Price has changed to {check_result['price']}")
        
        # 2. Create Booking
        # We need to construct the booking details for the CreateBooking op
        booking_details = {
            "flight_data": {}, # We might need to fetch this from cache or details if we verify it
            "pnr_reference": flight_id, # Using token as ref for now
            "passengers": passengers,
            "cabin_class": "economy" # TODO: Pass this from request
        }
        
        return self.create_booking(
            user_id=user_id,
            booking_type="flight",
            total_amount=check_result['price'],
            currency=check_result['currency'],
            notes="Created via API",
            booking_details=booking_details
        )

    def get_booking_by_id(self, booking_id: str) -> Booking:
        return GetBookingByID(self.db).execute(booking_id)

    def get_booking_by_reference(self, reference_code: str) -> Booking:
        return GetBookingByReference(self.db).execute(reference_code)
    
    def get_user_bookings(self, user_id: str) -> list[Booking]:
        return GetUserBookings(self.db).execute(user_id)

    def update_booking_status(self, booking_id: str, new_status: str) -> Booking:
        return UpdateBookingStatus(self.db).execute(booking_id, new_status)
    
    def add_passenger(self, booking_id: str, passenger_data: dict) -> Passenger:
        return AddPassengerToBooking(self.db).execute(booking_id, passenger_data)
        
    def cancel_booking(self, booking_id: str, reason: str = None) -> Booking:
        return CancelBooking(self.db).execute(booking_id, reason)
