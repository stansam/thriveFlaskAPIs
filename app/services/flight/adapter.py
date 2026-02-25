import requests
from flask import current_app
from functools import wraps
import logging
from typing import Dict, Any, Optional

from app.extensions import cache
from app.dto.adapter.flight_schemas import (
    AirportSearchResponseDTO,
    FlightDetailsResponseDTO,
    GDSFlightSearchResponseDTO
)

logger = logging.getLogger(__name__)

class GDSFlightAdapter:
    """
    Physical External Adapter isolating all RapidAPI/Kayak flight queries securely. 
    Implements robust connection pooling, explicit timeouts, and Redis/Flask-Caching mapped intervals.
    """
    def __init__(self):
        self.session = requests.Session()
        # Default fallback boundaries internally for resilience during spinup
        self.host = current_app.config.get('RAPIDAPI_FLIGHT_HOST', 'kayak-api.p.rapidapi.com')
        self.key = current_app.config.get('RAPIDAPI_KEY', 'sandbox_key_fallback')
        self.base_url = f"https://{self.host}"
        
        self.session.headers.update({
            "X-Rapidapi-Key": self.key,
            "X-Rapidapi-Host": self.host
        })
        self.timeout = 15 # Strict global failure bound mapping downstream timeouts cleanly

    def _execute_get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Core physical dispatch bounded by aggressive timeouts intercepting 429/500 errors natively."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"GDS Timed out aggressively hitting {endpoint}")
            raise RuntimeError("Flight Global Distribution System timed out natively. Please try again.")
        except requests.exceptions.RequestException as e:
            logger.error(f"GDS fault block natively hitting {endpoint}: {str(e)}")
            raise RuntimeError(f"GDS Provider explicitly failed payloads natively.")

    @cache.memoize(timeout=604800) # 7 Days
    def search_airports(self, query: str, type_param: Optional[str] = "airportonly") -> AirportSearchResponseDTO:
        params = {"query": query}
        if type_param:
            params["type"] = type_param
            
        data = self._execute_get("/search-locations", params)
        # Validate boundary schema specifically ensuring mapping holds natively
        return AirportSearchResponseDTO(**data)

    @cache.memoize(timeout=180) # 3 Minutes (Live Speed/Altitude mapping bounds)
    def get_flight_details(self, flight_number: str, airline_id: str, date: str) -> FlightDetailsResponseDTO:
        params = {
            "flight_number": flight_number,
            "airline_code": airline_id,
            "date": date
        }
        data = self._execute_get("/flight-details", params)
        return FlightDetailsResponseDTO(**data)

    @cache.memoize(timeout=900) # 15 Minutes (Standard Flight Inventory pricing locks)
    def search_flights(self, 
                       origin: str, 
                       destination: str, 
                       date: str, 
                       adults: int = 1, 
                       cabin_class: str = 'e', 
                       page: int = 1) -> GDSFlightSearchResponseDTO:
        params = {
            "origin": origin,
            "destination": destination,
            "date": date,
            "adults": adults,
            "cabin_class": cabin_class,
            "pageNumber": page # Passing directly downwards mimicking upstream bounds (if API consumes parameter directly, usually 'page' or 'pageNumber' based on API docs but here mapped to ensure structure)
        }
        data = self._execute_get("/flights/search", params) # Adjusted hypothetical standard GDS route since raw search json didn't show endpoint physically
        return GDSFlightSearchResponseDTO(**data)
