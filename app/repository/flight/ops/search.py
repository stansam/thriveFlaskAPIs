from app.repository.flight.adapters.kayak import KayakFlightAdapter
from app.repository.flight.mapper import ResponseMapper
from app.utils.cache import cache
import hashlib
from app.repository.flight.requestDTO import FlightSearchRequestDTO
from app.repository.flight.structure import SearchFlightResponseDTO

import logging

logger = logging.getLogger(__name__)

class SearchFlights:
    def execute(self, params: FlightSearchRequestDTO) -> SearchFlightResponseDTO:
        # Cache Strategy
        # Sort keys to ensure consistency. Use dict representation of Pydantic model
        param_dict = params.model_dump(exclude_none=True)
        param_string = json.dumps(param_dict, sort_keys=True, default=str)
        cache_key = f"flight_search:{hashlib.md5(param_string.encode()).hexdigest()}"
        
        cached_results = cache.get(cache_key)
        if cached_results:
            logger.info(f"Returning cached results for {cache_key}")
            return SearchFlightResponseDTO(**cached_results)

        # Call Adapter
        adapter = KayakFlightAdapter()
        raw_response = adapter.search_flights(params)
        
        # Normalize
        mapper = ResponseMapper()
        results = mapper.normalize_search_response(raw_response)
        
        # Cache
        # Convert Pydantic object to dict for caching
        cache.set(cache_key, results.model_dump(), timeout=900)
        
        return results
