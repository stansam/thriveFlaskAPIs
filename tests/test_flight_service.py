import pytest
from datetime import datetime
from unittest.mock import patch
from app.repository.flight.services import FlightService
from app.repository.flight.exceptions import FlightNotFound, SeatNotAvailable
from app.models.enums import BookingStatus

def test_search_flights(db_session):
    with patch('app.repository.flight.services.SearchFlights') as MockSearch:
        mock_instance = MockSearch.return_value
        mock_instance.execute.return_value = [{
            "departure_airport": "JFK",
            "arrival_airport": "LHR",
            "price": 500.0,
            "currency": "USD"
        }]
        
        service = FlightService(db_session)
        results = service.search_flights("JFK", "LHR", "2023-12-25")
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0]['departure_airport'] == "JFK"
        assert results[0]['arrival_airport'] == "LHR"

def test_create_manual_booking_success(db_session):
    service = FlightService(db_session)
    user_id = "test_user_123"
    
    flight_data = {
        "carrier_code": "BA",
        "flight_number": "112",
        "departure_airport": "JFK",
        "arrival_airport": "LHR",
        "departure_time": datetime.now(),
        "arrival_time": datetime.now()
    }
    
    amount = 500.0
    
    booking = service.create_manual_booking(user_id, flight_data, amount, "USD")
    
    assert booking.status == BookingStatus.PAYMENT_PENDING
    assert booking.total_amount == 500.0
    assert booking.user_id == user_id
    
    # Check flight segment
    flight_booking = booking.flight_booking
    assert flight_booking is not None
    assert flight_booking.pnr_reference == "PENDING"
    assert flight_booking.segments.count() == 1
    
    segment = flight_booking.segments.first()
    assert segment.carrier_code == "BA"

    # Check payment
    assert booking.payments.count() == 1
    payment = booking.payments.first()
    assert payment.amount == 500.0

def test_get_flight_not_found(db_session):
    service = FlightService(db_session)
    with pytest.raises(FlightNotFound):
        service.get_flight_by_id("non_existent_flight_id")
