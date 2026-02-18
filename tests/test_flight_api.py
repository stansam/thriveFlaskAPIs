import pytest
from unittest.mock import patch, MagicMock
from flask import url_for

def test_search_flights_success(client, app):
    """Test flight search with valid params"""
    
    # Mock Response from Adapter
    mock_response = {
        "results": [
            {
                "resultId": "res1",
                "bookingOptions": [
                    {"bookingUrl": "http://book.com", "totalPrice": 100.0}
                ],
                "legs": [{"id": "leg1"}]
            } 
        ],
        "legs": [
            {
                "id": "leg1",
                "departureAirportCode": "JFK",
                "arrivalAirportCode": "LHR",
                "departureTime": "2025-12-25T10:00:00",
                "arrivalTime": "2025-12-25T20:00:00",
                "duration": 600,
                "stopCount": 0,
                "segments": [{"id": "seg1"}]
            }
        ],
        "segments": [
            {
                "id": "seg1",
                "airlineCode": "BA",
                "flightNumber": "100",
                "departureAirportCode": "JFK",
                "arrivalAirportCode": "LHR",
                "departureTime": "2025-12-25T10:00:00",
                "arrivalTime": "2025-12-25T20:00:00",
                "duration": 600
            }
        ],
        "airlines": [{"code": "BA", "name": "British Airways"}],
        "airports": [{"code": "JFK", "name": "John F Kennedy"}]
    }

    with patch('app.repository.flight.adapters.kayak.KayakFlightAdapter.search_flights') as mock_search:
        mock_search.return_value = mock_response
        
        # We need to mock redis too if it fails connection in test env, 
        # but our utility handles that gracefully (falls back to local).
        
        payload = {
            "origin": "JFK",
            "destination": "LHR",
            "date": "2026-12-25", # Future date
            "passengers": {"adults": 1}
        }
        
        response = client.post('/api/flight/search', json=payload)
        
        assert response.status_code == 200
        data = response.get_json()
        assert "results" in data
        assert len(data['results']) == 1
        assert data['results'][0]['price']['amount'] == 100.0
        assert data['results'][0]['legs'][0]['segments'][0]['carrier']['name'] == "British Airways"

def test_search_flights_validation_error(client):
    """Test flight search with invalid params"""
    payload = {
        "origin": "J", # Invalid length
        "destination": "LHR",
        "date": "2025-12-25"
    }
    response = client.post('/api/flight/search', json=payload)
    assert response.status_code == 400
    
def test_get_details_success(client):
    """Test get flight details endpoint"""
    mock_details = {"id": "123", "status": "L"}
    
    with patch('app.repository.flight.adapters.kayak.KayakFlightAdapter.get_flight_details') as mock_get:
        mock_get.return_value = mock_details
        
        response = client.get('/api/flight/details/123')
        
        assert response.status_code == 200
        assert response.get_json() == mock_details
