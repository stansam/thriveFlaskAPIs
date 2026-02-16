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

class BookingService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_booking(self, user_id: str, booking_type: str, currency: str = "USD", notes: str = None) -> Booking:
        return CreateBooking(self.db).execute(user_id, booking_type, currency, notes)

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
