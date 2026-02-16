import pytest
from app.repository.booking.services import BookingService
from app.models.enums import BookingStatus, BookingType, Gender
from app.repository.booking.exceptions import BookingNotFound, InvalidBookingStatus

def test_create_booking(db_session, user_factory):
    user = user_factory()
    service = BookingService(db_session)
    
    booking = service.create_booking(
        user_id=user.id,
        booking_type="flight",
        currency="USD",
        notes="Test booking"
    )
    
    assert booking.id is not None
    assert booking.reference_code.startswith("THRIVE-")
    assert booking.status == BookingStatus.PENDING
    assert booking.booking_type == BookingType.FLIGHT
    assert booking.user_id == user.id

def test_get_booking(db_session, booking_factory):
    booking = booking_factory()
    service = BookingService(db_session)
    
    fetched_booking = service.get_booking_by_id(booking.id)
    assert fetched_booking.id == booking.id
    
    fetched_by_ref = service.get_booking_by_reference(booking.reference_code)
    assert fetched_by_ref.id == booking.id

def test_get_booking_not_found(db_session):
    service = BookingService(db_session)
    with pytest.raises(BookingNotFound):
        service.get_booking_by_id("non-existent-id")

def test_update_status(db_session, booking_factory):
    booking = booking_factory(status=BookingStatus.PENDING)
    service = BookingService(db_session)
    
    updated = service.update_booking_status(booking.id, "confirmed")
    assert updated.status == BookingStatus.CONFIRMED

def test_invalid_status_update(db_session, booking_factory):
    booking = booking_factory()
    service = BookingService(db_session)
    
    with pytest.raises(InvalidBookingStatus):
        service.update_booking_status(booking.id, "invalid_status")

def test_add_passenger(db_session, booking_factory):
    booking = booking_factory()
    service = BookingService(db_session)
    
    passenger_data = {
        "first_name": "John",
        "last_name": "Doe",
        "gender": "male"
    }
    
    passenger = service.add_passenger(booking.id, passenger_data)
    assert passenger.id is not None
    assert passenger.booking_id == booking.id
    assert passenger.first_name == "John"
    assert passenger.gender == Gender.MALE

def test_cancel_booking(db_session, booking_factory):
    booking = booking_factory(status=BookingStatus.CONFIRMED)
    service = BookingService(db_session)
    
    cancelled = service.cancel_booking(booking.id, reason="User request")
    assert cancelled.status == BookingStatus.CANCELLED
    assert "User request" in cancelled.notes

def test_cancel_already_cancelled(db_session, booking_factory):
    booking = booking_factory(status=BookingStatus.CANCELLED)
    service = BookingService(db_session)
    
    with pytest.raises(InvalidBookingStatus):
        service.cancel_booking(booking.id)
