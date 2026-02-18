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

def test_reserve_seat_success(db_session, booking_factory):
    service = FlightService(db_session)
    booking = booking_factory()
    
    flight_data = {
        "carrier_code": "BA",
        "flight_number": "112",
        "departure_airport": "JFK",
        "arrival_airport": "LHR",
        "departure_time": datetime.now(),
        "arrival_time": datetime.now()
    }
    
    flight_booking = service.reserve_seat(booking.id, flight_data, "12A")
    
    assert flight_booking.booking_id == booking.id
    # Check if flight segment was created
    assert flight_booking.segments.count() == 1
    segment = flight_booking.segments.first()
    assert segment.carrier_code == "BA"
    assert segment.seat_assignment == "12A"

def test_reserve_seat_unavailable(db_session, booking_factory):
    service = FlightService(db_session)
    booking = booking_factory()
    
    flight_data = {} # Data doesn't matter for this mock check
    
    with pytest.raises(SeatNotAvailable):
        service.reserve_seat(booking.id, flight_data, "X99")

def test_get_flight_not_found(db_session):
    service = FlightService(db_session)
    with pytest.raises(FlightNotFound):
        service.get_flight_by_id("non_existent_flight_id")
