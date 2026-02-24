import requests
from flask import current_app
import logging
from app.repository.flight.exceptions import FlightServiceError
from app.repository.flight.requestDTO import FlightSearchRequestDTO
logger = logging.getLogger(__name__)

class KayakFlightAdapter:
    def __init__(self):
        self.api_key = current_app.config.get('RAPIDAPI_KEY')
        self.api_host = current_app.config.get('RAPIDAPI_HOST', 'kayak-flight-search-api.p.rapidapi.com')
        self.base_url = f"https://{self.api_host}"
        
        if not self.api_key:
            logger.warning("RAPIDAPI_KEY is not set. Flight search may fail if not mocking.")

    def search_flights(self, params: FlightSearchRequestDTO ) -> dict:
        endpoint = f"{self.base_url}/search-flights"
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
        
        query_params = {
            "origin": params.origin,
            "destination": params.destination,
            "date": params.departure_date, # rapidapi expects 'date' not 'departure_date'
        }
        if params.return_date:
            query_params["returnDate"] = params.return_date # camelCase for API
            
        if params.filterParams is not None and len(params.filterParams) > 0:
            # We take the first filter params object as per common single-request usage
            filter_params_dto = params.filterParams[0]
            if filter_params_dto.fs:
                query_params["fs"] = filter_params_dto.fs
                
        # searchMetadata and userSearchParams are typically not direct URL params but might be needed 
        # in specific Kayak endpoints. Assuming they are mapped to specific API fields if present
        # but for standard RapidAPI GET /search-flights, only origin, destination, date, returnDate, fs are used.
        # So we omit them from query_params unless explicitly needed by the specific Kayak implementation.
        
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
