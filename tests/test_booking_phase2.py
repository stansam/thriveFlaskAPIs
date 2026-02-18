import pytest
from unittest.mock import patch, MagicMock
from app.models import Booking, FlightBooking, Passenger
from app.models.enums import BookingStatus

def test_initiate_booking_success(client, user_factory):
    # Create a test user (ifauth middleware is active, we might need token, 
    # but our route handles X-Test-User-ID for testing)
    user = user_factory()
    
    # Mock Flight Details for Price Check
    mock_details = {
        "price": {"amount": 500.0, "currency": "USD"},
        "bookingOptions": [{"totalPrice": 500.0}]
    }
    
    with patch('app.repository.flight.adapters.kayak.KayakFlightAdapter.get_flight_details') as mock_check:
        mock_check.return_value = mock_details
        
        payload = {
            "flight_id": "FL123TOKEN",
            "expected_price": 500.0,
            "currency": "USD",
            "passengers": [
                {
                    "first_name": "Alice",
                    "last_name": "Smith",
                    "dob": "1990-01-01",
                    "gender": "female",
                    "passport_number": "A1234567",
                    "passport_expiry": "2030-01-01"
                }
            ]
        }
        
        headers = {'X-Test-User-ID': user.id}
        response = client.post('/api/booking/initiate', json=payload, headers=headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert "booking_id" in data
        assert data['status'] == "pending"
        assert data['total_amount'] == 500.0
        
        # Verify DB records
        booking_id = data['booking_id']
        from app.extensions import db
        booking = db.session.get(Booking, booking_id)
        assert booking is not None
        assert booking.flight_booking is not None
        assert booking.flight_booking.pnr_reference == "FL123TOKEN"
        assert booking.passengers.count() == 1
        assert booking.passengers[0].first_name == "Alice"

def test_initiate_booking_unavailable(client, user_factory):
    user = user_factory()
    
    # Mock Flight Details raising error or empty
    with patch('app.repository.flight.adapters.kayak.KayakFlightAdapter.get_flight_details') as mock_check:
        from app.repository.flight.exceptions import FlightServiceError
        mock_check.side_effect = FlightServiceError("Flight not found")
        
        payload = {
            "flight_id": "INVALID",
            "expected_price": 100.0,
            "passengers": [{"first_name": "Bob", "last_name": "Jones", "dob": "1980-01-01", "gender": "male", "passport_number": "B123456", "passport_expiry": "2025-01-01"}]
        }
        
        headers = {'X-Test-User-ID': user.id}
        response = client.post('/api/booking/initiate', json=payload, headers=headers)
        
        assert response.status_code == 400
        assert "Flight is no longer available" in response.get_json()['message']
