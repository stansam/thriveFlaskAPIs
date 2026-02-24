from app.repository.flight.adapters.kayak import KayakFlightAdapter
from app.repository.flight.exceptions import FlightServiceError
from app.utils.cache import cache
import logging

logger = logging.getLogger(__name__)

class GetFlightDetails:
    def execute(self, flight_id: str, params: dict = None) -> dict:
        """
        Retrieves flight details. 
        It attempts to find the flight in the cache first (if it was part of a recent search).
        """
        # Logic: 
        # 1. Check if flight_id matches a cached "Detail" key (not implemented yet).
        # 2. Or if flight_id is a key from search results we might need to store them individually.
        # For now, we assume we fetch fresh details from API using the ID/Token.
        
        try:
            adapter = KayakFlightAdapter()
            
            # If params are not provided, we might interpret flight_id as a token 
            # containing necessary info, or pass it as 'id' to the adapter.
            query_params = params or {}
            query_params['id'] = flight_id
            
            raw_details = adapter.get_flight_details(query_params)
            
            # We can normalize this as well if needed. 
            # For now returning raw as per initial step, but ideally normalized.
            # TODO: Add ResponseMapper.normalize_details(raw_details)
            
            return raw_details
            
        except FlightServiceError as e:
            raise e
        except Exception as e:
            logger.error(f"Error fetching flight details: {e}")
            raise FlightServiceError("Failed to retrieve flight details")
