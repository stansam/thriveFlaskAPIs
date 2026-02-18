import requests
from flask import current_app
import logging
from app.repository.flight.exceptions import FlightServiceError

logger = logging.getLogger(__name__)

class KayakFlightAdapter:
    def __init__(self):
        self.api_key = current_app.config.get('RAPIDAPI_KEY')
        self.api_host = current_app.config.get('RAPIDAPI_HOST', 'kayak-flight-search-api.p.rapidapi.com')
        self.base_url = f"https://{self.api_host}"
        
        if not self.api_key:
            logger.warning("RAPIDAPI_KEY is not set. Flight search may fail if not mocking.")

    def search_flights(self, params: dict) -> dict:
        """
        Executes a flight search against the external API.
        
        Args:
            params (dict): Validated search parameters (origin, destination, date, etc.)
            
        Returns:
            dict: Raw API response (to be processed by mapper)
        """
        endpoint = f"{self.base_url}/search-flights"
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
        
        # Map internal params to external API params
        # Internal: origin, destination, date, cabin_class, passengers
        # External: origin, destination, departureDate, cabinClass, etc.
        
        query_params = {
            "origin": params.get('origin'),
            "destination": params.get('destination'),
            "departureDate": params.get('date'),
            "cabinClass": params.get('cabin_class', 'economy'),
            "currency": params.get('currency', 'USD')
        }
        
        # TODO: Handle passenger counts mapped to userSearchParams if API supports it in query
        # For this specific API, it seems some params might be needing special formatting. 
        # Based on documentation, we pass them as is for simple search.
        
        try:
            logger.info(f"Searching flights: {query_params}")
            response = requests.get(endpoint, headers=headers, params=query_params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"RapidAPI HTTP Error: {e.response.text}")
            raise FlightServiceError(f"Flight search failed: {e.response.status_code}")
    def get_flight_details(self, params: dict) -> dict:
        """
        Fetches detailed flight information.
        """
        # Note: If specific details endpoint exists in RapidAPI, use it.
        # Otherwise, this might need to re-trigger search or use a "poll" endpoint.
        # For this implementation, we assume a '/get-flight-details' endpoint exists 
        # as implied by the project structure/artifacts.
        endpoint = f"{self.base_url}/get-flight-details"
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
        
        try:
            logger.info(f"Fetching flight details: {params}")
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"RapidAPI Details Error: {e}")
            raise FlightServiceError("Flight details service unavailable")
